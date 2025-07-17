import re
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import (
    HTMLResponse,
    FileResponse,
    JSONResponse,
)
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import uuid
import uvicorn

from utils.types import PyMessage

# Load environmental variables file from .env
load_dotenv()

from utils.logger import setup_logger  # noqa: E402
from constants import (  # noqa: E402
    cloud_mode_enabled,
    env,
    loki_labels,
    loki_org_id,
    loki_password,
    loki_url,
    loki_user,
    mailgun_enabled,
    port,
    model,
    model_provider,
    service_name,
    top_p,
    temperature,
    frequency_penalty,
    presence_penalty,
    validate_ssr_configuration,
)


from utils.html_export import HTMLConversationExporter  # noqa: E402
from utils.email import send_email  # noqa: E402
from utils.llm import validate_access_key  # noqa: E402
from utils.filesystem import (  # noqa: E402
    check_directory_exists,
    list_directory,
)
from SessionCache import SessionCacheManager, session_manager  # noqa: E402
from LLM_Handler import invoke_llm_with_ssr  # noqa: E402


def get_session_manager():
    return session_manager


# Initialize with constructor arguments

# Initialize centralized logger
logger = setup_logger(
    name=service_name,
    model_provider=model_provider,
    model=model,
    env=env,
    loki_url=loki_url,
    loki_user=loki_user,
    loki_password=loki_password,
    loki_org_id=loki_org_id,
    loki_labels=loki_labels,
)


app = FastAPI(title="TutorBot", description="Your personal tutor", version="0.0.1")
# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")
# Allow all local network computers (example for 192.168.1.x range)
allowed_origins = ["*"]
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def startup_event():
    logger.info("Application startup")
    logger.info("Model configuration", extra={"model": model})
    logger.info("Temperature configuration", extra={"temperature": str(temperature)})
    if top_p:
        logger.info("Top P configuration", extra={"top_p": str(top_p)})
    if frequency_penalty:
        logger.info(
            "Frequency Penalty configuration",
            extra={"frequency_penalty": str(frequency_penalty)},
        )
    if presence_penalty:
        logger.info(
            "Presence Penalty configuration",
            extra={"presence_penalty": str(presence_penalty)},
        )


def shutdown_event():
    logger.info("Application shutdown")


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

        logger.info(
            "Session key in middleware",
            extra={"session_key": session_key or "undefined"},
        )
        if not session_key:
            logger.info(
                "Session key missing in request",
                extra={"request_path": request.url.path},
            )
            raise HTTPException(status_code=401, detail="Session key is missing")
    response = await call_next(request)
    return response


@app.get("/set-cookie/")
async def set_cookie(
    response: Response,
    manager: SessionCacheManager = Depends(get_session_manager),
):
    session_key = None
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
        logger.info(
            "Cookie set and session created",
            extra={"session_key": session_key},
        )
        return {"message": "Cookie set and session created"}
    except Exception as e:
        logger.error(
            "Exception caught in set_cookie",
            extra={"session_key": session_key or "undefined", "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Error in set_cookie")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")


# Define your chatbot logic
def generate_response(p_session_key, p_Request):

    sessionCache = session_manager.get_session(p_session_key)

    if sessionCache:
        if not p_Request.classSelection:
            # logger already initialized globally
            logger.error(
                "Session did not specify Conundrum",
                extra={"session_key": p_session_key},
            )
            return "You must select a lesson to use this Bot"
        if not p_Request.lesson:
            # logger already initialized globally
            logger.error(
                "Session did not specify Lesson", extra={"session_key": p_session_key}
            )
            return "You must select a lesson to use this Bot"
        if not p_Request.actionPlan:
            # logger already initialized globally
            logger.error(
                "Session did not specify Action Plan",
                extra={"session_key": p_session_key},
            )
            return "You must select an action plan to use this Bot"
        return invoke_llm_with_ssr(sessionCache, p_Request, p_session_key)
    else:
        response = "Received unknown session key"
        logger.error(
            "Session key not found in generate_response",
            extra={"session_key": p_session_key, "response": response},
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
            # logger already initialized globally
            logger.info(
                "Session validated access key",
                extra={"session_key": session_key, "access_key": access_key},
            )

    response_text = generate_response(session_key, message)

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
    session_key = None
    try:
        session_key = request.cookies.get("session_key")
        directories = list_directory("classes", "directory")

        logger.info(
            "Loaded classes from directory",
            extra={"session_key": session_key, "directories": str(directories)},
        )

        return JSONResponse(content={"directories": directories})
    except Exception as e:
        logger.error(
            "Error listing class directories",
            extra={"session_key": session_key or "unknown", "error": str(e)},
        )
        raise HTTPException(
            status_code=500,
            detail="Error listing classes directory",
            headers={"session_key": session_key or ""},
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
            # logger already initialized globally
            logger.error(
                "Directory does not exist in class configuration",
                extra={"session_key": session_key, "directory": non_existent_directory},
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

        logger.info(
            "Loaded available files for class directory",
            extra={
                "session_key": session_key,
                "class_directory": class_directory,
                "lessons": str(lessons),
                "action_plans": str(action_plans),
            },
        )

        session_cache.m_simpleCounterLLMConversation.clear()

        return JSONResponse(content={"lessons": lessons, "action_plans": action_plans})
    except Exception as e:
        logger.error(
            "Error listing files in class directory",
            extra={
                "session_key": session_key,
                "class_directory": class_directory,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="Error listing files in directory")


@app.get("/conversation/clear")
async def clear_conversation(request: Request):
    session_key = request.cookies.get("session_key")

    if session_key is None:
        raise HTTPException(status_code=401, detail="Session key is missing")

    session_cache = session_manager.get_session(session_key)

    session_cache.m_simpleCounterLLMConversation.clear()

    return JSONResponse(content={"message": "Conversation cleared"})


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

    # Get session cache
    if session_key is None:
        raise HTTPException(status_code=401, detail="Session key is missing")

    session_cache = session_manager.get_session(session_key)
    if session_cache is None:
        raise HTTPException(status_code=404, detail="Could not locate Session Key")

    # Create HTML exporter
    html_exporter = HTMLConversationExporter()

    try:
        # Generate HTML content
        html_content = await html_exporter.generate_conversation_html(
            session_key, class_name, lesson, action_plan, session_cache
        )

        logger.info("HTML created successfully for conversation email")

        with open("static/conversation-email-template.html", "r") as file:
            email_template = file.read()
            email_template = email_template.replace("{{class_name}}", class_name)
            email_template = email_template.replace("{{lesson}}", lesson)
            email_template = email_template.replace("{{action_plan}}", action_plan)

            filename = html_exporter.get_filename()

            send_email(
                email,
                "Conversation with TutorBot",
                email_template,
                [(filename, html_content)],  # type: ignore
            )

            return JSONResponse(content={"message": "HTML created successfully"})
    except Exception as e:
        logger.error(
            "Error creating HTML for conversation email",
            extra={"session_key": session_key, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Error creating HTML")


@app.post("/download-conversation")
async def download_conversation(request: Request, payload: dict):
    session_key = request.cookies.get("session_key")

    class_name = payload.get("classSelection")
    lesson = payload.get("lesson")
    action_plan = payload.get("actionPlan")

    # Get session cache
    if session_key is None:
        raise HTTPException(status_code=401, detail="Session key is missing")

    session_cache = session_manager.get_session(session_key)
    if session_cache is None:
        raise HTTPException(status_code=404, detail="Could not locate Session Key")

    # Create HTML exporter
    html_exporter = HTMLConversationExporter()

    try:
        # Generate HTML content
        html_content = await html_exporter.generate_conversation_html(
            session_key, class_name, lesson, action_plan, session_cache
        )

        logger.info("HTML created successfully for conversation download")

        # Get filename
        filename = html_exporter.get_filename()

        return Response(
            content=html_content,
            media_type="text/html",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/html; charset=utf-8",
            },
        )
    except Exception as e:
        logger.error(
            "Error creating HTML for conversation download",
            extra={"session_key": session_key, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Error creating HTML")


if __name__ == "__main__":
    # Initialize logging system
    logger.info("Logging setup configured and starting TutorBot_Server")

    # Validate SSR configuration
    validate_ssr_configuration()
    logger.info("SSR configuration validation completed")

    uvicorn.run("TutorBot_Server:app", host="0.0.0.0", port=port)
