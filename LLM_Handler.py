import logging
import re

from langchain_anthropic import ChatAnthropic
from langchain_google_vertexai import ChatVertexAI
from langchain_openai import ChatOpenAI
from langchain_ibm import ChatWatsonx
from langchain_ollama import ChatOllama

from bs4 import BeautifulSoup

import DefaultParameters
from Utilities import setup_csv_logging
from SessionCache import SessionCache

from constants import (
    model_provider,
    model,
    api_key,
    max_tokens,
    temperature,
    top_p,
    frequency_penalty,
    presence_penalty,
    max_retries,
    timeout,
    ibm_project_id,
    ibm_url,
)

LastResponse = ""


def initialize_llm():

    match model_provider:
        case "OPENAI":
            return ChatOpenAI(
                model=model,
                max_tokens=max_tokens,
                max_retries=max_retries,
                timeout=timeout,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                api_key=api_key,
            )
        case "GOOGLE":
            return ChatVertexAI(
                model_name=model,
                max_tokens=max_tokens,
                max_retries=max_retries,
                timeout=timeout,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )
        case "IBM":
            return ChatWatsonx(
                model_id=model,
                max_tokens=max_tokens,
                max_retries=max_retries,
                timeout=timeout,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                apikey=api_key,
                project_id=ibm_project_id,
                url=ibm_url,
            )
        case "ANTHROPIC":
            return ChatAnthropic(
                model_name=model,
                max_tokens=max_tokens,
                max_retries=max_retries,
                timeout=timeout,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                api_key=api_key,
                stop=None,
            )
        case "OLLAMA":
            return ChatOllama(model=model)
        case _:
            raise ValueError("Invalid model provider")


llm = initialize_llm()


def escape_xml_within_pre_tags(text):
    # This function finds all <pre>...</pre> blocks and escapes special XML characters within them
    def escape_xml(match):
        # Extract the content inside <pre>...</pre>
        xml_content = match.group(1)
        # Escape special characters in the XML content
        escaped_content = (
            xml_content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        # Return the reconstructed <pre>...</pre> with escaped content
        return "<pre>" + escaped_content + "</pre>"

    # Use regex to apply the escaping function to all content within <pre>...</pre>
    return re.sub(r"<pre>(.*?)</pre>", escape_xml, text, flags=re.DOTALL)


async def invoke_llm(p_SessionCache: SessionCache, p_Request: str, p_sessionKey: str):
    global LastResponse
    try:
        scenerio = DefaultParameters.get_default_scenario()
        conundrum = p_SessionCache.get_conundrum()

        if p_SessionCache.get_action_plan() != "":
            actionPlan = p_SessionCache.get_action_plan()
        else:
            actionPlan = DefaultParameters.get_default_action_plan()

        logging.warning(
            f"LLM User's Request ({p_Request})", extra={"sessionKey": p_sessionKey}
        )

        messages = [
            ("system", scenerio),
            ("system", conundrum),
            *p_SessionCache.m_simpleCounterLLMConversation.get_all_previous_messages(),
            ("user", p_Request),
            ("system", actionPlan),
        ]

        # Test the messages structure before formatting
        logging.warning(
            f"Messages structure: {messages}", extra={"sessionKey": p_sessionKey}
        )

        if llm is None:
            raise ValueError("LLM not initialized")

        llm_response = llm.invoke(messages)

        p_SessionCache.m_simpleCounterLLMConversation.add_message(
            "user", p_Request, "LLM"
        )  # now we add the request.

        BotResponse = str(llm_response.content)

        # Log token usage metrics
        if llm_response.response_metadata:
            usage = llm_response.response_metadata.get("token_usage")

            if usage:
                logging.info(
                    f"Tokens used - Prompt tokens: {usage.get('prompt_tokens')}, Completion tokens: \
            {usage.get('completion_tokens')}, Total tokens: {usage.get('total_tokens')}",
                    extra={"sessionKey": p_sessionKey},
                )

        # Strip HTML tags from BotResponse to put in conversation as it messes up the LLM to feed HTML into it.
        soup = BeautifulSoup(BotResponse, "html.parser")
        plain_text_response = soup.get_text().replace("\n", " ").strip()

        EscapedXMLTags = escape_xml_within_pre_tags(BotResponse)

        logging.warning(
            f"Response from LLM: ({plain_text_response})\n {BotResponse}. Details are ({llm_response})",
            extra={"sessionKey": p_sessionKey},
        )

        p_SessionCache.m_simpleCounterLLMConversation.add_message(
            "assistant", BotResponse, "LLM"
        )  # now we add the request.

        return EscapedXMLTags

    except Exception as e:
        # Handle general exceptions
        logging.error(
            f"An exception occurred while calling LLM with first message: {e}",
            exc_info=True,
            extra={"sessionKey": p_sessionKey},
        )
        return f"An error ({e}) occurred processing your request, Please try again"


if __name__ == "__main__":
    setup_csv_logging()
