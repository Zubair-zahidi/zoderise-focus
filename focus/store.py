"""Transactional local workspace. No cloud service or analytics."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import sqlite3
import time
import uuid
import zipfile
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

STATUSES = ("Inbox", "Next", "Doing", "Done")
PRIORITIES = ("Low", "Medium", "High")
RECURRENCES = ("None", "Daily", "Weekly")
TABLES = ("projects", "tasks", "checklist", "notes", "focus_sessions", "settings", "day_plans")
DEFAULTS = {"name": "", "goal": 60, "focus_minutes": 25, "break_minutes": 5,
            "accent": "Forest", "compact": False, "motion": True}

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
 color TEXT NOT NULL DEFAULT '#427365', archived INTEGER NOT NULL DEFAULT 0,
 created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS tasks (
 id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id), title TEXT NOT NULL,
 description TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'Inbox',
 priority TEXT NOT NULL DEFAULT 'Medium', due_date TEXT, recurrence TEXT NOT NULL DEFAULT 'None',
 estimate_minutes INTEGER NOT NULL DEFAULT 25, tags TEXT NOT NULL DEFAULT '[]',
 deleted_at REAL, created_at REAL NOT NULL, updated_at REAL NOT NULL, completed_at REAL,
 recurrence_source_id TEXT UNIQUE REFERENCES tasks(id));
CREATE TABLE IF NOT EXISTS checklist (
 id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
 text TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0, position INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS notes (
 id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id), title TEXT NOT NULL,
 body TEXT NOT NULL DEFAULT '', tags TEXT NOT NULL DEFAULT '[]', deleted_at REAL,
 updated_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS focus_sessions (
 id TEXT PRIMARY KEY, task_id TEXT REFERENCES tasks(id), intent TEXT NOT NULL,
 planned_seconds INTEGER NOT NULL, accumulated_seconds REAL NOT NULL DEFAULT 0,
 active_since REAL, state TEXT NOT NULL, started_at REAL NOT NULL, finished_at REAL);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_session ON focus_sessions((1))
 WHERE state IN ('running', 'paused');
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS day_plans (day TEXT PRIMARY KEY, goal_minutes INTEGER NOT NULL,
 journal TEXT NOT NULL DEFAULT '');
CREATE INDEX IF NOT EXISTS tasks_status ON tasks(status, deleted_at);
CREATE INDEX IF NOT EXISTS sessions_finished ON focus_sessions(finished_at);
"""


def data_home() -> Path:
    override = os.environ.get("FOCUS_DATA_HOME")
    if override:
        return Path(override).expanduser().resolve()
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ZoderiseFocus"
    return Path.home() / ".local" / "share" / "zoderise-focus"


def clean_text(value, limit=5000, required=False):
    value = str(value).strip()
    if required and not value:
        raise ValueError("Please enter a title or name.")
    if len(value) > limit:
        raise ValueError(f"Text must be {limit:,} characters or fewer.")
    return value


def clean_tags(tags):
    if isinstance(tags, str):
        tags = tags.split(",")
    return sorted(set(clean_text(t, 40).lower() for t in tags if str(t).strip()))[:15]


def clean_date(value):
    if value is None or value == "":
        return None
    return date.fromisoformat(str(value)).isoformat()


class Store:
    def __init__(self, path=None, clock=time.time):
        self.path = Path(path) if path else data_home() / "workspace.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def connect(self, write=False):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=10000")
        conn.execute("PRAGMA journal_mode=WAL")
        try:
            if write:
                conn.execute("BEGIN IMMEDIATE")
            yield conn
            if write:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def rows(self, sql, params=()):
        with self.connect() as c:
            return [dict(r) for r in c.execute(sql, params).fetchall()]

    def get(self, table, identifier):
        if table not in TABLES:
            raise ValueError("Unknown table")
        found = self.rows(f"SELECT * FROM {table} WHERE id=?", (identifier,))
        return found[0] if found else None

    def settings(self):
        values = DEFAULTS.copy()
        values.update({r["key"]: json.loads(r["value"]) for r in self.rows("SELECT * FROM settings")})
        return values

    def set_settings(self, **values):
        for key, value in values.items():
            if key not in DEFAULTS:
                raise ValueError("Unknown preference")
            if key == "name":
                if not isinstance(value, str):
                    raise ValueError("Your name must be text.")
                clean_text(value, 80)
            if key in ("goal", "focus_minutes", "break_minutes") and (type(value) is not int or not 1 <= value <= 720):
                raise ValueError("Minutes must be between 1 and 720.")
            if key == "accent" and value not in ("Forest", "Ocean", "Violet", "Copper"):
                raise ValueError("Unknown accent")
            if key in ("motion", "compact") and type(value) is not bool:
                raise ValueError("Expected a true/false preference.")
        with self.connect(True) as c:
            c.executemany("INSERT INTO settings VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                          [(k, json.dumps(v)) for k, v in values.items()])

    def projects(self, archived=False):
        return self.rows("SELECT * FROM projects WHERE archived=? ORDER BY name COLLATE NOCASE", (int(archived),))

    def save_project(self, name, description="", color="#427365", identifier=None):
        name, description = clean_text(name, 100, True), clean_text(description, 1000)
        if len(color) != 7 or color[0] != "#" or any(ch not in "0123456789abcdefABCDEF" for ch in color[1:]):
            raise ValueError("Invalid project color")
        identifier = identifier or str(uuid.uuid4())
        with self.connect(True) as c:
            c.execute("INSERT INTO projects VALUES (?,?,?,?,0,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,description=excluded.description,color=excluded.color",
                      (identifier, name, description, color, self.clock()))
        return identifier

    def archive_project(self, identifier, archived=True):
        with self.connect(True) as c:
            c.execute("UPDATE projects SET archived=? WHERE id=?", (int(archived), identifier))

    def tasks(self, project=None, query="", trash=False, include_archived=False):
        sql = "SELECT t.*,p.name AS project_name,p.color AS project_color FROM tasks t LEFT JOIN projects p ON p.id=t.project_id WHERE "
        sql += "t.deleted_at IS NOT NULL" if trash else "t.deleted_at IS NULL"
        args = []
        if not include_archived and not trash:
            sql += " AND (p.archived IS NULL OR p.archived=0)"
        if project:
            sql += " AND t.project_id=?"
            args.append(project)
        if query:
            sql += " AND (instr(lower(t.title),lower(?))>0 OR instr(lower(t.description),lower(?))>0 OR instr(lower(t.tags),lower(?))>0)"
            args.extend([query] * 3)
        sql += " ORDER BY CASE t.priority WHEN 'High' THEN 0 WHEN 'Medium' THEN 1 ELSE 2 END, COALESCE(t.due_date,'9999'),t.created_at DESC"
        return self.rows(sql, args)

    def save_task(self, title, project_id=None, description="", status="Inbox", priority="Medium", due_date=None,
                  recurrence="None", estimate_minutes=25, tags=(), identifier=None):
        title, description = clean_text(title, 200, True), clean_text(description, 10000)
        if status not in STATUSES or priority not in PRIORITIES or recurrence not in RECURRENCES:
            raise ValueError("Invalid task option")
        if type(estimate_minutes) is not int or not 1 <= estimate_minutes <= 720:
            raise ValueError("Estimate must be between 1 and 720 minutes.")
        if recurrence != "None" and not due_date:
            raise ValueError("Recurring tasks need a due date.")
        identifier, now = identifier or str(uuid.uuid4()), self.clock()
        with self.connect(True) as c:
            existing = c.execute("SELECT * FROM tasks WHERE id=?", (identifier,)).fetchone()
            # Status changes share the same completion/recurrence logic.
            initial_status = existing["status"] if existing else "Inbox"
            c.execute("""INSERT INTO tasks (id,project_id,title,description,status,priority,due_date,recurrence,estimate_minutes,tags,created_at,updated_at)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET project_id=excluded.project_id,title=excluded.title,
             description=excluded.description,priority=excluded.priority,due_date=excluded.due_date,recurrence=excluded.recurrence,
             estimate_minutes=excluded.estimate_minutes,tags=excluded.tags,updated_at=excluded.updated_at""",
                      (identifier, project_id, title, description, initial_status, priority, clean_date(due_date), recurrence,
                       estimate_minutes, json.dumps(clean_tags(tags)), now, now))
            self._move(c, identifier, status, now)
        return identifier

    def _move(self, c, identifier, status, now):
        if status not in STATUSES:
            raise ValueError("Invalid task status")
        row = c.execute("SELECT * FROM tasks WHERE id=? AND deleted_at IS NULL", (identifier,)).fetchone()
        if not row:
            raise ValueError("Task was removed or does not exist.")
        completed = row["completed_at"] if row["status"] == "Done" and status == "Done" else now if status == "Done" else None
        c.execute("UPDATE tasks SET status=?,updated_at=?,completed_at=? WHERE id=?", (status, now, completed, identifier))
        if status == "Done" and row["status"] != "Done" and row["recurrence"] != "None":
            exists = c.execute("SELECT id FROM tasks WHERE recurrence_source_id=?", (identifier,)).fetchone()
            if not exists:
                today = datetime.fromtimestamp(now).date()
                base = max(today, date.fromisoformat(row["due_date"]))
                due = (base + timedelta(days=1 if row["recurrence"] == "Daily" else 7)).isoformat()
                next_id = str(uuid.uuid4())
                c.execute("""INSERT INTO tasks (id,project_id,title,description,status,priority,due_date,recurrence,
                 estimate_minutes,tags,created_at,updated_at,recurrence_source_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                          (next_id, row["project_id"], row["title"], row["description"], "Next", row["priority"], due,
                           row["recurrence"], row["estimate_minutes"], row["tags"], now, now, identifier))
                for item in c.execute("SELECT * FROM checklist WHERE task_id=? ORDER BY position", (identifier,)).fetchall():
                    c.execute("INSERT INTO checklist VALUES (?,?,?,0,?)", (str(uuid.uuid4()), next_id, item["text"], item["position"]))

    def move_task(self, identifier, status):
        with self.connect(True) as c:
            self._move(c, identifier, status, self.clock())

    def trash(self, table, identifier, restore=False):
        if table not in ("tasks", "notes"):
            raise ValueError("Unsupported trash type")
        with self.connect(True) as c:
            c.execute(f"UPDATE {table} SET deleted_at=? WHERE id=?", (None if restore else self.clock(), identifier))

    def checklist(self, task_id):
        return self.rows("SELECT * FROM checklist WHERE task_id=? ORDER BY position", (task_id,))

    def add_check(self, task_id, text):
        with self.connect(True) as c:
            count = c.execute("SELECT COUNT(*) FROM checklist WHERE task_id=?", (task_id,)).fetchone()[0]
            c.execute("INSERT INTO checklist VALUES (?,?,?,0,?)", (str(uuid.uuid4()), task_id, clean_text(text, 300, True), count))

    def check(self, identifier, done):
        with self.connect(True) as c:
            c.execute("UPDATE checklist SET done=? WHERE id=?", (int(done), identifier))

    def remove_check(self, identifier):
        with self.connect(True) as c:
            c.execute("DELETE FROM checklist WHERE id=?", (identifier,))

    def notes(self, project=None, query="", trash=False):
        sql = "SELECT n.*,p.name AS project_name FROM notes n LEFT JOIN projects p ON p.id=n.project_id WHERE "
        sql += "n.deleted_at IS NOT NULL" if trash else "n.deleted_at IS NULL"
        args = []
        if project:
            sql += " AND project_id=?"
            args.append(project)
        if query:
            sql += " AND (instr(lower(title),lower(?))>0 OR instr(lower(body),lower(?))>0 OR instr(lower(tags),lower(?))>0)"
            args.extend([query] * 3)
        return self.rows(sql + " ORDER BY updated_at DESC", args)

    def save_note(self, title, body="", project_id=None, tags=(), identifier=None):
        identifier = identifier or str(uuid.uuid4())
        with self.connect(True) as c:
            c.execute("INSERT INTO notes VALUES (?,?,?,?,?,NULL,?) ON CONFLICT(id) DO UPDATE SET project_id=excluded.project_id,title=excluded.title,body=excluded.body,tags=excluded.tags,updated_at=excluded.updated_at",
                      (identifier, project_id, clean_text(title, 200, True), clean_text(body, 200000), json.dumps(clean_tags(tags)), self.clock()))
        return identifier

    def start_focus(self, intent, minutes, task_id=None):
        if type(minutes) is not int or not 1 <= minutes <= 180:
            raise ValueError("Choose a session between 1 and 180 minutes.")
        identifier, now = str(uuid.uuid4()), self.clock()
        with self.connect(True) as c:
            if c.execute("SELECT 1 FROM focus_sessions WHERE state IN ('running','paused')").fetchone():
                raise ValueError("Finish or cancel your existing session first.")
            c.execute("INSERT INTO focus_sessions VALUES (?,?,?,?,0,?,'running',?,NULL)",
                      (identifier, task_id, clean_text(intent, 200, True), minutes * 60, now, now))
        return identifier

    def elapsed(self, session):
        elapsed = session["accumulated_seconds"]
        if session["state"] == "running" and session["active_since"] is not None:
            elapsed += max(0, self.clock() - session["active_since"])
        return min(session["planned_seconds"], elapsed)

    def active(self):
        rows = self.rows("SELECT * FROM focus_sessions WHERE state IN ('running','paused') LIMIT 1")
        return rows[0] if rows else None

    def control_focus(self, action):
        with self.connect(True) as c:
            row = c.execute("SELECT * FROM focus_sessions WHERE state IN ('running','paused')").fetchone()
            if not row:
                return
            row = dict(row)
            now, elapsed = self.clock(), self.elapsed(row)
            if action == "pause":
                state, active, finished = "paused", None, None
            elif action == "resume":
                state, active, finished = "running", now, None
            elif action in ("complete", "cancel"):
                state, active, finished = "completed" if action == "complete" else "cancelled", None, now
            else:
                raise ValueError("Invalid timer action")
            c.execute("UPDATE focus_sessions SET state=?,active_since=?,accumulated_seconds=?,finished_at=? WHERE id=?",
                      (state, active, elapsed, finished, row["id"]))

    def history(self):
        return self.rows("SELECT s.*,t.title AS task_title FROM focus_sessions s LEFT JOIN tasks t ON s.task_id=t.id ORDER BY started_at DESC")

    def day_plan(self, day=None):
        day = clean_date(day or date.today())
        rows = self.rows("SELECT * FROM day_plans WHERE day=?", (day,))
        return rows[0] if rows else {"day": day, "goal_minutes": self.settings()["goal"], "journal": ""}

    def save_plan(self, goal_minutes, journal, day=None):
        if type(goal_minutes) is not int or not 1 <= goal_minutes <= 720:
            raise ValueError("Goal must be 1–720 minutes.")
        with self.connect(True) as c:
            c.execute("INSERT INTO day_plans VALUES (?,?,?) ON CONFLICT(day) DO UPDATE SET goal_minutes=excluded.goal_minutes,journal=excluded.journal",
                      (clean_date(day or date.today()), goal_minutes, clean_text(journal, 10000)))

    def snapshot(self):
        with self.connect() as c:
            c.execute("BEGIN")
            tables = {table: [dict(r) for r in c.execute(f"SELECT * FROM {table}")] for table in TABLES}
        for session in tables["focus_sessions"]:
            if session["state"] == "running":
                session["accumulated_seconds"] = self.elapsed(session)
                session["active_since"] = None
                session["state"] = "paused"
        return {"format": "zoderise-focus-v1", "exported_at": datetime.now(timezone.utc).isoformat(), "tables": tables}

    def backup(self):
        payload = json.dumps(self.snapshot(), ensure_ascii=False, separators=(",", ":")).encode()
        manifest = json.dumps({"format": "zoderise-focus-v1", "sha256": hashlib.sha256(payload).hexdigest()}).encode()
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("focus.json", payload)
            z.writestr("manifest.json", manifest)
        return output.getvalue()

    @staticmethod
    def inspect_backup(blob):
        if len(blob) > 20_000_000:
            raise ValueError("Backup exceeds 20 MB.")
        try:
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                infos = z.infolist()
                if sorted(i.filename for i in infos) != ["focus.json", "manifest.json"] or sum(i.file_size for i in infos) > 40_000_000:
                    raise ValueError("Unexpected backup contents or size.")
                payload, manifest = z.read("focus.json"), json.loads(z.read("manifest.json"))
            if manifest.get("sha256") != hashlib.sha256(payload).hexdigest():
                raise ValueError("Backup checksum failed. Nothing was restored.")
            snapshot = json.loads(payload)
            if snapshot.get("format") != "zoderise-focus-v1" or set(snapshot["tables"]) != set(TABLES):
                raise ValueError("Unsupported backup format.")
            tables = snapshot["tables"]
            if any(not isinstance(rows, list) or len(rows) > 50000 for rows in tables.values()):
                raise ValueError("Invalid backup table.")
            return snapshot
        except (zipfile.BadZipFile, KeyError, TypeError, AttributeError, RuntimeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("This is not a valid Zoderise Focus backup.") from exc

    def restore(self, blob):
        snapshot = self.inspect_backup(blob)
        tables = snapshot["tables"]
        # Validate into a disposable known-schema database; never execute uploaded SQL.
        validation = sqlite3.connect(":memory:")
        validation.execute("PRAGMA foreign_keys=ON")
        validation.executescript(SCHEMA)
        try:
            self._insert_snapshot(validation, tables)
            self._validate_snapshot(tables)
            if validation.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("Backup contains broken references.")
        except (sqlite3.Error, ValueError, TypeError, KeyError) as exc:
            raise ValueError(f"Backup validation failed: {exc}") from exc
        finally:
            validation.close()
        safety_dir = self.path.parent / "backups"
        safety_dir.mkdir(exist_ok=True)
        safety_path = safety_dir / f"before-restore-{time.time_ns()}.zip"
        # Capture and replace under one writer transaction to prevent lost concurrent edits.
        with self.connect(True) as c:
            current = {table: [dict(r) for r in c.execute(f"SELECT * FROM {table}")] for table in TABLES}
            for session in current["focus_sessions"]:
                if session["state"] == "running":
                    session["accumulated_seconds"] = self.elapsed(session)
                    session["state"], session["active_since"] = "paused", None
            payload = json.dumps({"format": "zoderise-focus-v1", "tables": current}).encode()
            with zipfile.ZipFile(safety_path, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("focus.json", payload)
                z.writestr("manifest.json", json.dumps({"sha256": hashlib.sha256(payload).hexdigest()}))
            c.execute("PRAGMA defer_foreign_keys=ON")
            for table in reversed(TABLES):
                c.execute(f"DELETE FROM {table}")
            self._insert_snapshot(c, tables)
            if c.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("Backup references failed.")
        return safety_path

    @staticmethod
    def _insert_snapshot(c, tables):
        c.execute("PRAGMA defer_foreign_keys=ON")
        for table in TABLES:
            cols = [r[1] for r in c.execute(f"PRAGMA table_info({table})")]
            for row in tables[table]:
                if not isinstance(row, dict) or set(row) != set(cols):
                    raise ValueError(f"Invalid columns in {table}.")
                if any(isinstance(v, (dict, list)) for v in row.values()):
                    raise ValueError("Invalid field type.")
                c.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})", [row[col] for col in cols])

    @staticmethod
    def _validate_snapshot(tables):
        for rows in tables.values():
            for row in rows:
                for key, value in row.items():
                    if key in ("id", "title", "name", "description", "body", "text", "intent", "journal", "tags", "key", "value") and not isinstance(value, str):
                        raise ValueError("Invalid text field type.")
                    if key in ("id", "project_id", "task_id", "recurrence_source_id") and value is not None and (not isinstance(value, str) or not 1 <= len(value) <= 80):
                        raise ValueError("Invalid item identifier.")
                    if key.endswith("_at") or key in ("active_since", "accumulated_seconds"):
                        if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value < 1e12):
                            raise ValueError("Invalid time value.")
                for value in row.values():
                    if isinstance(value, str) and len(value) > 200000:
                        raise ValueError("Backup text is too long.")
                    if isinstance(value, float) and not (-1e15 < value < 1e15):
                        raise ValueError("Invalid numeric value.")
        for p in tables["projects"]:
            clean_text(p["name"], 100, True)
            if p["archived"] not in (0, 1) or not isinstance(p["color"], str) or len(p["color"]) != 7 or p["color"][0] != "#" or any(ch not in "0123456789abcdefABCDEF" for ch in p["color"][1:]):
                raise ValueError("Invalid project.")
        for task in tables["tasks"]:
            clean_text(task["title"], 200, True)
            clean_date(task["due_date"])
            if task["status"] not in STATUSES or task["priority"] not in PRIORITIES or task["recurrence"] not in RECURRENCES:
                raise ValueError("Invalid task options.")
            if task["recurrence"] != "None" and task["due_date"] is None:
                raise ValueError("Recurring task has no deadline.")
            if type(task["estimate_minutes"]) is not int or not 1 <= task["estimate_minutes"] <= 720:
                raise ValueError("Invalid task estimate.")
            if task["created_at"] is None or task["updated_at"] is None or (task["status"] == "Done") != (task["completed_at"] is not None):
                raise ValueError("Invalid task completion state.")
        for row in tables["tasks"] + tables["notes"]:
            tags = json.loads(row["tags"])
            if not isinstance(tags, list) or len(tags) > 15 or any(not isinstance(t, str) or len(t) > 40 for t in tags):
                raise ValueError("Invalid tags.")
        for n in tables["notes"]:
            clean_text(n["title"], 200, True)
        for item in tables["checklist"]:
            clean_text(item["text"], 300, True)
            if item["done"] not in (0, 1):
                raise ValueError("Invalid checklist.")
        for s in tables["focus_sessions"]:
            if s["state"] not in ("paused", "completed", "cancelled") or s["active_since"] is not None:
                raise ValueError("Backups must contain paused or finished timers.")
            if type(s["planned_seconds"]) is not int or not 60 <= s["planned_seconds"] <= 10800 or not 0 <= s["accumulated_seconds"] <= s["planned_seconds"]:
                raise ValueError("Invalid session duration.")
            if s["state"] == "paused" and s["finished_at"] is not None or s["state"] != "paused" and s["finished_at"] is None:
                raise ValueError("Invalid session state.")
            if s["started_at"] is None:
                raise ValueError("Session has no start time.")
        for s in tables["settings"]:
            v, key = json.loads(s["value"]), s["key"]
            if key not in DEFAULTS:
                raise ValueError("Unknown backup preference.")
            if key in ("goal", "focus_minutes", "break_minutes") and (type(v) is not int or not 1 <= v <= 720):
                raise ValueError("Invalid minutes preference.")
            if key in ("motion", "compact") and type(v) is not bool:
                raise ValueError("Invalid appearance preference.")
            if key == "accent" and v not in ("Forest", "Ocean", "Violet", "Copper"):
                raise ValueError("Invalid accent preference.")
            if key == "name":
                if not isinstance(v, str):
                    raise ValueError("Invalid name preference.")
                clean_text(v, 80)
        for plan in tables["day_plans"]:
            clean_date(plan["day"])
            if type(plan["goal_minutes"]) is not int or not 1 <= plan["goal_minutes"] <= 720:
                raise ValueError("Invalid daily goal.")

    def csv_export(self):
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        cols = ("title", "project_name", "status", "priority", "due_date", "estimate_minutes", "description")
        writer.writerow(cols)
        for row in self.tasks(include_archived=True):
            writer.writerow([("'" + str(row[k])) if str(row[k] or "").lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else row[k] for k in cols])
        return "\ufeff" + output.getvalue()

    def calendar_export(self):
        def escape(value):
            return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace(";", "\\;").replace(",", "\\,")
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Zoderise//Focus 1.0//EN", "CALSCALE:GREGORIAN"]
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        for task in self.tasks(include_archived=True):
            if not task["due_date"] or task["status"] == "Done":
                continue
            d = date.fromisoformat(task["due_date"])
            lines += ["BEGIN:VEVENT", f"UID:{task['id']}@zoderise-focus", f"DTSTAMP:{stamp}",
                      f"DTSTART;VALUE=DATE:{d:%Y%m%d}", f"DTEND;VALUE=DATE:{d + timedelta(days=1):%Y%m%d}",
                      "SUMMARY:" + escape(task["title"]), "DESCRIPTION:" + escape(task["description"]), "END:VEVENT"]
        lines.append("END:VCALENDAR")
        folded = []
        for line in lines:
            chunk = ""
            for char in line:
                if len((chunk + char).encode()) > 73:
                    folded.append(chunk)
                    chunk = " "
                chunk += char
            folded.append(chunk)
        return "\r\n".join(folded) + "\r\n"

    def seed_demo(self):
        if self.projects() or self.tasks():
            return
        today = date.today()
        launch = self.save_project("Website launch", "A thoughtful home for the Zoderise brand.", "#427365")
        learn = self.save_project("Learning lab", "Small experiments, deeper understanding.", "#6779a0")
        life = self.save_project("Personal systems", "Make room for work that matters.", "#a57448")
        a = self.save_task("Refine the landing page", launch, "Polish the hero, simplify the navigation, and check the mobile layout.", "Doing", "High", today, tags="design, web", estimate_minutes=45)
        for text in ("Review visual hierarchy", "Check mobile navigation", "Test keyboard access"):
            self.add_check(a, text)
        self.check(self.checklist(a)[0]["id"], True)
        self.save_task("Write the product story", launch, "A short story about why we built it.", "Next", "High", today + timedelta(days=1), tags="writing")
        self.save_task("Study networking fundamentals", learn, "Draw the journey of an HTTP request.", "Next", "Medium", today, tags="learning", estimate_minutes=30)
        self.save_task("Organize this week's reading", learn, "Collect references in a single project note.", tags="reading")
        self.save_task("Weekly workspace review", life, "Choose three outcomes for the coming week.", "Next", "Medium", today + timedelta(days=3), "Weekly", tags="routine")
        self.save_task("Sketch the app navigation", launch, status="Done", tags="design")
        self.save_task("Capture ideas for a security lab", learn, priority="Low", tags="ideas")
        self.save_note("A calmer product experience", "# A calmer product experience\n\nThe next version should help people **start quickly** and finish with confidence.\n\n## Design principles\n- One clear action at a time\n- Real progress, honestly recorded\n- Local ownership of data\n\n> Good tools make room for good thinking.\n\n## Next experiment\nTest the navigation on a small screen before adding more features.", launch, "design, ideas")
        self.save_note("Networking field notes", "# HTTP, in my own words\n\nA client sends a request. A server sends a response.\n\n```text\nBrowser → DNS → Connection → Request → Response\n```\n\n## Questions to revisit\n- What changes when HTTPS is used?\n- Where does caching happen?", learn, "learning")
        now = self.clock()
        with self.connect(True) as c:
            for days, minutes in ((0, 25), (0, 20), (1, 35), (2, 50), (3, 25), (4, 60), (6, 30)):
                end = now - days * 86400 - 3600
                c.execute("INSERT INTO focus_sessions VALUES (?,?,?,?,?,NULL,'completed',?,?)",
                          (str(uuid.uuid4()), a, "Demo: thoughtful work", minutes * 60, minutes * 60, end - minutes * 60, end))
        self.set_settings(name="Zubair", goal=60)
