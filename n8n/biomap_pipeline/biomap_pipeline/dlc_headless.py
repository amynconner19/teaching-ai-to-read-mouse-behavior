"""Run one pretrained DeepLabCut project headlessly inside ``BIOMAP_DLC_ENV``.

This is the exact call the manual GUI "Analyze videos" step performs. It is
invoked by :class:`biomap_pipeline.dlc_stage.DlcStage` through ``conda run`` and
prints ``BIOMAP_DLC_SCORER=<scorer>`` so the orchestrator can locate the CSV
DeepLabCut wrote (``<video stem><scorer>.csv`` inside ``--destfolder``) without
guessing a scorer name.
"""

from __future__ import annotations

import argparse
from pathlib import Path


SCORER_PREFIX = "BIOMAP_DLC_SCORER="


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--shuffle", type=int, required=True)
    parser.add_argument("--trainingsetindex", type=int, default=0)
    parser.add_argument("--destfolder", type=Path, required=True)
    parser.add_argument("--label", default="DLC")
    parser.add_argument(
        "--device", default="cpu",
        help="PyTorch inference device (defaults to cpu; no automatic GPU selection)",
    )
    parser.add_argument(
        "--batch-size", type=int, default=None,
        help="Override the project's batch_size (performance only)",
    )
    return parser


def analyze(args: argparse.Namespace) -> str:
    config = args.config.resolve()
    video = args.video.resolve()
    destfolder = args.destfolder.resolve()
    if not config.is_file():
        raise FileNotFoundError(f"Runtime DeepLabCut config is missing: {config}")
    if not video.is_file():
        raise FileNotFoundError(f"Source video is missing: {video}")
    destfolder.mkdir(parents=True, exist_ok=True)

    try:
        import deeplabcut
    except ImportError as exc:
        raise RuntimeError(
            "The configured DeepLabCut environment cannot import deeplabcut: "
            f"{exc}"
        ) from exc

    print("[Python] DeepLabCut imported", flush=True)
    device = args.device
    print(f"DeepLabCut {deeplabcut.__version__}; device {device}", flush=True)
    keyword_arguments = {
        "video_extensions": video.suffix.lower(),
        "shuffle": args.shuffle,
        "trainingsetindex": args.trainingsetindex,
        "save_as_csv": True,
        "destfolder": str(destfolder),
        "device": device,
    }
    if args.batch_size is not None:
        keyword_arguments["batch_size"] = args.batch_size
    scorer = deeplabcut.analyze_videos(str(config), [str(video)], **keyword_arguments)
    if not isinstance(scorer, str) or not scorer:
        raise RuntimeError("deeplabcut.analyze_videos did not return the scorer name")
    return scorer


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        scorer = analyze(args)
    except Exception as exc:
        print(f"DeepLabCut failed: {exc}", flush=True)
        return 1
    print(f"{SCORER_PREFIX}{scorer}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
