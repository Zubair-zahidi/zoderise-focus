import io
import json
import sqlite3
import tempfile
import unittest
import zipfile
from datetime import date, timedelta
from pathlib import Path

from focus.store import Store


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.now = 1791887400.0
        self.db = Store(Path(self.tmp.name) / "focus.sqlite3", clock=lambda: self.now)

    def tearDown(self):
        self.tmp.cleanup()

    def test_task_edit_search_trash_and_project_archive(self):
        project = self.db.save_project("Build")
        task = self.db.save_task("Check keyboard navigation", project, tags="UI, ui, Access")
        self.assertEqual(len(self.db.tasks(query="access")), 1)
        self.db.save_task("Ship accessible UI", project, status="Doing", identifier=task)
        self.assertEqual(self.db.get("tasks", task)["status"], "Doing")
        self.db.trash("tasks", task)
        self.assertEqual(self.db.tasks(), [])
        self.assertEqual(len(self.db.tasks(trash=True)), 1)
        self.db.trash("tasks", task, restore=True)
        self.db.archive_project(project)
        self.assertEqual(self.db.tasks(), [])
        self.assertEqual(len(self.db.tasks(include_archived=True)), 1)
        self.db.archive_project(project, False)
        self.assertEqual(len(self.db.tasks()), 1)

    def test_recurring_completion_is_idempotent_and_copies_checks(self):
        task = self.db.save_task("Weekly review", due_date=date.today(), recurrence="Weekly")
        self.db.add_check(task, "Choose one outcome")
        self.db.check(self.db.checklist(task)[0]["id"], True)
        self.db.move_task(task, "Done")
        self.db.move_task(task, "Done")
        self.db.move_task(task, "Next")
        self.db.move_task(task, "Done")
        rows = self.db.tasks()
        self.assertEqual(len(rows), 2)
        followup = next(t for t in rows if t["id"] != task)
        self.assertEqual(followup["due_date"], (date.today() + timedelta(days=7)).isoformat())
        self.assertEqual(self.db.checklist(followup["id"])[0]["done"], 0)

    def test_validation_does_not_write_invalid_tasks(self):
        with self.assertRaises(ValueError):
            self.db.save_task(" ")
        with self.assertRaises(ValueError):
            self.db.save_task("Read", recurrence="Daily")
        with self.assertRaises(ValueError):
            self.db.save_task("Read", due_date="2026-02-30")
        self.assertEqual(self.db.tasks(), [])

    def test_timer_pause_resume_restart_and_single_session(self):
        self.db.start_focus("Design", 25)
        self.now += 100
        self.db.control_focus("pause")
        self.now += 400
        self.assertEqual(self.db.elapsed(self.db.active()), 100)
        reopened = Store(self.db.path, clock=lambda: self.now)
        self.assertEqual(reopened.active()["state"], "paused")
        with self.assertRaises(ValueError):
            self.db.start_focus("Other", 5)
        self.db.control_focus("resume")
        self.now += 80
        self.db.control_focus("complete")
        self.assertIsNone(self.db.active())
        self.assertEqual(self.db.history()[0]["accumulated_seconds"], 180)

    def test_timer_cap_and_cancel(self):
        self.db.start_focus("One minute", 1)
        self.now += 1000
        self.assertEqual(self.db.elapsed(self.db.active()), 60)
        self.db.control_focus("cancel")
        self.assertEqual(self.db.history()[0]["state"], "cancelled")

    def test_backup_roundtrip_safety_copy_and_paused_timer(self):
        p = self.db.save_project("Build")
        t = self.db.save_task("Ship", p, tags="release")
        self.db.add_check(t, "Run tests")
        self.db.save_note("Plan", "# Ship it", p)
        self.db.start_focus("Ship", 5, t)
        self.now += 90
        blob = self.db.backup()
        self.db.control_focus("cancel")
        self.db.save_task("Only after backup")
        safety = self.db.restore(blob)
        self.assertTrue(safety.exists())
        self.assertEqual(len(self.db.tasks()), 1)
        self.assertEqual(self.db.active()["state"], "paused")
        self.assertEqual(self.db.elapsed(self.db.active()), 90)
        self.assertEqual(len(self.db.inspect_backup(safety.read_bytes())["tables"]["tasks"]), 2)

    def test_corrupt_or_hostile_backup_leaves_workspace_untouched(self):
        self.db.save_task("Keep this")
        good = self.db.backup()
        with zipfile.ZipFile(io.BytesIO(good)) as z:
            manifest = z.read("manifest.json")
            payload = z.read("focus.json")
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            z.writestr("manifest.json", manifest)
            z.writestr("focus.json", payload + b" ")
        with self.assertRaises(ValueError):
            self.db.restore(out.getvalue())
        for invalid in (b"not zip",):
            with self.assertRaises(ValueError):
                self.db.restore(invalid)
        snapshot = self.db.snapshot()
        snapshot["tables"]["tasks"][0]["project_id"] = "missing"
        payload = json.dumps(snapshot).encode()
        import hashlib
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            z.writestr("focus.json", payload)
            z.writestr("manifest.json", json.dumps({"sha256": hashlib.sha256(payload).hexdigest()}))
        with self.assertRaises(ValueError):
            self.db.restore(out.getvalue())
        self.assertEqual(self.db.tasks()[0]["title"], "Keep this")

    def test_note_search_export_and_calendar_escaping(self):
        note = self.db.save_note("Reference", "Markdown contains networking ideas", tags="research")
        self.assertEqual(self.db.notes(query="networking")[0]["id"], note)
        task = self.db.save_task("=HYPERLINK(\"bad\")", due_date=date.today(), description="A,b; c\nline")
        self.assertIn("'=HYPERLINK", self.db.csv_export())
        ics = self.db.calendar_export()
        self.assertIn("DTEND;VALUE=DATE:", ics)
        self.assertIn("A\\,b\\; c\\nline", ics)
        self.db.move_task(task, "Done")
        self.assertNotIn("BEGIN:VEVENT", self.db.calendar_export())


if __name__ == "__main__":
    unittest.main()
