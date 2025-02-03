from datetime import datetime
import re
import subprocess
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import (
    HTMLResponse,
    FileResponse,
    JSONResponse,
)
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import logging
import uuid
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from utils.types import PyMessage


# Load environmental variables file from .env
load_dotenv()

from utils.logging import (  # noqa: E402
    drain_logs_to_s3,
    setup_csv_logging,
)
from constants import (  # noqa: E402
    cloud_mode_enabled,
    mailgun_enabled,
    pyppeteer_executable_path,
)


from utils.pdf import generate_conversation_pdf  # noqa: E402
from utils.email import send_email  # noqa: E402
from utils.llm import validate_access_key  # noqa: E402
from utils.filesystem import (  # noqa: E402
    check_directory_exists,
    list_directory,
)
from SessionCache import SessionCacheManager, session_manager  # noqa: E402
from LLM_Handler import invoke_llm  # noqa: E402


def get_session_manager():
    return session_manager


app = FastAPI(title="TutorBot", description="Your personal tutor", version="0.0.1")
# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")
# Allow all local network computers (example for 192.168.1.x range)
# allowed_origins = ["http://127.0.0.1:8000", "http://localhost:8000", "https://127.0.0.1:8000", "https://localhost:8000"]
allowed_origins = ["*"]
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = None


def startup_event():

    setup_csv_logging()
    logging.warning("Application startup")

    if cloud_mode_enabled:
        scheduler = BackgroundScheduler()
        drain_trigger = CronTrigger(hour="*", minute="*", second="0,30")

        scheduler.add_job(drain_logs_to_s3, trigger=drain_trigger)

        scheduler.start()


def shutdown_event():
    logging.warning("Application shutdown")

    if scheduler:
        scheduler.shutdown()


app.add_event_handler("startup", lambda: startup_event())
app.add_event_handler("shutdown", lambda: shutdown_event())


@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    # logging.warning(request.headers)
    response = await call_next(request)
    origin = request.headers.get("origin")
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.middleware("http")
async def check_session_key(request: Request, call_next):
    # logging.warning(request.headers)

    if request.url.path.startswith("/static/"):
        # Allow static file requests to pass through
        return await call_next(request)

    if request.method == "OPTIONS":
        response = Response(status_code=200)
        origin = request.headers.get("origin")
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    if request.url.path not in ["/set-cookie/", "/favicon.ico", "/"]:
        session_key = request.cookies.get("session_key")

        print(f"Session key in middleware: {session_key}")  # Debug statement
        if not session_key:
            print(
                f"Session key missing in request to {request.url.path}"
            )  # Debug statement
            raise HTTPException(status_code=401, detail="Session key is missing")
    response = await call_next(request)
    return response


@app.get("/set-cookie/")
async def set_cookie(
    response: Response,
    request: Request,
    manager: SessionCacheManager = Depends(get_session_manager),
):
    try:
        session_key = str(
            uuid.uuid4()
        )  # Use existing session key if available, otherwise set a default or generate a new one
        session_data = {"initial": "data"}  # Initial data for the session
        manager.add_session(session_key, session_data)
        response.set_cookie(
            key="session_key",
            value=session_key,
            samesite="lax",
        )
        logging.warning(
            f"Cookie ({session_key}) set and session created",
            extra={"sessionKey": session_key},
        )  # Debug statement
        return {"message": "Cookie set and session created"}
    except Exception as e:
        logging.error(f"Caught exception in set_cookie {session_key}: {e}")
        raise HTTPException(status_code=500, detail="Error in set_cookie")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")


# Define your chatbot logic
def generate_response(p_session_key, p_Request):

    sessionCache = session_manager.get_session(p_session_key)

    if sessionCache:
        if not p_Request.classSelection:
            logging.warning(f"Session ({p_session_key}) did not specify Conundrum")
            return "You must select a lesson to use this Bot"
        if not p_Request.lesson:
            logging.warning(f"Session ({p_session_key}) did not specify Lesson")
            return "You must select a lesson to use this Bot"
        if not p_Request.actionPlan:
            logging.warning(f"Session ({p_session_key}) did not specify Action Plan")
            return "You must select an action plan to use this Bot"
        return invoke_llm(sessionCache, p_Request, p_session_key)
    else:
        response = "Received unknown session key"
        logging.error(
            f"session key ({p_session_key}) was not found.  returning ({response})",
            extra={"sessionKey": p_session_key},
        )
        return response


# Define an endpoint to handle incoming messages
@app.post("/chatbot/")
def chatbot_endpoint(request: Request, message: PyMessage) -> JSONResponse:
    session_key = request.cookies.get("session_key")

    if not session_key:
        raise HTTPException(status_code=401, detail="Session key is missing")

    if cloud_mode_enabled:
        access_key = message.accessKey

        is_valid_key = validate_access_key(access_key, session_key)

        if not is_valid_key:
            raise HTTPException(status_code=403, detail="Invalid access key")
        else:
            logging.warning(
                f"Session ({session_key}) validated access key ({access_key})",
                extra={"sessionKey": session_key, "accessKey": access_key},
            )

    response_text = generate_response(session_key, message)

    #    logging.warning(f"Received chatbot request ({message.text}), response ({response_text})", extra={'sessionKey': session_key})  # Debug statement

    response = JSONResponse(content={"text": response_text})
    origin = request.headers.get("origin")
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


# Define a welcome endpoint
@app.get("/", response_class=HTMLResponse)
async def welcome():
    return FileResponse("static/index.html")


@app.delete("/session/{session_key}")
def delete_session(
    session_key: str, manager: SessionCacheManager = Depends(get_session_manager)
):
    manager.remove_session(session_key)
    return {"message": "Session deleted"}


@app.get("/classes/")
async def list_class_directories(request: Request):
    try:
        session_key = request.cookies.get("session_key")
        directories = list_directory("classes", "directory")

        logging.warning(
            f"Loaded classes ({directories})", extra={"sessionKey": session_key}
        )

        return JSONResponse(content={"directories": directories})
    except Exception as e:
        logging.error(f"Error listing class directories: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error listing classes directory",
            headers={"sessionKey": session_key or ""},
        )


@app.get("/classes/{class_directory}")
async def get_class_configuration(class_directory: str, request: Request):

    conundrums_path = f"classes/{class_directory}/conundrums"

    action_plans_path = f"classes/{class_directory}/actionplans"

    session_key = request.cookies.get("session_key") or "unknown"
    session_cache = session_manager.get_session(session_key)

    if session_cache is None:
        raise HTTPException(status_code=404, detail="Could not locate Session Key")

    conundrums_path_exists = check_directory_exists(conundrums_path)
    action_plans_path_exists = check_directory_exists(action_plans_path)

    try:
        non_existent_directory = (
            conundrums_path
            if not conundrums_path_exists
            else action_plans_path if not action_plans_path_exists else None
        )

        if non_existent_directory:
            error_message = f"Directory does not exist: {non_existent_directory}"
            logging.error(
                error_message,
                extra={"sessionKey": session_key},
            )
            raise HTTPException(status_code=404, detail=error_message)

        lessons = [
            lesson
            for lesson in list_directory(conundrums_path, "file")
            if lesson.endswith(".txt")
        ]

        lessons.sort()

        action_plans = [
            action_plan
            for action_plan in list_directory(action_plans_path, "file")
            if action_plan.endswith(".txt")
        ]

        action_plans.sort()

        logging.warning(
            f"Loaded available files for {class_directory} which contained lessons: ({lessons}) and action plans: ({action_plans})",
            extra={"sessionKey": session_key},
        )

        session_cache.m_simpleCounterLLMConversation.clear()

        return JSONResponse(content={"lessons": lessons, "action_plans": action_plans})
    except Exception as e:
        logging.error(
            f"Error listing files in directory {class_directory}: {e}",
            extra={"sessionKey": session_key},
        )
        raise HTTPException(status_code=500, detail="Error listing files in directory")


@app.post("/send-conversation")
async def send_conversation(request: Request, payload: dict):
    session_key = request.cookies.get("session_key")

    email = payload.get("email")

    valid_email = re.match(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email or ""
    )

    if valid_email is None or email is None:
        raise HTTPException(status_code=400, detail="Invalid email address")

    if not mailgun_enabled:
        raise HTTPException(
            status_code=500,
            detail="Sending conversations by email is currently disabled",
        )

    class_name = payload.get("classSelection") or "Unknown"
    lesson = payload.get("lesson") or "Unknown"
    action_plan = payload.get("actionPlan") or "Unknown"

    pdf = await generate_conversation_pdf(session_key, class_name, lesson, action_plan)

    if pdf is not None:

        print("PDF created successfully.")

        with open("static/conversation-email-template.html", "r") as file:
            email_template = file.read()
            email_template = email_template.replace("{{class_name}}", class_name)
            email_template = email_template.replace("{{lesson}}", lesson)
            email_template = email_template.replace("{{action_plan}}", action_plan)

            date_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            send_email(
                email,
                "Conversation with TutorBot",
                email_template,
                [(f"{date_string}_TutorBot_Conversation.pdf", pdf)],  # type: ignore
            )

            return JSONResponse(content={"message": "PDF created successfully"})
    else:
        raise HTTPException(status_code=500, detail="Error creating PDF")


@app.post("/download-conversation")
async def download_conversation(request: Request, payload: dict):
    session_key = request.cookies.get("session_key")

    class_name = payload.get("classSelection")
    lesson = payload.get("lesson")
    action_plan = payload.get("actionPlan")

    pdf = await generate_conversation_pdf(session_key, class_name, lesson, action_plan)

    if pdf is not None:

        print("PDF created successfully.")

        date_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename={date_string}_TutorBot_Conversation.pdf"
            },
        )
    else:
        raise HTTPException(status_code=500, detail="Error creating PDF")


if __name__ == "__main__":
    # This configures the logging utilities so outputs are csv files that can be read with a spreadsheet editor

    logging.warning("Logging setup is configured and running TutorBot_Server")

    if pyppeteer_executable_path is None:
        subprocess.run(["pyppeteer-install"], shell=True)

    uvicorn.run("TutorBot_Server:app", host="0.0.0.0", port=8000)
