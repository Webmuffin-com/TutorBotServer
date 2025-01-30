import requests

import logging

from constants import (
    mailgun_api_url,
    mailgun_api_key,
    mailgun_from_address,
)


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
