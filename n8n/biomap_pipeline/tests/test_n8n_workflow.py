"""Structural checks for the importable BIOMAP n8n workflow."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


WORKFLOW_PATH = Path(__file__).resolve().parents[2] / "n8n_biomap_workflow.json"


class N8nWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
        cls.nodes = {node["name"]: node for node in cls.workflow["nodes"]}

    def test_node_names_and_ids_are_unique(self) -> None:
        names = [node["name"] for node in self.workflow["nodes"]]
        ids = [node["id"] for node in self.workflow["nodes"]]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_connection_resolves_to_a_node(self) -> None:
        for source, outputs in self.workflow["connections"].items():
            self.assertIn(source, self.nodes)
            for branch in outputs["main"]:
                for connection in branch:
                    self.assertIn(connection["node"], self.nodes)

    def test_workflow_is_exactly_the_three_node_dlc_runner(self) -> None:
        self.assertEqual(
            self.workflow["name"], "BIOMAP DeepLabCut Runner"
        )
        self.assertEqual(
            list(self.nodes), ["Manual Trigger", "Pipeline Inputs", "Run DeepLabCut"]
        )
        connections = self.workflow["connections"]
        self.assertEqual(
            connections["Manual Trigger"]["main"][0][0]["node"],
            "Pipeline Inputs",
        )
        self.assertEqual(
            connections["Pipeline Inputs"]["main"][0][0]["node"],
            "Run DeepLabCut",
        )
        self.assertEqual(set(connections), {"Manual Trigger", "Pipeline Inputs"})

    def test_pipeline_inputs_only_exposes_video_directory(self) -> None:
        assignments = self.nodes["Pipeline Inputs"]["parameters"]["assignments"]["assignments"]
        self.assertEqual([item["name"] for item in assignments], ["video_dir"])
        self.assertEqual(assignments[0]["value"], "={{ $env.BIOMAP_VIDEO_DIR }}")

    def test_execute_command_is_portable_unbuffered_and_logged(self) -> None:
        node = self.nodes["Run DeepLabCut"]
        command = node["parameters"]["command"]
        self.assertIn('cd "$BIOMAP_REPO"', command)
        for variable in (
            "BIOMAP_REPO",
            "BIOMAP_VIDEO_DIR",
            "BIOMAP_DLC_ENV",
            "BIOMAP_DLC_DEVICE",
        ):
            self.assertIn(variable, command)
        self.assertIn("set -o pipefail", command)
        self.assertIn("PYTHONUNBUFFERED=1", command)
        self.assertIn('biomap dlc "$BIOMAP_VIDEO_DIR" --resume', command)
        self.assertIn("2>&1", command)
        self.assertIn("| tee n8n/biomap_pipeline/results/logs/dlc_live.log", command)
        self.assertNotIn("biomap analyze", command)
        self.assertNotIn("SimBA", command)
        self.assertNotIn("/Users/", command)
        self.assertEqual(node["onError"], "continueRegularOutput")

    def test_execute_command_has_valid_bash_syntax(self) -> None:
        command = self.nodes["Run DeepLabCut"]["parameters"]["command"]
        completed = subprocess.run(
            ["/bin/bash", "-n", "-c", command],
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_deleted_state_and_simba_nodes_are_absent(self) -> None:
        stale_names = {
            "Parse BIOMAP State",
            "If Success",
            "Success",
            "If ROI Required",
            "ROI Required",
            "If Calibration Required",
            "Calibration Required",
            "Failure",
            "SimBA",
        }
        self.assertTrue(stale_names.isdisjoint(self.nodes))


if __name__ == "__main__":
    unittest.main()
