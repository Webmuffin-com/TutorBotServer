import os
import platform
import typing
import logging
from pydantic import SecretStr


# Define the path to the 'classes' directory within the current working directory
current_working_directory = os.getcwd()
classes_directory = os.path.normpath(os.path.join(current_working_directory, "classes"))

if not os.path.exists(classes_directory):
    logging.error(f"Classes directory not found at {classes_directory}")


model_provider = typing.cast(str, os.getenv("MODEL_PROVIDER"))
if not model_provider:
    logging.error("No model provider selected, using OPENAI as default")
    model_provider = "OPENAI"

model = typing.cast(str, os.getenv("MODEL"))
if not model:
    logging.error("No model selected, using atgpt-4o-latest as default")
    model = "chatgpt-4o-latest"

api_key = typing.cast(SecretStr, os.getenv("API_KEY"))
if not api_key and model_provider != "GOOGLE":
    logging.error("Problems loading key because API_KEY environment variable not set")
    raise ValueError("API_KEY environment variable not set")

max_tokens = typing.cast(int, os.getenv("MAX_TOKENS"))
if not max_tokens:
    max_tokens = 10000

max_retries = typing.cast(int, os.getenv("MAX_RETRIES"))
if not max_retries:
    max_retries = 2

timeout = typing.cast(int, os.getenv("TIMEOUT"))
if not timeout:
    timeout = 60

temperature = typing.cast(float, os.getenv("TEMPERATURE"))
if not temperature:
    temperature = 0.7

top_p = typing.cast(float, os.getenv("TOP_P"))
if not top_p:
    top_p = None

frequency_penalty = typing.cast(float, os.getenv("FREQUENCY_PENALTY"))
if not frequency_penalty:
    frequency_penalty = None

presence_penalty = typing.cast(float, os.getenv("PRESENCE_PENALTY"))
if not presence_penalty:
    presence_penalty = None

ibm_url = typing.cast(SecretStr, os.getenv("IBM_URL"))
if not ibm_url:
    ibm_url = "https://us-south.ml.cloud.ibm.com"

ibm_project_id = typing.cast(str, os.getenv("IBM_PROJECT_ID"))
if not ibm_project_id and model_provider == "IBM":
    logging.error(
        "Problems loading project_id because IBM_PROJECT_ID environment variable not set"
    )
    raise ValueError("IBM_PROJECT_ID environment variable not set")

mailgun_api_url = typing.cast(str, os.getenv("MAILGUN_API_URL"))
if not mailgun_api_url:
    logging.error(
        "Problems loading url because MAILGUN_API_URL environment variable not set"
    )
 #   raise ValueError("MAILGUN_API_URL environment variable not set")

mailgun_api_key = typing.cast(str, os.getenv("MAILGUN_API_KEY"))
if not mailgun_api_key:
    logging.error(
        "Problems loading key because MAILGUN_API_KEY environment variable not set"
    )
 #   raise ValueError("MAILGUN_API_KEY environment variable not set")

mailgun_from_address = typing.cast(str, os.getenv("MAILGUN_FROM_ADDRESS"))
if not mailgun_from_address:
    logging.error(
        "Problems loading from address because MAILGUN_FROM_ADDRESS environment variable not set"
    )
 #   raise ValueError("MAILGUN_FROM_ADDRESS environment variable not set")

encoding = (
    "utf-8" if platform.system() == "Windows" else None
)  # None uses the default encoding in Linux
