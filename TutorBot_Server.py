import uuid
import os
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
import uvicorn

from LLM_Handler import invoke_llm
from SessionCache import SessionCacheManager
from Temp_html import temp_html_v3, temp_html_v5
import logging
from Utilities import setup_csv_logging

# This configures the logging utilities so outputs are csv files that can be read with a spreadsheet editor
setup_csv_logging()

session_manager = SessionCacheManager()
def get_session_manager():
    return session_manager

app = FastAPI(title="TutorBot", description="Your personal tutor", version="0.0.1")
# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")
template = Jinja2Templates(directory="templates")
# Allow all local network computers (example for 192.168.1.x range)
#allowed_origins = ["http://127.0.0.1:8000", "http://localhost:8000", "https://127.0.0.1:8000", "https://localhost:8000"]
allowed_origins  = ["*"]
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    logging.warning(request.headers)
    response = await call_next(request)
    origin = request.headers.get('origin')
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response
@app.middleware("http")
async def check_session_key(request: Request, call_next):
    logging.warning(request.headers)

    if request.url.path.startswith("/static/"):
        # Allow static file requests to pass through
        return await call_next(request)

    if request.method == "OPTIONS":
        response = Response(status_code=200)
        origin = request.headers.get('origin')
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
            print(f"Session key missing in request to {request.url.path}")  # Debug statement
            raise HTTPException(status_code=401, detail="Session key is missing")
    response = await call_next(request)
    return response

@app.get("/set-cookie/")
async def set_cookie(response: Response, request: Request, manager: SessionCacheManager = Depends(get_session_manager)):
    session_key = str(uuid.uuid4())  # Use existing session key if available, otherwise set a default or generate a new one
    session_data = {"initial": "data"}  # Initial data for the session
    manager.add_session(session_key, session_data)
    response.set_cookie(
        key="session_key",
        value=session_key,
        samesite="None",
        secure=False       # This needs to be set true once we move it to a https server.
    )
    logging.warning (f"Cookie ({session_key}) set and session created", extra={'sessionKey': session_key})  # Debug statement
    return {"message": "Cookie set and session created"}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")

# Define a Pydantic model for the request body
class PyMessage(BaseModel):
    text: str

# Define a Pydantic model for the response body
class PyResponse(BaseModel):
    text: str

# Define your chatbot logic
async def generate_response(p_session_key, p_Request):

    sessionCache = session_manager.get_session( p_session_key)

    if (sessionCache):
        return await invoke_llm (sessionCache, p_Request)
    else:
        response = "Received unknown session key"
        logging.error (f"session key ({p_session_key}) was not found.  returning ({response})", extra={'sessionKey': p_session_key})
        return response

# Define an endpoint to handle incoming messages
@app.post("/chatbot/")
async def chatbot_endpoint(request: Request, message: PyMessage) -> JSONResponse:
    session_key = request.cookies.get("session_key")
    response_text = await generate_response(session_key, message.text)

    logging.warning(f"Received chatbot request ({message.text}), response ({response_text})", extra={'sessionKey': session_key})  # Debug statement

    response = JSONResponse(content={"text": response_text})
    origin = request.headers.get('origin')
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# Define a welcome endpoint
@app.get("/", response_class=HTMLResponse)
async def welcome(request: Request):
    result = temp_html_v5()

    logging.warning (f"Loaded new client web page")
    return HTMLResponse(content=result)

@app.delete("/session/{session_key}")
def delete_session(session_key: str, manager: SessionCacheManager = Depends(get_session_manager)):
    manager.remove_session(session_key)
    return {"message": "Session deleted"}

# Define the path to the 'classes' directory within the current working directory
current_working_directory = os.getcwd()
CLASSES_DIR = os.path.join(current_working_directory, 'classes')
CLASSES_DIR = os.path.normpath(CLASSES_DIR)

@app.get("/classes/")
async def list_class_directories(request: Request):
    try:
        session_key = request.cookies.get("session_key")
        directories = [d for d in os.listdir(CLASSES_DIR) if os.path.isdir(os.path.join(CLASSES_DIR, d))]

        logging.warning (f"Loaded classes ({directories})", extra={'sessionKey': session_key})

        return JSONResponse(content={"directories": directories})
    except Exception as e:
        logging.error(f"Error listing class directories: {e}")
        raise HTTPException(status_code=500, detail="Error listing classes directory", extra={'sessionKey': session_key})


@app.get("/classes/{class_directory}/conundrums/")
async def list_conundrums(class_directory: str, request: Request):
    directory_path = os.path.join(CLASSES_DIR, class_directory, 'conundrums')
    directory_path = os.path.normpath(directory_path)

    sessionKey = request.cookies.get("session_key")
    try:
        if not os.path.exists(directory_path):
            logging.error(f"Directory does not exist: {directory_path}", extra={'sessionKey': sessionKey})
            raise HTTPException(status_code=404, detail="Directory does not exist")

        if not os.path.isdir(directory_path):
            logging.error(f"Path is not a directory: {directory_path}", extra={'sessionKey': sessionKey})
            raise HTTPException(status_code=400, detail="Path is not a directory")

        txt_files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f)) and f.endswith('.txt')]

        logging.warning(f"Loaded conundrum files for {class_directory} which contained ({txt_files})", extra={'sessionKey': sessionKey})
        return JSONResponse(content={"files": txt_files})
    except Exception as e:
        logging.error(f"Error listing files in directory {class_directory}: {e}", extra={'sessionKey': sessionKey})
        raise HTTPException(status_code=500, detail="Error listing files in directory")

@app.get("/classes/{class_directory}/conundrums/{file_name}")
async def load_conundrum_file(class_directory: str, file_name: str, request: Request):
    conundrum_file_path = os.path.join(CLASSES_DIR, class_directory, "conundrums", file_name)
    conundrum_file_path = os.path.normpath(conundrum_file_path)
    action_plan_file_path = os.path.join(CLASSES_DIR, class_directory, "action_plan.txt")
    action_plan_file_path = os.path.normpath(action_plan_file_path)
    scenario_file_path = os.path.join(CLASSES_DIR, class_directory, "scenario.txt")
    scenario_file_path = os.path.normpath(scenario_file_path)
    personality_file_path = os.path.join(CLASSES_DIR, class_directory, "personality.txt")
    personality_file_path = os.path.normpath(personality_file_path)

    session_key = request.cookies.get("session_key")
    session_cache = session_manager.get_session(session_key)

    if session_cache is None:
        raise HTTPException(status_code=404, detail="Could not locate Session Key")

    if not os.path.exists(conundrum_file_path):
        logging.warning(f"Failed to locate file {conundrum_file_path}", extra={'sessionKey': session_key})
        raise HTTPException(status_code=404, detail="Conundrum file not found")

    try:
        # Load conundrum file
        with open(conundrum_file_path, "r") as conundrum_file:
            conundrum_content = conundrum_file.read()

        if len(conundrum_content) == 0:
            logging.warning(f"conundrum file {conundrum_file_path} is empty.", extra={'sessionKey': session_key})
            raise HTTPException(status_code=404, detail="Conundrum file was empty")

        session_cache.set_conundrum(conundrum_content)

        logging.warning(f"Loaded conundrum file {conundrum_file_path}", extra={'sessionKey': session_key})

        # Load action plan file if it exists
        if os.path.exists(action_plan_file_path):
            with open(action_plan_file_path, "r") as action_plan_file:
                logging.warning(f"also loaded action_plan file {action_plan_file_path}", extra={'sessionKey': session_key})
                session_cache.set_action_plan(action_plan_file.read())

        # Load scenario file if it exists
        if os.path.exists(scenario_file_path):
            with open(scenario_file_path, "r") as scenario_file:
                logging.warning(f"also loaded scenario file {scenario_file_path}", extra={'sessionKey': session_key})
                session_cache.set_scenario(scenario_file.read())

        # Load personality file if it exists
        if os.path.exists(personality_file_path):
            with open(personality_file_path, "r") as personality_file:
                logging.warning(f"also loaded personality file {personality_file_path}", extra={'sessionKey': session_key})
                session_cache.set_personality(personality_file.read())

        return JSONResponse(content={"message": "Conundrum file loaded successfully"})

    except Exception as e:
        logging.error(f"Error loading conundrum file or action plan: {e}")
        raise HTTPException(status_code=500, detail="Error loading conundrum file or action plan")

if __name__ == '__main__':
    print('running TutorBot_Server')

    uvicorn.run(
        'TutorBot_Server:app', host='0.0.0.0', port=8000
    )

