import os
import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent


class AppWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.previous = os.environ.get("FOCUS_DATA_HOME")
        os.environ["FOCUS_DATA_HOME"] = self.tmp.name
        self.at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=15).run()

    def tearDown(self):
        if self.previous is None:
            os.environ.pop("FOCUS_DATA_HOME", None)
        else:
            os.environ["FOCUS_DATA_HOME"] = self.previous
        self.tmp.cleanup()

    def button(self, label):
        return next(b for b in self.at.button if b.label == label)

    def test_empty_workspace_and_all_demo_pages(self):
        self.assertFalse(self.at.exception)
        self.assertEqual(self.at.metric[0].value, "0")
        self.button("Explore sample workspace").click().run()
        self.assertFalse(self.at.exception)
        self.assertGreater(int(self.at.metric[0].value), 0)
        for page in ("board", "agenda", "notes", "focus", "review", "settings"):
            self.at.switch_page(f"app_pages/{page}.py").run()
            self.assertFalse(self.at.exception, str(self.at.exception))
        self.button("Leave demo").click().run()
        self.at.switch_page("app_pages/home.py").run()
        self.assertEqual(self.at.metric[0].value, "0")

    def test_task_capture_and_note_save(self):
        self.button("Capture a task").click().run()
        self.assertFalse(self.at.exception)
        next(t for t in self.at.text_input if t.label == "Task title").set_value("Build an accessible app")
        self.button("Save task").click().run()
        self.assertFalse(self.at.exception)
        self.at.run()
        self.assertEqual(self.at.metric[0].value, "1")
        self.at.switch_page("app_pages/notes.py").run()
        next(t for t in self.at.text_input if t.label == "Note title").set_value("An idea")
        next(t for t in self.at.text_area if t.label == "Markdown").set_value("# Keep it useful")
        self.button("Save note").click().run()
        self.assertFalse(self.at.exception)
        from focus.store import Store
        self.assertEqual(Store().notes()[0]["body"], "# Keep it useful")

    def test_focus_start_pause_finish_and_preferences(self):
        self.at.switch_page("app_pages/focus.py").run()
        next(t for t in self.at.text_input if t.label == "Session intention").set_value("Work on one thing")
        self.button("Start focusing").click().run()
        self.assertFalse(self.at.exception)
        self.button("Pause").click().run()
        self.assertFalse(self.at.exception)
        self.button("Finish & record").click().run()
        self.assertFalse(self.at.exception)
        self.at.switch_page("app_pages/settings.py").run()
        next(t for t in self.at.text_input if "first name" in t.label).set_value("Zubair")
        next(s for s in self.at.selectbox if s.label == "Accent palette").select("Violet")
        self.button("Save preferences").click().run()
        self.assertFalse(self.at.exception)
        from focus.store import Store
        self.assertEqual(Store().settings()["accent"], "Violet")

    def test_task_details_checklist_and_recovery(self):
        from focus.store import Store
        db = Store()
        task = db.save_task("Ship an accessible app", status="Doing")
        self.at.run()
        self.button("Details").click().run()
        self.assertFalse(self.at.exception)
        next(t for t in self.at.text_input if t.label == "Add a checklist item").set_value("Check tab order")
        self.button("Add item").click().run()
        self.assertFalse(self.at.exception)
        next(c for c in self.at.checkbox if c.label == "Check tab order").check().run()
        self.assertFalse(self.at.exception)
        self.assertEqual(db.checklist(task)[0]["done"], 1)
        self.button("Move task to trash").click().run()
        self.at.switch_page("app_pages/settings.py").run()
        self.button("Restore").click().run()
        self.assertFalse(self.at.exception)
        self.assertIsNone(db.get("tasks", task)["deleted_at"])


if __name__ == "__main__":
    unittest.main()
