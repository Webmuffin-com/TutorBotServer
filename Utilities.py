import logging
import os
import json
from datetime import datetime


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


global_conversation = SimpleCounterLLMConversation()


def generate_log_filename(prefix="logs/TutorBot_Log", extension="csv"):
    """
    Generate a unique file name with a timestamp for the log file.

    :param prefix: The prefix for the file name. Default is 'InventoriumLog'.
    :param extension: The file extension. Default is 'csv'.
    :return: A string representing the file name.
    """
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    log_dir = os.path.join(os.getcwd(), os.path.dirname(prefix))
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return os.path.join(log_dir, f"{os.path.basename(prefix)}_{timestamp}.{extension}")


"""
    we will prefix logs with the following tags
    TTS
    MIC
    LLM
    STATE
    LOOP   for general processing associated with looping function
"""


class CSVLogFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()

    def format(self, record):

        print("--------------")
        print(record)
        print("--------------")
        # Format time to separate date and time components
        formatted_date = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d")
        formatted_time = datetime.fromtimestamp(record.created).strftime("%H-%M-%S.%f")[
            :12
        ]  # Slices the string to keep only milliseconds
        message = record.getMessage().replace('"', '""')  # Escape quotes in the message
        # Use getattr to safely access sessionKey
        session_key = getattr(record, "sessionKey", "None")

        formatted_record = f'"{formatted_date}","{record.filename}","{record.funcName}","{record.levelname}","{record.thread}","{formatted_time}","{message}", "{session_key}"'
        return formatted_record


blogging_setup = False


def setup_csv_logging():
    global blogging_setup
    if blogging_setup:
        return
    blogging_setup = True

    log_filename = generate_log_filename()
    file_handler = logging.FileHandler(log_filename, mode="a")
    csv_formatter = CSVLogFormatter()
    file_handler.setFormatter(csv_formatter)

    # Check if the log file is new or empty, and if so, write the header
    if not os.path.exists(log_filename) or os.stat(log_filename).st_size == 0:
        with open(log_filename, "w") as f:
            f.write(
                '"Date","File Name","Func Name","Trace Level","Thread ID","Time","Message", "Session Key"\n'
            )

    # Create a StreamHandler for output to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Set the desired level for console output

    logger = logging.getLogger()
    # this code sets the trace level.  For now, all gets traced... we only want
    logger.setLevel(logging.WARNING)  # Capture all messages from DEBUG level upwards
    logger.handlers.clear()  # Clear existing handlers
    logger.addHandler(file_handler)  # Add the CSV file handler
    logger.addHandler(console_handler)


def format_messages(messages):
    # Start building the formatted message string
    formatted_message = ""

    # Iterate through each message in the list
    for message in messages:
        # Append each message as a dictionary to the formatted string
        formatted_message += f"{message}, \n\n"

    # Properly strip the last comma and newline for cleaner output
    if formatted_message.endswith(", \n\n"):
        formatted_message = formatted_message[
            :-3
        ]  # Remove the last three characters: comma, newline, newline

    # Return the fully formatted message
    return formatted_message


# Setup CSV logging immediately


def main():
    setup_csv_logging()
    # Example usage of different logging levels
    logging.debug("This is a debug message.")
    logging.info(
        "This is an info message with, commas and 'quotes' to demonstrate formatting."
    )
    logging.warning("This is a warning message.")
    logging.error("This is an error message.")
    logging.critical("This is a critical message.")

    # Test code for conversational history
    convo = SimpleCounterLLMConversation()
    convo.add_message("user", "What's the weather like today?", "Child")
    convo.add_message("assistant", "It's sunny and 75 degrees outside.", "FirstPassLLM")
    print(convo)  # Printing the conversation with enhanced details
    history = convo.get_history()
    print("History:", history)

    convo.clear()
    print("After clearing:", convo)


if __name__ == "__main__":
    main()
