"""Version 1.1 planning and recovery extensions, with backward-compatible tables."""
import calendar
import json
import time
import uuid
from datetime import date, datetime, timedelta

EXTRA_TABLES = ("task_plans", "dependencies", "daily_picks", "note_versions", "note_drafts", "templates", "alerts")
EXTRA_SCHEMA = """
CREATE TABLE IF NOT EXISTS task_plans (
 task_id TEXT PRIMARY KEY REFERENCES tasks(id), sort_order REAL NOT NULL DEFAULT 0,
 scheduled_day TEXT, weekdays TEXT NOT NULL DEFAULT '[]', interval_days INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS dependencies (
 task_id TEXT NOT NULL REFERENCES tasks(id), prerequisite_id TEXT NOT NULL REFERENCES tasks(id),
 PRIMARY KEY(task_id,prerequisite_id));
CREATE TABLE IF NOT EXISTS daily_picks (
 day TEXT NOT NULL, position INTEGER NOT NULL, task_id TEXT NOT NULL REFERENCES tasks(id), PRIMARY KEY(day,position), UNIQUE(day,task_id));
CREATE TABLE IF NOT EXISTS note_versions (
 id TEXT PRIMARY KEY, note_id TEXT NOT NULL REFERENCES notes(id), title TEXT NOT NULL, body TEXT NOT NULL,
 project_id TEXT REFERENCES projects(id), tags TEXT NOT NULL, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS note_drafts (
 id TEXT PRIMARY KEY, note_id TEXT REFERENCES notes(id), title TEXT NOT NULL, body TEXT NOT NULL,
 project_id TEXT REFERENCES projects(id), tags TEXT NOT NULL, updated_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS templates (id TEXT PRIMARY KEY, name TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS alerts (
 id TEXT PRIMARY KEY, dedupe_key TEXT UNIQUE NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL,
 created_at REAL NOT NULL, read_at REAL, delivered_at REAL);
"""

BUILTIN_TEMPLATES = {
 "Website launch": [("Define audience and outcome", ["Identify the audience", "Write the primary action"]),
                     ("Design the key pages", ["Sketch the navigation", "Check mobile layout"]),
                     ("Build and verify", ["Check keyboard access", "Test forms", "Review performance"]),
                     ("Publish and review", ["Prepare launch checklist", "Collect feedback"])],
 "Study plan": [("Choose a learning goal", ["Write the question to answer"]),
                ("Study and make notes", ["Read one reference", "Explain it in your own words"]),
                ("Practice and review", ["Solve practice questions", "Record what needs revision"])],
 "Software release": [("Define the release scope", ["Choose essential features"]),
                      ("Implement the change", ["Review edge cases"]),
                      ("Test the release", ["Run tests", "Check the packaged app"]),
                      ("Publish release notes", ["Prepare checksums", "Document limitations"])],
 "Weekly routine": [("Review last week", ["Celebrate one outcome", "Review unfinished work"]),
                    ("Choose this week's outcomes", ["Choose three priorities"]),
                    ("Prepare the workspace", ["Plan focus time", "Make a backup"])],
}


def next_due(base, recurrence, weekdays=(), interval=1):
    if recurrence == "Monthly":
        year, month = base.year + (base.month == 12), base.month % 12 + 1
        return date(year, month, min(base.day, calendar.monthrange(year, month)[1]))
    if recurrence in ("Weekdays", "Selected weekdays"):
        days = set(weekdays if recurrence == "Selected weekdays" else range(5))
        if not days:
            raise ValueError("Select at least one weekday.")
        for offset in range(1, 8):
            candidate = base + timedelta(days=offset)
            if candidate.weekday() in days:
                return candidate
    return base + timedelta(days=7 if recurrence == "Weekly" else interval if recurrence == "Custom interval" else 1)


def validate_preferences(key, value):
    if key == '_draft_epoch' and (not isinstance(value, str) or len(value)>100):
        raise ValueError('Invalid draft recovery epoch.')
    if key == "language" and value not in ("English", "Dari", "Pashto"):
        raise ValueError("Unknown interface language.")
    if key == "backup_interval" and value not in ("Off", "Daily", "Weekly"):
        raise ValueError("Unknown backup schedule.")
    if key == "backup_keep" and (type(value) is not int or not 3 <= value <= 30):
        raise ValueError("Keep between 3 and 30 automatic backups.")
    if key in ("reminders", "desktop_hotkey") and type(value) is not bool:
        raise ValueError("Expected a true/false preference.")


def validate_extras(tables):
    def day(value):
        if value is not None and date.fromisoformat(value).isoformat() != value:
            raise ValueError("Invalid planning date.")
    graph = {}
    for row in tables["dependencies"]:
        if row["task_id"] == row["prerequisite_id"]:
            raise ValueError("A task cannot depend on itself.")
        graph.setdefault(row["task_id"], []).append(row["prerequisite_id"])
    visiting, done = set(), set()
    def visit(task):
        if task in visiting:
            raise ValueError("Backup contains a dependency cycle.")
        if task in done:
            return
        visiting.add(task)
        for parent in graph.get(task, []):
            visit(parent)
        visiting.remove(task)
        done.add(task)
    for task in graph:
        visit(task)
    for row in tables["task_plans"]:
        day(row["scheduled_day"])
        days = json.loads(row["weekdays"])
        if not isinstance(days, list) or len(days) > 7 or any(type(d) is not int or not 0 <= d <= 6 for d in days):
            raise ValueError("Invalid weekday schedule.")
        if type(row["interval_days"]) is not int or not 1 <= row["interval_days"] <= 365:
            raise ValueError("Invalid recurring interval.")
        if type(row["sort_order"]) not in (int, float) or not -1e9 <= row["sort_order"] <= 1e9:
            raise ValueError("Invalid board order.")
    for row in tables["daily_picks"]:
        day(row["day"])
        if type(row["position"]) is not int or not 0 <= row["position"] <= 2:
            raise ValueError("Only three daily priorities are allowed.")
    for row in tables["templates"]:
        validate_template(json.loads(row["payload"]))
    for row in tables["note_drafts"] + tables["note_versions"]:
        if not isinstance(row["title"], str) or len(row["title"]) > 200 or not isinstance(row["body"], str) or len(row["body"]) > 200000:
            raise ValueError("Invalid note recovery content.")
        tags = json.loads(row["tags"])
        if not isinstance(tags, list) or len(tags) > 15 or any(not isinstance(t, str) or len(t) > 40 for t in tags):
            raise ValueError("Invalid recovery tags.")


def validate_template(payload):
    if not isinstance(payload, list) or not 1 <= len(payload) <= 100:
        raise ValueError("A template needs 1–100 tasks.")
    for task in payload:
        if set(task) != {"title", "description", "priority", "estimate_minutes", "tags", "checks"}:
            raise ValueError("Invalid template fields.")
        if not isinstance(task["title"], str) or not task["title"].strip() or len(task["title"]) > 200:
            raise ValueError("Invalid template task title.")
        if not isinstance(task["description"], str) or len(task["description"]) > 10000 or task["priority"] not in ("Low", "Medium", "High"):
            raise ValueError("Invalid template task.")
        if type(task["estimate_minutes"]) is not int or not 1 <= task["estimate_minutes"] <= 720:
            raise ValueError("Invalid template estimate.")
        if not isinstance(task["tags"], list) or len(task["tags"]) > 15 or any(not isinstance(t, str) or len(t) > 40 for t in task["tags"]):
            raise ValueError("Invalid template tags.")
        if not isinstance(task["checks"], list) or len(task["checks"]) > 100 or any(not isinstance(c, str) or not c.strip() or len(c) > 300 for c in task["checks"]):
            raise ValueError("Invalid template checklist.")


class Planning:
    def task_plan(self, identifier):
        rows = self.rows("SELECT * FROM task_plans WHERE task_id=?", (identifier,))
        return rows[0] if rows else {"task_id": identifier, "sort_order": 0, "scheduled_day": None, "weekdays": "[]", "interval_days": 1}

    def set_task_plan(self, identifier, scheduled_day=None, weekdays=(), interval_days=1, sort_order=None):
        from focus.store import clean_date
        if type(interval_days) is not int or not 1 <= interval_days <= 365 or any(type(d) is not int or not 0 <= d <= 6 for d in weekdays):
            raise ValueError("Invalid recurrence schedule.")
        plan = self.task_plan(identifier)
        with self.connect(True) as c:
            c.execute("INSERT INTO task_plans VALUES (?,?,?,?,?) ON CONFLICT(task_id) DO UPDATE SET sort_order=excluded.sort_order,scheduled_day=excluded.scheduled_day,weekdays=excluded.weekdays,interval_days=excluded.interval_days",
                      (identifier, plan["sort_order"] if sort_order is None else sort_order, clean_date(scheduled_day), json.dumps(sorted(set(weekdays))), interval_days))

    def prerequisites(self, identifier):
        return self.rows("SELECT t.* FROM tasks t JOIN dependencies d ON d.prerequisite_id=t.id WHERE d.task_id=?", (identifier,))

    def blocked(self, identifier):
        return [t for t in self.prerequisites(identifier) if t["status"] != "Done" or t["deleted_at"] is not None]

    def set_dependencies(self, identifier, prerequisites):
        with self.connect(True) as c:
            c.execute("DELETE FROM dependencies WHERE task_id=?", (identifier,))
            for parent in set(prerequisites):
                if identifier == parent:
                    raise ValueError("A task cannot depend on itself.")
                cycle = c.execute("WITH RECURSIVE chain(id) AS (SELECT prerequisite_id FROM dependencies WHERE task_id=? UNION SELECT d.prerequisite_id FROM dependencies d JOIN chain ON d.task_id=chain.id) SELECT 1 FROM chain WHERE id=?", (parent, identifier)).fetchone()
                if cycle:
                    raise ValueError("That dependency would create a cycle.")
                c.execute("INSERT INTO dependencies VALUES (?,?)", (identifier, parent))

    def board_order(self, identifier, status, before=None):
        with self.connect(True) as c:
            self._move(c, identifier, status, self.clock())
            ids = [r[0] for r in c.execute("SELECT t.id FROM tasks t LEFT JOIN task_plans p ON p.task_id=t.id WHERE t.status=? AND t.deleted_at IS NULL AND t.id<>? ORDER BY COALESCE(p.sort_order,0),CASE t.priority WHEN 'High' THEN 0 WHEN 'Medium' THEN 1 ELSE 2 END,COALESCE(t.due_date,'9999'),t.created_at DESC,t.id", (status, identifier))]
            index = ids.index(before) if before in ids else len(ids)
            ids.insert(index, identifier)
            for order, task in enumerate(ids):
                c.execute("INSERT INTO task_plans(task_id,sort_order) VALUES (?,?) ON CONFLICT(task_id) DO UPDATE SET sort_order=excluded.sort_order", (task, order))

    def picks(self, day=None):
        day = str(day or date.today())
        return self.rows("SELECT t.*,p.name AS project_name,p.color AS project_color FROM daily_picks d JOIN tasks t ON t.id=d.task_id LEFT JOIN projects p ON p.id=t.project_id WHERE d.day=? AND t.deleted_at IS NULL ORDER BY d.position", (day,))

    def save_picks(self, identifiers, day=None):
        if len(identifiers) > 3 or len(set(identifiers)) != len(identifiers):
            raise ValueError("Choose up to three different priorities.")
        from focus.store import clean_date
        day = clean_date(day or date.today())
        with self.connect(True) as c:
            c.execute("DELETE FROM daily_picks WHERE day=?", (day,))
            for index, identifier in enumerate(identifiers):
                c.execute("INSERT INTO daily_picks VALUES (?,?,?)", (day, index, identifier))

    def note_versions(self, identifier):
        return self.rows("SELECT * FROM note_versions WHERE note_id=? ORDER BY created_at DESC", (identifier,))

    def save_draft(self, identifier, title, body, project_id=None, tags=(), note_id=None):
        from focus.store import clean_text, clean_tags
        with self.connect(True) as c:
            c.execute("INSERT INTO note_drafts VALUES (?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,body=excluded.body,project_id=excluded.project_id,tags=excluded.tags,updated_at=excluded.updated_at",
                      (identifier, note_id, clean_text(title, 200), clean_text(body, 200000, strip=False), project_id, json.dumps(clean_tags(tags)), self.clock()))

    def clear_draft(self, identifier):
        with self.connect(True) as c:
            c.execute("DELETE FROM note_drafts WHERE id=?", (identifier,))

    def restore_note_version(self, identifier):
        version = self.get("note_versions", identifier)
        if not version:
            raise ValueError("Note version no longer exists.")
        return self.save_note(version["title"], version["body"], version["project_id"], json.loads(version["tags"]), version["note_id"])

    def templates(self):
        builtins = [{"id": "builtin:" + name, "name": name, "payload": json.dumps([
            {"title": title, "description": "", "priority": "Medium", "estimate_minutes": 25, "tags": [], "checks": checks}
            for title, checks in tasks])} for name, tasks in BUILTIN_TEMPLATES.items()]
        return builtins + self.rows("SELECT * FROM templates ORDER BY name")

    def save_template(self, project, name):
        from focus.store import clean_text
        payload = [{"title": t["title"], "description": t["description"], "priority": t["priority"], "estimate_minutes": t["estimate_minutes"],
                    "tags": json.loads(t["tags"]), "checks": [x["text"] for x in self.checklist(t["id"])]} for t in self.tasks(project)]
        validate_template(payload)
        identifier = str(uuid.uuid4())
        with self.connect(True) as c:
            c.execute("INSERT INTO templates VALUES (?,?,?)", (identifier, clean_text(name, 100, True), json.dumps(payload)))
        return identifier

    def apply_template(self, identifier, project_name):
        template = next((t for t in self.templates() if t["id"] == identifier), None)
        if not template:
            raise ValueError("Template does not exist.")
        payload = json.loads(template["payload"])
        validate_template(payload)
        from focus.store import clean_text
        project = str(uuid.uuid4())
        now = self.clock()
        with self.connect(True) as c:
            c.execute("INSERT INTO projects VALUES (?,?,?,'#427365',0,?)", (project, clean_text(project_name, 100, True), "Created from " + template["name"], now))
            for order, item in enumerate(payload):
                task = str(uuid.uuid4())
                c.execute("INSERT INTO tasks(id,project_id,title,description,status,priority,estimate_minutes,tags,created_at,updated_at) VALUES (?,?,?,?,'Inbox',?,?,?,?,?)",
                          (task, project, item["title"], item["description"], item["priority"], item["estimate_minutes"], json.dumps(item["tags"]), now, now))
                c.execute("INSERT INTO task_plans(task_id,sort_order) VALUES (?,?)", (task, order))
                for pos, text in enumerate(item["checks"]):
                    c.execute("INSERT INTO checklist VALUES (?,?,?,0,?)", (str(uuid.uuid4()), task, text, pos))
        return project

    def alert(self, key, title, body):
        with self.connect(True) as c:
            c.execute("INSERT OR IGNORE INTO alerts VALUES (?,?,?,?,?,NULL,NULL)", (str(uuid.uuid4()), key, title, body, self.clock()))

    def alerts(self):
        return self.rows("SELECT * FROM alerts WHERE created_at<=? ORDER BY created_at DESC LIMIT 50", (self.clock(),))

    def mark_alert(self, identifier):
        with self.connect(True) as c:
            c.execute("UPDATE alerts SET read_at=? WHERE id=?", (self.clock(), identifier))

    def take_notifications(self):
        with self.connect(True) as c:
            rows = [dict(r) for r in c.execute("SELECT * FROM alerts WHERE delivered_at IS NULL AND read_at IS NULL AND created_at>=? AND created_at<=? ORDER BY created_at LIMIT 5", (self.clock() - 86400, self.clock()))]
            for row in rows:
                c.execute("UPDATE alerts SET delivered_at=? WHERE id=?", (self.clock(), row["id"]))
            return rows

    def maintenance(self):
        settings = self.settings()
        active = self.active()
        if active and active["state"] == "running" and self.elapsed(active) >= active["planned_seconds"]:
            self.control_focus("complete", active["id"])
        if settings["reminders"]:
            today = datetime.fromtimestamp(self.clock()).date().isoformat()
            for task in self.tasks():
                if task["status"] != "Done" and task["due_date"] and task["due_date"] <= today:
                    self.alert("due:" + today + ":" + task["id"], "Task due", task["title"])
        self.auto_backup()

    def auto_backup(self, force=False):
        settings = self.settings()
        interval = settings["backup_interval"]
        if interval == "Off" and not force:
            return None
        folder = self.path.parent / ("demo-auto-backups" if self.path.name == "demo.sqlite3" else "auto-backups")
        folder.mkdir(exist_ok=True)
        # File reservation serializes UI/desktop workers; stale reservations can be recovered.
        lock = folder / ".backup-lock"
        try:
            if lock.exists() and time.time() - lock.stat().st_mtime > 300:
                lock.unlink()
            with lock.open("x"):
                pass
        except FileExistsError:
            return None
        try:
            files = sorted(folder.glob("focus-auto-*.zip"))
            seconds = 86400 * (7 if interval == "Weekly" else 1)
            if not force and files and self.clock() - files[-1].stat().st_mtime < seconds:
                return None
            blob = self.backup()
            self.inspect_backup(blob)
            output = folder / f"focus-auto-{time.time_ns()}.zip"
            temp = output.with_suffix(".pending")
            temp.write_bytes(blob)
            temp.replace(output)
            files.append(output)
            for old in files[:-settings["backup_keep"]]:
                old.unlink()
            return output
        finally:
            lock.unlink(missing_ok=True)

    def backup_preview(self, blob):
        snapshot = self.inspect_backup(blob)
        # Exactly the same semantic/foreign-key validation as restoration.
        self.validate_backup(snapshot)
        current = self.snapshot()["tables"]
        report = []
        for table in ("projects", "tasks", "notes", "focus_sessions", "note_drafts", "templates"):
            old = {r["id"]: r for r in current[table]}
            new = {r["id"]: r for r in snapshot["tables"][table]}
            report.append({"Area": table.replace("_", " "), "Current": len(old), "Backup": len(new),
                           "Added": len(new.keys()-old.keys()), "Removed": len(old.keys()-new.keys()),
                           "Changed": sum(old[k] != new[k] for k in old.keys() & new.keys())})
        return report
