from focus.i18n import t
import hashlib
import json
import uuid
from datetime import datetime
import streamlit as st
from focus.ui import store, header, project_choices, slug, flash
from focus.components import EDITOR
db = store()
header(t('Ideas & reference'), t('A place to think clearly.'), t('Searchable Markdown notes, with autosaved drafts and recoverable versions.'))
query = st.text_input(t('Search notes'), placeholder=t('Search titles, contents, or tags…'))
notes = db.notes(query=query)
left, right = st.columns([1, 3], gap='large')
with left:
    if st.button(t('New note'), type='primary', icon=':material/note_add:', width='stretch'):
        st.session_state.update(selected_note=None, note_new=True, new_draft=str(uuid.uuid4()))
        st.rerun()
    st.caption(f'{len(notes)} NOTES')
    for note in notes:
        if st.button(note['title'], key='select_note_' + note['id'], width='stretch', icon=':material/description:'):
            st.session_state.update(selected_note=note['id'], note_new=False)
            st.rerun()
        st.caption(note['project_name'] or 'Personal')
    with st.expander(t('Recover drafts')):
        drafts = db.rows('SELECT * FROM note_drafts ORDER BY updated_at DESC')
        if not drafts:
            st.caption(t('No unfinished drafts.'))
        for draft in drafts:
            if st.button(draft['title'] or 'Untitled draft', key='recover_' + draft['id']):
                st.session_state.update(selected_note=draft['note_id'], note_new=not bool(draft['note_id']))
                if not draft['note_id']:
                    st.session_state['new_draft'] = draft['id']
                st.session_state['note_revision'] = st.session_state.get('note_revision', 0) + 1
                st.rerun()
with right:
    identifier = st.session_state.get('selected_note')
    if not identifier and notes and (not st.session_state.get('note_new')):
        identifier = notes[0]['id']
    note = db.get('notes', identifier) if identifier else None
    if note and note['deleted_at'] is not None:
        note, identifier = (None, None)
    draft_id = identifier or st.session_state.setdefault('new_draft', str(uuid.uuid4()))
    content = db.get('note_drafts', draft_id) or note or {}
    revision = str(st.session_state.get('note_revision', 0))
    prefix = draft_id + '_' + revision
    title_key, project_key, tags_key, plain_key, editor_key = ['note_' + name + '_' + prefix for name in ('title', 'project', 'tags', 'plain', 'rich')]

    def autosave():
        try:
            body = st.session_state.get(plain_key, content.get('body', '')) if st.session_state.get('plain_editor', False) else st.session_state.get(editor_key, {}).get('body', content.get('body', ''))
            tags = st.session_state[tags_key] if tags_key in st.session_state else json.loads(content.get('tags', '[]'))
            db.save_draft(draft_id, st.session_state.get(title_key, content.get('title', '')), body, st.session_state.get(project_key, content.get('project_id')), tags, identifier)
        except ValueError as exc:
            st.session_state['draft_error'] = str(exc)
    tabs = st.tabs([t('Write'), t('Preview'), t('Version history')])
    options, labels = project_choices(content.get('project_id'))
    with tabs[0]:
        st.text_input(t('Note title'), content.get('title', ''), max_chars=200, key=title_key, on_change=autosave, placeholder=t('Give this idea a name'))
        st.selectbox(t('Linked project'), options, index=options.index(content.get('project_id')), format_func=labels, key=project_key, on_change=autosave)
        plain = st.toggle(t('Use plain editor'), key='plain_editor', help=t('The plain editor autosaves when you leave the field. The rich editor autosaves while typing.'))
        if plain:
            body = st.text_area(t('Markdown'), content.get('body', ''), height=360, max_chars=200000, key=plain_key, on_change=autosave)
        else:
            result = EDITOR(key=editor_key, data={'body': content.get('body', ''), 'identity': hashlib.sha256(str(db.path).encode()).hexdigest()[:16] + ':' + db.settings()['_draft_epoch'] + ':' + draft_id, 'token': prefix, 'updated': content.get('updated_at', 0), 'force': int(revision) > 0, 'direction': 'rtl' if db.settings()['language'] != 'English' else 'ltr', 'label': 'Markdown', 'saving': 'Saving draft…', 'saved': 'Draft saved', 'hint': 'Body autosaves after a short pause. Save note publishes a version.'}, default={'body': content.get('body', '')}, on_body_change=autosave)
            body = result.body
        tags = st.text_input(t('Tags'), ', '.join(json.loads(content.get('tags', '[]'))), key=tags_key, on_change=autosave, placeholder=t('ideas, research'))
        if (error := st.session_state.pop('draft_error', None)):
            st.error(error)
        if st.button(t('Save note'), type='primary', icon=':material/save:'):
            try:
                st.session_state['selected_note'] = db.save_note(st.session_state[title_key], body, st.session_state[project_key], tags, identifier)
                db.clear_draft(draft_id)
                st.session_state.update(note_new=False, note_revision=int(revision) + 1)
                flash('Note saved. The previous published version is available in history.')
            except ValueError as exc:
                st.error(str(exc))
    with tabs[1]:
        if body:
            preview = __import__('re').sub('!\\[([^\\]]*)\\](?:\\([^)]*\\))?', '[Image: \\1 — omitted]', body)
            st.markdown(preview)
        else:
            st.info(t('Start writing to preview your draft.'))
    with tabs[2]:
        versions = db.note_versions(identifier) if identifier else []
        st.caption(t('Up to 50 previous published versions per note. Restoring a version preserves the current published content in history.'))
        if not versions:
            st.caption(t('No previous published versions yet.'))
        for version in versions:
            with st.expander(version['title'] + ' · ' + datetime.fromtimestamp(version['created_at']).strftime('%d %b · %H:%M:%S')):
                st.code(version['body'], language='markdown')
                if st.button(t('Restore this version'), key='version_' + version['id']):
                    db.restore_note_version(version['id'])
                    db.clear_draft(draft_id)
                    st.session_state['note_revision'] = int(revision) + 1
                    flash('Previous version restored.')
    if identifier:
        with st.container(horizontal=True):
            st.download_button(t('Download Markdown'), body or '', slug(st.session_state[title_key]) + '.md', 'text/markdown', icon=':material/download:')
            if st.button(t('Move note to trash'), icon=':material/delete:', type='tertiary'):
                db.trash('notes', identifier)
                st.session_state['selected_note'] = None
                flash('Note moved to trash. Restore it in Settings.')
    st.caption(t('Drafts are stored locally and included in backups. Backup and restore passwords are never stored in the workspace.'))
