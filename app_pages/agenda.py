from focus.i18n import t
from datetime import date, timedelta
import streamlit as st
from focus.ui import store, header, task_card, task_editor
db = store()
header(t('Your agenda'), t('See what is coming.'), t('Deadlines, loose ends, and space to plan ahead.'))
with st.container(horizontal=True):
    query = st.text_input(t('Search agenda'), placeholder=t('Title or tag…'), width=320)
    if st.button(t('Add task'), type='primary', icon=':material/add:'):
        task_editor()
tasks = [t for t in db.tasks(query=query) if t['status'] != 'Done']
today, week = (date.today().isoformat(), (date.today() + timedelta(days=7)).isoformat())
groups = [('Overdue', [t for t in tasks if t['due_date'] and t['due_date'] < today]), ('Today', [t for t in tasks if t['due_date'] == today]), ('Next 7 days', [t for t in tasks if t['due_date'] and today < t['due_date'] <= week]), ('Later / no deadline', [t for t in tasks if not t['due_date'] or t['due_date'] > week])]
tabs = st.tabs([f'{label} · {len(items)}' for label, items in groups])
for tab, (label, items) in zip(tabs, groups):
    with tab:
        st.subheader(label)
        if not items:
            st.info(t('All clear in this view.'), icon=':material/check_circle:')
        for task in items:
            task_card(task, key_prefix='agenda_')
st.divider()
st.download_button(t('Export deadlines to calendar'), db.calendar_export(), 'zoderise-focus-deadlines.ics', 'text/calendar', icon=':material/event:')
st.caption(t('An all-day calendar file for unfinished tasks with due dates. Import manually; it does not sync automatically.'))
