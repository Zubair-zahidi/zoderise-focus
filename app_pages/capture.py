from focus.i18n import t
import streamlit as st
from focus.ui import store, header, project_choices, flash
header(t('Quick capture'), t('Get it out of your head.'), t('Capture one next action, then return to your work.'))
options, labels = project_choices()
with st.form('quick_capture', clear_on_submit=True):
    title = st.text_input(t('Task title'), placeholder=t('What needs doing?'), max_chars=200)
    project = st.selectbox(t('Project'), options, format_func=labels)
    if st.form_submit_button(t('Capture task'), type='primary'):
        try:
            store().save_task(title, project)
            flash('Task captured in Inbox.')
        except ValueError as exc:
            st.error(str(exc))
st.page_link('app_pages/home.py', label=t('Return to Today'), icon=':material/wb_sunny:')
st.caption(t('Windows desktop users can enable Ctrl+Alt+Space in Settings. It works while the app is running; it does not launch a closed app.'))
