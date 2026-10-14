from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from focus.ui import store, header, completed_minutes, flash

db = store()
header("Activity & review", "Notice the work you have done.", "Recorded sessions and completed tasks. A useful reflection, without a score to chase.")
start = date.today() - timedelta(days=6)
history = [s for s in db.history() if s["state"] == "completed" and datetime.fromtimestamp(s["finished_at"]).date() >= start]
done = [t for t in db.tasks(include_archived=True) if t["status"] == "Done" and t["completed_at"] and datetime.fromtimestamp(t["completed_at"]).date() >= start]
minutes = sum(s["accumulated_seconds"] for s in history) / 60
cols = st.columns(3)
cols[0].metric("7-day recorded focus", f"{minutes:.0f} min", border=True, icon=":material/timer:")
cols[1].metric("Completed sessions", len(history), border=True, icon=":material/check_circle:")
cols[2].metric("Tasks completed", len(done), border=True, icon=":material/task_alt:")
st.write("")
with st.container(border=True):
    st.subheader("A rhythm, day by day")
    days = [date.today() - timedelta(days=i) for i in range(13, -1, -1)]
    data = pd.DataFrame({"Day": [d.strftime("%d %b") for d in days], "Recorded minutes": [round(completed_minutes(d), 1) for d in days]})
    st.bar_chart(data, x="Day", y="Recorded minutes", color="#427365", height=260, sort=False)
    st.caption("Sessions count on the day they finish. Partial sessions count only when you choose Finish & record. Cancelled sessions are excluded.")
left, right = st.columns([3, 2], gap="large")
with left:
    st.subheader("This week's completed work")
    if done:
        for task in done[:20]:
            st.write(":material/check_circle: " + task["title"])
    else:
        st.info("Completed tasks will appear here. Start with one small next step.")
    st.subheader("Today's reflection")
    plan = db.day_plan()
    with st.form("reflection", border=False):
        journal = st.text_area("What worked? What needs a different approach?", plan["journal"], height=140)
        if st.form_submit_button("Save reflection", icon=":material/save:"):
            db.save_plan(plan["goal_minutes"], journal)
            flash("Reflection saved.")
with right:
    with st.container(border=True):
        st.caption("MAKE THE NEXT WEEK LIGHTER")
        st.markdown("### A five-minute review\n\n1. Celebrate one thing you finished.\n2. Revisit overdue tasks.\n3. Archive projects that are complete.\n4. Choose one outcome for next week.\n5. Make a backup.")
        report = f"# Zoderise Focus · weekly review\n\nWeek ending {date.today()}\n\n- Recorded focus: {minutes:.1f} minutes\n- Completed sessions: {len(history)}\n- Tasks completed: {len(done)}\n\n## Completed work\n" + "\n".join("- " + t["title"] for t in done) + "\n\n## Reflection\n" + plan["journal"]
        if st.session_state.get("demo"):
            report = "DEMO WORKSPACE — SAMPLE DATA\n\n" + report
        st.download_button("Download weekly review", report, f"focus-review-{date.today()}.md", "text/markdown", icon=":material/download:")
