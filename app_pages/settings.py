import json
from datetime import date

import streamlit as st

from focus.ui import store, header, flash

db = store()
header("Your space, your way", "Make it feel like yours.", "Appearance, routines, data ownership, and a way back when plans change.")
appearance_tab, data_tab, trash_tab, about_tab = st.tabs(["Appearance & routine", "Export & backup", "Trash & archive", "About"])
with appearance_tab:
    s = db.settings()
    with st.form("preferences", border=False):
        name = st.text_input("Your first name · optional", s["name"], max_chars=80)
        accent = st.selectbox("Accent palette", ["Forest", "Ocean", "Violet", "Copper"], index=["Forest", "Ocean", "Violet", "Copper"].index(s["accent"]))
        compact = st.toggle("Compact spacing", s["compact"])
        motion = st.toggle("Gentle transitions", s["motion"])
        c1, c2, c3 = st.columns(3)
        with c1:
            goal = st.number_input("Default daily goal · min", 1, 720, s["goal"])
        with c2:
            focus = st.number_input("Default session · min", 1, 180, min(180, s["focus_minutes"]))
        with c3:
            rest = st.number_input("Break · minutes", 1, 60, min(60, s["break_minutes"]))
        if st.form_submit_button("Save preferences", type="primary", icon=":material/check:"):
            db.set_settings(name=name, accent=accent, compact=compact, motion=motion, goal=int(goal), focus_minutes=int(focus), break_minutes=int(rest))
            flash("Preferences saved.")
    st.info("For light or dark appearance, use the app's top-right menu → Settings → theme. Your operating system's reduced-motion preference is respected.", icon=":material/palette:")
    st.caption("Accent and routine preferences belong to this workspace. Light/dark selection belongs to the browser or desktop view.")
with data_tab:
    st.subheader("Keep a copy you control.")
    st.write("Your workspace is stored locally. Exports and backups contain your notes and tasks in readable, unencrypted form. Keep them somewhere you trust.")
    with st.container(horizontal=True):
        st.download_button("Download verified backup", db.backup(), f"zoderise-focus-{date.today()}.zip", "application/zip", icon=":material/backup:")
        st.download_button("Export tasks CSV", db.csv_export(), "focus-tasks.csv", "text/csv", icon=":material/table_chart:")
        st.download_button("Export workspace JSON", json.dumps(db.snapshot(), ensure_ascii=False, indent=2), "focus-workspace.json", "application/json", icon=":material/data_object:")
    st.caption("ZIP backups include a SHA-256 corruption check. This is not encryption or a proof of who created the file. Running sessions are exported as paused.")
    st.divider()
    st.subheader("Restore a workspace")
    upload = st.file_uploader("Zoderise Focus backup (.zip)", type="zip", max_upload_size=20)
    if upload:
        blob = upload.getvalue()
        try:
            snapshot = db.inspect_backup(blob)
            st.caption("Backup contents: " + " · ".join(f"{len(snapshot['tables'][t])} {t.replace('_', ' ')}" for t in ("projects", "tasks", "notes", "focus_sessions")))
            confirmed = st.checkbox("Replace this workspace with the backup. A safety copy will be saved first.")
            if st.button("Restore backup", icon=":material/restore:", disabled=not confirmed):
                path = db.restore(blob)
                st.session_state.pop("selected_note", None)
                flash(f"Backup restored. Safety copy saved to {path.name} in your local backups folder.")
        except ValueError as exc:
            st.error(str(exc))
    st.caption(f"Workspace location: {db.path.parent}")
with trash_tab:
    st.subheader("Nothing disappears by accident.")
    st.caption("Trashed items remain available until you restore them. This release has no permanent-delete button.")
    for table, rows in (("tasks", db.tasks(trash=True)), ("notes", db.notes(trash=True))):
        st.markdown("**" + table.capitalize() + "**")
        if not rows:
            st.caption("Trash is empty.")
        for item in rows:
            with st.container(horizontal=True, horizontal_alignment="distribute"):
                st.write(item["title"])
                if st.button("Restore", icon=":material/undo:", key="restore_" + item["id"]):
                    db.trash(table, item["id"], restore=True)
                    flash("Item restored.")
    st.markdown("**Archived projects**")
    archived = db.projects(archived=True)
    if not archived:
        st.caption("No archived projects.")
    for p in archived:
        with st.container(horizontal=True, horizontal_alignment="distribute"):
            st.write(p["name"])
            if st.button("Unarchive", key="unarchive_" + p["id"], icon=":material/unarchive:"):
                db.archive_project(p["id"], False)
                flash("Project unarchived.")
with about_tab:
    st.subheader("Zoderise Focus")
    st.write("A personal productivity workspace by **Zubair Zahidi**, founder of **Zoderise**.")
    st.write("Built to help people organize practical work, capture useful ideas, and find time for focused progress.")
    st.markdown("**Version 1.0.0** · Projects · Notes · Focus · Local control")
    st.caption("No account, cloud sync, AI model, telemetry, or collaboration service. The desktop server binds to this computer only. Local files are not encrypted; device permissions and disk security still matter.")
    st.link_button("Source & releases", "https://github.com/Zubair-zahidi/zoderise-focus", icon=":material/code:")
