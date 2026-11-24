import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app.schemas import TaskStatus
from app.service import list_tasks


class ListTasksTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        data_file = Path(directory.name) / "tasks.json"
        self.tasks = [
            {"id": 1, "status": "open"},
            {"id": 2, "status": "done"},
            {"id": 3, "status": "open"},
        ]
        data_file.write_text(json.dumps(self.tasks), encoding="utf-8")
        patcher = patch("app.store.DATA_FILE", data_file)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_no_status_returns_all_tasks(self):
        self.assertEqual(list_tasks(), self.tasks)

    def test_open_status_returns_only_open_tasks(self):
        self.assertEqual(
            list_tasks(status=TaskStatus.open), [self.tasks[0], self.tasks[2]]
        )

    def test_done_status_returns_only_done_tasks(self):
        self.assertEqual(list_tasks(status=TaskStatus.done), [self.tasks[1]])
