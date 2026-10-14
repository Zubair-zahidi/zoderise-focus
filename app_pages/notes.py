import json

import streamlit as st

from focus.ui import store, header, project_choices, slug, flash

db = store()
header("Ideas & reference", "A place to think clearly.", "Searchable Markdown notes, connected to the projects behind them.")
query = st.text_input("Search notes", placeholder="Search titles, contents, or tags…")
notes = db.notes(query=query)
left, right = st.columns([1, 3], gap="large")
with left:
    if st.button("New note", type="primary", icon=":material/note_add:", width="stretch"):
        st.session_state["selected_note"] = None
        st.session_state["note_new"] = True
        st.rerun()
    st.caption(f"{len(notes)} NOTES")
    for note in notes:
        if st.button(note["title"], key="select_note_" + note["id"], width="stretch", icon=":material/description:"):
            st.session_state["selected_note"] = note["id"]
            st.session_state["note_new"] = False
            st.rerun()
        st.caption(note["project_name"] or "Personal")
with right:
    identifier = st.session_state.get("selected_note")
    if not identifier and notes and not st.session_state.get("note_new"):
        identifier = notes[0]["id"]
    note = db.get("notes", identifier) if identifier else {}
    if note and note["deleted_at"] is not None:
        note, identifier = {}, None
    note = note or {}
    tabs = st.tabs(["Write", "Preview"])
    options, labels = project_choices(note.get("project_id"))
    with tabs[0]:
        with st.form("note_form_" + str(identifier), border=False):
            title = st.text_input("Note title", note.get("title", ""), max_chars=200, placeholder="Give this idea a name")
            project = st.selectbox("Linked project", options, index=options.index(note.get("project_id")), format_func=labels)
            body = st.text_area("Markdown", note.get("body", ""), height=360, placeholder="# An idea worth keeping\n\nStart writing…", max_chars=200000)
            tags = st.text_input("Tags", ", ".join(json.loads(note.get("tags", "[]"))), placeholder="ideas, research")
            save = st.form_submit_button("Save note", type="primary", icon=":material/save:")
        if save:
            try:
                st.session_state["selected_note"] = db.save_note(title, body, project, tags, identifier)
                st.session_state["note_new"] = False
                flash("Note saved. Preview shows the saved version.")
            except ValueError as exc:
                st.error(str(exc))
    with tabs[1]:
        if note:
            st.subheader(note["title"])
            # Raw HTML is not executed; remote images are not fetched into the preview.
            preview = __import__("re").sub(r"!\[([^\]]*)\]\([^)]*\)", r"[Image: \1 — open separately]", note["body"])
            st.markdown(preview)
        else:
            st.info("Save your note to see its Markdown preview.")
    if identifier:
        with st.container(horizontal=True):
            st.download_button("Download Markdown", note["body"], slug(note["title"]) + ".md", "text/markdown", icon=":material/download:")
            if st.button("Move note to trash", icon=":material/delete:", type="tertiary"):
                db.trash("notes", identifier)
                st.session_state["selected_note"] = None
                flash("Note moved to trash. Restore it in Settings.")
    st.caption("Markdown supports headings, lists, links, quotes, and code. Preview shows saved content; remote images are omitted.")
