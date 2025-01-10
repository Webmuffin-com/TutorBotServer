from datetime import datetime, timedelta
import json


class SessionCache:
    def __init__(self, session_key: str, data: dict):
        self.m_session_key = session_key
        self.m_data = data
        self.m_last_update = datetime.utcnow()
        self.m_simpleCounterLLMConversation = SimpleCounterLLMConversation()

    def update(self, data: dict):
        self.m_data.update(data)
        self.m_last_update = datetime.utcnow()


class SessionCacheManager:
    def __init__(self, idle_timeout: timedelta = timedelta(hours=4)):
        self.sessions = {}
        self.idle_timeout = idle_timeout

    def add_session(self, session_key: str, data: dict):
        session = SessionCache(session_key, data)
        self.sessions[session_key] = session

    def get_session(self, session_key: str) -> SessionCache:
        session = self.sessions.get(session_key)
        if session is None:
            raise KeyError(f"Session with key {session_key} not found")
        return session

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


session_manager = SessionCacheManager()


class SimpleCounterLLMConversation:
    def __init__(self):
        self.conversation = []
        self.message_id_counter = 1  # Initialize message ID counter

    def add_message(self, role, content, participant_id=None):
        """
        Adds a message to the conversation with a timestamp and a simple incremental ID.
        :param role: The role of the message sender ('user' or 'assistant').
        :param content: The content of the message.
        :param participant_id: An optional identifier for the participant.
        """
        message = {
            "id": self.message_id_counter,
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "participant_id": participant_id or "default",
        }
        self.conversation.append(message)
        self.message_id_counter += 1  # Increment the counter for the next message
        # Reset counter if it's too high; adjust this limit as needed
        if self.message_id_counter > 1e9:
            self.message_id_counter = 1

    def clear(self):
        """
        Clears the conversation and resets the message ID counter.
        """
        self.conversation.clear()
        self.message_id_counter = 1  # Reset counter

    def to_string(self):
        """
        Converts the conversation to a string in a format suitable for the LLM.
        """
        return json.dumps({"messages": self.conversation}, indent=2)

    def to_conversation(self):
        """
        Outputs the conversation in a simplified format, focusing on 'role' and 'content'.
        """
        return json.dumps(
            [
                {"role": msg["role"], "content": msg["content"]}
                for msg in self.conversation
            ],
            indent=2,
        )

    def get_history(self):
        """
        Retrieves the conversation history.
        :return: A copy of the conversation history.
        """
        return list(self.conversation)

    def __str__(self):
        """
        String representation of the conversation history.
        """
        return self.to_string()

    def __repr__(self):
        """
        Provides a detailed representation of the conversation for debugging.
        """
        conversation_preview = ", ".join(
            f"{msg['role']}: {msg['content'][:30]}..." for msg in self.conversation[:5]
        )
        return (
            f"<SimpleCounterLLMConversation (Last 5 Messages): {conversation_preview}>"
        )

    def get_all_previous_messages(self):
        """
        Retrieves all messages from the conversation.
        Returns:
            A list of dictionaries, each containing the role and content of each message in the conversation.
        """
        return [(message["role"], message["content"]) for message in self.conversation]

    def __iter__(self):
        """
        Returns an iterator over a snapshot of the conversation list.
        """
        return iter(self.conversation.copy())

    def get_user_questions_as_string(self):
        """
        Retrieves all user questions and concatenates them into a single string.
        Returns:
            A string containing all user questions separated by a space.
        """
        # Filter for messages where the role is 'user' and concatenate the content
        user_questions = " ".join(
            msg["content"] for msg in self.conversation if msg["role"] == "user"
        )
        return user_questions

    def get_last_assistance_response(self):
        """
        Returns the content of the last message in the conversation where the role is 'assistant'.
        Returns None if there are no assistant messages in the conversation.
        """
        # Iterate backwards through the conversation to find the last 'assistant' message and return only its content
        for message in reversed(self.conversation):
            if message["role"] == "assistant":
                return message[
                    "content"
                ]  # Return only the content of the last assistant message
        return None  # Return None if no 'assistant' messages are found

    def prune_oldest_pair(self):
        """
        Removes the oldest pair of user and assistant messages from the conversation.
        This helps conserve space while keeping the conversation balanced.
        """
        user_index, assistant_index = None, None

        # Find the indices of the oldest 'user' and 'assistant' messages
        for i, message in enumerate(self.conversation):
            if message["role"] == "user" and user_index is None:
                user_index = i
            elif message["role"] == "assistant" and assistant_index is None:
                assistant_index = i
            # Stop the loop if both indices are found
            if user_index is not None and assistant_index is not None:
                break

        # Remove the oldest pair if both exist
        if user_index is not None and assistant_index is not None:
            # Remove the assistant message first if it comes before the user in the list
            if assistant_index < user_index:
                self.conversation.pop(assistant_index)
                self.conversation.pop(user_index - 1)  # Adjust for shifted index
            else:
                self.conversation.pop(user_index)
                self.conversation.pop(assistant_index - 1)  # Adjust for shifted index


global_conversation = SimpleCounterLLMConversation()
