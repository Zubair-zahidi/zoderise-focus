from focus.i18n import t
from pathlib import Path
import streamlit as st
from focus import __version__
from focus.ui import appearance, store, quick_find, render_task_editor, render_project_editor
st.set_page_config(page_title='Zoderise Focus', page_icon=':material/center_focus_strong:', layout='wide')
appearance()
st.logo(str(Path(__file__).parent / 'assets' / 'wordmark.svg'), size='large', icon_image=str(Path(__file__).parent / 'assets' / 'icon.png'))
with st.sidebar:
    st.caption(t('Space for your best work.'))
    st.button(t('Quick find & create'), icon=':material/search:', width='stretch', on_click=quick_find, shortcut='Ctrl+K', disabled=bool(st.session_state.get('open_task') or st.session_state.get('open_project')))
    st.divider()
page = st.navigation({'WORKSPACE': [st.Page('app_pages/home.py', title=t('Today'), icon=':material/wb_sunny:', default=True), st.Page('app_pages/board.py', title=t('Projects & board'), icon=':material/view_kanban:'), st.Page('app_pages/agenda.py', title=t('Agenda'), icon=':material/calendar_today:'), st.Page('app_pages/notes.py', title=t('Notes'), icon=':material/description:'), st.Page('app_pages/focus.py', title=t('Focus room'), icon=':material/timer:'), st.Page('app_pages/review.py', title=t('Activity & review'), icon=':material/insights:'), st.Page('app_pages/planning.py', title=t('Planning & templates'), icon=':material/date_range:'), st.Page('app_pages/reminders.py', title=t('Reminders'), icon=':material/notifications:'), st.Page('app_pages/capture.py', title=t('Quick capture'), icon=':material/add_task:', visibility='hidden')], 'YOUR SPACE': [st.Page('app_pages/settings.py', title=t('Settings & backup'), icon=':material/tune:')]})
with st.sidebar:
    st.divider()
    is_demo = st.session_state.get('demo', False)
    st.caption('SAMPLE WORKSPACE' if is_demo else 'LOCAL WORKSPACE')
    st.caption(t('Offline · no account required'))
    if st.button('Leave demo' if is_demo else 'Explore sample workspace', icon=':material/science:', width='stretch'):
        st.session_state.clear()
        st.session_state['demo'] = not is_demo
        if not is_demo:
            store().seed_demo()
        st.rerun()
    st.caption(f'v{__version__} · By Zubair Zahidi')
    st.caption(t('Founder, Zoderise'))
if st.session_state.get('demo', False):
    st.info(t('Demo workspace · sample projects and activity. Your personal data stays separate.'), icon=':material/science:')
if (message := st.session_state.pop('flash', None)):
    st.toast(message, icon=':material/check_circle:')
page.run()
if (open_task := st.session_state.get('open_task')):
    render_task_editor(None if open_task is True else open_task)
elif (open_project := st.session_state.get('open_project')):
    render_project_editor(None if open_project is True else open_project)

@st.fragment(run_every=30)
def background_work():
    try:
        store().maintenance()
    except (ValueError, OSError) as exc:
        st.warning('Background task could not finish: ' + str(exc))
background_work()
