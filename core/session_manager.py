"""
core/session_manager.py — Persistent sessions across browser refreshes & tabs

Uses st.query_params (synchronous, no async component issues) to keep a
session token in the URL.  The actual session payload is stored in a
server-side dict that survives Streamlit reruns via @st.cache_resource.

  Refresh  → query-param is still in the URL → session restored instantly.
  New tab  → copy the URL (includes ?sid=…) → same session.
  Logout   → token removed from URL + server store.
"""

import uuid
import datetime
import streamlit as st


# ── Server-side session store (survives reruns, shared across users) ──
@st.cache_resource
def _get_session_store() -> dict:
    return {}  # { token: { username, role, … , ts } }


class SessionManager:
    PARAM_NAME = "sid"          # query-parameter key
    TTL_HOURS = 24              # auto-expire

    def __init__(self):
        self._store = _get_session_store()

    # ── Write ────────────────────────────────────────────────
    def create_session(self, user_data: dict):
        """Generate a token, persist data server-side, put token in URL."""
        token = uuid.uuid4().hex
        user_data["ts"] = datetime.datetime.now().isoformat()
        self._store[token] = user_data
        st.query_params[self.PARAM_NAME] = token

    # ── Read ─────────────────────────────────────────────────
    def get_session(self) -> dict | None:
        """Return session dict if a valid token exists, else None."""
        token = st.query_params.get(self.PARAM_NAME)
        if not token or token not in self._store:
            return None

        data = self._store[token]

        # TTL check
        ts = data.get("ts")
        if ts:
            created = datetime.datetime.fromisoformat(ts)
            age = (datetime.datetime.now() - created).total_seconds()
            if age > self.TTL_HOURS * 3600:
                self.destroy_session()
                return None
        return data

    # ── Delete ───────────────────────────────────────────────
    def destroy_session(self):
        """Remove token from URL and from server store."""
        token = st.query_params.get(self.PARAM_NAME)
        if token:
            self._store.pop(token, None)
        # Clear only our param, leave others intact
        if self.PARAM_NAME in st.query_params:
            del st.query_params[self.PARAM_NAME]

    # ── Convenience ──────────────────────────────────────────
    def is_logged_in(self) -> bool:
        return self.get_session() is not None

    # ── Restore full Streamlit session_state from token ──────
    def restore_session_state(self, db) -> bool:
        """
        Try to restore login state from the query-param token.
        Returns True if a valid session was found and state restored.
        """
        session = self.get_session()
        if not session:
            return False

        username = session.get("username")
        role = session.get("role")
        if not username or not role:
            return False

        # ── Candidate flow ──────────────────────────────
        if role == "Candidate":
            st.session_state.show_application_form = True
            if session.get("candidate_step"):
                st.session_state.candidate_step = session["candidate_step"]
            if session.get("current_candidate_id"):
                st.session_state.current_candidate_id = session["current_candidate_id"]
            return True

        # ── Employee / Admin ────────────────────────────
        user = db.users.get(username)
        if not user:
            self.destroy_session()
            return False

        st.session_state.logged_in = True
        st.session_state.current_user = user
        st.session_state.user_role = role
        return True

    # ── Save candidate progress ─────────────────────────────
    def save_candidate_progress(self, step: str, candidate_id: str = None):
        """Update the stored session with the candidate's current step."""
        token = st.query_params.get(self.PARAM_NAME)
        if token and token in self._store:
            self._store[token]["candidate_step"] = step
            if candidate_id:
                self._store[token]["current_candidate_id"] = candidate_id
