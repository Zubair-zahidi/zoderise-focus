from pathlib import Path

import streamlit as st

from focus import __version__
from focus.ui import appearance, store, quick_find, render_task_editor, render_project_editor

st.set_page_config(page_title="Zoderise Focus", page_icon=":material/center_focus_strong:", layout="wide")
appearance()
st.logo(str(Path(__file__).parent / "assets" / "wordmark.svg"), size="large",
        icon_image=str(Path(__file__).parent / "assets" / "icon.png"))
with st.sidebar:
    st.caption("Space for your best work.")
    st.button("Quick find & create", icon=":material/search:", width="stretch", on_click=quick_find, shortcut="Ctrl+K")
    st.divider()

page = st.navigation({"WORKSPACE": [
    st.Page("app_pages/home.py", title="Today", icon=":material/wb_sunny:", default=True),
    st.Page("app_pages/board.py", title="Projects & board", icon=":material/view_kanban:"),
    st.Page("app_pages/agenda.py", title="Agenda", icon=":material/calendar_today:"),
    st.Page("app_pages/notes.py", title="Notes", icon=":material/description:"),
    st.Page("app_pages/focus.py", title="Focus room", icon=":material/timer:"),
    st.Page("app_pages/review.py", title="Activity & review", icon=":material/insights:"),
], "YOUR SPACE": [st.Page("app_pages/settings.py", title="Settings & backup", icon=":material/tune:")]})

with st.sidebar:
    st.divider()
    is_demo = st.session_state.get("demo", False)
    st.caption("SAMPLE WORKSPACE" if is_demo else "LOCAL WORKSPACE")
    st.caption("Offline · no account required")
    if st.button("Leave demo" if is_demo else "Explore sample workspace", icon=":material/science:", width="stretch"):
        st.session_state.clear()
        st.session_state["demo"] = not is_demo
        if not is_demo:
            store().seed_demo()
        st.rerun()
    st.caption(f"v{__version__} · By Zubair Zahidi")
    st.caption("Founder, Zoderise")

if st.session_state.get("demo", False):
    st.info("Demo workspace · sample projects and activity. Your personal data stays separate.", icon=":material/science:")
if message := st.session_state.pop("flash", None):
    st.toast(message, icon=":material/check_circle:")
page.run()
if open_task := st.session_state.get("open_task"):
    render_task_editor(None if open_task is True else open_task)
elif open_project := st.session_state.get("open_project"):
    render_project_editor(None if open_project is True else open_project)
