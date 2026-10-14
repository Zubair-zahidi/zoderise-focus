from datetime import date, datetime

import streamlit as st

from focus.ui import store, header, task_editor, task_card, completed_minutes, flash

db = store()
settings = db.settings()
name = settings["name"]
header(date.today().strftime("%A · %d %B %Y"), f"Make room for what matters{', ' + name if name else ''}.",
       "A clear plan. A little focus. Meaningful progress.")

with st.container(border=True, key="hero"):
    c1, c2 = st.columns([3, 2], vertical_alignment="center")
    with c1:
        st.caption("LESS FRICTION. MORE INTENTION.")
        st.subheader("One clear action. A better day.")
        st.write("Capture what is on your mind, choose what matters today, and give it your attention.")
        with st.container(horizontal=True):
            if st.button("Capture a task", icon=":material/add:", type="primary"):
                task_editor()
            if st.button("Enter focus room", icon=":material/timer:"):
                st.switch_page("app_pages/focus.py")
    with c2:
        from focus.ui import ROOT
        st.image(str(ROOT / "assets" / "focus-orbit.svg"), width="stretch")

tasks = db.tasks()
open_tasks = [t for t in tasks if t["status"] != "Done"]
today = date.today().isoformat()
due = [t for t in open_tasks if t["due_date"] and t["due_date"] <= today]
minutes = completed_minutes()
plan = db.day_plan()
cols = st.columns(4)
for col, label, value, icon in zip(cols, ["Open tasks", "Due & overdue", "Recorded focus", "Active projects"],
                                   [len(open_tasks), len(due), f"{minutes:.0f} min", len(db.projects())],
                                   [":material/task_alt:", ":material/event:", ":material/timelapse:", ":material/folder_open:"]):
    col.metric(label, value, icon=icon, border=True)

st.write("")
left, right = st.columns([3, 2], gap="large")
with left:
    with st.container(horizontal=True, vertical_alignment="center", horizontal_alignment="distribute"):
        st.subheader("On your radar")
        st.page_link("app_pages/agenda.py", label="See agenda", icon=":material/arrow_forward:")
    selected = due[:4] or [t for t in open_tasks if t["status"] in ("Doing", "Next")][:4] or open_tasks[:4]
    if not selected:
        with st.container(border=True):
            st.subheader("A fresh workspace")
            st.write("Start with one task or create a project. You can also explore the sample workspace in the sidebar.")
            if st.button("Create your first task", type="primary"):
                task_editor()
    for task in selected:
        task_card(task, key_prefix="today_")
with right:
    with st.container(border=True):
        st.caption("TODAY'S INTENTION")
        st.subheader("Protect a little time.")
        st.progress(min(1.0, minutes / plan["goal_minutes"]), text=f"{minutes:.0f} / {plan['goal_minutes']} minutes recorded")
        st.caption("Completed timer sessions, not a measure of attention or productivity.")
        with st.form("daily_plan", border=False):
            goal = st.number_input("Daily focus goal · minutes", min_value=1, max_value=720, value=plan["goal_minutes"], step=5)
            journal = st.text_area("What would make today worthwhile?", plan["journal"], height=110, placeholder="One outcome worth making time for…")
            if st.form_submit_button("Save intention", icon=":material/check:"):
                db.save_plan(int(goal), journal)
                flash("Today's intention saved.")
    active = db.active()
    if active:
        with st.container(border=True):
            st.caption("SESSION IN PROGRESS")
            st.write(active["intent"])
            st.caption(active["state"].capitalize())
            st.page_link("app_pages/focus.py", label="Return to your session", icon=":material/timer:")
    with st.container(border=True):
        st.caption("A SIMPLE RHYTHM")
        st.markdown("**01** Capture the task.\n\n**02** Choose your next action.\n\n**03** Focus, then reflect.")
