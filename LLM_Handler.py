import os
import json
import httpx
import logging

from bs4 import BeautifulSoup

import DefaultParameters
from Utilities import setup_csv_logging
from SessionCache import SessionCache

api_key = os.getenv('OPENAI_API_KEY_TUTORBOT')
print(api_key)
if not api_key:
    logging.error("Problems loading key because OPENAI_API_KEY_TUTORBOT environment variable not set")

LastResponse = ""

async def invoke_llm(p_SessionCache: SessionCache, p_Request: str, p_sessionKey: str):
    global LastResponse
    try:
        scenerio = DefaultParameters.get_default_scenario()
        personality = DefaultParameters.get_default_personality()
        conundrum = p_SessionCache.get_conundrum()

        if (p_SessionCache.get_action_plan() != ""):
            actionPlan = p_SessionCache.get_action_plan()
        else:
            actionPlan = DefaultParameters.get_default_action_plan()

        messages = []

        messages.append({"role": "system", "content": scenerio})
        messages.append({"role": "system", "content": personality})
        messages.append({"role": "system", "content": conundrum})
        messages.extend(p_SessionCache.m_simpleCounterLLMConversation.get_all_previous_messages())
        messages.append({"role": "user", "content": p_Request})
        messages.append({"role": "system", "content": actionPlan})

       # logging.warning(f"LLM User's Request ({p_Request})", extra={'sessionKey': session_key})

        p_SessionCache.m_simpleCounterLLMConversation.add_message('user', p_Request, 'LLM')  # now we add the request.

        # Test the messages structure before formatting
      #  logging.warning(f"Messages structure: {messages}", extra={'sessionKey': session_key})

        # Format messages for the payload
        json_payload = {
            "model": "gpt-4-0125-preview",
            "messages": messages,
            "temperature": 0.0,
            "top_p": 0.0
        }

        # Debugging: Print out the JSON payload
        logging.warning(f"Request from User: ({p_Request})\n {json.dumps(json_payload, indent=2)}", extra={'sessionKey': p_sessionKey})

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                'https://api.openai.com/v1/chat/completions',
                json=json_payload,
                headers={"Authorization": f"Bearer {api_key}"}
            )

        response.raise_for_status()
        completion = response.json()
        BotResponse = completion['choices'][0]['message']['content']

        # Log token usage metrics
        if 'usage' in completion:
            usage = completion['usage']
            logging.info(f"Tokens used - Prompt tokens: {usage.get('prompt_tokens')}, Completion tokens: \
            {usage.get('completion_tokens')}, Total tokens: {usage.get('total_tokens')}", extra={'sessionKey': p_sessionKey})

        # Strip HTML tags from BotResponse to put in conversation as it messes up the LLM to feed HTML into it.
        soup = BeautifulSoup(BotResponse, 'html.parser')
        plain_text_response = soup.get_text().replace('\n', ' ').strip()

        logging.warning(f"Response from LLM: ({plain_text_response})\n {completion['choices'][0]['message']['content']}. Details are ({completion})", extra={'sessionKey': p_sessionKey})

        p_SessionCache.m_simpleCounterLLMConversation.add_message('assistant', BotResponse, 'LLM')  # now we add the request.

        return BotResponse

    except httpx.HTTPStatusError as e:
        # Handle HTTP errors
        logging.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}", extra={'sessionKey': p_sessionKey})
        return f"An HTTP error ({e.response.status_code}) occurred: {e.response.text}"
    except Exception as e:
        # Handle general exceptions
        logging.error(f"An exception occurred while calling LLM with first message: {e}", exc_info=True, extra={'sessionKey': p_sessionKey})
        return f"An error ({e}) occurred processing your request, Please try again"

if __name__ == "__main__":
    setup_csv_logging()
