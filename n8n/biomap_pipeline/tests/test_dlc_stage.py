"""Synthetic, test-only tests for the Paw DeepLabCut stage and its CLI.

No DeepLabCut inference runs here. A fake runner stands in for the headless
``biomap_pipeline.dlc_headless`` subprocess and writes generated CSVs with a
DeepLabCut-style scorer suffix into the private prediction folder, exactly
where the real runner's output would appear.

Tracking CSVs are generated in code rather than checked in, because the
repository routes every ``*.csv`` through Git LFS and these fixtures are tiny.
"""

from __future__ import annotations

import ast
import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from biomap_pipeline import cli
from biomap_pipeline.cli import build_parser, main
from biomap_pipeline.dlc_csv import DlcCsvError, index_by_video, video_stem
from biomap_pipeline.dlc_headless import SCORER_PREFIX as HEADLESS_SCORER_PREFIX
from biomap_pipeline.dlc_headless import build_parser as headless_parser
from biomap_pipeline.dlc_stage import (
    DLC_MODELS_DIRNAME,
    PAW_BODY_PARTS,
    SCORER_PREFIX,
    DlcModel,
    DlcStage,
    DlcStageError,
    count_avi_frames,
    is_lfs_pointer,
    paw_model,
    read_project_layout,
    validate_project,
)
from biomap_pipeline.paths import ContributionPaths


PACKAGE_DIR = Path(cli.__file__).resolve().parent
CONTRIBUTION_DIR = PACKAGE_DIR.parent
LAUNCHER = CONTRIBUTION_DIR / "biomap"

VIDEO_STEM = "SYNTHETIC_TEST_ONLY_video"
PAW_SCORER = "DLC_SyntheticTestOnly_PawJan1shuffle1_snapshot_best-1"

#: Modules deliberately excluded from this Paw-only contribution.
OUT_OF_SCOPE_MODULES = (
    "simba_stage",
    "simba_headless",
    "simba_project",
    "dlc_merge",
    "simulate",
    "status_report",
    "states",
    "roi",
)

LFS_POINTER = (
    b"version https://git-lfs.github.com/spec/v1\n"
    b"oid sha256:0000000000000000000000000000000000000000000000000000000000000000\n"
    b"size 4909\n"
)


def dlc_csv_text(body_parts=PAW_BODY_PARTS, *, frames: int = 2, scorer: str = "S") -> str:
    """A minimal, valid three-header-row DeepLabCut CSV."""

    rows = [
        ["scorer"] + [scorer] * (3 * len(body_parts)),
        ["bodyparts"] + [part for part in body_parts for _ in range(3)],
        ["coords"] + ["x", "y", "likelihood"] * len(body_parts),
    ]
    for frame in range(frames):
        values: list[str] = [str(frame)]
        for index in range(len(body_parts)):
            values += [f"{10 + index}.0", f"{20 + index}.0", "0.99"]
        rows.append(values)
    return "\n".join(",".join(row) for row in rows) + "\n"


def write_project(
    repository: Path, model: DlcModel, *, lfs_pointer_config: bool = False
) -> Path:
    """Create a synthetic DeepLabCut project shaped like the real one."""

    project = repository / DLC_MODELS_DIRNAME / model.project_dirname
    project.mkdir(parents=True, exist_ok=True)
    task = "SyntheticPaw"
    (project / "config.yaml").write_text(
        "# Project definitions (do not edit)\n"
        f"Task: {task}\n"
        "scorer: Test\n"
        "date: Jan1\n"
        "multianimalproject: false\n\n"
        "project_path: C:\\Users\\someone\\Desktop\\original project\n\n"
        "engine: pytorch\n\n"
        "video_sets:\n"
        "  C:\\original\\videos\\training.avi:\n"
        "bodyparts:\n"
        + "".join(f"- {part}\n" for part in model.required_body_parts)
        + "TrainingFraction:\n- 0.95\niteration: 0\nsnapshotindex: -1\nbatch_size: 8\n",
        encoding="utf-8",
    )
    shuffle_dir = (
        project / "dlc-models-pytorch" / "iteration-0"
        / f"{task}Jan1-trainset95shuffle{model.shuffle}"
    )
    (shuffle_dir / "train").mkdir(parents=True, exist_ok=True)
    (shuffle_dir / "test").mkdir(parents=True, exist_ok=True)
    pytorch_config = shuffle_dir / "train" / "pytorch_config.yaml"
    if lfs_pointer_config:
        pytorch_config.write_bytes(LFS_POINTER)
    else:
        pytorch_config.write_text("device: cuda\nnet_type: synthetic\n", encoding="utf-8")
    (shuffle_dir / "train" / "snapshot-best-001.pt").write_bytes(
        b"SYNTHETIC TEST-ONLY SNAPSHOT"
    )
    (shuffle_dir / "test" / "pose_cfg.yaml").write_text("synthetic: true\n", encoding="utf-8")
    dataset = project / "training-datasets" / "iteration-0" / f"UnaugmentedDataSet_{task}Jan1"
    dataset.mkdir(parents=True, exist_ok=True)
    (dataset / "metadata.yaml").write_text("shuffles: {}\n", encoding="utf-8")
    return project


class FakeDlcRunner:
    """Write a generated CSV where DeepLabCut would, and return its scorer."""

    def __init__(self, *, fail: bool = False, extra_outputs: int = 0) -> None:
        self.calls: list[tuple[str, Path, Path, Path]] = []
        self.fail = fail
        self.extra_outputs = extra_outputs

    def __call__(
        self, runtime_config: Path, video_path: Path, model: DlcModel, destfolder: Path
    ) -> str:
        self.calls.append((model.key, runtime_config, video_path, destfolder))
        if self.fail:
            raise DlcStageError(f"{model.label} failed: synthetic DeepLabCut error")
        text = dlc_csv_text(model.required_body_parts)
        (destfolder / f"{video_path.stem}{PAW_SCORER}.csv").write_text(text, encoding="utf-8")
        (destfolder / f"{video_path.stem}{PAW_SCORER}_meta.pickle").write_bytes(
            b"SYNTHETIC META"
        )
        for index in range(self.extra_outputs):
            (destfolder / f"{video_path.stem}DLC_extra{index}.csv").write_text(
                text, encoding="utf-8"
            )
        return PAW_SCORER

    @property
    def call_count(self) -> int:
        return len(self.calls)


class DependencyClosureTests(unittest.TestCase):
    """The committed Paw-only files must import without the excluded modules."""

    def test_cli_imports(self) -> None:
        import biomap_pipeline.cli  # noqa: F401

    def test_dlc_stage_imports(self) -> None:
        import biomap_pipeline.dlc_stage  # noqa: F401

    def test_every_committed_module_imports_in_a_fresh_interpreter(self) -> None:
        modules = [
            f"biomap_pipeline.{path.stem}"
            for path in sorted(PACKAGE_DIR.glob("*.py"))
            if path.stem != "__init__"
        ]
        self.assertIn("biomap_pipeline.cli", modules)
        self.assertIn("biomap_pipeline.dlc_stage", modules)
        completed = subprocess.run(
            [sys.executable, "-c", "".join(f"import {name}\n" for name in modules)],
            cwd=CONTRIBUTION_DIR, capture_output=True, text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_no_committed_source_imports_an_out_of_scope_module(self) -> None:
        offenders: list[str] = []
        for path in sorted(PACKAGE_DIR.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                names: list[str] = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""] + [alias.name for alias in node.names]
                for name in names:
                    if name.rsplit(".", 1)[-1] in OUT_OF_SCOPE_MODULES:
                        offenders.append(f"{path.name}:{node.lineno} imports {name}")
        self.assertEqual(offenders, [], "; ".join(offenders))

    def test_excluded_modules_are_absent_from_the_package(self) -> None:
        for name in OUT_OF_SCOPE_MODULES:
            self.assertFalse(
                (PACKAGE_DIR / f"{name}.py").exists(),
                f"{name}.py is out of scope for the Paw-only contribution",
            )


class CliParserTests(unittest.TestCase):
    def test_parser_exposes_only_the_dlc_command(self) -> None:
        subparsers = [
            action for action in build_parser()._actions
            if hasattr(action, "choices") and isinstance(action.choices, dict)
        ]
        self.assertEqual(len(subparsers), 1)
        self.assertEqual(list(subparsers[0].choices), ["dlc"])

    def test_dlc_arguments(self) -> None:
        args = build_parser().parse_args(["dlc", "/videos", "--resume"])
        self.assertEqual(args.video_dir, Path("/videos"))
        self.assertTrue(args.resume)
        self.assertFalse(build_parser().parse_args(["dlc", "/videos"]).resume)

    def test_removed_commands_are_rejected(self) -> None:
        for argv in (["analyze", "/videos"], ["simulate-state", "PASS"]):
            with self.subTest(argv=argv), self.assertRaises(SystemExit):
                with contextlib.redirect_stderr(io.StringIO()):
                    build_parser().parse_args(argv)

    def test_launcher_help_succeeds(self) -> None:
        for argv in ([], ["dlc"]):
            with self.subTest(argv=argv):
                completed = subprocess.run(
                    [sys.executable, str(LAUNCHER), *argv, "--help"],
                    cwd=CONTRIBUTION_DIR, capture_output=True, text=True,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("dlc", completed.stdout)


class AviFrameCountTests(unittest.TestCase):
    """Frame counting is OpenCV-based and never reaches for SimBA."""

    def test_frame_counting_does_not_import_simba(self) -> None:
        source = (PACKAGE_DIR / "dlc_stage.py").read_text(encoding="utf-8")
        import_lines = [
            line for line in source.splitlines()
            if line.lstrip().startswith(("import ", "from ")) and "simba" in line.lower()
        ]
        self.assertEqual(import_lines, [])
        tree = ast.parse(source)
        function = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "count_avi_frames"
        )
        imported = [
            alias.name
            for node in ast.walk(function)
            if isinstance(node, ast.Import)
            for alias in node.names
        ]
        self.assertEqual(imported, ["cv2"])

    def test_non_avi_input_skips_the_check(self) -> None:
        from biomap_pipeline.dlc_stage import _count_frames_if_avi

        self.assertIsNone(_count_frames_if_avi(Path("/videos/clip.mkv")))
        self.assertIsNone(_count_frames_if_avi(Path("/videos/clip.mp4")))

    def test_opencv_frame_count_is_returned_for_avi(self) -> None:
        class Capture:
            def isOpened(self):
                return True

            def get(self, prop):
                return 116451.0

            def release(self):
                return None

        fake_cv2 = type("cv2", (), {})()
        fake_cv2.CAP_PROP_FRAME_COUNT = 7
        fake_cv2.VideoCapture = lambda path: Capture()
        with patch.dict(sys.modules, {"cv2": fake_cv2}):
            self.assertEqual(count_avi_frames(Path("/videos/clip.avi")), 116451)

    def test_missing_opencv_returns_none_with_an_explanation(self) -> None:
        stream = io.StringIO()
        real_import = __import__

        def no_cv2(name, *args, **kwargs):
            if name == "cv2":
                raise ImportError("No module named 'cv2'")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=no_cv2):
            with contextlib.redirect_stdout(stream):
                self.assertIsNone(count_avi_frames(Path("/videos/clip.avi")))
        self.assertIn("frame count unavailable", stream.getvalue())
        self.assertIn("OpenCV", stream.getvalue())

    def test_unopenable_video_returns_none_with_an_explanation(self) -> None:
        class Capture:
            def isOpened(self):
                return False

            def get(self, prop):
                return 0.0

            def release(self):
                return None

        fake_cv2 = type("cv2", (), {})()
        fake_cv2.CAP_PROP_FRAME_COUNT = 7
        fake_cv2.VideoCapture = lambda path: Capture()
        stream = io.StringIO()
        with patch.dict(sys.modules, {"cv2": fake_cv2}):
            with contextlib.redirect_stdout(stream):
                self.assertIsNone(count_avi_frames(Path("/videos/clip.avi")))
        self.assertIn("cannot open", stream.getvalue())


class DlcStageTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.repository = self.root / "repo"
        self.paths = ContributionPaths(self.root / "n8n" / "biomap_pipeline")
        self.paw_model = paw_model()
        self.paw_project = write_project(self.repository, self.paw_model)
        self.video_dir = self.repository / "videos"
        self.video_dir.mkdir(parents=True)
        self.video = self.video_dir / f"{VIDEO_STEM}.mkv"
        self.video.write_bytes(b"SYNTHETIC TEST-ONLY VIDEO")
        self.runner = FakeDlcRunner()
        self.stage = self.make_stage(self.runner)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def make_stage(self, runner) -> DlcStage:
        return DlcStage(self.repository, contribution_paths=self.paths, runner=runner)

    def cache_output(self, *, valid: bool = True, scorer: str = PAW_SCORER) -> Path:
        destination = self.paths.paw_tracking / f"{VIDEO_STEM}{scorer}.csv"
        destination.parent.mkdir(parents=True, exist_ok=True)
        if valid:
            destination.write_text(dlc_csv_text(), encoding="utf-8")
        else:
            destination.write_text("scorer,x\nbodyparts,y\n", encoding="utf-8")
        return destination.resolve()

    def project_snapshot(self) -> dict[Path, tuple[int, float]]:
        return {
            path: (path.stat().st_size, path.stat().st_mtime)
            for path in self.paw_project.rglob("*") if path.is_file()
        }


class PawStageTests(DlcStageTestCase):
    def test_paw_model_is_the_committed_scope(self) -> None:
        self.assertEqual(self.paw_model.key, "paw")
        self.assertEqual(
            self.paw_model.project_dirname, "BIOMAP Paw Digits-Megan G-2026-06-10"
        )
        self.assertEqual(self.paw_model.shuffle, 1)
        self.assertEqual(self.paw_model.trainingsetindex, 0)
        self.assertEqual(self.paw_model.required_body_parts, PAW_BODY_PARTS)

    def test_shuffle_override_from_environment(self) -> None:
        with patch.dict(os.environ, {"BIOMAP_DLC_PAW_SHUFFLE": "3"}):
            self.assertEqual(paw_model().shuffle, 3)
        with patch.dict(os.environ, {"BIOMAP_DLC_PAW_SHUFFLE": "zero"}):
            with self.assertRaises(DlcStageError):
                paw_model()

    def test_layout_follows_deeplabcut_naming(self) -> None:
        layout = read_project_layout(self.paw_project, self.paw_model)
        self.assertEqual(
            layout.model_folder,
            self.paw_project / "dlc-models-pytorch" / "iteration-0"
            / "SyntheticPawJan1-trainset95shuffle1",
        )
        self.assertEqual([path.name for path in layout.snapshots()], ["snapshot-best-001.pt"])

    def test_missing_paw_output_invokes_the_dlc_runner(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            output = self.stage.ensure(self.video, self.paw_model, resume=True)
        self.assertEqual(self.runner.call_count, 1)
        self.assertEqual(
            output, (self.paths.paw_tracking / f"{VIDEO_STEM}{PAW_SCORER}.csv").resolve()
        )
        self.assertTrue(output.is_file())
        self.assertEqual(video_stem(output), VIDEO_STEM)

    def test_valid_cached_output_with_resume_skips_the_dlc_runner(self) -> None:
        cached = self.cache_output()
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            output = self.stage.ensure(self.video, self.paw_model, resume=True)
        self.assertEqual(self.runner.call_count, 0)
        self.assertEqual(output, cached)
        self.assertIn(f"[DLC Paw] SKIP_CACHED: {cached}", stream.getvalue())

    def test_cached_output_is_ignored_without_resume(self) -> None:
        self.cache_output()
        with contextlib.redirect_stdout(io.StringIO()):
            self.stage.ensure(self.video, self.paw_model, resume=False)
        self.assertEqual(self.runner.call_count, 1)

    def test_invalid_cached_output_is_rerun_with_resume(self) -> None:
        self.cache_output(valid=False)
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            output = self.stage.ensure(self.video, self.paw_model, resume=True)
        self.assertEqual(self.runner.call_count, 1)
        self.assertIn("cached output invalid; rerunning", stream.getvalue())
        self.assertTrue(output.is_file())

    def test_duplicate_cached_outputs_fail_clearly(self) -> None:
        self.cache_output()
        self.cache_output(scorer="DLC_AnotherScorer_snapshot-9")
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(DlcStageError, "ambiguous cached outputs") as ctx:
                self.stage.ensure(self.video, self.paw_model, resume=True)
        self.assertIn("describe video", str(ctx.exception))
        self.assertIn("Remove the duplicate CSVs", ctx.exception.next_action)
        self.assertEqual(self.runner.call_count, 0)

    def test_index_by_video_rejects_duplicates_directly(self) -> None:
        self.cache_output()
        self.cache_output(scorer="DLC_AnotherScorer_snapshot-9")
        with self.assertRaisesRegex(DlcCsvError, "describe video"):
            index_by_video(self.paths.paw_tracking)

    def test_ambiguous_generated_outputs_are_rejected(self) -> None:
        stage = self.make_stage(FakeDlcRunner(extra_outputs=1))
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(DlcStageError, "expected exactly one CSV"):
                stage.ensure(self.video, self.paw_model, resume=False)
        self.assertFalse(self.paths.paw_tracking.exists())

    def test_superseded_output_for_same_video_is_replaced(self) -> None:
        stale = self.paths.paw_tracking / f"{VIDEO_STEM}DLC_old_scorer.csv"
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_text(dlc_csv_text(), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            output = self.stage.ensure(self.video, self.paw_model, resume=False)
        self.assertFalse(stale.exists())
        self.assertEqual([p.name for p in self.paths.paw_tracking.glob("*.csv")], [output.name])

    def test_dlc_failure_is_identified_and_actionable(self) -> None:
        stage = self.make_stage(FakeDlcRunner(fail=True))
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            with self.assertRaisesRegex(DlcStageError, "DLC Paw failed") as ctx:
                stage.ensure(self.video, self.paw_model, resume=False)
        self.assertIn("[DLC Paw] START", stream.getvalue())
        self.assertIn("[DLC Paw] FAIL:", stream.getvalue())
        self.assertIsNotNone(ctx.exception.next_action)
        self.assertFalse(self.paths.paw_tracking.exists())

    def test_lfs_pointer_blocks_inference_with_pull_command(self) -> None:
        write_project(self.repository, self.paw_model, lfs_pointer_config=True)
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(DlcStageError, "Git LFS pointers") as ctx:
                self.stage.ensure(self.video, self.paw_model, resume=False)
        self.assertIn(
            'git lfs pull --include="deeplabcut-models/BIOMAP Paw Digits-Megan G-2026-06-10/**"',
            ctx.exception.next_action,
        )
        self.assertEqual(self.runner.call_count, 0)

    def test_missing_shuffle_is_reported(self) -> None:
        with patch.dict(os.environ, {"BIOMAP_DLC_PAW_SHUFFLE": "7"}):
            model = paw_model()
        with self.assertRaisesRegex(DlcStageError, "shuffle 7 is not present"):
            validate_project(self.paw_project, model)

    def test_is_lfs_pointer(self) -> None:
        pointer = self.root / "pointer.yaml"
        pointer.write_bytes(LFS_POINTER)
        self.assertTrue(is_lfs_pointer(pointer))
        real = self.root / "real.csv"
        real.write_text(dlc_csv_text(), encoding="utf-8")
        self.assertFalse(is_lfs_pointer(real))

    def test_runtime_mirror_is_portable_and_leaves_project_untouched(self) -> None:
        before = self.project_snapshot()
        with contextlib.redirect_stdout(io.StringIO()):
            self.stage.ensure(self.video, self.paw_model, resume=False)
        self.assertEqual(self.project_snapshot(), before)
        runtime_config = self.runner.calls[0][1]
        runtime = self.paths.dlc_runtime_project("paw")
        self.assertEqual(runtime_config, runtime / "config.yaml")
        text = runtime_config.read_text(encoding="utf-8")
        self.assertIn(f"project_path: {runtime.resolve()}", text)
        self.assertIn("snapshotindex: -1", text)
        snapshot = (
            runtime / "dlc-models-pytorch" / "iteration-0"
            / "SyntheticPawJan1-trainset95shuffle1" / "train" / "snapshot-best-001.pt"
        )
        self.assertTrue(snapshot.is_symlink())
        self.assertEqual(self.runner.calls[0][3], self.paths.dlc_predictions("paw", VIDEO_STEM))


class HeadlessContractTests(DlcStageTestCase):
    """The validated DeepLabCut invocation must not drift."""

    def test_conda_command_uses_configured_environment_and_cpu_default(self) -> None:
        stage = DlcStage(
            self.repository, contribution_paths=self.paths,
            dlc_environment="synthetic-dlc-env",
        )
        layout = validate_project(self.paw_project, self.paw_model)
        runtime_config = stage._prepare_runtime_project(layout, self.paw_model)
        destfolder = self.paths.dlc_predictions("paw", VIDEO_STEM)
        environment = {k: v for k, v in os.environ.items() if k != "BIOMAP_DLC_DEVICE"}
        with (
            patch("biomap_pipeline.dlc_stage.shutil.which", return_value="/synthetic/bin/conda"),
            patch.dict(os.environ, environment, clear=True),
        ):
            command = stage._conda_command(
                runtime_config, self.video, self.paw_model, destfolder
            )
            subprocess_env = stage._subprocess_environment()
        self.assertEqual(
            command[:6],
            ["/synthetic/bin/conda", "run", "--no-capture-output", "-n",
             "synthetic-dlc-env", "python"],
        )
        self.assertIn("-u", command)
        self.assertIn("biomap_pipeline.dlc_headless", command)
        self.assertEqual(command[command.index("--shuffle") + 1], "1")
        self.assertEqual(command[command.index("--trainingsetindex") + 1], "0")
        self.assertEqual(command[command.index("--device") + 1], "cpu")
        self.assertEqual(command[command.index("--destfolder") + 1], str(destfolder))
        self.assertEqual(subprocess_env["PYTHONUNBUFFERED"], "1")
        self.assertEqual(subprocess_env["PYTORCH_ENABLE_MPS_FALLBACK"], "1")
        self.assertEqual(
            subprocess_env["PYTHONPATH"].split(os.pathsep)[0], str(CONTRIBUTION_DIR)
        )

    def test_device_override_is_passed_through(self) -> None:
        stage = DlcStage(self.repository, contribution_paths=self.paths)
        layout = validate_project(self.paw_project, self.paw_model)
        runtime_config = stage._prepare_runtime_project(layout, self.paw_model)
        with (
            patch("biomap_pipeline.dlc_stage.shutil.which", return_value="/synthetic/bin/conda"),
            patch.dict(os.environ, {"BIOMAP_DLC_DEVICE": "mps"}),
        ):
            command = stage._conda_command(
                runtime_config, self.video, self.paw_model,
                self.paths.dlc_predictions("paw", VIDEO_STEM),
            )
        self.assertEqual(command[command.index("--device") + 1], "mps")

    def test_headless_parser_accepts_the_generated_command(self) -> None:
        stage = DlcStage(self.repository, contribution_paths=self.paths)
        layout = validate_project(self.paw_project, self.paw_model)
        runtime_config = stage._prepare_runtime_project(layout, self.paw_model)
        destfolder = self.paths.dlc_predictions("paw", VIDEO_STEM)
        with patch(
            "biomap_pipeline.dlc_stage.shutil.which", return_value="/synthetic/bin/conda"
        ):
            command = stage._conda_command(
                runtime_config, self.video, self.paw_model, destfolder
            )
        parsed = headless_parser().parse_args(command[command.index("--config"):])
        self.assertEqual(parsed.config, runtime_config)
        self.assertEqual(parsed.video, self.video)
        self.assertEqual(parsed.destfolder, destfolder)
        self.assertEqual(parsed.shuffle, 1)
        self.assertEqual(SCORER_PREFIX, HEADLESS_SCORER_PREFIX)

    def test_headless_keyword_arguments_match_the_validated_call(self) -> None:
        source = (PACKAGE_DIR / "dlc_headless.py").read_text(encoding="utf-8")
        for fragment in (
            '"video_extensions": video.suffix.lower()',
            '"shuffle": args.shuffle',
            '"trainingsetindex": args.trainingsetindex',
            '"save_as_csv": True',
            '"destfolder": str(destfolder)',
            '"device": device',
        ):
            self.assertIn(fragment, source)

    def test_output_is_streamed_with_stage_prefix_and_scorer_is_captured(self) -> None:
        class FakeProcess:
            def __init__(self, command, **kwargs):
                self.stdout = io.BytesIO(
                    b"Running pose prediction with batch size 8\n"
                    b"  0%|          | 0/6\r 100%|##########| 6/6\n"
                    + SCORER_PREFIX.encode() + PAW_SCORER.encode() + b"\n"
                )

            def wait(self):
                return 0

        stage = DlcStage(self.repository, contribution_paths=self.paths)
        stream = io.StringIO()
        with (
            patch("biomap_pipeline.dlc_stage.subprocess.Popen", FakeProcess),
            patch("biomap_pipeline.dlc_stage.shutil.which", return_value="/synthetic/bin/conda"),
            contextlib.redirect_stdout(stream),
        ):
            scorer = stage._run_headless(
                self.root / "config.yaml", self.video, self.paw_model, self.root / "dest"
            )
        self.assertEqual(scorer, PAW_SCORER)
        lines = stream.getvalue().splitlines()
        self.assertIn("[DLC Paw] Running pose prediction with batch size 8", lines)
        self.assertIn("[DLC Paw]  100%|##########| 6/6", lines)
        self.assertNotIn(SCORER_PREFIX, stream.getvalue())

    def test_nonzero_exit_fails_the_stage_with_diagnostics(self) -> None:
        class FailingProcess:
            def __init__(self, command, **kwargs):
                self.stdout = io.BytesIO(b"Traceback: synthetic failure\n")

            def wait(self):
                return 3

        stage = DlcStage(self.repository, contribution_paths=self.paths)
        with (
            patch("biomap_pipeline.dlc_stage.subprocess.Popen", FailingProcess),
            patch("biomap_pipeline.dlc_stage.shutil.which", return_value="/synthetic/bin/conda"),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            with self.assertRaisesRegex(DlcStageError, "exited with status 3") as ctx:
                stage._run_headless(
                    self.root / "config.yaml", self.video, self.paw_model, self.root / "dest"
                )
        self.assertIn("synthetic failure", str(ctx.exception))

    def test_missing_conda_is_reported(self) -> None:
        stage = DlcStage(self.repository, contribution_paths=self.paths)
        with patch("biomap_pipeline.dlc_stage.shutil.which", return_value=None):
            with self.assertRaisesRegex(DlcStageError, "conda is not on PATH"):
                stage._conda_command(
                    self.root / "config.yaml", self.video, self.paw_model, self.root / "dest"
                )


class CliWiringTests(DlcStageTestCase):
    """Drive ``biomap dlc`` with the DeepLabCut subprocess faked."""

    def run_cli(self, *flags: str, runner: FakeDlcRunner | None = None):
        runner = runner or self.runner
        stream = io.StringIO()
        with (
            patch("biomap_pipeline.cli.ContributionPaths", return_value=self.paths),
            patch("biomap_pipeline.cli.repository_root", return_value=self.repository),
            patch(
                "biomap_pipeline.cli.DlcStage",
                side_effect=lambda repository, **kwargs: DlcStage(
                    repository, runner=runner, **kwargs
                ),
            ),
            contextlib.redirect_stdout(stream),
        ):
            exit_code = main(["dlc", str(self.video_dir), *flags])
        return exit_code, stream.getvalue(), runner

    def test_missing_output_runs_dlc_and_succeeds(self) -> None:
        exit_code, log, runner = self.run_cli("--resume")
        self.assertEqual(exit_code, 0, log)
        self.assertEqual(runner.call_count, 1)
        self.assertIn("[n8n] DeepLabCut command started", log)
        self.assertIn("[DLC Paw] PASS:", log)

    def test_valid_cached_output_with_resume_skips_dlc(self) -> None:
        self.cache_output()
        exit_code, log, runner = self.run_cli("--resume")
        self.assertEqual(exit_code, 0, log)
        self.assertEqual(runner.call_count, 0)
        self.assertIn("[DLC Paw] SKIP_CACHED:", log)

    def test_dlc_failure_returns_nonzero_with_next_action(self) -> None:
        exit_code, log, _runner = self.run_cli(runner=FakeDlcRunner(fail=True))
        self.assertEqual(exit_code, 1)
        self.assertIn("[DLC Paw] FAIL:", log)
        self.assertIn("[DLC Paw] NEXT ACTION:", log)

    def test_missing_video_directory_is_reported(self) -> None:
        stream = io.StringIO()
        with (
            patch("biomap_pipeline.cli.ContributionPaths", return_value=self.paths),
            patch("biomap_pipeline.cli.repository_root", return_value=self.repository),
            contextlib.redirect_stdout(stream),
        ):
            exit_code = main(["dlc", str(self.root / "absent"), "--resume"])
        self.assertEqual(exit_code, 1)
        self.assertIn("Video directory does not exist", stream.getvalue())

    def test_empty_video_directory_is_reported(self) -> None:
        empty = self.root / "empty"
        empty.mkdir()
        stream = io.StringIO()
        with (
            patch("biomap_pipeline.cli.ContributionPaths", return_value=self.paths),
            patch("biomap_pipeline.cli.repository_root", return_value=self.repository),
            contextlib.redirect_stdout(stream),
        ):
            exit_code = main(["dlc", str(empty), "--resume"])
        self.assertEqual(exit_code, 1)
        self.assertIn("No supported videos found", stream.getvalue())

    def test_cli_uses_the_configured_dlc_environment(self) -> None:
        captured: dict[str, object] = {}
        real_stage = DlcStage

        def capture(repository, **kwargs):
            captured.update(kwargs)
            return real_stage(repository, runner=self.runner, **kwargs)

        with (
            patch("biomap_pipeline.cli.ContributionPaths", return_value=self.paths),
            patch("biomap_pipeline.cli.repository_root", return_value=self.repository),
            patch("biomap_pipeline.cli.DlcStage", side_effect=capture),
            patch.dict(os.environ, {"BIOMAP_DLC_ENV": "synthetic-env"}),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            main(["dlc", str(self.video_dir), "--resume"])
        self.assertEqual(captured["dlc_environment"], "synthetic-env")


if __name__ == "__main__":
    unittest.main()
