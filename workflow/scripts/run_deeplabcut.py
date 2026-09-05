#!/usr/bin/env python3
"""Run one BIOMAP DeepLabCut model and create a predictably named CSV."""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a trained DeepLabCut project on one video."
    )
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--shuffle", default=1, type=int)
    parser.add_argument("--trainingsetindex", default=0, type=int)
    parser.add_argument("--batch-size", default=1, type=int)
    return parser.parse_args()


def require_file(path: Path, label: str) -> Path:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    return path


def is_lfs_pointer(path: Path) -> bool:
    if path.stat().st_size > 1024:
        return False
    return path.read_bytes().startswith(b"version https://git-lfs.github.com/spec/v1")


def validate_model_files(project_dir: Path, model_config: Path) -> None:
    snapshots = list(project_dir.glob("dlc-models-pytorch/**/snapshot*.pt"))
    if not snapshots:
        raise FileNotFoundError(
            f"No PyTorch snapshots were found beneath {project_dir}. "
            "Download the repository's Git LFS model files before running the workflow."
        )

    pointers = [path for path in [model_config, *snapshots] if is_lfs_pointer(path)]
    if pointers:
        relative_project = project_dir.name
        raise RuntimeError(
            "Required DeepLabCut files are still Git LFS pointers. From the repository "
            "root, download this model with:\n"
            f"git lfs pull --include=\"deeplabcut-models/{relative_project}/**\""
        )


def portable_config(source: Path, project_dir: Path, destination: Path) -> None:
    with source.open("r", encoding="utf-8") as handle:
        project_config = yaml.safe_load(handle)
    project_config["project_path"] = str(project_dir)
    with destination.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(project_config, handle, sort_keys=False)


def main() -> None:
    args = parse_args()
    model_config = require_file(args.config, "Model config")
    video = require_file(args.video, "Input video")
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    project_dir = model_config.parent
    validate_model_files(project_dir, model_config)

    # Import only after validating paths so setup errors remain easy to understand.
    import deeplabcut

    with tempfile.TemporaryDirectory(
        prefix=f".{output.stem}-", dir=output.parent
    ) as temporary_directory:
        temporary_directory = Path(temporary_directory)
        runtime_config = temporary_directory / "config.yaml"
        predictions_dir = temporary_directory / "predictions"
        predictions_dir.mkdir()
        portable_config(model_config, project_dir, runtime_config)

        deeplabcut.analyze_videos(
            str(runtime_config),
            [str(video)],
            videotype=video.suffix,
            shuffle=args.shuffle,
            trainingsetindex=args.trainingsetindex,
            save_as_csv=True,
            destfolder=str(predictions_dir),
            batchsize=args.batch_size,
            device=args.device,
        )

        csv_files = sorted(predictions_dir.glob(f"{video.stem}*.csv"))
        if len(csv_files) != 1:
            found = ", ".join(path.name for path in csv_files) or "none"
            raise RuntimeError(
                "Expected exactly one DeepLabCut CSV for "
                f"{video.name}, but found: {found}"
            )
        shutil.copy2(csv_files[0], output)

    print(f"Saved standardized DeepLabCut output: {output}")


if __name__ == "__main__":
    main()
