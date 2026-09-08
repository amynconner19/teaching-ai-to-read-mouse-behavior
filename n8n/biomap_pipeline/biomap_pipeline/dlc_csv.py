"""Reusable validation and staging for DeepLabCut multi-row CSV files."""

from __future__ import annotations

import csv
import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


class DlcCsvError(ValueError):
    """Raised when a DeepLabCut CSV cannot safely enter the pipeline."""


def video_stem(path: Path | str) -> str:
    """The video a DeepLabCut CSV belongs to.

    DeepLabCut names outputs ``<video><scorer>.csv``, where the scorer always
    begins with ``DLC``. Everything before that marker identifies the video.
    """

    stem = Path(path).stem
    return stem.split("DLC", 1)[0]


def index_by_video(directory: Path | str) -> dict[str, Path]:
    """Map video stem -> DeepLabCut CSV for every CSV in a directory.

    Two CSVs describing the same video are refused rather than resolved by
    guessing, so a stale scorer left beside a new one can never be silently
    reused as a cached result.
    """

    directory = Path(directory)
    if not directory.is_dir():
        raise DlcCsvError(f"DeepLabCut CSV directory does not exist: {directory}")
    index: dict[str, Path] = {}
    for path in sorted(directory.glob("*.csv")):
        stem = video_stem(path)
        if stem in index:
            raise DlcCsvError(
                f"Two DeepLabCut CSVs in {directory} describe video '{stem}': "
                f"{index[stem].name} and {path.name}"
            )
        index[stem] = path
    return index


@dataclass(frozen=True)
class DlcCsv:
    """A validated DLC table with dynamic body-part column mappings."""

    path: Path
    rows: tuple[tuple[str, ...], ...]
    body_parts: tuple[str, ...]
    column_groups: dict[str, tuple[int, int, int]]
    frame_indices: tuple[int, ...]

    @property
    def frame_count(self) -> int:
        return len(self.frame_indices)

    def write_in_body_part_order(
        self, destination: Path, body_part_order: Sequence[str]
    ) -> Path:
        """Write the same DLC values in the SimBA project's body-part order."""

        missing = [bp for bp in body_part_order if bp not in self.column_groups]
        if missing:
            raise DlcCsvError(
                f"Cannot stage {self.path}: missing required body parts: "
                f"{', '.join(missing)}"
            )

        selected_columns = [0]
        for body_part in body_part_order:
            selected_columns.extend(self.column_groups[body_part])

        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                newline="",
                encoding="utf-8",
                prefix=f".{destination.name}.",
                suffix=".tmp",
                dir=destination.parent,
                delete=False,
            ) as handle:
                temp_name = handle.name
                writer = csv.writer(handle, lineterminator="\n")
                for row in self.rows:
                    writer.writerow([row[index] for index in selected_columns])
            os.replace(temp_name, destination)
        except Exception:
            if temp_name is not None:
                Path(temp_name).unlink(missing_ok=True)
            raise
        return destination


def _normalise_header(value: str) -> str:
    return value.strip().lower()


def _read_rows(path: Path) -> list[list[str]]:
    try:
        with path.open("r", newline="", encoding="utf-8-sig") as handle:
            return list(csv.reader(handle))
    except OSError as exc:
        raise DlcCsvError(f"Cannot read DLC CSV {path}: {exc}") from exc


def validate_dlc_csv(
    path: Path | str,
    *,
    required_body_parts: Iterable[str] = (),
    expected_frame_count: int | None = None,
) -> DlcCsv:
    """Validate the three-row DLC schema and return its body-part mapping."""

    path = Path(path)
    if not path.is_file():
        raise DlcCsvError(f"DLC tracking CSV is missing: {path}")

    rows = _read_rows(path)
    if not rows or not any(cell.strip() for row in rows for cell in row):
        raise DlcCsvError(f"DLC CSV is empty: {path}")
    if len(rows) < 3:
        raise DlcCsvError(
            f"Malformed DLC header in {path}: expected scorer, bodyparts, and "
            "coords rows"
        )

    expected_labels = ("scorer", "bodyparts", "coords")
    actual_labels = tuple(
        _normalise_header(rows[index][0]) if rows[index] else ""
        for index in range(3)
    )
    if actual_labels != expected_labels:
        raise DlcCsvError(
            f"Malformed DLC header in {path}: expected first cells "
            f"{expected_labels}, found {actual_labels}"
        )

    width = len(rows[0])
    if width < 4 or (width - 1) % 3 != 0:
        raise DlcCsvError(
            f"Malformed DLC header in {path}: coordinate columns must be complete "
            "x/y/likelihood triplets"
        )
    for row_number, row in enumerate(rows, start=1):
        if len(row) != width:
            raise DlcCsvError(
                f"Malformed DLC CSV {path}: row {row_number} has {len(row)} "
                f"columns; expected {width}"
            )

    body_parts: list[str] = []
    groups: dict[str, tuple[int, int, int]] = {}
    for start in range(1, width, 3):
        indices = (start, start + 1, start + 2)
        names = [rows[1][index].strip() for index in indices]
        if not names[0] or len(set(names)) != 1:
            raise DlcCsvError(
                f"Malformed DLC header in {path}: columns {start + 1}-"
                f"{start + 3} do not identify one body part"
            )
        body_part = names[0]
        if body_part in groups:
            raise DlcCsvError(f"Duplicate body part '{body_part}' in {path}")

        coords = tuple(_normalise_header(rows[2][index]) for index in indices)
        if coords != ("x", "y", "likelihood"):
            raise DlcCsvError(
                f"Body part '{body_part}' in {path} must contain x, y, likelihood "
                f"in that order; found {coords}"
            )

        scorers = [rows[0][index].strip() for index in indices]
        if not scorers[0] or len(set(scorers)) != 1:
            raise DlcCsvError(
                f"Malformed scorer header for body part '{body_part}' in {path}"
            )
        body_parts.append(body_part)
        groups[body_part] = indices

    missing = [bp for bp in required_body_parts if bp not in groups]
    if missing:
        raise DlcCsvError(
            f"Missing required body parts in {path}: {', '.join(missing)}"
        )

    if len(rows) == 3:
        raise DlcCsvError(f"DLC CSV has no tracking frames: {path}")

    frame_indices: list[int] = []
    for row_number, row in enumerate(rows[3:], start=4):
        try:
            frame_value = float(row[0].strip())
        except ValueError as exc:
            raise DlcCsvError(
                f"Invalid frame index '{row[0]}' at row {row_number} in {path}"
            ) from exc
        if not frame_value.is_integer():
            raise DlcCsvError(
                f"Non-integer frame index '{row[0]}' at row {row_number} in {path}"
            )
        frame_indices.append(int(frame_value))

        for column_number, raw_value in enumerate(row[1:], start=2):
            try:
                value = float(raw_value.strip())
            except ValueError as exc:
                raise DlcCsvError(
                    f"Non-numeric tracking value at row {row_number}, column "
                    f"{column_number} in {path}"
                ) from exc
            if not math.isfinite(value):
                raise DlcCsvError(
                    f"NaN or infinite tracking value at row {row_number}, column "
                    f"{column_number} in {path}"
                )

    expected_indices = list(range(len(frame_indices)))
    if frame_indices != expected_indices:
        raise DlcCsvError(
            f"Frame index mismatch in {path}: expected contiguous indices 0-"
            f"{len(frame_indices) - 1}"
        )
    if expected_frame_count is not None and len(frame_indices) != expected_frame_count:
        raise DlcCsvError(
            f"Frame-count mismatch for {path}: tracking has {len(frame_indices)} "
            f"frames but video has {expected_frame_count}"
        )

    return DlcCsv(
        path=path,
        rows=tuple(tuple(row) for row in rows),
        body_parts=tuple(body_parts),
        column_groups=groups,
        frame_indices=tuple(frame_indices),
    )
