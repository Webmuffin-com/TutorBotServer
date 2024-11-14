import os
import typing
import logging
from pydantic import SecretStr


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
