import logging
import re
from bs4 import BeautifulSoup
import DefaultParameters
from Utilities import setup_csv_logging
from SessionCache import SessionCache
import markdown2
import html

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
            from langchain_openai import ChatOpenAI
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
            from langchain_google_vertexai import ChatVertexAI
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
            from langchain_ibm import ChatWatsonx
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
            from langchain_anthropic import ChatAnthropic
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
            from langchain_ollama import ChatOllama
            return ChatOllama(model=model)
        case _:
            raise ValueError("Invalid model provider")

llm = initialize_llm()

def convert_llm_output_to_html(llm_output):
    """
    Convert mixed Markdown, including code blocks and inline HTML, to safe HTML.
    Was written by ChatGPT
    :param llm_output: str, text output from LLM including Markdown and HTML tags.
    :return: str, HTML formatted text.
    """
    # First, escape any raw HTML to avoid XSS attacks or unintended HTML rendering
    # The markdown2 library will convert HTML tags inside markdown back to HTML
    escaped_output = html.escape(llm_output)

    # Convert Markdown to HTML
    # Note: safe_mode and extras can be adjusted based on your needs
    html_output = markdown2.markdown(escaped_output, extras=["fenced-code-blocks", "safe-mode", "spoiler"])

    # Unescape only the intended HTML that is safe (You might need to customize this based on your context)
    # This step assumes you have specific tags you want to allow directly from your LLM and are handled separately
    final_html = html.unescape(html_output)

    return final_html

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
            f"PROMPT ({messages})", extra={"sessionKey": p_sessionKey}
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

        EscapedXMLTags = convert_llm_output_to_html (BotResponse)

        #logging.warning (f"RESPONSE start: {BotResponse}")
        #EscapedXMLTags = escape_xml_within_pre_tags(BotResponse)
        #logging.warning(f"RESPONSE CONVERTED: {EscapedXMLTags}")
        #BotResponseHtml = markdown2.markdown(EscapedXMLTags)
        #logging.warning (f"RESPONSE html :{BotResponseHtml}")

        logging.warning(
            f"RESPONSE FROM LLM: ({plain_text_response})\nSENT TO CLIENT ({EscapedXMLTags}).\n DETAILS ({llm_response})",
            extra={"sessionKey": p_sessionKey},
        )

     #   logging.warning(f"Response to Client: ({BotResponseHtml})")

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
