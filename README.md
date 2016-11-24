Both the client and server store their files in ~/.tmp_collab/ directory, which is created automatically in initialization.

Server is launched by starting server.py from backend folder.
Server default port and IP address are  written in backend/common.py

Client is started by running main.py
Client has the option to choose server IP and port in GUI.
Normally client ID would be hidden (program handles creating and storing ID on it's own), but in order to make starting multiple clients with different ID's easier, the ID entry is made visible.

In the next menu client can choose existing file on his ID from list (if he has any from previous logins).
Other option is to enter his own id and some random name - after which the server will create a new file for the user.
If the user wants to access some other users file, he has to enter other users ID and the filename of the file you want to access.

If private checkbox is checked when creating a new file, the only the owner of the file has rights to access that file.

This of client (where client ID can not be chosen):
![alt text](https://cloud.githubusercontent.com/assets/23189252/20583141/601b0f04-b1f0-11e6-92fd-81eefbacb1d3.png "Screenshot_1")

