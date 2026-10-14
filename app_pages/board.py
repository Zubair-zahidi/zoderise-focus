from focus.i18n import t
import streamlit as st
from focus.ui import store, header, task_editor, project_editor, task_card
from focus.store import STATUSES
from focus.components import BOARD
db = store()
header(t('Projects & tasks'), t('From idea to done.'), t('Keep the work visible. Move each task forward at your own pace.'))
projects = db.projects()
mapping = {p['id']: p['name'] for p in projects}
with st.container(horizontal=True, vertical_alignment='bottom'):
    selected = st.selectbox(t('Project'), [None] + list(mapping), format_func=lambda key: mapping.get(key, 'All active projects'), width=280)
    query = st.text_input(t('Filter tasks'), placeholder=t('Title or tag…'), width=280)
    if st.button(t('New task'), type='primary', icon=':material/add:'):
        task_editor()
    if st.button(t('New project'), icon=':material/create_new_folder:'):
        project_editor()
    if selected and st.button(t('Edit project'), icon=':material/edit:'):
        project_editor(selected)
if selected:
    p = db.get('projects', selected)
    if p['description']:
        st.info(p['description'], icon=':material/folder:')
elif projects:
    with st.expander(f'Your projects · {len(projects)}'):
        for p in projects:
            with st.container(horizontal=True, horizontal_alignment='distribute'):
                st.write(p['name'])
                if st.button(t('Edit'), key='project_' + p['id'], icon=':material/edit:', type='tertiary'):
                    project_editor(p['id'])
tasks = db.tasks(selected, query)
st.caption(t('Drag cards between columns or onto a card to reorder. Status menus and arrow buttons work with a keyboard and on touch screens.'))

def handle_board():
    event = st.session_state.get('focus_board', {}).get('event')
    if not event or event.get('nonce') == st.session_state.get('board_nonce'):
        return
    st.session_state['board_nonce'] = event.get('nonce')
    try:
        if event.get('action') == 'edit':
            st.session_state['open_task'] = event['id']
        elif event.get('action') == 'move':
            db.board_order(event['id'], event['status'], event.get('before'))
    except ValueError as exc:
        st.session_state['board_error'] = str(exc)
cards = []
for task in tasks:
    checks = db.checklist(task['id'])
    cards.append({'id': task['id'], 'title': task['title'], 'status': task['status'], 'project': task['project_name'], 'color': task['project_color'] or '#879b8e', 'detail': f"{task['priority']} · {task['estimate_minutes']} min" + (' · ' + task['due_date'] if task['due_date'] else ''), 'checks': f"{sum((x['done'] for x in checks))}/{len(checks)}" if checks else '', 'blocked': len(db.blocked(task['id']))})
BOARD(key='focus_board', data={'tasks': cards, 'statuses': list(STATUSES), 'labels': [t(s) for s in STATUSES], 'direction': 'rtl' if db.settings()['language'] != 'English' else 'ltr', 'details': t('Details'), 'move': t('Move'), 'up': t('Move up'), 'down': t('Move down'), 'inbox': t('Inbox'), 'blocked': t('Blocked'), 'empty': t('A little breathing room.')}, on_event_change=handle_board)
if (error := st.session_state.pop('board_error', None)):
    st.error(error)
with st.expander(t('Accessible list view')):
    for task in tasks:
        task_card(task, key_prefix='list_')
