"""
Conversation Memory System for AI Chatbot
Remembers chat history and provides context-aware responses
"""

import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class ConversationMemory:
    def __init__(self, max_messages=20, session_timeout_minutes=30, max_sessions=50, max_memory_mb=100):
        """
        Initialize conversation memory system
        
        Args:
            max_messages: Maximum number of messages to remember per session
            session_timeout_minutes: Minutes before a session expires
            max_sessions: Maximum number of concurrent sessions to keep
            max_memory_mb: Maximum memory usage in MB before cleanup
        """
        self.sessions = {}  # Store conversations by session ID
        self.max_messages = max_messages
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.max_sessions = max_sessions
        self.max_memory_mb = max_memory_mb
    
    def get_session_id(self, request):
        """Generate or retrieve session ID from request"""
        # In a real app, you'd use actual session management
        # For now, we'll use IP address + user agent as simple session ID
        ip = request.environ.get('REMOTE_ADDR', 'unknown')
        user_agent = request.headers.get('User-Agent', 'unknown')[:50]
        return f"{ip}_{hash(user_agent)}"[:20]
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Dict = None):
        """Add a message to conversation history"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'messages': [],
                'created_at': datetime.now(),
                'last_activity': datetime.now(),
                'user_preferences': {}
            }
        
        session = self.sessions[session_id]
        
        # Clean old sessions periodically
        self._cleanup_old_sessions()
        
        # Add new message
        message = {
            'role': role,  # 'user' or 'assistant'
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        session['messages'].append(message)
        session['last_activity'] = datetime.now()
        
        # Keep only recent messages to avoid token limits
        if len(session['messages']) > self.max_messages:
            session['messages'] = session['messages'][-self.max_messages:]
        
        print(f"💾 Added message to session {session_id}: {role} - {content[:50]}...")
    
    def get_conversation_history(self, session_id: str, include_system_prompt: bool = True) -> List[Dict]:
        """Get conversation history formatted for AI API"""
        if session_id not in self.sessions:
            return []
        
        session = self.sessions[session_id]
        
        # Check if session is expired
        if datetime.now() - session['last_activity'] > self.session_timeout:
            print(f"🕒 Session {session_id} expired, starting fresh")
            del self.sessions[session_id]
            return []
        
        # Convert to API format
        messages = []
        
        # Add system prompt if requested
        if include_system_prompt:
            from ai_training_system import LAPTOP_EXPERT_SYSTEM_PROMPT
            messages.append({
                'role': 'system',
                'content': LAPTOP_EXPERT_SYSTEM_PROMPT
            })
        
        # Add conversation history
        for msg in session['messages']:
            messages.append({
                'role': msg['role'],
                'content': msg['content']
            })
        
        return messages
    
    def get_context_summary(self, session_id: str) -> str:
        """Get a summary of conversation context for enhanced prompts"""
        if session_id not in self.sessions:
            return ""
        
        session = self.sessions[session_id]
        messages = session['messages']
        
        if not messages:
            return ""
        
        # Analyze conversation for key context
        context_info = []
        
        # Look for user preferences mentioned in conversation
        user_messages = [msg['content'].lower() for msg in messages if msg['role'] == 'user']
        all_user_text = ' '.join(user_messages)
        
        # Extract mentioned preferences
        if 'gaming' in all_user_text:
            context_info.append("User is interested in gaming")
        if 'student' in all_user_text:
            context_info.append("User is a student")
        if 'budget' in all_user_text or '$' in all_user_text:
            context_info.append("User has budget considerations")
        if any(brand in all_user_text for brand in ['asus', 'dell', 'hp', 'lenovo', 'apple', 'acer', 'msi']):
            context_info.append("User has brand preferences")
        
        # Look for previous recommendations
        assistant_messages = [msg['content'].lower() for msg in messages if msg['role'] == 'assistant']
        if assistant_messages:
            context_info.append("Previous recommendations have been made")
        
        if context_info:
            return f"CONVERSATION CONTEXT: {', '.join(context_info)}"
        
        return ""
    
    def update_user_preferences(self, session_id: str, preferences: Dict):
        """Update user preferences based on conversation"""
        if session_id not in self.sessions:
            return
        
        self.sessions[session_id]['user_preferences'].update(preferences)
    
    def get_user_preferences(self, session_id: str) -> Dict:
        """Get stored user preferences"""
        if session_id not in self.sessions:
            return {}
        
        return self.sessions[session_id]['user_preferences']
    
    def _cleanup_old_sessions(self):
        """Remove expired sessions to save memory"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session['last_activity'] > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            print(f"🗑️ Cleaned up expired session: {session_id}")
        
        # Also enforce session limits
        self._enforce_session_limits()
    
    def _enforce_session_limits(self):
        """Enforce maximum session and memory limits"""
        # Check session count limit
        if len(self.sessions) > self.max_sessions:
            # Remove oldest sessions
            sessions_by_activity = sorted(
                self.sessions.items(),
                key=lambda x: x[1]['last_activity']
            )
            
            excess_count = len(self.sessions) - self.max_sessions
            for session_id, _ in sessions_by_activity[:excess_count]:
                del self.sessions[session_id]
                print(f"🗑️ Removed old session due to limit: {session_id}")
        
        # Check memory usage
        memory_usage = self.get_memory_usage_mb()
        if memory_usage > self.max_memory_mb:
            print(f"⚠️ Memory usage ({memory_usage:.1f}MB) exceeds limit ({self.max_memory_mb}MB)")
            self._reduce_memory_usage()
    
    def get_memory_usage_mb(self) -> float:
        """Estimate memory usage in MB"""
        import sys
        total_size = 0
        
        for session_id, session in self.sessions.items():
            # Estimate size of session data
            session_str = json.dumps(session, default=str)
            total_size += len(session_str.encode('utf-8'))
        
        return total_size / (1024 * 1024)  # Convert to MB
    
    def _reduce_memory_usage(self):
        """Reduce memory usage by removing old messages and sessions"""
        # First, reduce messages per session
        for session_id, session in self.sessions.items():
            if len(session['messages']) > self.max_messages // 2:
                # Keep only half the messages
                session['messages'] = session['messages'][-(self.max_messages // 2):]
                print(f"🗑️ Reduced messages in session {session_id}")
        
        # If still over limit, remove oldest sessions
        if self.get_memory_usage_mb() > self.max_memory_mb:
            sessions_by_activity = sorted(
                self.sessions.items(),
                key=lambda x: x[1]['last_activity']
            )
            
            # Remove oldest 25% of sessions
            remove_count = max(1, len(self.sessions) // 4)
            for session_id, _ in sessions_by_activity[:remove_count]:
                del self.sessions[session_id]
                print(f"🗑️ Removed session for memory: {session_id}")
    
    def clear_all_sessions(self):
        """Clear all sessions to free memory"""
        session_count = len(self.sessions)
        self.sessions.clear()
        print(f"🗑️ Cleared all {session_count} sessions")
    
    def get_memory_stats(self) -> Dict:
        """Get detailed memory statistics"""
        memory_usage = self.get_memory_usage_mb()
        session_count = len(self.sessions)
        total_messages = sum(len(session['messages']) for session in self.sessions.values())
        
        return {
            'memory_usage_mb': round(memory_usage, 2),
            'memory_limit_mb': self.max_memory_mb,
            'memory_usage_percent': round((memory_usage / self.max_memory_mb) * 100, 1),
            'active_sessions': session_count,
            'session_limit': self.max_sessions,
            'total_messages': total_messages,
            'max_messages_per_session': self.max_messages,
            'session_timeout_minutes': self.session_timeout.total_seconds() / 60
        }
    
    def get_session_stats(self) -> Dict:
        """Get statistics about active sessions"""
        active_sessions = len(self.sessions)
        total_messages = sum(len(session['messages']) for session in self.sessions.values())
        
        return {
            'active_sessions': active_sessions,
            'total_messages': total_messages,
            'sessions': {sid: len(session['messages']) for sid, session in self.sessions.items()}
        }

def create_contextual_prompt(user_message: str, laptop_data: List, conversation_context: str) -> str:
    """Create enhanced prompt with conversation context"""
    
    # Build laptop context
    laptop_context = ""
    if laptop_data:
        laptop_context = "\n".join([
            f"""**{laptop['brand']} {laptop['model']}** (€{laptop['specifications'].get('price', 'N/A')})
   • CPU: {laptop['specifications'].get('cpu', 'N/A')}
   • GPU: {laptop['specifications'].get('gpu', 'N/A')}
   • RAM: {laptop['specifications'].get('ram', 'N/A')}
   • Storage: {laptop['specifications'].get('storage', 'N/A')}
   • Screen: {laptop['specifications'].get('screen_size', 'N/A')}\" {laptop['specifications'].get('resolution', '')}"""
            for laptop in laptop_data[:3]
        ])
    
    context_section = f"\n{conversation_context}\n" if conversation_context else ""
    
    enhanced_prompt = f"""CURRENT MESSAGE: "{user_message}"
{context_section}
AVAILABLE LAPTOPS:
{laptop_context}

Based on our conversation history and the user's current message, provide a helpful, personalized response. Consider:
1. What we've discussed before
2. User's established preferences and needs
3. Any budget or brand preferences mentioned previously
4. Previous recommendations and their feedback

Keep the response conversational and build on our previous discussion. If this relates to earlier conversation, acknowledge that context."""

    return enhanced_prompt

# Example usage and testing
if __name__ == "__main__":
    # Test the conversation memory system
    memory = ConversationMemory()
    
    # Simulate a conversation
    session_id = "test_session"
    
    # Add some conversation history
    memory.add_message(session_id, "user", "I'm a student looking for a gaming laptop")
    memory.add_message(session_id, "assistant", "Great! For student gaming, I'd recommend laptops with RTX 4050 or 4060 GPUs for good performance without breaking the bank.")
    memory.add_message(session_id, "user", "What about budget? I can spend up to $1200")
    memory.add_message(session_id, "assistant", "Perfect! With $1200, you can get excellent gaming laptops like the ASUS TUF Gaming A15 or Acer Nitro 5.")
    
    # Get conversation history
    history = memory.get_conversation_history(session_id)
    print("Conversation History:")
    for msg in history:
        print(f"{msg['role']}: {msg['content'][:50]}...")
    
    # Get context summary
    context = memory.get_context_summary(session_id)
    print(f"\nContext Summary: {context}")
    
    # Get session stats
    stats = memory.get_session_stats()
    print(f"\nSession Stats: {stats}")
