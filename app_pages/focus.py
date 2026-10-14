from datetime import datetime
import time

import streamlit as st

from focus.ui import store, header, flash

db = store()
header("Focus room", "One thing. Your full attention.", "Set an intention, start the timer, and give yourself room to work.")


@st.fragment(run_every=1)
def timer():
    db = store()
    session = db.active()
    if not session:
        return
    elapsed = db.elapsed(session)
    if session["state"] == "running" and elapsed >= session["planned_seconds"]:
        db.control_focus("complete")
        st.session_state["break_until"] = time.time() + db.settings()["break_minutes"] * 60
        flash("Session complete. Take a breath and a short break.")
    remaining = max(0, int(session["planned_seconds"] - elapsed))
    with st.container(border=True, key="timer_room"):
        st.caption("PAUSED · YOUR PLACE IS SAVED" if session["state"] == "paused" else "IN FOCUS · ONE STEP AT A TIME")
        st.subheader(session["intent"])
        st.html(f'<div class="timer-number">{remaining // 60:02d}<span>:</span>{remaining % 60:02d}</div>')
        st.progress(min(1.0, elapsed / session["planned_seconds"]), text=f"{int(elapsed / 60)} of {session['planned_seconds'] // 60} minutes")
        with st.container(horizontal=True, horizontal_alignment="center"):
            action = "resume" if session["state"] == "paused" else "pause"
            if st.button(action.capitalize(), type="primary", icon=":material/play_arrow:" if action == "resume" else ":material/pause:", key="timer_action"):
                db.control_focus(action)
                st.rerun()
            if st.button("Finish & record", icon=":material/check:", key="finish_focus"):
                db.control_focus("complete")
                st.session_state["break_until"] = time.time() + db.settings()["break_minutes"] * 60
                flash("Session recorded using the elapsed timer time.")
            with st.popover("Cancel", icon=":material/close:"):
                st.caption("Cancel without adding time to activity totals.")
                if st.button("Cancel this session", key="cancel_focus"):
                    db.control_focus("cancel")
                    flash("Session cancelled.")
        st.caption("Timer state is saved locally. A running timer continues while the app is closed; pause it before stepping away.")


if db.active():
    timer()
else:
    @st.fragment(run_every=1)
    def break_timer():
        remaining = int(st.session_state.get("break_until", 0) - time.time())
        if remaining > 0:
            st.info(f"A little reset · {remaining // 60:02d}:{remaining % 60:02d} left. Stretch, look away from the screen, drink water.", icon=":material/spa:")
        elif st.session_state.pop("break_until", None):
            st.success("Your break is over. Start again when you are ready.")
    break_timer()
    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        with st.container(border=True):
            st.caption("BEGIN WITH INTENTION")
            st.subheader("What will you work on?")
            tasks = [t for t in db.tasks() if t["status"] != "Done"]
            choices = {t["id"]: t["title"] for t in tasks}
            selected = st.selectbox("Link a task · optional", [None] + list(choices), format_func=lambda key: choices.get(key, "An independent session"))
            with st.form("start_focus", border=False):
                intent = st.text_input("Session intention", value=choices.get(selected, ""), placeholder="Make meaningful progress on…", max_chars=200)
                settings = db.settings()
                minutes = st.slider("Duration · minutes", 1, 180, min(settings["focus_minutes"], 180), step=1)
                start = st.form_submit_button("Start focusing", type="primary", icon=":material/play_arrow:", width="stretch")
            if start:
                try:
                    db.start_focus(intent, minutes, selected)
                    flash("Focus session started.")
                except ValueError as exc:
                    st.error(str(exc))
    with c2:
        with st.container(border=True):
            st.caption("YOUR FOCUS RITUAL")
            st.markdown("### Make a little space.\n\n**Silence distractions.** Choose one task, close what you do not need.\n\n**Take the next step.** Progress can be small and still count.\n\n**Pause with intention.** The timer remembers where you left off.")
            st.caption("No blocked websites, background surveillance, or invented productivity scores.")

st.write("")
st.subheader("Recent sessions")
history = db.history()[:6]
if history:
    st.dataframe([{"Intention": s["intent"], "Recorded minutes": round(s["accumulated_seconds"] / 60, 1),
                   "State": s["state"].capitalize(), "Started": datetime.fromtimestamp(s["started_at"]).strftime("%d %b · %H:%M")} for s in history],
                 hide_index=True, width="stretch")
else:
    st.caption("Your first session starts the story. Completed sessions appear in Activity & review.")
