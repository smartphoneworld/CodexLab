from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app.service import complete_task, get_task


class CompleteTaskTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.data_file = Path(directory.name) / "tasks.json"
        self.tasks = [
            {
                "id": task_id,
                "title": f"Task {task_id}",
                "description": "",
                "status": "open",
                "priority": "medium",
                "created_at": "2026-02-25T16:00:00+00:00",
                "completed_at": None,
            }
            for task_id in (1, 2)
        ]
        self.data_file.write_text(json.dumps(self.tasks), encoding="utf-8")
        patcher = patch("app.store.DATA_FILE", self.data_file)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_completion_persists_across_disk_reads_and_processes(self):
        completed = complete_task(1)
        self.assertIsNotNone(completed)
        self.assertEqual(completed["status"], "done")
        timestamp = datetime.fromisoformat(completed["completed_at"])
        self.assertIsNotNone(timestamp.utcoffset())
        expected = dict(self.tasks[0], status="done", completed_at=completed["completed_at"])
        self.assertEqual(completed, expected)
        self.assertEqual(
            json.loads(self.data_file.read_text(encoding="utf-8")),
            [expected, self.tasks[1]],
        )
        self.assertEqual(get_task(1), completed)

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import json, sys; from pathlib import Path; "
                "from app import store; store.DATA_FILE = Path(sys.argv[1]); "
                "from app.service import get_task; print(json.dumps(get_task(1)))",
                str(self.data_file),
            ],
            cwd=Path(__file__).resolve().parent.parent,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(json.loads(result.stdout), completed)

    def test_missing_task_does_not_change_storage(self):
        original = self.data_file.read_bytes()
        self.assertIsNone(complete_task(999))
        self.assertEqual(self.data_file.read_bytes(), original)
