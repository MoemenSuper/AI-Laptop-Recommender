import json
from datetime import datetime, timedelta


class ConversationMemory:
    def __init__(self, max_messages=20, session_timeout_minutes=30, max_sessions=50, max_memory_mb=100):
        self.sessions = {}
        self.max_messages = max_messages
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.max_sessions = max_sessions
        self.max_memory_mb = max_memory_mb

    def get_session_id(self, request):
        ip_address = request.environ.get("REMOTE_ADDR", "unknown")
        user_agent = request.headers.get("User-Agent", "unknown")[:50]
        return f"{ip_address}_{hash(user_agent)}"[:20]

    def has_messages(self, session_id):
        session = self.sessions.get(session_id)
        return bool(session and session["messages"])

    def add_message(self, session_id, role, content, metadata=None):
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "messages": [],
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
                "user_preferences": {},
            }

        self._cleanup_old_sessions()

        session = self.sessions[session_id]
        session["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        })
        session["last_activity"] = datetime.now()

        if len(session["messages"]) > self.max_messages:
            session["messages"] = session["messages"][-self.max_messages:]

        print(f"Added message to session {session_id}: {role} - {content[:50]}...")

    def get_conversation_history(self, session_id, include_system_prompt=True):
        session = self.sessions.get(session_id)
        if not session:
            return []

        if datetime.now() - session["last_activity"] > self.session_timeout:
            del self.sessions[session_id]
            print(f"Session {session_id} expired, starting fresh")
            return []

        messages = []
        if include_system_prompt:
            from .ai_training_system import LAPTOP_EXPERT_SYSTEM_PROMPT

            messages.append({
                "role": "system",
                "content": LAPTOP_EXPERT_SYSTEM_PROMPT,
            })

        for message in session["messages"]:
            messages.append({
                "role": message["role"],
                "content": message["content"],
            })

        return messages

    def get_context_summary(self, session_id):
        session = self.sessions.get(session_id)
        if not session or not session["messages"]:
            return ""

        user_messages = [
            message["content"].lower()
            for message in session["messages"]
            if message["role"] == "user"
        ]
        all_user_text = " ".join(user_messages)

        context = []
        if "gaming" in all_user_text:
            context.append("User is interested in gaming")
        if "student" in all_user_text:
            context.append("User is a student")
        if "budget" in all_user_text or "$" in all_user_text:
            context.append("User has budget considerations")
        if any(brand in all_user_text for brand in ["asus", "dell", "hp", "lenovo", "apple", "acer", "msi"]):
            context.append("User has brand preferences")
        if any(message["role"] == "assistant" for message in session["messages"]):
            context.append("Previous recommendations have been made")

        return f"CONVERSATION CONTEXT: {', '.join(context)}" if context else ""

    def update_user_preferences(self, session_id, preferences):
        if session_id in self.sessions:
            self.sessions[session_id]["user_preferences"].update(preferences)

    def get_user_preferences(self, session_id):
        if session_id not in self.sessions:
            return {}
        return self.sessions[session_id]["user_preferences"]

    def clear_all_sessions(self):
        session_count = len(self.sessions)
        self.sessions.clear()
        print(f"Cleared all {session_count} sessions")

    def get_memory_stats(self):
        memory_usage = self.get_memory_usage_mb()
        session_count = len(self.sessions)
        total_messages = sum(len(session["messages"]) for session in self.sessions.values())

        return {
            "memory_usage_mb": round(memory_usage, 2),
            "memory_limit_mb": self.max_memory_mb,
            "memory_usage_percent": round((memory_usage / self.max_memory_mb) * 100, 1),
            "active_sessions": session_count,
            "session_limit": self.max_sessions,
            "total_messages": total_messages,
            "max_messages_per_session": self.max_messages,
            "session_timeout_minutes": self.session_timeout.total_seconds() / 60,
        }

    def get_session_stats(self):
        return {
            "active_sessions": len(self.sessions),
            "total_messages": sum(len(session["messages"]) for session in self.sessions.values()),
            "sessions": {
                session_id: len(session["messages"])
                for session_id, session in self.sessions.items()
            },
        }

    def get_memory_usage_mb(self):
        total_size = 0
        for session in self.sessions.values():
            session_json = json.dumps(session, default=str)
            total_size += len(session_json.encode("utf-8"))
        return total_size / (1024 * 1024)

    def _cleanup_old_sessions(self):
        current_time = datetime.now()
        expired_session_ids = [
            session_id
            for session_id, session in self.sessions.items()
            if current_time - session["last_activity"] > self.session_timeout
        ]

        for session_id in expired_session_ids:
            del self.sessions[session_id]
            print(f"Cleaned up expired session: {session_id}")

        self._enforce_session_limits()

    def _enforce_session_limits(self):
        if len(self.sessions) > self.max_sessions:
            sessions_by_activity = sorted(
                self.sessions.items(),
                key=lambda item: item[1]["last_activity"],
            )
            excess_count = len(self.sessions) - self.max_sessions
            for session_id, _ in sessions_by_activity[:excess_count]:
                del self.sessions[session_id]
                print(f"Removed old session due to limit: {session_id}")

        if self.get_memory_usage_mb() > self.max_memory_mb:
            self._reduce_memory_usage()

    def _reduce_memory_usage(self):
        for session_id, session in self.sessions.items():
            if len(session["messages"]) > self.max_messages // 2:
                session["messages"] = session["messages"][-(self.max_messages // 2):]
                print(f"Reduced messages in session {session_id}")

        if self.get_memory_usage_mb() <= self.max_memory_mb:
            return

        sessions_by_activity = sorted(
            self.sessions.items(),
            key=lambda item: item[1]["last_activity"],
        )
        remove_count = max(1, len(self.sessions) // 4)
        for session_id, _ in sessions_by_activity[:remove_count]:
            del self.sessions[session_id]
            print(f"Removed session for memory: {session_id}")
