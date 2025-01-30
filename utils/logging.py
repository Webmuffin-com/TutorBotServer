from datetime import datetime
import io
import logging
import os

from SessionCache import SimpleCounterLLMConversation
from constants import cloud_mode_enabled
from utils.filesystem import open_text_file, save_file

csv_headers = "Date,File Name,Func Name,Trace Level,Thread ID,Time,Message,Session Key,Access Key\n"


def generate_cloud_log_filename(prefix="TutorBot-Log", extension="csv"):

    now = datetime.now()

    timestamp = now.strftime("%Y-%m-%d")

    return f"{prefix}_{timestamp}.{extension}"


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


class CSVLogFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()

    def format(self, record):
        """print("--------------")
        print(record)
        print("--------------")"""
        # Format time to separate date and time components
        formatted_date = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d")
        formatted_time = datetime.fromtimestamp(record.created).strftime("%H-%M-%S.%f")[
            :12
        ]  # Slices the string to keep only milliseconds
        message = record.getMessage().replace('"', '""')  # Escape quotes in the message
        # Use getattr to safely access sessionKey
        session_key = getattr(record, "sessionKey", "None")
        access_key = getattr(record, "accessKey", "None")

        formatted_record = f'"{formatted_date}","{record.filename}","{record.funcName}","{record.levelname}","{record.thread}","{formatted_time}","{message}", "{session_key}", "{access_key}"'
        return formatted_record


string_handler = None


def drain_logs_to_s3():
    global string_handler

    if string_handler:
        log_filename = generate_cloud_log_filename()
        log_path = f"logs/{log_filename}"

        new_log = string_handler.getvalue()

        if new_log and len(new_log) > 1:

            existing_log_content = open_text_file(log_path)

            final_log = ""

            if not existing_log_content or len(existing_log_content) == 0:

                final_log += f"{csv_headers}"

            final_log += (
                f"{existing_log_content if existing_log_content else ""}{new_log}"
            )

            save_file(log_path, final_log.encode("utf-8"))

            string_handler.truncate(0)
            string_handler.seek(0)


def setup_csv_logging():
    global string_handler
    log_filename = generate_log_filename()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    logger = logging.getLogger()
    logger.handlers.clear()

    csv_formatter = CSVLogFormatter()

    external_handler = None

    if cloud_mode_enabled:

        string_handler = io.StringIO()
        external_handler = logging.StreamHandler(string_handler)

    else:

        external_handler = logging.FileHandler(log_filename, mode="a")

        # Check if the log file is new or empty, and if so, write the header
        if not os.path.exists(log_filename) or os.stat(log_filename).st_size == 0:
            with open(log_filename, "w") as f:
                f.write(csv_headers)

    external_handler.setFormatter(csv_formatter)

    logger.setLevel(logging.WARNING)

    logger.addHandler(external_handler)
    logger.addHandler(console_handler)


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


def bytes_to_binary_string(bytes_data):
    return "".join(f"{byte:08b}" for byte in bytes_data)


if __name__ == "__main__":
    main()
