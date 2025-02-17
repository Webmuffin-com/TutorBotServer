import os
import platform
import typing
import logging
from pydantic import SecretStr


current_working_path = os.getcwd()
local_assets_path = os.path.normpath(current_working_path)
if not os.path.exists(local_assets_path):
    logging.error(f"Classes path not found at {local_assets_path}")


port = int(os.getenv("PORT") or 3000)


cloud_mode_enabled = typing.cast(bool, os.getenv("CLOUD_MODE") == "true")
if not cloud_mode_enabled:
    logging.warning(
        "Cloud mode is not enabled because CLOUD_MODE environment variable not set, files for classes will be retrieved from the local filesystem"
    )

s3_bucket_endpoint = typing.cast(str, os.getenv("S3_BUCKET_ENDPOINT"))
if not s3_bucket_endpoint and cloud_mode_enabled:
    error_message = "Cloud mode is enabled but the required environment variable S3_BUCKET_ENDPOINT is not set."

    logging.error(error_message)
    raise ValueError(error_message)

s3_bucket_access_key = typing.cast(SecretStr, os.getenv("S3_BUCKET_ACCESS_KEY"))
if not s3_bucket_access_key and cloud_mode_enabled:
    error_message = "Cloud mode is enabled but the required environment variable S3_BUCKET_ACCESS_KEY is not set."

    logging.error(error_message)
    raise ValueError(error_message)

s3_bucket_access_secret = typing.cast(SecretStr, os.getenv("S3_BUCKET_ACCESS_SECRET"))
if not s3_bucket_access_secret and cloud_mode_enabled:
    error_message = "Cloud mode is enabled but the required environment variable S3_BUCKET_ACCESS_SECRET is not set."

    logging.error(error_message)
    raise ValueError(error_message)

s3_bucket_name = typing.cast(str, os.getenv("S3_BUCKET_NAME"))
if not s3_bucket_name and cloud_mode_enabled:
    error_message = "Cloud mode is enabled but the required environment variable S3_BUCKET_NAME is not set."

    logging.error(error_message)
    raise ValueError(error_message)

s3_bucket_path = typing.cast(str, os.getenv("S3_BUCKET_PATH"))
if not s3_bucket_path and cloud_mode_enabled:
    error_message = "Cloud mode is enabled but the required environment variable S3_BUCKET_PATH is not set."

    logging.error(error_message)
    raise ValueError(error_message)

pyppeteer_executable_path = typing.cast(str, os.getenv("PYPPETEER_EXECUTABLE_PATH"))
if not pyppeteer_executable_path:
    error_message = "Pyppeteer executable path not set, using default path"

    logging.warning(error_message)

mailgun_enabled = typing.cast(bool, os.getenv("MAILGUN_ENABLED") == "true")
if not mailgun_enabled:
    logging.warning(
        "Mailgun is not enabled because MAILGUN_ENABLED environment variable not set, users wont be able to send conversations to their email"
    )

mailgun_api_url = typing.cast(str, os.getenv("MAILGUN_API_URL"))
if not mailgun_api_url and mailgun_enabled:
    error_message = "Mailgun is enabled but the required environment variable MAILGUN_API_URL is not set."

    logging.error(error_message)
    raise ValueError(error_message)

mailgun_api_key = typing.cast(str, os.getenv("MAILGUN_API_KEY"))
if not mailgun_api_key and mailgun_enabled:
    error_message = "Mailgun is enabled but the required environment variable MAILGUN_API_KEY is not set."

    logging.error(error_message)
    raise ValueError(error_message)

mailgun_from_address = typing.cast(str, os.getenv("MAILGUN_FROM_ADDRESS"))
if not mailgun_from_address and mailgun_enabled:
    error_message = "Mailgun is enabled but the required environment variable MAILGUN_FROM_ADDRESS is not set."

    logging.error(error_message)
    raise ValueError(error_message)


model_provider = typing.cast(str, os.getenv("MODEL_PROVIDER"))
if not model_provider:
    logging.error("No model provider selected, using OPENAI as default")
    model_provider = "OPENAI"

model = typing.cast(str, os.getenv("MODEL"))
if not model:
    logging.error("No model selected, using atgpt-4o-latest as default")
    model = "chatgpt-4o-latest"
print(f"model: {model}")

api_key = typing.cast(SecretStr, os.getenv("API_KEY"))
if not api_key and model_provider != "GOOGLE":
    logging.error("Problems loading key because API_KEY environment variable not set")
    raise ValueError("API_KEY environment variable not set")

max_tokens = int(os.getenv("MAX_TOKENS") or 10000)

max_retries = int(os.getenv("MAX_RETRIES") or "2")

timeout = int(os.getenv("TIMEOUT") or "60")

temperature = float(os.getenv("TEMPERATURE") or "0.7")
print(f"temperature: {temperature}")

top_p = None
if os.getenv("TOP_P"):
    top_p = float(os.getenv("TOP_P"))  # type: ignore
print(f"top_p: {top_p}")

frequency_penalty = None
if os.getenv("FREQUENCY_PENALTY"):
    frequency_penalty = float(os.getenv("FREQUENCY_PENALTY"))  # type: ignore
    print(f"frequency_penalty: {frequency_penalty}")

presence_penalty = None
if os.getenv("PRESENCE_PENALTY"):
    presence_penalty = float(os.getenv("PRESENCE_PENALTY"))  # type: ignore
    print(f"presence_penalty: {presence_penalty}")

ibm_url = typing.cast(SecretStr, os.getenv("IBM_URL"))
if not ibm_url:
    ibm_url = "https://us-south.ml.cloud.ibm.com"

ibm_project_id = typing.cast(str, os.getenv("IBM_PROJECT_ID"))
if not ibm_project_id and model_provider == "IBM":
    logging.error(
        "Problems loading project_id because IBM_PROJECT_ID environment variable not set"
    )
    raise ValueError("IBM_PROJECT_ID environment variable not set")

system_encoding = (
    "utf-8" if platform.system() == "Windows" else None
)  # None uses the default system_encoding in Linux
