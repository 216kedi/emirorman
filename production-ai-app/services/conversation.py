"""Multi-turn conversation state and memory management."""
from dataclasses import dataclass, field


@dataclass
class Message:
    role: str
    content: str


@dataclass
class Conversation:
    conversation_id: str
    messages: list[Message] = field(default_factory=list)

    def append(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))


class ConversationStore:
    def get(self, conversation_id: str) -> Conversation:
        raise NotImplementedError

    def save(self, conversation: Conversation) -> None:
        raise NotImplementedError
