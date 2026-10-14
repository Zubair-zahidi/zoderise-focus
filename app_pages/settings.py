from focus.i18n import t
import json
from datetime import date
import streamlit as st
from focus.ui import store, header, flash
db = store()
header(t('Your space, your way'), t('Make it feel like yours.'), t('Appearance, routines, data ownership, and a way back when plans change.'))
appearance_tab, data_tab, trash_tab, about_tab = st.tabs([t('Appearance & routine'), t('Export & backup'), t('Trash & archive'), t('About')])
with appearance_tab:
    s = db.settings()
    with st.form('preferences', border=False):
        name = st.text_input(t('Your first name · optional'), s['name'], max_chars=80)
        accent = st.selectbox(t('Accent palette'), ['Forest', 'Ocean', 'Violet', 'Copper'], index=['Forest', 'Ocean', 'Violet', 'Copper'].index(s['accent']))
        compact = st.toggle(t('Compact spacing'), s['compact'])
        motion = st.toggle(t('Gentle transitions'), s['motion'])
        language = st.selectbox(t('Interface language'), ['English', 'Dari', 'Pashto'], index=['English', 'Dari', 'Pashto'].index(s['language']))
        reminders = st.toggle(t('Deadline and session reminders'), s['reminders'])
        hotkey = st.toggle(t('Windows global quick capture · Ctrl+Alt+Space'), s['desktop_hotkey'])
        schedule = st.selectbox(t('Automatic backup schedule'), ['Off', 'Daily', 'Weekly'], index=['Off', 'Daily', 'Weekly'].index(s['backup_interval']))
        keep = st.number_input(t('Automatic backups to keep'), 3, 30, s['backup_keep'])
        c1, c2, c3 = st.columns(3)
        with c1:
            goal = st.number_input(t('Default daily goal · min'), 1, 720, s['goal'])
        with c2:
            focus = st.number_input(t('Default session · min'), 1, 180, min(180, s['focus_minutes']))
        with c3:
            rest = st.number_input(t('Break · minutes'), 1, 60, min(60, s['break_minutes']))
        if st.form_submit_button(t('Save preferences'), type='primary', icon=':material/check:'):
            db.set_settings(name=name, accent=accent, compact=compact, motion=motion, goal=int(goal), focus_minutes=int(focus), break_minutes=int(rest), language=language, reminders=reminders, desktop_hotkey=hotkey, backup_interval=schedule, backup_keep=int(keep))
            flash('Preferences saved.')
    st.info(t("For light or dark appearance, use the app's top-right menu → Settings → theme. Your operating system's reduced-motion preference is respected."), icon=':material/palette:')
    st.caption(t('Accent and routine preferences belong to this workspace. Light/dark selection belongs to the browser or desktop view.'))
    st.caption(t('Restart the Windows app after changing the global shortcut. Notifications can show task titles and follow Windows notification settings.'))
    st.caption(t('Automatic backups are local unencrypted ZIP files. They run while the app is open, or when you next open it after the interval. Closing the app stops the scheduler.'))
with data_tab:
    st.subheader(t('Keep a copy you control.'))
    st.write(t('Your workspace is stored locally. Exports and backups contain your notes and tasks in readable, unencrypted form. Keep them somewhere you trust.'))
    with st.container(horizontal=True):
        st.download_button(t('Download verified backup'), db.backup(), f'zoderise-focus-{date.today()}.zip', 'application/zip', icon=':material/backup:')
        st.download_button(t('Export tasks CSV'), db.csv_export(), 'focus-tasks.csv', 'text/csv', icon=':material/table_chart:')
        st.download_button(t('Export workspace JSON'), json.dumps(db.snapshot(), ensure_ascii=False, indent=2), 'focus-workspace.json', 'application/json', icon=':material/data_object:')
    st.caption(t('ZIP backups include a SHA-256 corruption check. This is not encryption or a proof of who created the file. Running sessions are exported as paused.'))
    if st.button(t('Create automatic backup now'), icon=':material/backup:'):
        path = db.auto_backup(force=True)
        if path:
            st.success('Backup created: ' + path.name)
    with st.expander(t('Password-encrypted backup')):
        from focus.crypto import encrypt_backup
        st.caption(t('Encryption protects this exported file. Your live database, automatic backups, and ordinary exports remain unencrypted. Lost passwords cannot be recovered.'))
        with st.form('encrypt_backup', border=False):
            password = st.text_input(t('Backup password · at least 12 characters'), type='password')
            confirm = st.text_input(t('Confirm backup password'), type='password')
            if st.form_submit_button(t('Create encrypted backup')):
                try:
                    if password != confirm:
                        raise ValueError('Backup passwords do not match.')
                    st.session_state['encrypted_backup'] = encrypt_backup(db.backup(), password)
                except ValueError as exc:
                    st.error(str(exc))
        if (payload := st.session_state.get('encrypted_backup')):
            st.download_button(t('Download encrypted backup'), payload, f'zoderise-focus-{date.today()}.focus', 'application/octet-stream')
    st.divider()
    st.subheader(t('Restore a workspace'))
    upload = st.file_uploader(t('Zoderise Focus backup (.zip or .focus)'), type=['zip', 'focus'], max_upload_size=28)
    if upload:
        blob = upload.getvalue()
        try:
            from focus.crypto import decrypt_backup, MAGIC
            if blob.startswith(MAGIC):
                password = st.text_input(t('Restore password'), type='password')
                if not password:
                    raise ValueError("Enter the encrypted backup's password to preview its contents.")
                blob = decrypt_backup(blob, password)
            snapshot = db.inspect_backup(blob)
            st.dataframe(db.backup_preview(blob), hide_index=True, width='stretch')
            st.caption(t('This is a replacement, not a merge. Removed means current records absent from the backup. A safety copy preserves the current workspace.'))
            st.caption('Backup contents: ' + ' · '.join((f"{len(snapshot['tables'][t])} {t.replace('_', ' ')}" for t in ('projects', 'tasks', 'notes', 'focus_sessions'))))
            confirmed = st.checkbox(t('Replace this workspace with the backup. A safety copy will be saved first.'))
            if st.button(t('Restore backup'), icon=':material/restore:', disabled=not confirmed):
                path = db.restore(blob)
                st.session_state.pop('selected_note', None)
                flash(f'Backup restored. Safety copy saved to {path.name} in your local backups folder.')
        except ValueError as exc:
            st.error(str(exc))
    st.caption(f'Workspace location: {db.path.parent}')
with trash_tab:
    st.subheader(t('Nothing disappears by accident.'))
    st.caption(t('Trashed items remain available until you restore them. This release has no permanent-delete button.'))
    for table, rows in (('tasks', db.tasks(trash=True)), ('notes', db.notes(trash=True))):
        st.markdown('**' + table.capitalize() + '**')
        if not rows:
            st.caption(t('Trash is empty.'))
        for item in rows:
            with st.container(horizontal=True, horizontal_alignment='distribute'):
                st.write(item['title'])
                if st.button(t('Restore'), icon=':material/undo:', key='restore_' + item['id']):
                    db.trash(table, item['id'], restore=True)
                    flash('Item restored.')
    st.markdown(t('**Archived projects**'))
    archived = db.projects(archived=True)
    if not archived:
        st.caption(t('No archived projects.'))
    for p in archived:
        with st.container(horizontal=True, horizontal_alignment='distribute'):
            st.write(p['name'])
            if st.button(t('Unarchive'), key='unarchive_' + p['id'], icon=':material/unarchive:'):
                db.archive_project(p['id'], False)
                flash('Project unarchived.')
with about_tab:
    st.subheader(t('Zoderise Focus'))
    st.write(t('A personal productivity workspace by **Zubair Zahidi**, founder of **Zoderise**.'))
    st.write(t('Built to help people organize practical work, capture useful ideas, and find time for focused progress.'))
    st.markdown(t('**Version 1.1.0** · Planning · Notes · Focus · Local control'))
    st.caption(t('No account, cloud sync, AI model, telemetry, or collaboration service. The desktop server binds to this computer only. Local files are not encrypted; device permissions and disk security still matter.'))
    st.link_button('Source & releases', 'https://github.com/Zubair-zahidi/zoderise-focus', icon=':material/code:')
