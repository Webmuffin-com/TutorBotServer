# TutorBot Server
This application is designed as a TutorBot that can Tutor anything that can be done with text alone.  It is similar to a traditional ChatBot, but provides places to inject user defined content.  Here are the key features:

1.  A unique prompt parameter ordering that prevents the bot from drifting of its prompts intentions.
2.  Prebuilt Scenerio, Personality, Conundrum and ActionPlan.
3.  A conundrum file that defines content, defines restrictions and give permissions to the LLM to use or not use it's own content.
4.  Prebuilt functionality to show users what content you are defining and what is provided by the LLM.

The design is simple and can be easily modified to do different things.

# Caveat
1. Conversational histories are maintained through the session's life.  As there grow, they increase costs.   \
Dropping previous conversations has downsides and needs to be factored in when needed.
2. Sessions are not cleared out.  As they grow it could slow down processing, but that is unlikely for prototyping purposes


## Pre requisites

In order to set the required secrets you need to duplicate the file `env.example.txt` and name it `env.txt` and fill its contents with the corresponding secrets.

## Build executable bundles

### MacOS / Linux

In order to get an executable bundle that includes every necessary asset follow this steps:

- Using the terminal navigate to the root directory of this repository.
- If you haven't created a virtual environment create one using the following command:
``` bash
python3 -m venv .venv 
```
- Activate the virtual environment you just provisioned using the command:
``` bash
source .venv/bin/activate
```
- Install the dependencies running the command:
``` bash
python3 -m pip install -r ./requirements-unix.txt
```
- Test the application by running the command:
``` bash
python3 ./TutorBot_Server.py
```
- Test the application by opening the url: `http://localhost:8000`
- Build the executable by running the command:
``` bash
pyinstaller TutorBot_Server.spec
```
- Copy all of the folder and files referenced at `TutorBot_Server.spec` `a.datas` to the dist folder. Currently just the `static` folder.
- You can now move the folder `dist` or zip it and execute it from any directory where you want.


### Windows

In order to get an executable bundle that includes every necessary asset follow this steps:

- Using the terminal navigate to the root directory of this repository.
- If you haven't created a virtual environment create one using the following command:
``` bash
python3 -m venv .venv 
```
- Activate the virtual environment you just provisioned using the command:
``` bash
# In cmd.exe
venv\Scripts\activate.bat
# In PowerShell
venv\Scripts\Activate.ps1
```
- If you get this error message:
```
.venv\scripts\Activate.ps1 cannot be loaded because running 
scripts is disabled on this system.
```
Run the command:
``` bash
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```
- Install the dependencies running the command:
``` bash
python3 -m pip install -r ./requirements-windows.txt
```
- Test the application by running the command:
``` bash
python3 ./TutorBot_Server.py
```
- Test the application by opening the url: `http://localhost:8000`
- Build the executable by running the command:
``` bash
python3 -m PyInstaller .\TutorBot_Server.spec
```
- Copy all of the folder and files referenced at `TutorBot_Server.spec` `a.datas` to the dist folder. Currently just the `static` folder.
- You can now move the folder `dist` or zip it and execute it from any directory where you want.


## Run the TutorBot_Server Bundle

### From MacOS / Linux

- Using the terminal navigate to the `dist` directory.
- Run the command: `./TutorBot_Server`

### From windows

- Using the file explorer navigate to the `dist` directory.
- Double click `TutorBot_Server.exe`.


pyinstaller TutorBot_Server.py --onefile --console --log-level=WARN --noconfirm --hidden-import=TutorBot_Server --add-data "static:static"





## Update requirements files after adding dependency

There are two requirements files for windows and unix based systems, every time you add a dependency you should update this files by running the following commands.

### MacOS / Unix

``` bash
python3 -m pip freeze > requirements-unix.txt
```

### Windows

``` bash
python3 -m pip freeze > requirements-windows.txt --exclude uvloop
```


## Contibutors

This application was written by Michael Schmidt <mike.schmidt@webmuffin.com> and Santiago Forero <biolimbo@pm.me>.
