import requests

from constants import (
    mailgun_api_url,
    mailgun_api_key,
    mailgun_from_address,
)
from utils.logger import get_logger

logger = get_logger()


def send_email(
    to_address: str,
    subject: str,
    html: str,
    attachments: list[tuple[str, str]] = [],
    session_key: str = "",
    class_selection: str = "",
    lesson: str = "",
    action_plan: str = "",
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
            logger.info(
                "Successfully sent email via Mailgun API",
                extra={
                    "to_address": to_address,
                    "session_key": session_key,
                    "class_selection": class_selection,
                    "lesson": lesson,
                    "action_plan": action_plan,
                },
            )
        else:
            # error
            logger.error(
                "Could not send email",
                extra={
                    "reason": response.text,
                    "status_code": str(response.status_code),
                    "session_key": session_key,
                    "class_selection": class_selection,
                    "lesson": lesson,
                    "action_plan": action_plan,
                },
            )
    except Exception as ex:
        logger.exception(
            "Mailgun error",
            extra={
                "error": str(ex),
                "session_key": session_key,
                "class_selection": class_selection,
                "lesson": lesson,
                "action_plan": action_plan,
            },
        )
