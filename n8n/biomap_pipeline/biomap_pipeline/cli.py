"""Command-line entry point for the n8n-contained BIOMAP contribution."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .dlc_csv import DlcCsvError, validate_dlc_csv
from .dlc_merge import index_by_video, merge_paw_and_facial
from .dlc_stage import DlcModel, DlcStage, dlc_models
from .paths import ContributionPaths, repository_root
from .simba_stage import (
    REQUIRED_BODY_PARTS,
    SimbaStage,
    SimbaStageResult,
)
from .simulate import (
    DEFAULT_VIDEO_STEM,
    SIMULATED_STATES,
    SIMULATION_ENV_VAR,
    SIMULATION_ENV_VALUE,
    SimulationDisabled,
    parse_state,
    simulate_state,
)
from .states import BiomapError, DlcStageError, PrerequisiteRequired, SimbaStageError, StageState
from .status_report import StatusReporter, record_for_state


VIDEO_SUFFIXES = {".avi", ".mp4", ".mov", ".mkv"}


def _videos(video_dir: Path) -> list[Path]:
    if not video_dir.is_dir():
        raise SimbaStageError(f"Video directory does not exist: {video_dir}")
    videos = sorted(
        path for path in video_dir.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES
    )
    if not videos:
        raise SimbaStageError(f"No supported videos found in {video_dir}")
    return videos


def _tracking_indexes(paths: ContributionPaths) -> tuple[dict[str, Path], dict[str, Path]]:
    paw = index_by_video(paths.paw_tracking) if paths.paw_tracking.is_dir() else {}
    facial = index_by_video(paths.facial_tracking) if paths.facial_tracking.is_dir() else {}
    return paw, facial


def _prepare_merged(
    video_path: Path,
    paths: ContributionPaths,
    paw: dict[str, Path],
    facial: dict[str, Path],
    *,
    resume: bool,
) -> Path:
    stem = video_path.stem
    destination = paths.merged_csv(stem)
    if resume and destination.is_file():
        try:
            merged = validate_dlc_csv(destination, required_body_parts=REQUIRED_BODY_PARTS)
            if merged.body_parts != REQUIRED_BODY_PARTS:
                raise DlcCsvError(
                    f"cached merge body-part order is {merged.body_parts}; "
                    f"expected {REQUIRED_BODY_PARTS}"
                )
        except DlcCsvError as exc:
            print(f"[3] Merge cached result invalid; rebuilding: {exc}", flush=True)
        else:
            cached_path = destination.resolve()
            print(f"[Merge] SKIP_CACHED: {cached_path}", flush=True)
            return cached_path

    missing = []
    if stem not in paw:
        missing.append(f"PawDigits CSV under {paths.paw_tracking}")
    if stem not in facial:
        missing.append(f"facial CSV under {paths.facial_tracking}")
    if missing:
        raise DlcCsvError(
            f"Tracking input missing for {stem}; DLC output missing: "
            + "; ".join(missing)
        )

    print(f"[Merge] START: {paw[stem].resolve()} + {facial[stem].resolve()}", flush=True)
    merged_path = merge_paw_and_facial(
        paw[stem], facial[stem], destination, expected_video_stem=stem
    )
    print(f"[Merge] PASS: {merged_path}", flush=True)
    return merged_path


def _tracking_inputs(
    video_path: Path,
    paths: ContributionPaths,
    paw: dict[str, Path],
    facial: dict[str, Path],
    *,
    dlc: DlcStage | None,
    resume: bool,
    demo: bool,
) -> dict[str, Path]:
    """Obtain both DeepLabCut CSVs for one video, running DLC when required.

    With a :class:`DlcStage` (production ``analyze``) each model is executed
    in order unless ``resume`` finds a verified cached output. Without one
    (``--demo``) only cached outputs are accepted and DeepLabCut never runs.
    """

    stem = video_path.stem
    outputs: dict[str, Path] = {}
    for model in dlc_models():
        cached = paw if model.key == "paw" else facial
        if dlc is not None:
            outputs[model.key] = dlc.ensure(video_path, model, resume=resume)
            cached[stem] = outputs[model.key]
            continue
        existing = cached.get(stem)
        if existing is None:
            reason = "; --demo never runs DeepLabCut" if demo else ""
            raise DlcCsvError(
                f"Tracking input missing for {stem}; DLC output missing: "
                f"{model.label} CSV under {model.tracking_dir(paths)}{reason}"
            )
        outputs[model.key] = existing.resolve()
        print(f"[{model.label}] PASS: {outputs[model.key]} (cached DeepLabCut output)", flush=True)
    return outputs


def _handoff_to_simba(
    *,
    video_path: Path,
    paths: ContributionPaths,
    paw: dict[str, Path],
    facial: dict[str, Path],
    stage: SimbaStage,
    resume: bool,
    dlc: DlcStage | None = None,
    demo: bool = False,
) -> tuple[Path, SimbaStageResult]:
    """Run DLC (unless cached), merge the exact outputs, then invoke SimBA.

    There is deliberately no SimBA-side lookup. The exact CSV paths returned by
    the DLC stage feed ``_prepare_merged``, and the ``Path`` it returns is
    logged and passed unchanged to ``SimbaStage.run``.
    """

    stem = video_path.stem
    tracking = _tracking_inputs(
        video_path, paths, paw, facial, dlc=dlc, resume=resume, demo=demo
    )
    merged_path = _prepare_merged(
        video_path, paths, {stem: tracking["paw"]}, {stem: tracking["facial"]},
        resume=resume,
    )
    print(f"[SimBA] INPUT: {merged_path}", flush=True)
    simba_result = stage.run(
        video_path=video_path, merged_csv=merged_path, resume=resume
    )
    return merged_path, simba_result


def analyze(args: argparse.Namespace) -> int:
    paths = ContributionPaths()
    reporter = StatusReporter(paths.run_status)
    try:
        checkout = repository_root()
        videos = _videos(args.video_dir)
        paw, facial = _tracking_indexes(paths)
    except (DlcCsvError, SimbaStageError, FileNotFoundError) as exc:
        reporter.emit(
            record_for_state(
                StageState.FAIL, video_stem=None, error=str(exc)
            )
        )
        print(f"BIOMAP FAIL: {exc}", flush=True)
        return 1

    stage = SimbaStage(
        checkout,
        contribution_paths=paths,
        simba_environment=os.environ.get("BIOMAP_SIMBA_ENV", "biomap-simba"),
    )
    demo = bool(getattr(args, "demo", False))
    resume = bool(args.resume or demo)
    dlc = None if demo else DlcStage(
        checkout,
        contribution_paths=paths,
        dlc_environment=os.environ.get("BIOMAP_DLC_ENV", "biomap-dlc"),
    )
    if demo:
        print("[DLC] --demo: cache-only mode; DeepLabCut will not run", flush=True)
    for video_path in videos:
        video_stem = video_path.stem
        reporter.emit(
            record_for_state(StageState.READY, video_stem=video_stem)
        )
        try:
            _merged, result = _handoff_to_simba(
                video_path=video_path,
                paths=paths,
                paw=paw,
                facial=facial,
                stage=stage,
                resume=resume,
                dlc=dlc,
                demo=demo,
            )
        except PrerequisiteRequired as exc:
            reporter.emit(
                record_for_state(
                    exc.state,
                    video_stem=video_stem,
                    error=exc.detail or None,
                )
            )
            return 2
        except (DlcCsvError, BiomapError, FileNotFoundError) as exc:
            reporter.emit(
                record_for_state(
                    StageState.FAIL,
                    video_stem=video_stem,
                    error=str(exc),
                    next_action=getattr(exc, "next_action", None),
                )
            )
            print(f"BIOMAP FAIL: {exc}", flush=True)
            return 1
        reporter.emit(
            record_for_state(
                result.status,
                video_stem=video_stem,
                output_path=result.output,
            )
        )
    return 0


def run_dlc(args: argparse.Namespace) -> int:
    """Run only the pretrained PawDigits DeepLabCut stage.

    This deliberately small entry point is what the simplified n8n workflow
    invokes while DeepLabCut stability is evaluated. It does not construct or
    execute the facial, merge, SimBA, or state-routing stages.
    """

    print("[n8n] DeepLabCut command started", flush=True)
    try:
        checkout = repository_root()
        videos = _videos(args.video_dir)
        paw_model = next(model for model in dlc_models() if model.key == "paw")
        stage = DlcStage(
            checkout,
            contribution_paths=ContributionPaths(),
            dlc_environment=os.environ.get("BIOMAP_DLC_ENV", "biomap-dlc"),
        )
        for video_path in videos:
            stage.ensure(video_path, paw_model, resume=args.resume)
    except (DlcCsvError, BiomapError, FileNotFoundError, StopIteration) as exc:
        print(f"[DLC Paw] FAIL: {exc}", flush=True)
        return 1
    return 0


def _simulated_state(token: str) -> StageState:
    try:
        return parse_state(token)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def simulate(args: argparse.Namespace) -> int:
    """TEST-ONLY: emit a terminal state without any scientific computation."""

    try:
        exit_code, _payload = simulate_state(
            args.state, video_stem=args.video_stem
        )
    except SimulationDisabled as exc:
        print(f"BIOMAP SIMULATION REFUSED: {exc}", file=sys.stderr, flush=True)
        return 64
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="biomap")
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze_parser = subparsers.add_parser(
        "analyze",
        help=(
            "Run both pretrained DeepLabCut models, merge their exact outputs, "
            "and run headless SimBA"
        ),
    )
    analyze_parser.add_argument("video_dir", type=Path)
    analyze_parser.add_argument(
        "--resume", action="store_true",
        help=(
            "Reuse only verified DeepLabCut CSVs, merged tracking, and SimBA "
            "machine results; rerun whatever is missing or invalid"
        ),
    )
    analyze_parser.add_argument(
        "--demo", action="store_true",
        help=(
            "Cache-only mode: never run DeepLabCut; use existing verified "
            "tracking CSVs (implies --resume) and fail if they are missing"
        ),
    )
    analyze_parser.set_defaults(handler=analyze)

    dlc_parser = subparsers.add_parser(
        "dlc",
        help="Run only the pretrained PawDigits DeepLabCut model",
    )
    dlc_parser.add_argument("video_dir", type=Path)
    dlc_parser.add_argument(
        "--resume", action="store_true",
        help="Reuse a verified PawDigits CSV and rerun missing or invalid output",
    )
    dlc_parser.set_defaults(handler=run_dlc)

    simulate_parser = subparsers.add_parser(
        "simulate-state",
        help=(
            "TEST-ONLY: emit one terminal state through the real status "
            f"contract without running any science; requires "
            f"{SIMULATION_ENV_VAR}={SIMULATION_ENV_VALUE}"
        ),
    )
    simulate_parser.add_argument(
        "state",
        type=_simulated_state,
        metavar="STATE",
        help="One of: " + ", ".join(item.value for item in SIMULATED_STATES),
    )
    simulate_parser.add_argument(
        "--video-stem",
        default=DEFAULT_VIDEO_STEM,
        help=f"Synthetic video identity to report (default: {DEFAULT_VIDEO_STEM})",
    )
    simulate_parser.set_defaults(handler=simulate)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)
