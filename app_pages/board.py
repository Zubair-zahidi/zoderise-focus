import streamlit as st

from focus.ui import store, header, task_editor, project_editor, task_card
from focus.store import STATUSES

db = store()
header("Projects & tasks", "From idea to done.", "Keep the work visible. Move each task forward at your own pace.")
projects = db.projects()
mapping = {p["id"]: p["name"] for p in projects}
with st.container(horizontal=True, vertical_alignment="bottom"):
    selected = st.selectbox("Project", [None] + list(mapping), format_func=lambda key: mapping.get(key, "All active projects"), width=280)
    query = st.text_input("Filter tasks", placeholder="Title or tag…", width=280)
    if st.button("New task", type="primary", icon=":material/add:"):
        task_editor()
    if st.button("New project", icon=":material/create_new_folder:"):
        project_editor()
    if selected and st.button("Edit project", icon=":material/edit:"):
        project_editor(selected)
if selected:
    p = db.get("projects", selected)
    if p["description"]:
        st.info(p["description"], icon=":material/folder:")
elif projects:
    with st.expander(f"Your projects · {len(projects)}"):
        for p in projects:
            with st.container(horizontal=True, horizontal_alignment="distribute"):
                st.write(p["name"])
                if st.button("Edit", key="project_" + p["id"], icon=":material/edit:", type="tertiary"):
                    project_editor(p["id"])
tasks = db.tasks(selected, query)
st.caption("Use the action on a card to advance it. Details lets you choose any status.")
for col, status in zip(st.columns(4, gap="medium"), STATUSES):
    with col:
        items = [t for t in tasks if t["status"] == status]
        with st.container(horizontal=True, horizontal_alignment="distribute"):
            st.subheader(status)
            st.caption(f"{len(items):02d}")
        st.divider()
        for task in items:
            task_card(task, key_prefix="board_")
        if not items:
            with st.container(border=True):
                st.caption("Nothing here yet.")
                st.write("A little breathing room.")
