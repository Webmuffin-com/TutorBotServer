# TutorBot Server

In order to get an executable file with the configuration from the specfile you can run the following command:

``` bash
pyinstaller TutorBot_Server.spec
```


After running the command you should copy all of the folder and files referenced at `TutorBot_Server.spec` `a.datas` to the dist folder.

Finally you can zip it or move the dist folder to any directory where you want to run the TutorBot Server from.


## Run the TutorBot Server from linux and mac

- Using the terminal navigate to the `dist` directory.
- Run the command: `./TutorBot_Server`

## Run the TutorBot Server from windows

- Using the file explorer navigate to the `dist` directory.
- Double click `TutorBot_Server.exe`.


pyinstaller TutorBot_Server.py --onefile --console --log-level=WARN --noconfirm --hidden-import=TutorBot_Server --add-data "static:static"