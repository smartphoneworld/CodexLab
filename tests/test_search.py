import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app.schemas import TaskStatus
from app.service import complete_task, list_tasks


class SearchTasksTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        data_file = Path(directory.name) / "tasks.json"
        self.tasks = [
            {
                "id": 1,
                "status": "open",
                "title": "Launch checklist",
                "description": "Coordinate the release.",
            },
            {
                "id": 2,
                "status": "done",
                "title": "Archive report",
                "description": "Record LAUNCH findings.",
            },
            {
                "id": 3,
                "status": "open",
                "title": "Plan workshop",
                "description": "Review the roadmap.",
            },
        ]
        data_file.write_text(json.dumps(self.tasks), encoding="utf-8")
        patcher = patch("app.store.DATA_FILE", data_file)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_title_substring(self):
        self.assertEqual(list_tasks(q="check"), [self.tasks[0]])

    def test_description_substring(self):
        self.assertEqual(list_tasks(q="release"), [self.tasks[0]])

    def test_search_is_case_insensitive_across_both_fields(self):
        for query in ("launch", "LAUNCH", "LaUnCh"):
            with self.subTest(query=query):
                self.assertEqual(list_tasks(q=query), self.tasks[:2])

    def test_no_match_returns_empty_list(self):
        self.assertEqual(list_tasks(q="nonexistent"), [])

    def test_search_and_status_both_apply(self):
        cases = [
            (TaskStatus.open, "launch", [self.tasks[0]]),
            (TaskStatus.done, "launch", [self.tasks[1]]),
            (TaskStatus.open, "report", []),
            (TaskStatus.done, "release", []),
        ]
        for status, query, expected in cases:
            with self.subTest(status=status, query=query):
                self.assertEqual(list_tasks(status=status, q=query), expected)

    def test_omitted_query_preserves_listing_and_status_filter(self):
        self.assertEqual(list_tasks(), self.tasks)
        self.assertEqual(
            list_tasks(status=TaskStatus.open), [self.tasks[0], self.tasks[2]]
        )

    def test_completed_task_moves_to_done_search_results(self):
        completed = complete_task(1)
        self.assertEqual(list_tasks(status=TaskStatus.open, q="launch"), [])
        self.assertEqual(
            list_tasks(status=TaskStatus.done, q="launch"),
            [completed, self.tasks[1]],
        )
