from __future__ import annotations

import html
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st

from focus.store import Store, STATUSES, PRIORITIES, RECURRENCES, data_home

ROOT = Path(__file__).resolve().parent.parent
ACCENTS = {"Forest": "#427365", "Ocean": "#426d9a", "Violet": "#73629d", "Copper": "#97643f"}


def store():
    return Store(data_home() / ("demo.sqlite3" if st.session_state.get("demo", False) else "workspace.sqlite3"))


def flash(message):
    st.session_state.pop("open_task", None)
    st.session_state.pop("open_project", None)
    st.session_state["flash"] = message
    st.rerun()


def header(eyebrow, title, description):
    st.caption(eyebrow.upper())
    st.title(title)
    st.write(description)
    st.write("")


def appearance():
    settings = store().settings()
    accent = ACCENTS[settings["accent"]]
    css = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
    extra = ""
    if settings["compact"]:
        extra += '[data-testid="stVerticalBlock"]{gap:0.6rem;} .stMainBlockContainer{padding-top:1.8rem;}'
    if not settings["motion"]:
        extra += '*,*::before,*::after{animation:none!important;transition:none!important;}'
    st.html(f"<style>:root{{--focus-accent:{accent};}}{css}{extra}</style>")


def project_choices(include=None):
    projects = store().projects()
    if include and not any(p["id"] == include for p in projects):
        p = store().get("projects", include)
        if p:
            projects.append(p)
    mapping = {p["id"]: p["name"] for p in projects}
    return [None] + list(mapping), lambda key: mapping.get(key, "No project · inbox")


def task_editor(identifier=None):
    st.session_state["open_task"] = identifier or True
    st.rerun()


def dismiss_task():
    st.session_state.pop("open_task", None)


@st.dialog("Task details", width="large", on_dismiss=dismiss_task)
def render_task_editor(identifier=None):
    db = store()
    task = db.get("tasks", identifier) if identifier else {}
    if identifier and not task:
        st.warning("This task is no longer available.")
        return
    options, labels = project_choices(task.get("project_id"))
    with st.form("task_editor", border=False):
        title = st.text_input("Task title", task.get("title", ""), placeholder="What is the next concrete action?", max_chars=200)
        project = st.selectbox("Project", options, index=options.index(task.get("project_id")), format_func=labels)
        description = st.text_area("Details", task.get("description", ""), height=100)
        c1, c2, c3 = st.columns(3)
        with c1:
            status = st.selectbox("Status", STATUSES, index=STATUSES.index(task.get("status", "Inbox")))
        with c2:
            priority = st.selectbox("Priority", PRIORITIES, index=PRIORITIES.index(task.get("priority", "Medium")))
        with c3:
            estimate = st.number_input("Estimate · minutes", min_value=1, max_value=720, value=task.get("estimate_minutes", 25), step=5)
        c1, c2 = st.columns(2)
        with c1:
            due = st.date_input("Due date · optional", value=date.fromisoformat(task["due_date"]) if task.get("due_date") else None)
        with c2:
            recurrence = st.selectbox("Repeat after completion", RECURRENCES, index=RECURRENCES.index(task.get("recurrence", "None")))
        tags = st.text_input("Tags · separated by commas", ", ".join(json.loads(task.get("tags", "[]"))))
        submitted = st.form_submit_button("Save task", type="primary", icon=":material/check:")
    if submitted:
        try:
            db.save_task(title, project, description, status, priority, due, recurrence, int(estimate), tags, identifier)
            flash("Task saved.")
        except ValueError as exc:
            st.error(str(exc))
    if identifier:
        st.divider()
        st.subheader("Checklist")
        for item in db.checklist(identifier):
            with st.container(horizontal=True, vertical_alignment="center"):
                done = st.checkbox(item["text"], bool(item["done"]), key="check_" + item["id"])
                if done != bool(item["done"]):
                    db.check(item["id"], done)
                if st.button("Remove", icon=":material/close:", key="rm_" + item["id"], type="tertiary"):
                    db.remove_check(item["id"])
                    st.session_state["open_task"] = identifier
                    st.rerun()
        with st.form("add_check", clear_on_submit=True, border=False):
            text = st.text_input("Add a checklist item", max_chars=300)
            add = st.form_submit_button("Add item", icon=":material/add:")
        if add:
            try:
                db.add_check(identifier, text)
                st.session_state["open_task"] = identifier
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if st.button("Move task to trash", icon=":material/delete:", type="tertiary"):
            db.trash("tasks", identifier)
            flash("Task moved to trash. Restore it in Settings.")


def project_editor(identifier=None):
    st.session_state["open_project"] = identifier or True
    st.rerun()


def dismiss_project():
    st.session_state.pop("open_project", None)


@st.dialog("Project details", on_dismiss=dismiss_project)
def render_project_editor(identifier=None):
    db = store()
    p = db.get("projects", identifier) if identifier else {}
    with st.form("project_editor", border=False):
        name = st.text_input("Project name", p.get("name", ""), max_chars=100)
        desc = st.text_area("Purpose", p.get("description", ""), height=100)
        color = st.color_picker("Project accent", p.get("color", "#427365"))
        save = st.form_submit_button("Save project", type="primary")
    if save:
        try:
            db.save_project(name, desc, color, identifier)
            flash("Project saved.")
        except ValueError as exc:
            st.error(str(exc))
    if identifier and st.button("Archive project", icon=":material/archive:", type="tertiary"):
        db.archive_project(identifier)
        flash("Project archived. Its tasks are hidden from active views; notes and history are preserved.")


def task_card(task, actions=True, key_prefix=""):
    db = store()
    with st.container(border=True, key=key_prefix + "card_" + task["id"]):
        project = task.get("project_name") or "INBOX"
        color = task.get("project_color") or "#879b8e"
        st.html(f'<div class="project-chip"><span style="background:{color}"></span>{html.escape(project.upper())}</div>')
        st.markdown(f"**{html.escape(task['title'])}**")
        bits = [task["priority"] + " priority", f"{task['estimate_minutes']} min"]
        if task["due_date"]:
            due = date.fromisoformat(task["due_date"])
            bits.append("Today" if due == date.today() else due.strftime("%d %b"))
            if due < date.today() and task["status"] != "Done":
                bits.append("Overdue")
        if task["recurrence"] != "None":
            bits.append(task["recurrence"])
        st.caption(" · ".join(bits))
        checks = db.checklist(task["id"])
        if checks:
            completed = sum(c["done"] for c in checks)
            st.progress(completed / len(checks), text=f"{completed}/{len(checks)} checklist items")
        tags = json.loads(task["tags"])
        if tags:
            st.caption(" ".join("#" + html.escape(t) for t in tags))
        if actions:
            with st.container(horizontal=True):
                if st.button("Details", icon=":material/open_in_new:", key=key_prefix + "edit_" + task["id"], type="tertiary"):
                    task_editor(task["id"])
                if task["status"] != "Done":
                    next_status = STATUSES[STATUSES.index(task["status"]) + 1]
                    if st.button(next_status, icon=":material/arrow_forward:", key=key_prefix + "move_" + task["id"], type="tertiary"):
                        db.move_task(task["id"], next_status)
                        flash(f"Task moved to {next_status}.")
                elif st.button("Reopen", icon=":material/undo:", key=key_prefix + "reopen_" + task["id"], type="tertiary"):
                    db.move_task(task["id"], "Next")
                    flash("Task reopened.")


@st.dialog("Quick find & create", width="large")
def quick_find():
    with st.container(horizontal=True):
        if st.button("New task", icon=":material/add_task:"):
            st.session_state["open_task"] = True
            st.rerun()
        if st.button("New note", icon=":material/note_add:"):
            st.switch_page("app_pages/notes.py")
        if st.button("Start focus", icon=":material/timer:"):
            st.switch_page("app_pages/focus.py")
    query = st.text_input("Search tasks and notes", placeholder="Try a title, phrase, or tag…")
    if query.strip():
        tasks = store().tasks(query=query)[:12]
        notes = store().notes(query=query)[:12]
        st.caption(f"{len(tasks)} tasks · {len(notes)} notes shown")
        for task in tasks:
            if st.button(task["title"], key="found_" + task["id"], icon=":material/task_alt:", width="stretch"):
                st.session_state["open_task"] = task["id"]
                st.rerun()
        for note in notes:
            if st.button(note["title"], key="found_" + note["id"], icon=":material/description:", width="stretch"):
                st.session_state["selected_note"] = note["id"]
                st.switch_page("app_pages/notes.py")
        if not tasks and not notes:
            st.info("No results. Try a shorter phrase or another tag.")


def completed_minutes(day=None):
    day = day or date.today()
    sessions = store().history()
    return sum(s["accumulated_seconds"] for s in sessions if s["state"] == "completed" and datetime.fromtimestamp(s["finished_at"]).date() == day) / 60


def slug(title):
    return re.sub(r"[^\w .-]", "", title, flags=re.UNICODE).strip(" .")[:80] or "note"
