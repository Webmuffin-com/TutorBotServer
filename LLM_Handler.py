import logging
import re
from bs4 import BeautifulSoup
import DefaultParameters
from Utilities import setup_csv_logging
from SessionCache import SessionCache
from DefaultParameters import get_result_formatting
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
             #   max_tokens=max_tokens,
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
            #    max_tokens=max_tokens,
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
            #    max_tokens=max_tokens,
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
            #    max_tokens=max_tokens,
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
    logging.warning(f"LLM OUTPUT =========================================\n{llm_output}")
    # First, escape any raw HTML to avoid XSS attacks or unintended HTML rendering
    # The markdown2 library will convert HTML tags inside markdown back to HTML
    escaped_output = html.escape(llm_output)

    logging.warning(f"ESCAPED OUTPUT =========================================\n{escaped_output}")

    # Convert Markdown to HTML
    # Note: safe_mode and extras can be adjusted based on your needs
    html_output = markdown2.markdown(escaped_output, extras=["fenced-code-blocks", "safe-mode", "spoiler"])
    #html_output = escaped_output
    logging.warning(f"HTML MARKDOWN OUTPUT =========================================\n{html_output}")

    # Unescape only the intended HTML that is safe (You might need to customize this based on your context)
    # This step assumes you have specific tags you want to allow directly from your LLM and are handled separately
    final_html = html.unescape(html_output)
    #final_html = html_output

    logging.warning(f"FINAL OUTPUT =========================================\n{final_html}")

    return final_html


def convert_llm_output_to_html_old(llm_output):
    """
    Convert mixed Markdown, including code blocks and inline HTML, to safe HTML.
    Was written by ChatGPT
    :param llm_output: str, text output from LLM including Markdown and HTML tags.
    :return: str, HTML formatted text.
    """
    logging.warning (f"BEFORE {llm_output}")
    # First, escape any raw HTML to avoid XSS attacks or unintended HTML rendering
    # The markdown2 library will convert HTML tags inside markdown back to HTML
    escaped_output = html.escape(llm_output)

    logging.warning(f"ESCAPED OUTPUT....{escaped_output}")

    # Convert Markdown to HTML
    # Note: safe_mode and extras can be adjusted based on your needs
   #html_output = markdown2.markdown(escaped_output, extras=["fenced-code-blocks", "safe-mode", "spoiler"])
    html_output = escaped_output
    #logging.warning(f"HTML OUTPUT....{html_output}")

    # Unescape only the intended HTML that is safe (You might need to customize this based on your context)
    # This step assumes you have specific tags you want to allow directly from your LLM and are handled separately
  # final_html = html.unescape(html_output)
    final_html = html_output

 #   logging.warning(f"FINAL OUTPUT....{final_html}")

    return final_html

async def invoke_llm(p_SessionCache: SessionCache, p_Request: str, p_sessionKey: str):
    global LastResponse
    try:

        # we no longer need to define scenario here.  If empty, assume in conundrum
        scenerio   = ""  #DefaultParameters.get_default_scenario()
        conundrum  = p_SessionCache.get_conundrum()

        action_plan = p_SessionCache.get_action_plan()

        if action_plan is None:
            action_plan = ""  # Default to an empty string if no action plan is found

        actionPlan = action_plan + get_result_formatting()

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

        current_token_usage = 0

        # Log token usage metrics
        if llm_response.response_metadata:
            token_usage = llm_response.response_metadata.get("token_usage")

            if token_usage:
                current_token_usage = token_usage.get('prompt_tokens')
                logging.info(
                    f"Tokens used - Prompt tokens: {token_usage.get('prompt_tokens')}, Completion tokens: \
            {token_usage.get('completion_tokens')}, Total tokens: {token_usage.get('total_tokens')}",
                    extra={"sessionKey": p_sessionKey},
                )

        # Strip HTML tags from BotResponse to put in conversation as it messes up the LLM to feed HTML into it.
        soup = BeautifulSoup(BotResponse, "html.parser")
        plain_text_response = soup.get_text().replace("\n", " ").strip()

        EscapedXMLTags = convert_llm_output_to_html (BotResponse)

        logging.warning(
            f"RESPONSE FROM LLM Cleaned: ({plain_text_response})\n\n\nSENT TO CLIENT ({EscapedXMLTags}).\n\n\nRAW_LLM_OUTPUT ({BotResponse}).\n\n\nDETAILS ({llm_response})",
            extra={"sessionKey": p_sessionKey},
        )

        p_SessionCache.m_simpleCounterLLMConversation.add_message(
            "assistant", BotResponse, "LLM"
        )  # now we add the request.

        if (current_token_usage > max_tokens):
            logging.warning(f"Token usage ({token_usage}) exceeded Max Token ({max_tokens}).  Removing oldest part of user,attendant conversation")
            p_SessionCache.m_simpleCounterLLMConversation.prune_oldest_pair()

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

