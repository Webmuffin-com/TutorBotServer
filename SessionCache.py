from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple, Optional, Iterator, TypedDict


# Type definitions for messages
class Message(TypedDict):
    id: int
    timestamp: str
    role: str  # 'user' or 'assistant'
    content: str
    conv_content: Optional[str]


class SessionData(TypedDict, total=False):
    initial: str
    # Add other session data fields as they are discovered


class MessageSummary(TypedDict):
    id: int
    timestamp: str
    role: str
    content_preview: str
    has_conv_content: bool


class ConversationSummaryDict(TypedDict):
    total_messages: int
    user_messages_count: int
    assistant_messages_count: int
    conversation_start: Optional[str]
    conversation_latest: Optional[str]
    messages: List[MessageSummary]


ConversationHistory = List[Message]
RoleContentTuple = Tuple[str, str]


class SessionCache:
    def __init__(self, session_key: str, data: SessionData) -> None:
        self.m_session_key: str = session_key
        self.m_data: SessionData = data
        self.m_last_update: datetime = datetime.utcnow()
        self.m_simpleCounterLLMConversation: "SimpleCounterLLMConversation" = (
            SimpleCounterLLMConversation()
        )

    def update(self, data: SessionData) -> None:
        self.m_data.update(data)
        self.m_last_update = datetime.utcnow()


class SessionCacheManager:
    def __init__(self, idle_timeout: timedelta = timedelta(hours=4)) -> None:
        self.sessions: Dict[str, SessionCache] = {}
        self.idle_timeout: timedelta = idle_timeout

    def add_session(self, session_key: str, data: SessionData) -> None:
        session = SessionCache(session_key, data)
        self.sessions[session_key] = session

    def get_session(self, session_key: str) -> SessionCache:
        session = self.sessions.get(session_key)
        if session is None:
            raise KeyError(f"Session with key {session_key} not found")
        return session

    def remove_session(self, session_key: str) -> None:
        if session_key in self.sessions:
            del self.sessions[session_key]

    def cleanup_idle_sessions(self) -> None:
        now = datetime.utcnow()
        idle_sessions: List[str] = [
            key
            for key, session in self.sessions.items()
            if now - session.m_last_update > self.idle_timeout
        ]
        for session_key in idle_sessions:
            self.remove_session(session_key)


session_manager: SessionCacheManager = SessionCacheManager()


class SimpleCounterLLMConversation:
    def __init__(self) -> None:
        self.conversation: ConversationHistory = []
        self.message_id_counter: int = 1  # Initialize message ID counter

    def add_message(self, role: str, content: str, conv_content: Optional[str]) -> None:
        """
        Adds a message to the conversation with a timestamp and a simple incremental ID.
        :param role: The role of the message sender ('user' or 'assistant').
        :param content: The content of the message.
        :param conv_content: if not null, then add to download for user facing conversation
        """
        message: Message = {
            "id": self.message_id_counter,
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "conv_content": conv_content,
        }
        self.conversation.append(message)
        self.message_id_counter += 1  # Increment the counter for the next message
        # Reset counter if it's too high; adjust this limit as needed
        if self.message_id_counter > 1e9:
            self.message_id_counter = 1

    def clear(self) -> None:
        """
        Clears the conversation and resets the message ID counter.
        """
        self.conversation.clear()
        self.message_id_counter = 1  # Reset counter

    def to_string(self) -> str:
        """
        Converts the conversation to a string in a format suitable for the LLM.
        """
        return json.dumps({"messages": self.conversation})

    def to_conversation(self) -> str:
        """
        Outputs the conversation in a simplified format, focusing on 'role' and 'content'.
        """
        return json.dumps(
            [
                {"role": msg["role"], "content": msg["content"]}
                for msg in self.conversation
            ]
        )

    def get_history(self) -> ConversationHistory:
        """
        Retrieves the conversation history.
        :return: A copy of the conversation history.
        """
        return list(self.conversation)

    def __str__(self) -> str:
        """
        String representation of the conversation history.
        """
        return self.to_string()

    def __repr__(self) -> str:
        """
        Provides a detailed representation of the conversation for debugging.
        """
        conversation_preview = ", ".join(
            f"{msg['role']}: {msg['content'][:30]}..." for msg in self.conversation[:5]
        )
        return (
            f"<SimpleCounterLLMConversation (Last 5 Messages): {conversation_preview}>"
        )

    def get_all_previous_messages(self) -> List[RoleContentTuple]:
        """
        Retrieves all messages from the conversation.
        Returns:
            A list of tuples, each containing the role and content of each message in the conversation.
        """
        return [(message["role"], message["content"]) for message in self.conversation]

    def get_user_conversation_messages(self) -> List[Tuple[str, Optional[str]]]:
        """
        Retrieves all messages from the conversation where conv_content is not None.
        Returns:
            A list of tuples, each containing the role and conv_content of each message.
        """
        return [
            (message["role"], message["conv_content"])
            for message in self.conversation
            if message.get("conv_content") is not None
        ]

    def get_total_conv_content_bytes(self) -> int:
        """
        Calculates the total byte size of all conv_content fields in the conversation
        where conv_content is not None.

        Returns:
            The total number of bytes used by conv_content strings.
        """
        return sum(
            len(message["conv_content"].encode("utf-8"))
            for message in self.conversation
            if message.get("conv_content") is not None
            and message["conv_content"] is not None
        )

    def __iter__(self) -> Iterator[Message]:
        """
        Returns an iterator over a snapshot of the conversation list.
        """
        return iter(self.conversation.copy())

    def get_user_questions_as_string(self) -> str:
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

    def get_last_assistance_response(self) -> Optional[str]:
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

    def prune_oldest_pair(self) -> None:
        """
        Removes the oldest pair of user and assistant messages from the conversation.
        This helps conserve space while keeping the conversation balanced.
        """
        user_index: Optional[int] = None
        assistant_index: Optional[int] = None

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

    def get_serializable_conversation(self) -> List[Message]:
        """
        Returns the entire conversation in a JSON-friendly format.

        This function returns all conversation data as JSON-serializable dictionaries,
        avoiding any tuples or classes in favor of plain Python data structures.

        Returns:
            A dictionary containing the complete conversation with all fields.
        """
        return [
            {
                "id": msg["id"],
                "timestamp": msg["timestamp"],
                "role": msg["role"],
                "content": msg["content"],
                "conv_content": msg["conv_content"],
            }
            for msg in self.conversation
        ]

    def get_serializable_conversation_summary(self) -> ConversationSummaryDict:
        """
        Returns a summary of the conversation in JSON-serializable format.

        This includes metadata about the conversation and simplified message data.

        Returns:
            A dictionary with conversation summary information.
        """
        user_messages = [msg for msg in self.conversation if msg["role"] == "user"]
        assistant_messages = [
            msg for msg in self.conversation if msg["role"] == "assistant"
        ]

        return {
            "total_messages": len(self.conversation),
            "user_messages_count": len(user_messages),
            "assistant_messages_count": len(assistant_messages),
            "conversation_start": (
                self.conversation[0]["timestamp"] if self.conversation else None
            ),
            "conversation_latest": (
                self.conversation[-1]["timestamp"] if self.conversation else None
            ),
            "messages": [
                {
                    "id": msg["id"],
                    "timestamp": msg["timestamp"],
                    "role": msg["role"],
                    "content_preview": (
                        msg["content"][:100] + "..."
                        if len(msg["content"]) > 100
                        else msg["content"]
                    ),
                    "has_conv_content": msg["conv_content"] is not None,
                }
                for msg in self.conversation
            ],
        }


global_conversation: SimpleCounterLLMConversation = SimpleCounterLLMConversation()
