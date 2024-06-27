# TutorBot Server


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

## From windows

- Using the file explorer navigate to the `dist` directory.
- Double click `TutorBot_Server.exe`.


pyinstaller TutorBot_Server.py --onefile --console --log-level=WARN --noconfirm --hidden-import=TutorBot_Server --add-data "static:static"