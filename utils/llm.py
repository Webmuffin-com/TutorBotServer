import markdown
import nh3
from copy import deepcopy

from utils.filesystem import open_text_file
from utils.logger import get_logger

logger = get_logger()


def validate_access_key(access_key: str, session_key: str):

    available_keys = open_text_file("config/access_keys.txt")

    if available_keys is None:
        logger.error(
            "Access key file not found",
            extra={"session_key": session_key},
        )
        return False

    if access_key not in available_keys.splitlines():
        logger.warning(
            "Invalid access key",
            extra={"session_key": session_key},
        )
        return False

    return True


def get_llm_file(class_directory: str, type: str, file_name: str, session_key: str):

    if (type):
        content = open_text_file(f"classes/{class_directory}/{type}/{file_name}")
    else:
        content = open_text_file(f"classes/{class_directory}/{file_name}")

    if content is None:
        logger.warning(
            "Failed to locate file",
            extra={"session_key": session_key, "file_name": file_name},
        )
        return ""

    if len(content) == 0:
        logger.warning(
            "File is empty",
            extra={"session_key": session_key, "type": type, "file_name": file_name},
        )
    else:
        logger.warning(
            "Loaded file",
            extra={"session_key": session_key, "type": type, "file_name": file_name},
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
