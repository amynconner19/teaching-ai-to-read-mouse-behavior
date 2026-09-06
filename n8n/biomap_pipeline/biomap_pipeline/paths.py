"""Filesystem layout for the n8n-contained BIOMAP contribution.

Every path this contribution writes stays inside ``n8n/biomap_pipeline`` so that
a pull request touching this feature never contains generated artifacts, and so
the repository's scientific SimBA project is only ever read.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


#: ``n8n/biomap_pipeline`` - the root of this self-contained contribution.
CONTRIBUTION_ROOT = Path(__file__).resolve().parent.parent


def repository_root(start: Path | None = None) -> Path:
    """Find the checkout root from its checked-in scientific project folders."""

    origin = (start or CONTRIBUTION_ROOT).resolve()
    for parent in (origin, *origin.parents):
        if (parent / "deeplabcut-models").is_dir():
            return parent
    raise FileNotFoundError(
        "Cannot locate the repository root containing deeplabcut-models"
    )


@dataclass(frozen=True)
class ContributionPaths:
    """Contribution-relative output locations.

    All of these live under ``n8n/biomap_pipeline/results`` and are ignored by
    ``n8n/biomap_pipeline/.gitignore``.
    """

    root: Path = CONTRIBUTION_ROOT

    @property
    def results(self) -> Path:
        return self.root / "results"

    @property
    def tracking(self) -> Path:
        return self.results / "tracking"

    @property
    def paw_tracking(self) -> Path:
        """Output directory of the upstream DeepLabCut PawDigits stage."""

        return self.tracking / "paw"

    @property
    def facial_tracking(self) -> Path:
        """Output directory of the upstream facial DeepLabCut stage."""

        return self.tracking / "facial"

    @property
    def merged_tracking(self) -> Path:
        """Merged pose input handed to SimBA."""

        return self.tracking / "merged"

    @property
    def simba_results(self) -> Path:
        """Standardized machine-results, one CSV per video stem."""

        return self.results / "simba"

    @property
    def simba_native(self) -> Path:
        """Preserved copies of SimBA's own per-video output files."""

        return self.simba_results / "native"

    @property
    def work(self) -> Path:
        """Disposable runtime SimBA projects, one per video."""

        return self.results / ".work"

    @property
    def dlc_work(self) -> Path:
        """Disposable DeepLabCut runtime mirrors and per-video prediction folders."""

        return self.work / "dlc"

    def dlc_runtime_project(self, model_key: str) -> Path:
        """Read-only mirror of one DLC project with a portable ``project_path``."""

        return self.dlc_work / model_key / "project"

    def dlc_predictions(self, model_key: str, video_stem: str) -> Path:
        """Private ``destfolder`` for one model and one video."""

        return self.dlc_work / model_key / "predictions" / video_stem

    @property
    def cache(self) -> Path:
        """Scratch caches for matplotlib/numba so SimBA never writes to $HOME."""

        return self.results / ".cache"

    @property
    def run_status(self) -> Path:
        """Latest machine-readable CLI state consumed by n8n."""

        return self.results / "run_status.json"

    @property
    def logs(self) -> Path:
        """Live command logs written by the n8n Execute Command node."""

        return self.results / "logs"

    def merged_csv(self, video_stem: str) -> Path:
        return self.merged_tracking / f"{video_stem}.csv"

    def simba_csv(self, video_stem: str) -> Path:
        return self.simba_results / f"{video_stem}.csv"

    def native_dir(self, video_stem: str) -> Path:
        return self.simba_native / video_stem
