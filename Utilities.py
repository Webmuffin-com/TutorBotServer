from copy import deepcopy
from datetime import datetime
from fastapi import HTTPException
from pyppeteer import launch
import requests
import logging
import nh3
import os


from constants import (
    classes_directory,
    mailgun_api_url,
    mailgun_api_key,
    mailgun_from_address,
    encoding,
)

from SessionCache import SimpleCounterLLMConversation, session_manager

def get_scenario (class_directory: str, scenario_file_name: str, session_key: str):
    scenario_file_name = os.path.join(
        classes_directory, class_directory, scenario_file_name
    )
    scenario_file_name = os.path.normpath(scenario_file_name)

    if not os.path.exists(scenario_file_name):
        logging.warning(
            f"Failed to locate file {scenario_file_name}",
            extra={"sessionKey": session_key},
        )
        #raise HTTPException(status_code=404, detail="Scenario file not found")
        return ""

    # Load conundrum file
    with open(scenario_file_name, "r", encoding=encoding) as scenario_file:
        scenario_content = scenario_file.read()

        if len(scenario_content) == 0:
            logging.warning(
                f"scenario file {scenario_file_name} is empty.  Assuming in conundrum",
                extra={"sessionKey": session_key},
            )
        else:
            logging.warning(
                f"Loaded scenario file {scenario_file_name}",
                extra={"sessionKey": session_key},
        )

        return scenario_content


def get_conundrum(class_directory: str, conundrum_file_name: str, session_key: str):
    """
    Get the conundrum from a file.
    """

    conundrum_file_path = os.path.join(
        classes_directory, class_directory, "conundrums", conundrum_file_name
    )
    conundrum_file_path = os.path.normpath(conundrum_file_path)

    if not os.path.exists(conundrum_file_path):
        logging.warning(
            f"Failed to locate file {conundrum_file_path}",
            extra={"sessionKey": session_key},
        )
        raise HTTPException(status_code=404, detail="Conundrum file not found")

    # Load conundrum file
    with open(conundrum_file_path, "r", encoding=encoding) as conundrum_file:
        conundrum_content = conundrum_file.read()

        if len(conundrum_content) == 0:
            logging.warning(
                f"conundrum file {conundrum_file_path} is empty.",
                extra={"sessionKey": session_key},
            )
            raise HTTPException(status_code=404, detail="Conundrum file was empty")

        logging.warning(
            f"Loaded conundrum file {conundrum_file_path}",
            extra={"sessionKey": session_key},
        )

        return conundrum_content


def get_action_plan(class_directory: str, action_plan_file_path: str, session_key: str):
    """
    Get the action plan from a file.
    """

    action_plan_file_path = os.path.join(
        classes_directory, class_directory, "actionplans", action_plan_file_path
    )
    action_plan_file_path = os.path.normpath(action_plan_file_path)

    if not os.path.exists(action_plan_file_path):
        logging.warning(
            f"Failed to locate file {action_plan_file_path}",
            extra={"sessionKey": session_key},
        )
        raise HTTPException(status_code=404, detail="Action plan file not found")

    # Load action_plan file
    with open(action_plan_file_path, "r", encoding=encoding) as action_plan_file:
        action_plan_content = action_plan_file.read()

        if len(action_plan_content) == 0:
            logging.warning(
                f"Action plan file {action_plan_file_path} is empty.",
                extra={"sessionKey": session_key},
            )
            raise HTTPException(status_code=404, detail="Action plan file was empty")

        logging.warning(
            f"Loaded action plan file {action_plan_file_path}",
            extra={"sessionKey": session_key},
        )

        return action_plan_content


def convert_llm_output_to_html(llm_output):
#    logging.warning(
#         f"LLM OUTPUT =========================================\n{llm_output}"
#     )
    attributes = deepcopy(nh3.ALLOWED_ATTRIBUTES)
    attributes["div"] = set()

    attributes["div"].add("class")

    print(attributes)
    clean_html = nh3.clean(llm_output, attributes=attributes)

#     logging.warning(
#        f"CLEAN HTML SANITIZED BY NH3 =========================================\n{clean_html}"
#    )

    final_html = clean_html

#    logging.warning(
#         f"FINAL OUTPUT =========================================\n{final_html}"
#     )

    return final_html


def format_conversation(conversation):
    """
    Format a conversation for sending by email.
    """

    user_message = """<div class="user-message"><h2 class="message-text">User: </h2><p>{user_input}</p></div>"""
    assistant_message = """<div class="bot-message"><h2 class="message-text">Bot:</h2>{assistant_response}</div>"""

    messages = []

    for message in conversation:
        role = message[0]
        content = message[1]

        if role == "user":
            messages.append(user_message.format(user_input=content))
        elif role == "assistant":
            EscapedXMLTags = convert_llm_output_to_html(content)

            messages.append(assistant_message.format(assistant_response=EscapedXMLTags))

    return messages


async def generate_conversation_pdf(
    session_key: str | None,
    class_name: str | None,
    lesson: str | None,
    action_plan: str | None,
):

    if session_key is None:
        raise HTTPException(status_code=404, detail="Session Key not found")

    session_cache = session_manager.get_session(session_key)

    if session_cache is None:
        raise HTTPException(status_code=404, detail="Could not locate Session Key")

    conversation = (
        session_cache.m_simpleCounterLLMConversation.get_all_previous_messages()
    )

    formatted_conversation = format_conversation(conversation)

    print(f"Conversation: {formatted_conversation}")

    with open("static/style-pdf.css", "r", encoding=encoding) as style_file:

        style = style_file.read()

        html_content = """
        <html>
            <head>
                <style type="text/css">
                    {style}
                </style>
            </head>
            <body>
                <div class="response-output-pdf">
                    <div class="header">
                        <h1>TutorBot Learning Center</h1>
                        <p>This document contains the conversation you had with the TutorBot.</p>
                        <p>Class: {class_name}    Lesson: {lesson}    Mode: {action_plan}.</p>
                    </div>
                    {formatted_conversation}
                </div>
            </body>
        </html>""".format(
            style=style,
            class_name=class_name,
            lesson=lesson,
            action_plan=action_plan,
            formatted_conversation="".join(formatted_conversation),
        )

        print(f"HTML Content: {html_content}")

        # pdf = HTML(string=html_content).write_pdf()

        pdf = await create_pdf(html_content)

        return pdf


def send_email(
    to_address: str, subject: str, html: str, attachments: list[tuple[str, str]] = []
):
    try:
        files = files = [("attachment", attachment) for attachment in attachments]

        response = requests.post(
            mailgun_api_url,
            auth=("api", mailgun_api_key),
            files=files,
            data={
                "from": mailgun_from_address,
                "to": to_address,
                "subject": subject,
                "html": html,
            },
        )

        if response.status_code == 200:
            # success
            logging.info(
                f"Successfully sent an email to '{to_address}' via Mailgun API."
            )
        else:
            # error
            logging.error(f"Could not send the email, reason: {response.text}")
    except Exception as ex:
        logging.exception(f"Mailgun error: {ex}")


async def create_pdf(html):
    browser = await launch()
    page = await browser.newPage()

    await page.setContent(html)
    pdf = await page.pdf({"format": "Letter"})
    await browser.close()

    return pdf


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


def bytes_to_binary_string(bytes_data):
    return "".join(f"{byte:08b}" for byte in bytes_data)


if __name__ == "__main__":
    main()
