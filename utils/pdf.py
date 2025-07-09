from fastapi import HTTPException
from pyppeteer import launch

from constants import system_encoding, pyppeteer_executable_path

from SessionCache import session_manager
from utils.llm import format_conversation


async def generate_conversation_pdf(
    session_key: str | None,
    class_name: str | None,
    lesson: str | None,
    action_plan: str | None,
):

    if session_key is None:
        raise HTTPException(status_code=404, detail="Session Key not found")

    session_cache = session_manager.get_session(session_key)

    if session_cache is None:
        raise HTTPException(status_code=404, detail="Could not locate Session Key")

    conversation = (
        session_cache.m_simpleCounterLLMConversation.get_user_conversation_messages()
    )

    formatted_conversation = format_conversation(conversation)

    with open("static/style-pdf.css", "r", encoding=system_encoding) as style_file:

        style = style_file.read()

        html_content = """
        <html>
            <head>
                <style type="text/css">
                    {style}
                </style>
            </head>
            <body>
                <div class="response-output-pdf">
                    <div class="header">
                        <h1>TutorBot Learning Center</h1>
                        <p>This document contains the conversation you had with the TutorBot.</p>
                        <p>Class: {class_name}    Lesson: {lesson}    Mode: {action_plan}.</p>
                    </div>
                    {formatted_conversation}
                </div>
            </body>
        </html>""".format(
            style=style,
            class_name=class_name,
            lesson=lesson,
            action_plan=action_plan,
            formatted_conversation="".join(formatted_conversation),
        )

        pdf = await create_pdf(html_content)

        return pdf


async def create_pdf(html):
    browser = await launch(
        executablePath=pyppeteer_executable_path,
        headless=True,
        args=["--no-sandbox"],
    )
    page = await browser.newPage()

    await page.setContent(html)
    pdf = await page.pdf({"format": "Letter"})
    await browser.close()

    return pdf
