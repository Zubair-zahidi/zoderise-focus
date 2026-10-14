from focus.i18n import t
from datetime import date, timedelta, datetime
import calendar
import json
import streamlit as st
from focus.ui import store, header, task_card, flash
db = store()
header(t('Plan with intention'), t('Make the week workable.'), t('Plan work days separately from deadlines, reuse good routines, and learn from recorded time.'))
calendar_tab, templates_tab, time_tab = st.tabs([t('Calendar planning'), t('Project templates'), t('Estimated & recorded time')])
with calendar_tab:
    anchor = st.date_input(t('A day in the week to plan'), date.today())
    monday = anchor - timedelta(days=anchor.weekday())
    tasks = [t for t in db.tasks() if t['status'] != 'Done']
    names = {t['id']: t['title'] for t in tasks}
    if tasks:
        with st.form('schedule_task', border=False):
            chosen = st.selectbox(t('Task to schedule'), list(names), format_func=lambda key: names[key])
            work_day = st.date_input(t('Work day'), anchor)
            if st.form_submit_button(t('Plan this task'), type='primary'):
                plan = db.task_plan(chosen)
                db.set_task_plan(chosen, work_day, json.loads(plan['weekdays']), plan['interval_days'])
                flash('Task scheduled. Its deadline is unchanged.')
    st.caption(t('A planning date is not a timed calendar appointment. Dates use the Gregorian calendar.'))
    for offset in range(7):
        day = monday + timedelta(days=offset)
        with st.expander(day.strftime('%A · %d %b'), expanded=day == anchor):
            scheduled = [t for t in tasks if db.task_plan(t['id'])['scheduled_day'] == day.isoformat()]
            deadlines = [t for t in tasks if t['due_date'] == day.isoformat()]
            st.markdown(t('**Planned work**'))
            for task in scheduled:
                task_card(task, key_prefix=f'plan_{offset}_')
                if st.button(t('Unplan'), key='unplan_' + task['id']):
                    plan = db.task_plan(task['id'])
                    db.set_task_plan(task['id'], None, json.loads(plan['weekdays']), plan['interval_days'])
                    flash('Planning date cleared.')
            if not scheduled:
                st.caption(t('No planned tasks.'))
            st.markdown(t('**Deadlines**'))
            for task in deadlines:
                st.write(task['title'])
with templates_tab:
    templates = db.templates()
    mapping = {t['id']: t['name'] for t in templates}
    selected = st.selectbox(t('Template'), list(mapping), format_func=lambda key: mapping[key])
    template = next((t for t in templates if t['id'] == selected))
    for task in json.loads(template['payload']):
        st.write('• ' + task['title'])
    with st.form('apply_template', border=False):
        name = st.text_input(t('New project name'), mapping[selected])
        if st.form_submit_button(t('Create project from template'), type='primary'):
            try:
                db.apply_template(selected, name)
                flash('Project and checklists created from the template.')
            except ValueError as exc:
                st.error(str(exc))
    projects = db.projects()
    if projects:
        with st.form('save_template', border=False):
            choices = {p['id']: p['name'] for p in projects}
            project = st.selectbox(t("Save a project's tasks as a template"), list(choices), format_func=lambda key: choices[key])
            name = st.text_input(t('Template name'))
            if st.form_submit_button(t('Save reusable template')):
                try:
                    db.save_template(project, name)
                    flash('Reusable template saved.')
                except ValueError as exc:
                    st.error(str(exc))
with time_tab:
    sessions = db.history()
    rows = [{'Task': task['title'], 'Estimate (min)': task['estimate_minutes'], 'Recorded (min)': round(sum((s['accumulated_seconds'] for s in sessions if s['state'] == 'completed' and s['task_id'] == task['id'])) / 60, 1), 'Status': task['status']} for task in db.tasks(include_archived=True)]
    if rows:
        st.dataframe(rows, hide_index=True, width='stretch')
    else:
        st.info(t('Link focus sessions to tasks to compare estimates with recorded time.'))
    st.caption(t('Recorded time includes completed linked timer sessions only. It does not measure attention or automatically track computer use.'))
