"""Command-line entry point for the n8n-contained BIOMAP contribution.

This contribution currently exposes one command, ``biomap dlc``, which runs the
pretrained PawDigits DeepLabCut model over a directory of videos. Facial
tracking, the DLC merge, SimBA, ROI and calibration prerequisites, and terminal
state routing are deliberately not part of this contribution, so nothing here
imports them.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from .dlc_csv import DlcCsvError
from .dlc_stage import DlcStage, DlcStageError, paw_model
from .paths import ContributionPaths, repository_root


VIDEO_SUFFIXES = {".avi", ".mp4", ".mov", ".mkv"}


def _videos(video_dir: Path) -> list[Path]:
    if not video_dir.is_dir():
        raise DlcStageError(
            f"Video directory does not exist: {video_dir}",
            "Set BIOMAP_VIDEO_DIR to a readable directory of input videos.",
        )
    videos = sorted(
        path for path in video_dir.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES
    )
    if not videos:
        raise DlcStageError(
            f"No supported videos found in {video_dir}",
            "Place at least one .avi, .mp4, .mov, or .mkv file in the video directory.",
        )
    return videos


def run_dlc(args: argparse.Namespace) -> int:
    """Run only the pretrained PawDigits DeepLabCut stage.

    This is what the simplified n8n workflow invokes. It never constructs or
    executes the facial, merge, SimBA, or state-routing stages.
    """

    print("[n8n] DeepLabCut command started", flush=True)
    try:
        checkout = repository_root()
        print(f"[n8n] repo: {checkout}", flush=True)
        videos = _videos(args.video_dir)
        stage = DlcStage(
            checkout,
            contribution_paths=ContributionPaths(),
            dlc_environment=os.environ.get("BIOMAP_DLC_ENV", "biomap-dlc"),
        )
        model = paw_model()
        for video_path in videos:
            stage.ensure(video_path, model, resume=args.resume)
    except (DlcCsvError, DlcStageError, FileNotFoundError) as exc:
        print(f"[DLC Paw] FAIL: {exc}", flush=True)
        next_action = getattr(exc, "next_action", None)
        if next_action:
            print(f"[DLC Paw] NEXT ACTION: {next_action}", flush=True)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="biomap",
        description="Run the pretrained PawDigits DeepLabCut model.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)
