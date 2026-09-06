"""Per-video DeepLabCut orchestration for the two pretrained BIOMAP projects.

This module never touches the checked-in DeepLabCut projects: it builds a
disposable runtime mirror under ``n8n/biomap_pipeline/results/.work/dlc`` whose
``config.yaml`` carries a portable ``project_path`` (DeepLabCut rewrites that
field to the config's own directory, so the config can only live inside a
project-shaped directory), copies the small YAML files and symlinks the large
snapshot files. Inference itself runs through :mod:`biomap_pipeline.dlc_headless`
inside the configured Conda environment, exactly as the SimBA stage does.

Every scientific parameter comes from the project: ``snapshotindex``,
``TrainingFraction``, ``iteration``, body parts, and cropping are read by
DeepLabCut from the mirrored ``config.yaml``. The only per-model selection made
here is which trained shuffle to run, chosen from repository evidence and
overridable with ``BIOMAP_DLC_PAW_SHUFFLE`` / ``BIOMAP_DLC_FACIAL_SHUFFLE``.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .dlc_csv import DlcCsvError, validate_dlc_csv
from .dlc_merge import index_by_video, video_stem
from .paths import CONTRIBUTION_ROOT, ContributionPaths
from .states import DlcStageError


#: Directory in the checkout that holds both pretrained projects.
DLC_MODELS_DIRNAME = "deeplabcut-models"

#: Marker line the headless runner prints once DeepLabCut returns its scorer.
SCORER_PREFIX = "BIOMAP_DLC_SCORER="

#: Body parts SimBA needs from the PawDigits project (nosetip comes from facial).
PAW_BODY_PARTS = (
    "front_right_finger_tip",
    "right_wrist",
    "front_left_finger_tip",
    "left_wrist",
    "back_right_toe_tip",
    "right_heel",
    "back_left_toe_tip",
    "left_heel",
    "tail_base",
    "back",
)
FACIAL_BODY_PARTS = ("nosetip",)

LFS_POINTER_SIGNATURE = b"version https://git-lfs.github.com/spec/v1"


@dataclass(frozen=True)
class DlcModel:
    """One pretrained DeepLabCut project and the shuffle the pipeline runs."""

    key: str
    label: str
    project_dirname: str
    shuffle: int
    trainingsetindex: int
    required_body_parts: tuple[str, ...]

    def project_dir(self, repository: Path) -> Path:
        return repository / DLC_MODELS_DIRNAME / self.project_dirname

    def tracking_dir(self, paths: ContributionPaths) -> Path:
        return paths.paw_tracking if self.key == "paw" else paths.facial_tracking

    @property
    def lfs_pull_command(self) -> str:
        return f'git lfs pull --include="{DLC_MODELS_DIRNAME}/{self.project_dirname}/**"'


def _shuffle_from_environment(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise DlcStageError(f"{name} must be an integer shuffle number; found {raw!r}") from exc
    if value < 1:
        raise DlcStageError(f"{name} must be a positive shuffle number; found {value}")
    return value


def dlc_models() -> tuple[DlcModel, ...]:
    """The two projects in production order: PawDigits first, then facial.

    Shuffle defaults come from the checked-in projects: PawDigits only has
    shuffle 1. The facial project has shuffles 1 and 2; shuffle 2
    (``snapshot-best-175``) is the later, better-evaluated training and is the
    scorer the PI's analysis script consumes, so it is the default.
    """

    return (
        DlcModel(
            key="paw",
            label="DLC Paw",
            project_dirname="BIOMAP Paw Digits-Megan G-2026-06-10",
            shuffle=_shuffle_from_environment("BIOMAP_DLC_PAW_SHUFFLE", 1),
            trainingsetindex=0,
            required_body_parts=PAW_BODY_PARTS,
        ),
        DlcModel(
            key="facial",
            label="DLC Facial",
            project_dirname="BIOMAP-Megan_G_-2026-03-17",
            shuffle=_shuffle_from_environment("BIOMAP_DLC_FACIAL_SHUFFLE", 2),
            trainingsetindex=0,
            required_body_parts=FACIAL_BODY_PARTS,
        ),
    )


def is_lfs_pointer(path: Path) -> bool:
    try:
        if path.stat().st_size > 1024:
            return False
        with path.open("rb") as handle:
            return handle.read(len(LFS_POINTER_SIGNATURE)) == LFS_POINTER_SIGNATURE
    except OSError:
        return False


def _read_scalar(text: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:[ \t]*(.*?)[ \t]*$", text, flags=re.M)
    if match is None or not match.group(1):
        raise DlcStageError(f"DeepLabCut config.yaml does not define '{key}'")
    return match.group(1).strip().strip("'\"")


def _read_list(text: str, key: str) -> list[str]:
    match = re.search(
        rf"^{re.escape(key)}:[ \t]*\n((?:[ \t]*-[ \t]*.*\n)+)", text, flags=re.M
    )
    if match is None:
        raise DlcStageError(f"DeepLabCut config.yaml does not define the '{key}' list")
    return [line.split("-", 1)[1].strip() for line in match.group(1).splitlines()]


@dataclass(frozen=True)
class DlcProjectLayout:
    """Paths DeepLabCut reads for one shuffle, derived exactly as DLC does."""

    project_dir: Path
    config: Path
    model_folder: Path
    training_set_folder: Path

    @property
    def pytorch_config(self) -> Path:
        return self.model_folder / "train" / "pytorch_config.yaml"

    @property
    def pose_cfg(self) -> Path:
        return self.model_folder / "test" / "pose_cfg.yaml"

    @property
    def metadata(self) -> Path:
        return self.training_set_folder / "metadata.yaml"

    def snapshots(self) -> list[Path]:
        return sorted((self.model_folder / "train").glob("snapshot-*.pt"))


def read_project_layout(project_dir: Path, model: DlcModel) -> DlcProjectLayout:
    """Locate the shuffle's model folder using DeepLabCut's own naming rules."""

    config = project_dir / "config.yaml"
    if not config.is_file():
        raise DlcStageError(
            f"{model.label} failed: DeepLabCut project is missing: {config}",
            next_action=(
                "Restore the checked-in deeplabcut-models directory; the pipeline "
                "only reads the pretrained projects and never recreates them."
            ),
        )
    if is_lfs_pointer(config):
        raise DlcStageError(
            f"{model.label} failed: DeepLabCut config is still a Git LFS pointer: {config}",
            next_action=f"From the repository root run: {model.lfs_pull_command}",
        )
    text = config.read_text(encoding="utf-8")
    task = _read_scalar(text, "Task")
    date = _read_scalar(text, "date")
    iteration = _read_scalar(text, "iteration")
    fractions = _read_list(text, "TrainingFraction")
    try:
        train_fraction = float(fractions[model.trainingsetindex])
    except (IndexError, ValueError) as exc:
        raise DlcStageError(
            f"DeepLabCut config {config} has no TrainingFraction for "
            f"trainingsetindex={model.trainingsetindex}"
        ) from exc
    # Mirrors deeplabcut.utils.auxiliaryfunctions.get_model_folder and
    # get_training_set_folder for the PyTorch engine.
    model_folder = (
        project_dir
        / "dlc-models-pytorch"
        / f"iteration-{iteration}"
        / f"{task}{date}-trainset{int(train_fraction * 100)}shuffle{model.shuffle}"
    )
    training_set_folder = (
        project_dir / "training-datasets" / f"iteration-{iteration}"
        / f"UnaugmentedDataSet_{task}{date}"
    )
    return DlcProjectLayout(project_dir, config, model_folder, training_set_folder)


def validate_project(project_dir: Path, model: DlcModel) -> DlcProjectLayout:
    """Refuse to start inference unless every file DeepLabCut needs is real."""

    layout = read_project_layout(project_dir, model)
    if not layout.model_folder.is_dir():
        raise DlcStageError(
            f"{model.label}: trained shuffle {model.shuffle} is not present at "
            f"{layout.model_folder}",
            next_action=(
                "Confirm the shuffle number for this project or set "
                f"BIOMAP_DLC_{model.key.upper()}_SHUFFLE to the trained shuffle."
            ),
        )
    required = [layout.pytorch_config, layout.pose_cfg, layout.metadata]
    missing = [path for path in required if not path.is_file()]
    if missing:
        raise DlcStageError(
            f"{model.label}: DeepLabCut files are missing: "
            + ", ".join(str(path) for path in missing),
            next_action=f"From the repository root run: {model.lfs_pull_command}",
        )
    snapshots = layout.snapshots()
    if not snapshots:
        raise DlcStageError(
            f"{model.label}: no snapshot-*.pt files under {layout.model_folder / 'train'}",
            next_action=f"From the repository root run: {model.lfs_pull_command}",
        )
    pointers = [path for path in [*required, *snapshots] if is_lfs_pointer(path)]
    if pointers:
        raise DlcStageError(
            f"{model.label}: required DeepLabCut files are still Git LFS pointers: "
            + ", ".join(str(path.relative_to(project_dir)) for path in pointers),
            next_action=f"From the repository root run: {model.lfs_pull_command}",
        )
    return layout


def _clear_directory(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _atomic_copy(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{destination.name}.", suffix=".tmp",
            dir=destination.parent, delete=False,
        ) as handle:
            temporary = handle.name
        shutil.copy2(source, temporary)
        os.replace(temporary, destination)
    except Exception:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)
        raise
    return destination


#: ``runner(runtime_config, video_path, model, destfolder) -> scorer`` runs the
#: analysis and returns the DeepLabCut scorer string it used.
Runner = Callable[[Path, Path, "DlcModel", Path], str]


class DlcStage:
    """Run one pretrained DeepLabCut model on one video and publish its CSV."""

    def __init__(
        self,
        repository: Path | str,
        *,
        contribution_paths: ContributionPaths | None = None,
        dlc_environment: str = "biomap-dlc",
        runner: Runner | None = None,
        frame_counter: Callable[[Path], int | None] | None = None,
    ) -> None:
        self.repository = Path(repository).resolve()
        self.paths = contribution_paths or ContributionPaths()
        self.dlc_environment = dlc_environment
        self.runner = runner or self._run_headless
        self.frame_counter = frame_counter or _count_frames_if_avi

    # ----------------------------------------------------------------- cache
    def cached_output(self, video_path: Path, model: DlcModel) -> Path | None:
        """Return a verified existing CSV for this video, or ``None``."""

        stem = video_path.stem
        tracking_dir = model.tracking_dir(self.paths)
        if not tracking_dir.is_dir():
            return None
        try:
            index = index_by_video(tracking_dir)
        except DlcCsvError as exc:
            raise DlcStageError(
                f"{model.label}: ambiguous cached outputs: {exc}",
                next_action=f"Remove the duplicate CSVs under {tracking_dir} and rerun.",
            ) from exc
        candidate = index.get(stem)
        if candidate is None:
            return None
        try:
            self._validate_output(candidate, video_path, model)
        except DlcCsvError as exc:
            print(f"[{model.label}] cached output invalid; rerunning: {exc}", flush=True)
            return None
        return candidate.resolve()

    def _validate_output(self, csv_path: Path, video_path: Path, model: DlcModel) -> None:
        stem = video_path.stem
        if video_stem(csv_path) != stem:
            raise DlcCsvError(
                f"{csv_path.name} does not belong to video '{stem}'"
            )
        try:
            validate_dlc_csv(
                csv_path,
                required_body_parts=model.required_body_parts,
                expected_frame_count=self.frame_counter(video_path),
            )
        except DlcCsvError as exc:
            empty = count_empty_tracking_cells(csv_path)
            if empty and "Non-numeric tracking value" in str(exc):
                raise DlcCsvError(
                    f"{exc}. DeepLabCut left {empty} tracking cell(s) empty, which is "
                    "how it records keypoints below its detection threshold (NaN). "
                    "The pipeline's tracking contract rejects NaN, so a NaN policy "
                    "(for example SimBA's import interpolation) must be decided "
                    "before this output can continue."
                ) from exc
            raise

    # --------------------------------------------------------------- runtime
    def _prepare_runtime_project(self, layout: DlcProjectLayout, model: DlcModel) -> Path:
        """Mirror the read-only project so DeepLabCut can resolve ``project_path``."""

        runtime = self.paths.dlc_runtime_project(model.key)
        _clear_directory(runtime)
        for source_dir, files in (
            (layout.model_folder / "train", [layout.pytorch_config, *layout.snapshots()]),
            (layout.model_folder / "test", [layout.pose_cfg]),
            (layout.training_set_folder, [layout.metadata]),
        ):
            target_dir = runtime / source_dir.relative_to(layout.project_dir)
            target_dir.mkdir(parents=True, exist_ok=True)
            for source in files:
                target = target_dir / source.name
                if source.suffix == ".pt":
                    target.symlink_to(source.resolve())
                else:
                    shutil.copy2(source, target)
        text = layout.config.read_text(encoding="utf-8")
        text, replaced = re.subn(
            r"^project_path:.*$", f"project_path: {runtime.resolve()}", text,
            count=1, flags=re.M,
        )
        if replaced != 1:
            raise DlcStageError(
                f"{model.label}: cannot rewrite project_path in {layout.config}"
            )
        runtime_config = runtime / "config.yaml"
        runtime_config.write_text(text, encoding="utf-8")
        return runtime_config

    def _conda_command(
        self, runtime_config: Path, video_path: Path, model: DlcModel, destfolder: Path
    ) -> list[str]:
        conda = shutil.which("conda")
        if conda is None:
            raise DlcStageError(
                f"{model.label}: conda is not on PATH, so the "
                f"{self.dlc_environment} environment cannot be used",
                next_action="Start n8n from a shell where `conda` is available.",
            )
        command = [
            conda, "run", "--no-capture-output", "-n", self.dlc_environment,
            "python", "-u", "-m", "biomap_pipeline.dlc_headless",
            "--config", str(runtime_config),
            "--video", str(video_path),
            "--shuffle", str(model.shuffle),
            "--trainingsetindex", str(model.trainingsetindex),
            "--destfolder", str(destfolder),
            "--label", model.label,
        ]
        # CPU is deliberate: these checkpoints were serialized on CUDA, and
        # Mac hosts cannot deserialize them safely without an explicit map
        # device. Operators may opt into another known-good device explicitly.
        device = os.environ.get("BIOMAP_DLC_DEVICE", "cpu").strip() or "cpu"
        command.extend(["--device", device])
        batch_size = os.environ.get("BIOMAP_DLC_BATCH_SIZE", "").strip()
        if batch_size:
            command.extend(["--batch-size", batch_size])
        return command

    def _subprocess_environment(self) -> dict[str, str]:
        environment = os.environ.copy()
        environment["PYTHONUNBUFFERED"] = "1"
        # Apple Silicon: DeepLabCut's dlcrnet uses one operator MPS lacks
        # (aten::_upsample_bilinear2d_aa); PyTorch must fall back to CPU for it.
        environment.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
        environment.setdefault("TQDM_MININTERVAL", "5")
        # ``python -m biomap_pipeline.dlc_headless`` must import this package
        # regardless of the working directory the subprocess inherits.
        package_parent = str(CONTRIBUTION_ROOT)
        existing = environment.get("PYTHONPATH", "")
        environment["PYTHONPATH"] = (
            package_parent if not existing else f"{package_parent}{os.pathsep}{existing}"
        )
        environment["MPLCONFIGDIR"] = str(self.paths.cache / "matplotlib")
        environment["XDG_CACHE_HOME"] = str(self.paths.cache / "xdg")
        for name in ("MPLCONFIGDIR", "XDG_CACHE_HOME"):
            Path(environment[name]).mkdir(parents=True, exist_ok=True)
        return environment

    def _run_headless(
        self, runtime_config: Path, video_path: Path, model: DlcModel, destfolder: Path
    ) -> str:
        command = self._conda_command(runtime_config, video_path, model, destfolder)
        process = subprocess.Popen(
            command,
            cwd=self.paths.root,
            env=self._subprocess_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        scorer: str | None = None
        output_tail: deque[str] = deque(maxlen=20)
        assert process.stdout is not None
        pending = b""
        # BufferedReader.read(size) may wait for the whole requested size;
        # read1() returns bytes currently available from the pipe so DLC/tqdm
        # progress reaches n8n's tee as it is produced.
        read_available = getattr(process.stdout, "read1", process.stdout.read)
        while True:
            chunk = read_available(4096)
            if not chunk:
                break
            pending += chunk
            *segments, pending = re.split(rb"\r\n|\r|\n", pending)
            for segment in segments:
                line = segment.decode("utf-8", errors="replace").rstrip()
                if line.strip() and not line.startswith(SCORER_PREFIX):
                    output_tail.append(line)
                scorer = self._emit_line(segment, model, scorer)
        if pending:
            line = pending.decode("utf-8", errors="replace").rstrip()
            if line.strip() and not line.startswith(SCORER_PREFIX):
                output_tail.append(line)
            scorer = self._emit_line(pending, model, scorer)
        returncode = process.wait()
        if returncode != 0:
            detail = " | ".join(output_tail) or "no diagnostic output was emitted"
            raise DlcStageError(
                f"{model.label} failed: headless DeepLabCut exited with status "
                f"{returncode}: {detail}",
                next_action=(
                    f"Fix the DeepLabCut error shown in the live log for {model.label} "
                    f"(environment {self.dlc_environment}), then rerun with --resume."
                ),
            )
        if not scorer:
            raise DlcStageError(
                f"{model.label} failed: DeepLabCut did not report its scorer",
                next_action="Inspect the live log for the DeepLabCut output, then rerun.",
            )
        return scorer

    @staticmethod
    def _emit_line(segment: bytes, model: DlcModel, scorer: str | None) -> str | None:
        line = segment.decode("utf-8", errors="replace").rstrip()
        if not line.strip():
            return scorer
        if line.startswith(SCORER_PREFIX):
            return line[len(SCORER_PREFIX):].strip()
        if line.startswith("[Python]"):
            print(line, flush=True)
        else:
            print(f"[{model.label}] {line}", flush=True)
        return scorer

    # ------------------------------------------------------------------ run
    def ensure(self, video_path: Path | str, model: DlcModel, *, resume: bool) -> Path:
        """Return the exact tracking CSV for this video, running DLC if needed."""

        video_path = Path(video_path).resolve()
        if resume:
            cached = self.cached_output(video_path, model)
            if cached is not None:
                print(f"[{model.label}] SKIP_CACHED: {cached}", flush=True)
                return cached
        print(f"[{model.label}] START", flush=True)
        default_next_action = (
            f"Review the {model.label} error in the live log, correct the input or "
            f"environment ({self.dlc_environment}), then rerun with --resume."
        )
        try:
            return self._run(video_path, model)
        except DlcStageError as exc:
            print(f"[{model.label}] FAIL: {exc}", flush=True)
            if exc.next_action is None:
                exc.next_action = default_next_action
            raise
        except (DlcCsvError, OSError) as exc:
            print(f"[{model.label}] FAIL: {exc}", flush=True)
            raise DlcStageError(
                f"{model.label} failed: {exc}", next_action=default_next_action
            ) from exc

    def _run(self, video_path: Path, model: DlcModel) -> Path:
        stem = video_path.stem
        if not video_path.is_file():
            raise DlcStageError(f"{model.label} failed: source video is missing: {video_path}")
        layout = validate_project(model.project_dir(self.repository), model)
        runtime_config = self._prepare_runtime_project(layout, model)
        destfolder = self.paths.dlc_predictions(model.key, stem)
        _clear_directory(destfolder)
        print(
            f"[{model.label}] project {layout.project_dir.name}; shuffle {model.shuffle}; "
            f"model folder {layout.model_folder.relative_to(layout.project_dir)}",
            flush=True,
        )

        scorer = self.runner(runtime_config, video_path, model, destfolder)

        candidates = sorted(destfolder.glob(f"{stem}DLC_*.csv"))
        expected = destfolder / f"{stem}{scorer}.csv"
        if expected not in candidates or len(candidates) != 1:
            names = ", ".join(path.name for path in candidates) or "none"
            raise DlcStageError(
                f"{model.label} failed: expected exactly one CSV named "
                f"{expected.name} in {destfolder}; found: {names}",
                next_action=f"Inspect {destfolder} and rerun {model.label} with --resume.",
            )
        self._validate_output(expected, video_path, model)
        published = self._publish(expected, model, stem)
        print(f"[{model.label}] PASS: {published}", flush=True)
        return published

    def _publish(self, csv_path: Path, model: DlcModel, stem: str) -> Path:
        tracking_dir = model.tracking_dir(self.paths)
        tracking_dir.mkdir(parents=True, exist_ok=True)
        for stale in sorted(tracking_dir.iterdir()):
            if stale.is_file() and video_stem(stale) == stem and stale.name != csv_path.name:
                print(f"[{model.label}] removing superseded output {stale.name}", flush=True)
                stale.unlink()
        meta = csv_path.with_name(csv_path.stem + "_meta.pickle")
        if meta.is_file():
            _atomic_copy(meta, tracking_dir / meta.name)
        destination = _atomic_copy(csv_path, tracking_dir / csv_path.name).resolve()
        validate_dlc_csv(destination, required_body_parts=model.required_body_parts)
        return destination


def count_empty_tracking_cells(csv_path: Path) -> int:
    """Number of empty coordinate cells in a DLC CSV (pandas writes NaN as '')."""

    import csv

    try:
        with csv_path.open("r", newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.reader(handle))
    except OSError:
        return 0
    return sum(1 for row in rows[3:] for cell in row[1:] if not cell.strip())


def _count_frames_if_avi(video_path: Path) -> int | None:
    """Frame count from the AVI header, or ``None`` when it cannot be read.

    The SimBA stage enforces the frame count against the merged CSV with its
    own error reporting; here an unreadable header only disables the early
    check rather than failing the DeepLabCut stage.
    """

    if video_path.suffix.lower() != ".avi":
        return None
    from .simba_stage import SimbaStageError, count_avi_frames

    try:
        return count_avi_frames(video_path)
    except SimbaStageError as exc:
        print(f"[DLC] frame count unavailable from AVI header; SimBA will verify it: {exc}", flush=True)
        return None
