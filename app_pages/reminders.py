from focus.i18n import t
from datetime import datetime
import streamlit as st
from focus.ui import store, header, flash
db = store()
header(t('Gentle reminders'), t('Keep the important things visible.'), t('Due tasks and finished focus sessions, without a cloud notification service.'))
if not db.settings()['reminders']:
    st.info(t('Enable reminders in Settings to record deadline and session reminders.'))
alerts = db.alerts()
for alert in alerts:
    with st.container(border=True):
        st.subheader(alert['title'])
        st.write(alert['body'])
        st.caption(datetime.fromtimestamp(alert['created_at']).strftime('%d %b · %H:%M') + (' · Read' if alert['read_at'] else ' · Unread'))
        if not alert['read_at'] and st.button(t('Mark as read'), key='alert_' + alert['id']):
            db.mark_alert(alert['id'])
            flash('Reminder marked as read.')
if not alerts:
    st.caption(t('No reminders yet. Due-task reminders are recorded once per task each day while the app is active.'))
st.caption(t("Windows desktop notifications follow the operating system's notification settings. The browser app keeps reminders here; it does not send OS notifications."))
