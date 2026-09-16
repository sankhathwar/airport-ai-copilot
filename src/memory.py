"""
Short-term conversation memory for the Airport Operations AI Copilot.

Stores recent user questions and assistant responses so that
follow-up questions can be understood in context.
"""


class ConversationMemory:

    def __init__(self, max_turns: int = 5):
        """
        max_turns = maximum number of conversation turns to retain.
        """

        self.history = []
        self.max_turns = max_turns

    def add_turn(self, user_message: str, assistant_message: str):
        """
        Store one user-assistant interaction.
        """

        self.history.append(
            {
                "user": user_message,
                "assistant": assistant_message
            }
        )

        # Keep only the most recent turns
        self.history = self.history[-self.max_turns:]

    def get_history(self):
        """
        Return conversation history.
        """

        return self.history

    def format_history(self):
        """
        Convert conversation history into text
        that can be passed to the LLM.
        """

        if not self.history:
            return "No previous conversation."

        formatted_history = []

        for turn in self.history:

            formatted_history.append(
                f"User: {turn['user']}\n"
                f"Assistant: {turn['assistant']}"
            )

        return "\n\n".join(formatted_history)

    def clear(self):
        """
        Clear conversation history.
        """

        self.history = []