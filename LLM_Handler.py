import logging

from fastapi import HTTPException

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
from DefaultParameters import get_result_formatting
from SessionCache import SessionCache
from utils.types import PyMessage
from utils.llm import get_llm_file
from utils.logging import setup_csv_logging
from bs4 import BeautifulSoup


LastResponse = ""


def initialize_llm():

    match model_provider:
        case "OPENAI":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model=model,
                max_completion_tokens=max_tokens,
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
                model_kwargs={
                    "frequency_penalty": frequency_penalty,
                    "presence_penalty": presence_penalty,
                },
                api_key=api_key,
                stop=None,
            )
        case "OLLAMA":
            from langchain_ollama import ChatOllama

            return ChatOllama(model=model)
        case _:
            raise ValueError("Invalid model provider")


try:
    llm = initialize_llm()
except Exception as e:
    logging.critical(f"Failed to initialize LLM: {e}")


def invoke_llm(p_SessionCache: SessionCache, p_Request: PyMessage, p_sessionKey: str):
    global LastResponse
    try:

        # we no longer need to define scenario here.  If empty, assume in conundrum
        scenario = get_llm_file(
            p_Request.classSelection, "conundrums", "scenario.txt", p_sessionKey
        )

        # we can work with an empty scenario file
        if scenario is None:
            scenario = ""

        conundrum = get_llm_file(
            p_Request.classSelection, "conundrums", p_Request.lesson, p_sessionKey
        )

        if conundrum is None:
            raise HTTPException(status_code=404, detail="Conundrum file not found")

        action_plan = get_llm_file(
            p_Request.classSelection, "actionplans", p_Request.actionPlan, p_sessionKey
        )

        print(f"ACTION PLAN: {action_plan}")

        if action_plan is None:
            action_plan = ""  # Default to an empty string if no action plan is found

        actionPlan = action_plan + get_result_formatting()

        logging.warning(
            f"LLM User's Request ({p_Request.text})", extra={"sessionKey": p_sessionKey}
        )

        if model_provider == "ANTHROPIC":
            Scenario_Conundrum = f"{scenario}\n{conundrum}\n"
            Request_ActionPlan = f"Respond to Users Request = ({p_Request.text}) following these instructions ({actionPlan})"

            messages = [
                ("system", Scenario_Conundrum),
                *p_SessionCache.m_simpleCounterLLMConversation.get_all_previous_messages(),
                ("user", Request_ActionPlan),
            ]
        else:
            messages = [
                *([] if scenario == "" else [("system", scenario)]),
                ("system", conundrum),
                *p_SessionCache.m_simpleCounterLLMConversation.get_all_previous_messages(),
                ("user", p_Request.text),
                ("system", actionPlan),
            ]

        # Test the messages structure before formatting
        logging.warning(f"LLM REQUEST\n{messages}", extra={"sessionKey": p_sessionKey})

        if llm is None:
            raise ValueError("LLM not initialized")

        llm_response = llm.invoke(messages)

        p_SessionCache.m_simpleCounterLLMConversation.add_message(
            "user", p_Request.text, "LLM"
        )  # now we add the request.

        BotResponse = str(llm_response.content)

        current_token_usage = 0

        # Log token usage metrics
        if llm_response.response_metadata:
            token_usage = llm_response.response_metadata.get("token_usage")

            if token_usage:
                current_token_usage = token_usage.get("prompt_tokens")
                logging.info(
                    f"Tokens used - Prompt tokens: {token_usage.get('prompt_tokens')}, Completion tokens: \
            {token_usage.get('completion_tokens')}, Total tokens: {token_usage.get('total_tokens')}",
                    extra={"sessionKey": p_sessionKey},
                )

        logging.warning(
            f"LLM_RESPONSE:\n{BotResponse}).\n\nDETAILS ({llm_response})",
            extra={"sessionKey": p_sessionKey},
        )
        p_SessionCache.m_simpleCounterLLMConversation.add_message(
            "assistant", BotResponse, "LLM"
        )  # now we add the request.

        # Hacked because conversation limits are drawfed by other prompt components.
        # This code only consider what the user request/response is ignore SSR activity.
        user_conversation_size = p_SessionCache.m_simpleCounterLLMConversation.get_total_conv_content_bytes()
        if user_conversation_size > max_tokens * 4: #rough that 1 token is 4 bytes.
            logging.warning(
                f"Token usage ({user_conversation_size}) exceeded Max conversation in bytes ({max_tokens*4}).  Removing oldest part of user,attendant conversation"
            )
            p_SessionCache.m_simpleCounterLLMConversation.prune_oldest_pair()

        return BotResponse

    except Exception as e:
        # Handle general exceptions
        logging.error(
            f"An exception occurred while calling LLM with first message: {e}",
            exc_info=True,
            extra={"sessionKey": p_sessionKey},
        )
        return f"An error ({e}) occurred processing your request, Please try again"

def get_token_count(llm_response, p_sessionKey):
    input_tokens = output_tokens = 0

    # Safely access token usage metrics
    response_metadata = getattr(llm_response, 'response_metadata', {})
    usage = response_metadata.get("usage", {})

    if usage:
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        logging.info(
            f"Tokens used - Input tokens: {input_tokens}, Output tokens: {output_tokens}, Total tokens: {input_tokens + output_tokens}",
            extra={"sessionKey": p_sessionKey},
        )

    return input_tokens, output_tokens

def load_ssr_files(p_Request, p_sessionKey, p_ssrfilelist):
    content_result = "<ssrcontent>"
    content_loaded = "Loaded SSR Content "
    contents_added = []

    for ssrfile in p_ssrfilelist:
        content = get_llm_file(p_Request.classSelection, "ssrcontent", ssrfile + ".txt", p_sessionKey)

        if content:
            if not contents_added:
                running_size = len(content)
                # Always load the first content, even if it exceeds the limit
                contents_added.append(content)
                content_loaded += f"{ssrfile},"
            else:
                running_size += len(content)
                # Check if adding the new content exceeds the limit
                if running_size > 20000 * 4: # 4 bytes/token
                    logging.warning(f"Content limit exceeded with ({ssrfile}). Returning less content than requested.")
                    break
                contents_added.append(content)
                content_loaded += f"{ssrfile},"
        else:
            logging.warning(f"Failed to load content for {ssrfile}")

    content_result += ", ".join(contents_added)
    content_result += "</ssrcontent>"
    content_loaded += " for this request only."
    return content_result, content_loaded


def invoke_llm_2(p_SessionCache, p_Request, p_sessionKey):
    global LastResponse
    try:
        total_request_token_count = 0
        total_response_token_count= 0

        # start by getting the various prompt components.
        # The p_Request contains the Lesson, Conundrum (Lesson), ActionPlan,
        scenario  = get_llm_file(p_Request.classSelection, "", "scenario.txt", p_sessionKey) or ""

        conundrum = get_llm_file(p_Request.classSelection, "conundrums", p_Request.lesson, p_sessionKey)
        if conundrum is None:
            raise HTTPException(status_code=404, detail="Conundrum file not found")

        action_plan = get_llm_file(p_Request.classSelection, "actionplans", p_Request.actionPlan, p_sessionKey)
        if action_plan is None:
            raise HTTPException(status_code=404, detail="action_plan file not found")

        actionPlan = action_plan # + get_result_formatting()  Disabled for now. Not sure why this is here.

        def build_prompt(p_working_request, p_additional_content="", p_SSRs_loaded=""):
            if model_provider == "ANTHROPIC":
                scenario_conundrum  = f"{scenario}\n{conundrum}\n{p_additional_content}"
                request_action_plan = f"Respond to User's Request = ({p_SSRs_loaded + p_working_request}) following these instructions ({actionPlan})"
                return [
                    ("system", scenario_conundrum),
                    *p_SessionCache.m_simpleCounterLLMConversation.get_all_previous_messages(),
                    ("user", request_action_plan),
                ]
            else:
                return [
                    *([] if scenario == "" else [("system", scenario)]),
                    ("system", conundrum + p_additional_content),
                    *p_SessionCache.m_simpleCounterLLMConversation.get_all_previous_messages(),
                    ("user", p_SSRs_loaded + p_working_request),
                    ("system", actionPlan),
                ]

        additional_content  = ""
        SSRs_loaded         = ""
        pass_count          = 0

        while True:
            messages    = build_prompt(p_Request.text, additional_content, SSRs_loaded)

            if (not pass_count):
                logging.warning(f"LLM_REQUEST:\n({messages})", extra={"sessionKey": p_sessionKey})
            else:
                logging.warning(f"LLM_SSR_REQUEST:\n({messages})", extra={"sessionKey": p_sessionKey})

            if (pass_count > 4):
                return "SSR Loop exceeded 4 loops.  Aborting Operation"
            pass_count += 1

            LLMResponse = llm.invoke(messages)
            LLMMessage  = LLMResponse.content
            request_token_count, response_token_count = get_token_count(LLMResponse, p_sessionKey)

            total_request_token_count += request_token_count
            total_response_token_count+= response_token_count

            # Process the LLM response.  We want to process xml code if any returned.
            soup        = BeautifulSoup(LLMResponse.content, "lxml-xml")
            ssr_response= soup.find("SSR_response")

            if not ssr_response:
                # We only intercept this xml tag.  Others bypass SSR processing code.
                break

            primary_keys_element = ssr_response.find("SSR_requesting_content")
            if not primary_keys_element or not primary_keys_element.PrimaryKeys:
                LLMMessage =  f"Total Input Tokens ({total_request_token_count}), Total Output Tokens ({total_response_token_count}) over ({pass_count}) passes\n"
                LLMMessage += ssr_response.find("answer").text
                break

            # We are adding in a new user request acknowledging file content added and its response
            p_SessionCache.m_simpleCounterLLMConversation.add_message("user"     , p_Request.text, None)
            p_SessionCache.m_simpleCounterLLMConversation.add_message("assistant", LLMResponse.content, None)

            primary_keys = [key.strip() for key in primary_keys_element.PrimaryKeys.text.split(",")]
            content_loaded, SSRs_loaded = load_ssr_files(p_Request, p_sessionKey, primary_keys)

            logging.warning(f"SSR_CONTENT_LOADED ({SSRs_loaded}) and reissued request", extra={"sessionKey": p_sessionKey})

            additional_content += content_loaded

            # End of while loop

        # Logging and adding messages to cache.  We did not
        p_SessionCache.m_simpleCounterLLMConversation.add_message("user"     , p_Request.text     , p_Request.text)
        p_SessionCache.m_simpleCounterLLMConversation.add_message("assistant", LLMResponse.content, LLMMessage)

        logging.warning(f"LLM_RESPONSE({request_token_count}, {response_token_count}):\n{LLMResponse}", extra={"sessionKey": p_sessionKey})

        # Hacked because conversation limits are drawfed by other prompt components.
        # This code only consider what the user request/response is ignore SSR activity.
        user_conversation_size = p_SessionCache.m_simpleCounterLLMConversation.get_total_conv_content_bytes()
        if user_conversation_size > max_tokens * 4: #rough that 1 token is 4 bytes.
            logging.warning(
                f"Token usage ({user_conversation_size}) exceeded Max conversation in bytes ({max_tokens*4}).  Removing oldest part of user,attendant conversation"
            )
            p_SessionCache.m_simpleCounterLLMConversation.prune_oldest_pair()


        return LLMMessage

    except Exception as e:
        logging.error(f"An exception occurred while calling LLM: {e}", exc_info=True, extra={"sessionKey": p_sessionKey})
        return f"An error ({e}) occurred processing your request. Please try again."

if __name__ == "__main__":
    setup_csv_logging()
