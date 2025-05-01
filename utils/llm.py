import logging
import markdown
import nh3
from copy import deepcopy

from utils.filesystem import open_text_file


def validate_access_key(access_key: str, session_key: str):

    available_keys = open_text_file("config/access_keys.txt")

    if available_keys is None:
        logging.warning(
            "Access key file not found",
            extra={"sessionKey": session_key},
        )
        return False

    if access_key not in available_keys.splitlines():
        logging.warning(
            "Invalid access key",
            extra={"sessionKey": session_key},
        )
        return False

    return True


def get_llm_file(class_directory: str, type: str, file_name: str, session_key: str):

    content = open_text_file(f"classes/{class_directory}/{type}/{file_name}")

    if content is None:
        logging.warning(
            f"Failed to locate file {file_name}",
            extra={"sessionKey": session_key},
        )
        return ""

    if len(content) == 0:
        logging.warning(
            f"{type} file {file_name} is empty.",
            extra={"sessionKey": session_key},
        )
    else:
        logging.warning(
            f"Loaded {type} file {file_name}",
            extra={"sessionKey": session_key},
        )

    return content


def format_conversation(conversation):
    user_message = """<div class="user-message"><h2 class="message-text">User: </h2><p>{user_input}</p></div>"""
    assistant_message = """<div class="bot-message"><h2 class="message-text">Bot:</h2>{assistant_response}</div>"""

    messages = []

    for message in conversation:
        role = message[0]
        content = message[1]

        if role == "user":
            messages.append(user_message.format(user_input=content))
        elif role == "assistant":
            html = markdown.markdown(content)

            attributes = deepcopy(nh3.ALLOWED_ATTRIBUTES)
            attributes["div"] = set()
            attributes["div"].add("class")

            clean_html = nh3.clean(html, attributes=attributes)
            messages.append(assistant_message.format(assistant_response=clean_html))

    return messages
