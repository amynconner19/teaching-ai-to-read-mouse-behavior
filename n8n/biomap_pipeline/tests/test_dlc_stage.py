"""Synthetic/test-only tests for the DeepLabCut stage and its CLI wiring.

No DeepLabCut inference runs here. A fake runner stands in for the headless
``biomap_pipeline.dlc_headless`` subprocess and writes fixture CSVs with a
DeepLabCut-style scorer suffix into the private prediction folder, exactly
where the real runner's output would appear.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from biomap_pipeline import cli
from biomap_pipeline.cli import _handoff_to_simba, main
from biomap_pipeline.dlc_headless import SCORER_PREFIX as HEADLESS_SCORER_PREFIX
from biomap_pipeline.dlc_headless import analyze as headless_analyze
from biomap_pipeline.dlc_headless import build_parser as headless_parser
from biomap_pipeline.dlc_merge import video_stem
from biomap_pipeline.dlc_stage import (
    DLC_MODELS_DIRNAME,
    SCORER_PREFIX,
    DlcModel,
    DlcStage,
    dlc_models,
    is_lfs_pointer,
    read_project_layout,
    validate_project,
)
from biomap_pipeline.paths import ContributionPaths
from biomap_pipeline.simba_stage import REQUIRED_BODY_PARTS, SimbaStageResult
from biomap_pipeline.states import DlcStageError, StageState
from biomap_pipeline.status_report import STDOUT_PREFIX


FIXTURES = Path(__file__).parent / "fixtures"
PAW_FIXTURE = FIXTURES / "SYNTHETIC_TEST_ONLY_paw.csv"
FACIAL_FIXTURE = FIXTURES / "SYNTHETIC_TEST_ONLY_facial.csv"
VIDEO_STEM = "SYNTHETIC_TEST_ONLY_video"
PAW_SCORER = "DLC_SyntheticTestOnly_PawJun10shuffle1_snapshot_best-1"
FACIAL_SCORER = "DLC_SyntheticTestOnly_FacialMar17shuffle2_snapshot_best-1"
LFS_POINTER = (
    b"version https://git-lfs.github.com/spec/v1\n"
    b"oid sha256:0000000000000000000000000000000000000000000000000000000000000000\n"
    b"size 4909\n"
)


def write_project(
    repository: Path, model: DlcModel, *, lfs_pointer_config: bool = False
) -> Path:
    """Create a synthetic DeepLabCut project shaped like the real ones."""

    project = repository / DLC_MODELS_DIRNAME / model.project_dirname
    project.mkdir(parents=True, exist_ok=True)
    task = "SyntheticPaw" if model.key == "paw" else "SyntheticFacial"
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
    (shuffle_dir / "train" / "snapshot-best-001.pt").write_bytes(b"SYNTHETIC TEST-ONLY SNAPSHOT")
    (shuffle_dir / "test" / "pose_cfg.yaml").write_text("synthetic: true\n", encoding="utf-8")
    dataset = project / "training-datasets" / "iteration-0" / f"UnaugmentedDataSet_{task}Jan1"
    dataset.mkdir(parents=True, exist_ok=True)
    (dataset / "metadata.yaml").write_text("shuffles: {}\n", encoding="utf-8")
    return project


class FakeDlcRunner:
    """Write the fixture CSV where DeepLabCut would, and return its scorer."""

    def __init__(self, *, fail_for: set[str] = frozenset(), extra_outputs: int = 0) -> None:
        self.calls: list[tuple[str, Path, Path, Path]] = []
        self.fail_for = set(fail_for)
        self.extra_outputs = extra_outputs

    def __call__(self, runtime_config: Path, video_path: Path, model: DlcModel, destfolder: Path) -> str:
        self.calls.append((model.key, runtime_config, video_path, destfolder))
        if model.key in self.fail_for:
            raise DlcStageError(f"{model.label} failed: synthetic DeepLabCut error")
        fixture = PAW_FIXTURE if model.key == "paw" else FACIAL_FIXTURE
        scorer = PAW_SCORER if model.key == "paw" else FACIAL_SCORER
        shutil.copy2(fixture, destfolder / f"{video_path.stem}{scorer}.csv")
        (destfolder / f"{video_path.stem}{scorer}_meta.pickle").write_bytes(b"SYNTHETIC META")
        for index in range(self.extra_outputs):
            shutil.copy2(fixture, destfolder / f"{video_path.stem}DLC_extra{index}.csv")
        return scorer

    def keys(self) -> list[str]:
        return [call[0] for call in self.calls]


class CapturingSimbaStage:
    """Record the exact merged path the CLI hands to SimBA; never run it."""

    def __init__(self, paths: ContributionPaths) -> None:
        self.paths = paths
        self.merged_csv: Path | None = None
        self.calls = 0

    def run(self, *, video_path, merged_csv, resume):
        self.calls += 1
        self.merged_csv = merged_csv
        return SimbaStageResult(StageState.PASS, self.paths.simba_csv(video_path.stem), False)


class DlcStageTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.repository = self.root / "repo"
        self.paths = ContributionPaths(self.root / "n8n" / "biomap_pipeline")
        self.paw_model, self.facial_model = dlc_models()
        self.paw_project = write_project(self.repository, self.paw_model)
        self.facial_project = write_project(self.repository, self.facial_model)
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

    def cache_output(self, model: DlcModel, *, valid: bool = True) -> Path:
        fixture = PAW_FIXTURE if model.key == "paw" else FACIAL_FIXTURE
        scorer = PAW_SCORER if model.key == "paw" else FACIAL_SCORER
        destination = model.tracking_dir(self.paths) / f"{VIDEO_STEM}{scorer}.csv"
        destination.parent.mkdir(parents=True, exist_ok=True)
        if valid:
            shutil.copy2(fixture, destination)
        else:
            destination.write_text("scorer,x\nbodyparts,y\n", encoding="utf-8")
        return destination.resolve()

    def project_snapshot(self) -> dict[Path, tuple[int, float]]:
        return {
            path: (path.stat().st_size, path.stat().st_mtime)
            for project in (self.paw_project, self.facial_project)
            for path in project.rglob("*") if path.is_file()
        }


class DlcStageUnitTests(DlcStageTestCase):
    def test_production_order_is_paw_then_facial(self) -> None:
        self.assertEqual([model.key for model in dlc_models()], ["paw", "facial"])
        self.assertEqual(self.paw_model.project_dirname, "BIOMAP Paw Digits-Megan G-2026-06-10")
        self.assertEqual(self.facial_model.project_dirname, "BIOMAP-Megan_G_-2026-03-17")
        self.assertEqual((self.paw_model.shuffle, self.facial_model.shuffle), (1, 2))
        self.assertEqual(
            self.paw_model.required_body_parts + self.facial_model.required_body_parts,
            REQUIRED_BODY_PARTS,
        )

    def test_shuffle_override_from_environment(self) -> None:
        with patch.dict(os.environ, {"BIOMAP_DLC_FACIAL_SHUFFLE": "1"}):
            self.assertEqual(dlc_models()[1].shuffle, 1)
        with patch.dict(os.environ, {"BIOMAP_DLC_FACIAL_SHUFFLE": "zero"}):
            with self.assertRaises(DlcStageError):
                dlc_models()

    def test_layout_follows_deeplabcut_naming(self) -> None:
        layout = read_project_layout(self.paw_project, self.paw_model)
        self.assertEqual(
            layout.model_folder,
            self.paw_project / "dlc-models-pytorch" / "iteration-0" / "SyntheticPawJan1-trainset95shuffle1",
        )
        self.assertEqual(
            layout.metadata,
            self.paw_project / "training-datasets" / "iteration-0"
            / "UnaugmentedDataSet_SyntheticPawJan1" / "metadata.yaml",
        )
        self.assertEqual([path.name for path in layout.snapshots()], ["snapshot-best-001.pt"])

    def test_missing_paw_csv_invokes_paw_runner(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            output = self.stage.ensure(self.video, self.paw_model, resume=True)
        self.assertEqual(self.runner.keys(), ["paw"])
        self.assertEqual(output, (self.paths.paw_tracking / f"{VIDEO_STEM}{PAW_SCORER}.csv").resolve())
        self.assertTrue(output.is_file())
        self.assertEqual(video_stem(output), VIDEO_STEM)

    def test_missing_facial_csv_invokes_facial_runner(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            output = self.stage.ensure(self.video, self.facial_model, resume=True)
        self.assertEqual(self.runner.keys(), ["facial"])
        self.assertEqual(
            output, (self.paths.facial_tracking / f"{VIDEO_STEM}{FACIAL_SCORER}.csv").resolve()
        )

    def test_valid_cached_paw_csv_skips_paw_dlc_with_resume(self) -> None:
        cached = self.cache_output(self.paw_model)
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            output = self.stage.ensure(self.video, self.paw_model, resume=True)
        self.assertEqual(self.runner.calls, [])
        self.assertEqual(output, cached)
        self.assertIn(f"[DLC Paw] SKIP_CACHED: {cached}", stream.getvalue())

    def test_valid_cached_facial_csv_skips_facial_dlc_with_resume(self) -> None:
        cached = self.cache_output(self.facial_model)
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            output = self.stage.ensure(self.video, self.facial_model, resume=True)
        self.assertEqual(self.runner.calls, [])
        self.assertEqual(output, cached)
        self.assertIn(f"[DLC Facial] SKIP_CACHED: {cached}", stream.getvalue())

    def test_cached_csv_is_ignored_without_resume(self) -> None:
        self.cache_output(self.paw_model)
        with contextlib.redirect_stdout(io.StringIO()):
            self.stage.ensure(self.video, self.paw_model, resume=False)
        self.assertEqual(self.runner.keys(), ["paw"])

    def test_invalid_cached_csv_is_rerun_with_resume(self) -> None:
        self.cache_output(self.paw_model, valid=False)
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            output = self.stage.ensure(self.video, self.paw_model, resume=True)
        self.assertEqual(self.runner.keys(), ["paw"])
        self.assertIn("cached output invalid; rerunning", stream.getvalue())
        self.assertTrue(output.is_file())
        self.assertEqual(
            [path.name for path in self.paths.paw_tracking.glob("*.csv")],
            [f"{VIDEO_STEM}{PAW_SCORER}.csv"],
        )

    def test_cached_csv_for_wrong_body_parts_is_rerun(self) -> None:
        # A facial CSV placed in the paw directory lacks the paw body parts.
        destination = self.paths.paw_tracking / f"{VIDEO_STEM}{PAW_SCORER}.csv"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(FACIAL_FIXTURE, destination)
        with contextlib.redirect_stdout(io.StringIO()):
            self.stage.ensure(self.video, self.paw_model, resume=True)
        self.assertEqual(self.runner.keys(), ["paw"])

    def test_ambiguous_cached_outputs_are_rejected(self) -> None:
        self.cache_output(self.paw_model)
        shutil.copy2(PAW_FIXTURE, self.paths.paw_tracking / f"{VIDEO_STEM}DLC_other.csv")
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(DlcStageError, "ambiguous cached outputs"):
                self.stage.ensure(self.video, self.paw_model, resume=True)
        self.assertEqual(self.runner.calls, [])

    def test_ambiguous_generated_outputs_are_rejected(self) -> None:
        stage = self.make_stage(FakeDlcRunner(extra_outputs=1))
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(DlcStageError, "expected exactly one CSV"):
                stage.ensure(self.video, self.paw_model, resume=False)
        self.assertFalse(self.paths.paw_tracking.exists())

    def test_generated_output_must_belong_to_the_video(self) -> None:
        def wrong_video_runner(runtime_config, video_path, model, destfolder):
            shutil.copy2(PAW_FIXTURE, destfolder / f"another_video{PAW_SCORER}.csv")
            return PAW_SCORER

        stage = self.make_stage(wrong_video_runner)
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(DlcStageError, "expected exactly one CSV"):
                stage.ensure(self.video, self.paw_model, resume=False)

    def test_superseded_output_for_same_video_is_replaced(self) -> None:
        stale = self.paths.paw_tracking / f"{VIDEO_STEM}DLC_old_scorer.csv"
        stale.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PAW_FIXTURE, stale)
        with contextlib.redirect_stdout(io.StringIO()):
            output = self.stage.ensure(self.video, self.paw_model, resume=False)
        self.assertFalse(stale.exists())
        self.assertEqual([p.name for p in self.paths.paw_tracking.glob("*.csv")], [output.name])

    def test_dlc_failure_is_identified_and_actionable(self) -> None:
        stage = self.make_stage(FakeDlcRunner(fail_for={"facial"}))
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            with self.assertRaisesRegex(DlcStageError, "DLC Facial failed") as context:
                stage.ensure(self.video, self.facial_model, resume=False)
        self.assertIn("[DLC Facial] START", stream.getvalue())
        self.assertIn("[DLC Facial] FAIL: DLC Facial failed", stream.getvalue())
        self.assertFalse(self.paths.facial_tracking.exists())
        self.assertIsInstance(context.exception, DlcStageError)

    def test_lfs_pointer_blocks_inference_with_pull_command(self) -> None:
        write_project(self.repository, self.paw_model, lfs_pointer_config=True)
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(DlcStageError, "Git LFS pointers") as context:
                self.stage.ensure(self.video, self.paw_model, resume=False)
        self.assertIn(
            'git lfs pull --include="deeplabcut-models/BIOMAP Paw Digits-Megan G-2026-06-10/**"',
            context.exception.next_action,
        )
        self.assertEqual(self.runner.calls, [])

    def test_missing_shuffle_is_reported(self) -> None:
        with patch.dict(os.environ, {"BIOMAP_DLC_PAW_SHUFFLE": "7"}):
            model = dlc_models()[0]
        with self.assertRaisesRegex(DlcStageError, "shuffle 7 is not present"):
            validate_project(self.paw_project, model)

    def test_unreadable_avi_header_defers_frame_check_to_simba(self) -> None:
        from biomap_pipeline.dlc_stage import _count_frames_if_avi

        avi = self.video_dir / f"{VIDEO_STEM}.avi"
        avi.write_bytes(b"SYNTHETIC TEST-ONLY NOT A REAL AVI")
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            self.assertIsNone(_count_frames_if_avi(avi))
            output = self.stage.ensure(avi, self.paw_model, resume=False)
        self.assertIn("frame count unavailable", stream.getvalue())
        self.assertTrue(output.is_file())

    def test_undetected_keypoints_are_explained(self) -> None:
        def nan_runner(runtime_config, video_path, model, destfolder):
            text = PAW_FIXTURE.read_text(encoding="utf-8").splitlines()
            cells = text[3].split(",")
            cells[1] = ""
            text[3] = ",".join(cells)
            (destfolder / f"{video_path.stem}{PAW_SCORER}.csv").write_text(
                "\n".join(text) + "\n", encoding="utf-8"
            )
            return PAW_SCORER

        stage = self.make_stage(nan_runner)
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(DlcStageError, "1 tracking cell\\(s\\) empty") as context:
                stage.ensure(self.video, self.paw_model, resume=False)
        self.assertIn("NaN policy", str(context.exception))
        self.assertFalse(self.paths.paw_tracking.exists())

    def test_is_lfs_pointer(self) -> None:
        pointer = self.root / "pointer.yaml"
        pointer.write_bytes(LFS_POINTER)
        self.assertTrue(is_lfs_pointer(pointer))
        self.assertFalse(is_lfs_pointer(PAW_FIXTURE))

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
        self.assertNotIn("C:\\Users\\someone", text.split("video_sets")[0])
        self.assertIn("snapshotindex: -1", text)
        snapshot = runtime / "dlc-models-pytorch" / "iteration-0" / "SyntheticPawJan1-trainset95shuffle1" / "train" / "snapshot-best-001.pt"
        self.assertTrue(snapshot.is_symlink())
        self.assertFalse((runtime / "dlc-models-pytorch").is_symlink())
        self.assertTrue((runtime / "dlc-models-pytorch" / "iteration-0" / "SyntheticPawJan1-trainset95shuffle1" / "test" / "pose_cfg.yaml").is_file())
        self.assertTrue((runtime / "training-datasets" / "iteration-0" / "UnaugmentedDataSet_SyntheticPawJan1" / "metadata.yaml").is_file())
        self.assertEqual(self.runner.calls[0][3], self.paths.dlc_predictions("paw", VIDEO_STEM))

    def test_headless_api_call_matches_production_contract_for_both_models(self) -> None:
        avi = self.video_dir / f"{VIDEO_STEM}.avi"
        avi.write_bytes(b"SYNTHETIC TEST-ONLY NOT A REAL AVI")
        for model in (self.paw_model, self.facial_model):
            with self.subTest(model=model.key):
                layout = validate_project(model.project_dir(self.repository), model)
                runtime_config = self.stage._prepare_runtime_project(layout, model)
                destination = self.paths.dlc_predictions(model.key, VIDEO_STEM)
                analyze_videos = Mock(return_value=f"DLC_Synthetic_{model.key}")
                fake_deeplabcut = SimpleNamespace(
                    __version__="synthetic-test-only",
                    analyze_videos=analyze_videos,
                )
                args = headless_parser().parse_args([
                    "--config", str(runtime_config),
                    "--video", str(avi),
                    "--shuffle", str(model.shuffle),
                    "--trainingsetindex", str(model.trainingsetindex),
                    "--destfolder", str(destination),
                    "--label", model.label,
                ])
                with (
                    patch.dict("sys.modules", {"deeplabcut": fake_deeplabcut}),
                    contextlib.redirect_stdout(io.StringIO()),
                ):
                    scorer = headless_analyze(args)
                self.assertEqual(scorer, f"DLC_Synthetic_{model.key}")
                analyze_videos.assert_called_once_with(
                    str(runtime_config.resolve()),
                    [str(avi.resolve())],
                    video_extensions=".avi",
                    shuffle=model.shuffle,
                    trainingsetindex=model.trainingsetindex,
                    save_as_csv=True,
                    destfolder=str(destination.resolve()),
                    device="cpu",
                )

    def test_headless_command_uses_configured_environment_and_cpu_default(self) -> None:
        stage = DlcStage(self.repository, contribution_paths=self.paths, dlc_environment="synthetic-dlc-env")
        layout = validate_project(self.paw_project, self.paw_model)
        runtime_config = stage._prepare_runtime_project(layout, self.paw_model)
        destfolder = self.paths.dlc_predictions("paw", VIDEO_STEM)
        with (
            patch("biomap_pipeline.dlc_stage.shutil.which", return_value="/synthetic/bin/conda"),
            patch.dict(os.environ, {}, clear=True),
        ):
            command = stage._conda_command(runtime_config, self.video, self.paw_model, destfolder)
            environment = stage._subprocess_environment()
        self.assertEqual(
            command[:6],
            ["/synthetic/bin/conda", "run", "--no-capture-output", "-n", "synthetic-dlc-env", "python"],
        )
        self.assertIn("biomap_pipeline.dlc_headless", command)
        self.assertEqual(command[command.index("--shuffle") + 1], "1")
        self.assertEqual(command[command.index("--device") + 1], "cpu")
        self.assertEqual(command[command.index("--destfolder") + 1], str(destfolder))
        self.assertEqual(environment["PYTHONUNBUFFERED"], "1")
        self.assertEqual(environment["PYTORCH_ENABLE_MPS_FALLBACK"], "1")
        package_parent = Path(cli.__file__).resolve().parents[1]
        self.assertEqual(environment["PYTHONPATH"].split(os.pathsep)[0], str(package_parent))
        parsed = headless_parser().parse_args(command[command.index("--config"):])
        self.assertEqual(parsed.config, runtime_config)
        self.assertEqual(parsed.video, self.video)
        self.assertEqual(parsed.destfolder, destfolder)
        self.assertEqual(parsed.device, "cpu")
        self.assertEqual(SCORER_PREFIX, HEADLESS_SCORER_PREFIX)

    def test_biomap_dlc_device_override_is_passed_without_auto_selection(self) -> None:
        stage = DlcStage(self.repository, contribution_paths=self.paths)
        layout = validate_project(self.paw_project, self.paw_model)
        runtime_config = stage._prepare_runtime_project(layout, self.paw_model)
        destination = self.paths.dlc_predictions("paw", VIDEO_STEM)
        with (
            patch("biomap_pipeline.dlc_stage.shutil.which", return_value="/synthetic/bin/conda"),
            patch.dict(os.environ, {"BIOMAP_DLC_DEVICE": "cuda"}),
        ):
            command = stage._conda_command(
                runtime_config, self.video, self.paw_model, destination
            )
        self.assertEqual(command[command.index("--device") + 1], "cuda")

    def test_headless_output_is_streamed_with_stage_prefix_and_scorer_is_captured(self) -> None:
        class FakeProcess:
            last_command = None
            last_kwargs = None

            def __init__(self, command, **kwargs):
                type(self).last_command = command
                type(self).last_kwargs = kwargs
                self.kwargs = kwargs
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
            scorer = stage._run_headless(self.root / "config.yaml", self.video, self.paw_model, self.root / "dest")
        self.assertEqual(scorer, PAW_SCORER)
        lines = stream.getvalue().splitlines()
        self.assertIn("[DLC Paw] Running pose prediction with batch size 8", lines)
        self.assertIn("[DLC Paw]  100%|##########| 6/6", lines)
        self.assertNotIn(SCORER_PREFIX, stream.getvalue())
        self.assertIn("-u", FakeProcess.last_command)
        self.assertEqual(FakeProcess.last_kwargs["env"]["PYTHONUNBUFFERED"], "1")
        self.assertEqual(FakeProcess.last_kwargs["stdout"], subprocess.PIPE)
        self.assertEqual(FakeProcess.last_kwargs["stderr"], subprocess.STDOUT)

    def test_headless_nonzero_exit_fails_the_stage(self) -> None:
        class FailingProcess:
            def __init__(self, command, **kwargs):
                self.stdout = io.BytesIO(b"[DLC Paw] FAIL: synthetic\n")

            def wait(self):
                return 3

        stage = DlcStage(self.repository, contribution_paths=self.paths)
        with (
            patch("biomap_pipeline.dlc_stage.subprocess.Popen", FailingProcess),
            patch("biomap_pipeline.dlc_stage.shutil.which", return_value="/synthetic/bin/conda"),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            with self.assertRaisesRegex(
                DlcStageError, "exited with status 3.*synthetic"
            ):
                stage._run_headless(self.root / "config.yaml", self.video, self.paw_model, self.root / "dest")


class DlcCliWiringTests(DlcStageTestCase):
    """Drive ``biomap analyze`` with the DLC runner and SimBA stage faked."""

    def run_analyze(self, *flags: str, runner: FakeDlcRunner | None = None):
        runner = runner or self.runner
        simba = CapturingSimbaStage(self.paths)
        stream = io.StringIO()
        with (
            patch("biomap_pipeline.cli.ContributionPaths", return_value=self.paths),
            patch("biomap_pipeline.cli.repository_root", return_value=self.repository),
            patch("biomap_pipeline.cli.SimbaStage", return_value=simba),
            patch(
                "biomap_pipeline.cli.DlcStage",
                side_effect=lambda repository, **kwargs: DlcStage(
                    repository, runner=runner, **kwargs
                ),
            ),
            contextlib.redirect_stdout(stream),
        ):
            exit_code = main(["analyze", str(self.video_dir), *flags])
        return exit_code, stream.getvalue(), simba, runner

    def status(self) -> dict[str, object]:
        return json.loads(self.paths.run_status.read_text(encoding="utf-8"))

    def test_dlc_only_entry_point_runs_paw_and_never_constructs_simba(self) -> None:
        stream = io.StringIO()
        with (
            patch("biomap_pipeline.cli.ContributionPaths", return_value=self.paths),
            patch("biomap_pipeline.cli.repository_root", return_value=self.repository),
            patch(
                "biomap_pipeline.cli.DlcStage",
                side_effect=lambda repository, **kwargs: DlcStage(
                    repository, runner=self.runner, **kwargs
                ),
            ),
            patch("biomap_pipeline.cli.SimbaStage") as simba_constructor,
            contextlib.redirect_stdout(stream),
        ):
            exit_code = main(["dlc", str(self.video_dir), "--resume"])
        self.assertEqual(exit_code, 0, stream.getvalue())
        self.assertEqual(self.runner.keys(), ["paw"])
        simba_constructor.assert_not_called()
        self.assertIn("[n8n] DeepLabCut command started", stream.getvalue())
        self.assertIn("[DLC Paw] PASS:", stream.getvalue())
        self.assertNotIn("[DLC Facial]", stream.getvalue())
        self.assertNotIn("[Merge]", stream.getvalue())
        self.assertNotIn("[SimBA]", stream.getvalue())

    def test_dlc_only_entry_point_returns_failure_without_downstream_work(self) -> None:
        runner = FakeDlcRunner(fail_for={"paw"})
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
            patch("biomap_pipeline.cli.SimbaStage") as simba_constructor,
            contextlib.redirect_stdout(stream),
        ):
            exit_code = main(["dlc", str(self.video_dir), "--resume"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(runner.keys(), ["paw"])
        simba_constructor.assert_not_called()
        self.assertIn("DLC Paw failed: synthetic DeepLabCut error", stream.getvalue())

    def test_production_analyze_invokes_both_dlc_models_when_outputs_are_missing(self) -> None:
        exit_code, log, simba, runner = self.run_analyze()
        self.assertEqual(exit_code, 0, log)
        self.assertEqual(runner.keys(), ["paw", "facial"])
        self.assertEqual(simba.calls, 1)
        self.assertEqual(self.status()["state"], "PASS")

    def test_cli_uses_biomap_dlc_environment_for_the_dlc_subprocess_stage(self) -> None:
        captured: dict[str, str] = {}

        def stage_factory(repository, **kwargs):
            captured["environment"] = kwargs["dlc_environment"]
            return DlcStage(repository, runner=self.runner, **kwargs)

        simba = CapturingSimbaStage(self.paths)
        with (
            patch.dict(os.environ, {"BIOMAP_DLC_ENV": "synthetic-from-environment"}),
            patch("biomap_pipeline.cli.ContributionPaths", return_value=self.paths),
            patch("biomap_pipeline.cli.repository_root", return_value=self.repository),
            patch("biomap_pipeline.cli.SimbaStage", return_value=simba),
            patch("biomap_pipeline.cli.DlcStage", side_effect=stage_factory),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            exit_code = main(["analyze", str(self.video_dir)])
        self.assertEqual(exit_code, 0)
        self.assertEqual(captured["environment"], "synthetic-from-environment")

    def test_production_analyze_with_resume_runs_dlc_when_outputs_are_missing(self) -> None:
        exit_code, log, _simba, runner = self.run_analyze("--resume")
        self.assertEqual(exit_code, 0, log)
        self.assertEqual(runner.keys(), ["paw", "facial"])
        self.assertNotIn("DLC output missing", log)

    def test_resume_skips_only_the_cached_model(self) -> None:
        self.cache_output(self.paw_model)
        exit_code, log, _simba, runner = self.run_analyze("--resume")
        self.assertEqual(exit_code, 0, log)
        self.assertEqual(runner.keys(), ["facial"])
        self.assertIn("[DLC Paw] SKIP_CACHED", log)
        self.assertIn("[DLC Facial] START", log)

    def test_exact_generated_paths_reach_merge(self) -> None:
        captured: dict[str, Path] = {}
        real_merge = cli.merge_paw_and_facial

        def capturing_merge(paw_csv, facial_csv, destination, **kwargs):
            captured["paw"] = Path(paw_csv)
            captured["facial"] = Path(facial_csv)
            return real_merge(paw_csv, facial_csv, destination, **kwargs)

        with patch("biomap_pipeline.cli.merge_paw_and_facial", side_effect=capturing_merge):
            exit_code, log, _simba, _runner = self.run_analyze()
        self.assertEqual(exit_code, 0, log)
        expected_paw = (self.paths.paw_tracking / f"{VIDEO_STEM}{PAW_SCORER}.csv").resolve()
        expected_facial = (self.paths.facial_tracking / f"{VIDEO_STEM}{FACIAL_SCORER}.csv").resolve()
        self.assertEqual(captured, {"paw": expected_paw, "facial": expected_facial})
        self.assertIn(f"[DLC Paw] PASS: {expected_paw}", log)
        self.assertIn(f"[DLC Facial] PASS: {expected_facial}", log)
        self.assertIn(f"[Merge] START: {expected_paw} + {expected_facial}", log)

    def test_exact_merged_path_reaches_simba(self) -> None:
        exit_code, log, simba, _runner = self.run_analyze()
        self.assertEqual(exit_code, 0, log)
        merged = self.paths.merged_csv(VIDEO_STEM).resolve()
        self.assertEqual(simba.merged_csv, merged)
        self.assertIn(f"[Merge] PASS: {merged}", log)
        self.assertIn(f"[SimBA] INPUT: {merged}", log)
        self.assertLess(log.index("[DLC Paw] START"), log.index("[DLC Facial] START"))
        self.assertLess(log.index("[DLC Facial] PASS"), log.index("[Merge] PASS"))
        self.assertLess(log.index("[Merge] PASS"), log.index("[SimBA] INPUT"))

    def test_dlc_failure_stops_downstream_merge_and_simba(self) -> None:
        exit_code, log, simba, runner = self.run_analyze(runner=FakeDlcRunner(fail_for={"paw"}))
        self.assertEqual(exit_code, 1)
        self.assertEqual(runner.keys(), ["paw"])
        self.assertEqual(simba.calls, 0)
        self.assertNotIn("[Merge]", log)
        self.assertNotIn("[SimBA] INPUT", log)
        self.assertFalse(self.paths.merged_csv(VIDEO_STEM).exists())
        status = self.status()
        self.assertEqual(status["state"], "FAIL")
        self.assertIn("DLC Paw failed", status["error"])
        self.assertIn("DLC Paw", status["next_action"])
        markers = [json.loads(line.removeprefix(STDOUT_PREFIX)) for line in log.splitlines() if line.startswith(STDOUT_PREFIX)]
        self.assertEqual(markers[-1], status)

    def test_facial_failure_after_paw_success_still_fails(self) -> None:
        exit_code, log, simba, runner = self.run_analyze(runner=FakeDlcRunner(fail_for={"facial"}))
        self.assertEqual(exit_code, 1)
        self.assertEqual(runner.keys(), ["paw", "facial"])
        self.assertEqual(simba.calls, 0)
        self.assertIn("DLC Facial failed", self.status()["error"])

    def test_lfs_pointer_failure_reports_pull_command_in_next_action(self) -> None:
        write_project(self.repository, self.facial_model, lfs_pointer_config=True)
        exit_code, _log, _simba, runner = self.run_analyze()
        self.assertEqual(exit_code, 1)
        self.assertEqual(runner.keys(), ["paw"])
        status = self.status()
        self.assertIn("DLC Facial", status["error"])
        self.assertIn("git lfs pull --include=", status["next_action"])

    def test_demo_never_invokes_dlc(self) -> None:
        with patch("biomap_pipeline.cli.DlcStage") as constructor:
            simba = CapturingSimbaStage(self.paths)
            stream = io.StringIO()
            with (
                patch("biomap_pipeline.cli.ContributionPaths", return_value=self.paths),
                patch("biomap_pipeline.cli.repository_root", return_value=self.repository),
                patch("biomap_pipeline.cli.SimbaStage", return_value=simba),
                contextlib.redirect_stdout(stream),
            ):
                exit_code = main(["analyze", str(self.video_dir), "--demo"])
        constructor.assert_not_called()
        self.assertEqual(exit_code, 1)
        self.assertEqual(simba.calls, 0)
        status = self.status()
        self.assertEqual(status["state"], "FAIL")
        self.assertIn("--demo never runs DeepLabCut", status["error"])
        self.assertIn("[DLC] --demo: cache-only mode", stream.getvalue())

    def test_demo_uses_cached_outputs_only(self) -> None:
        paw = self.cache_output(self.paw_model)
        facial = self.cache_output(self.facial_model)
        with patch("biomap_pipeline.cli.DlcStage") as constructor:
            simba = CapturingSimbaStage(self.paths)
            stream = io.StringIO()
            with (
                patch("biomap_pipeline.cli.ContributionPaths", return_value=self.paths),
                patch("biomap_pipeline.cli.repository_root", return_value=self.repository),
                patch("biomap_pipeline.cli.SimbaStage", return_value=simba),
                contextlib.redirect_stdout(stream),
            ):
                exit_code = main(["analyze", str(self.video_dir), "--demo"])
        constructor.assert_not_called()
        self.assertEqual(exit_code, 0, stream.getvalue())
        self.assertEqual(simba.merged_csv, self.paths.merged_csv(VIDEO_STEM).resolve())
        self.assertIn(f"[DLC Paw] PASS: {paw}", stream.getvalue())
        self.assertIn(f"[DLC Facial] PASS: {facial}", stream.getvalue())

    def test_handoff_without_dlc_stage_uses_cached_outputs(self) -> None:
        paw = self.cache_output(self.paw_model)
        facial = self.cache_output(self.facial_model)
        simba = CapturingSimbaStage(self.paths)
        with contextlib.redirect_stdout(io.StringIO()):
            merged, _result = _handoff_to_simba(
                video_path=self.video, paths=self.paths,
                paw={VIDEO_STEM: paw}, facial={VIDEO_STEM: facial},
                stage=simba, resume=False,
            )
        self.assertIs(merged, simba.merged_csv)


if __name__ == "__main__":
    unittest.main()
