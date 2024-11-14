from datetime import datetime, timedelta

import DefaultParameters
from Utilities import SimpleCounterLLMConversation


class SessionCache:
    def __init__(self, session_key: str, data: dict):
        self.m_session_key = session_key
        self.m_data = data
        self.m_last_update = datetime.utcnow()
        self.m_simpleCounterLLMConversation = SimpleCounterLLMConversation()
        self.m_conundrum = None   #DefaultParameters.get_default_conundrum()
        self.m_scenario = DefaultParameters.get_default_scenario()
        self.m_actionPlan = DefaultParameters.get_default_action_plan()

    def update(self, data: dict):
        self.m_data.update(data)
        self.m_last_update = datetime.utcnow()

    def set_conundrum(self, p_conundrum):
        self.m_conundrum = p_conundrum

    def set_scenario(self, p_scenario):
        self.m_scenario = p_scenario

    def set_action_plan(self, p_action_plan):
        self.m_actionPlan = p_action_plan

    def get_conundrum(self):
        return self.m_conundrum

    def get_scenario(self):
        return self.m_scenario

    def get_action_plan(self):
        return self.m_actionPlan


class SessionCacheManager:
    def __init__(self, idle_timeout: timedelta = timedelta(hours=4)):
        self.sessions = {}
        self.idle_timeout = idle_timeout

    def add_session(self, session_key: str, data: dict):
        session = SessionCache(session_key, data)
        self.sessions[session_key] = session

    def get_session(self, session_key: str) -> SessionCache:
        return self.sessions.get(session_key)

    def remove_session(self, session_key: str):
        if session_key in self.sessions:
            del self.sessions[session_key]

    def cleanup_idle_sessions(self):
        now = datetime.utcnow()
        idle_sessions = [
            key
            for key, session in self.sessions.items()
            if now - session.last_update > self.idle_timeout
        ]
        for session_key in idle_sessions:
            self.remove_session(session_key)
