# FTP Client and Server
## University of the Witwatersrand, Johannesburg
## ELEN4017 Network Fundamentals

_Basheq Tarifi_

This folder contains the code to an FTP implementation for the subject Network Fundamentals.

## Requirements 
This should work on different systems but it is not tested.
The test environment was as follows:
- Windows 10
- Python 3

## Running the code
The server should be run first. In order to run it on Windows, navigate to the folder and, in CMD or PowerShell:
```
> python .\ftp-server-multithreaded.py
```
Alternatively, in a unix terminal:
```
$ python3 ftp-server-multithreaded.py
```
To run the serial version, just use `ftp-server.py`.

Once the server is running, navigate to the client and run (in CMD or PowerShell):
```
> python .\ftp-client.py
```
Or, in a unix terminal:
```
$ python3 ftp-client.py
```

You can now interact with the CLI and send commands to the FTP server. The following commands are implemented:
```
USER <username>
PORT [h1,h2,h3,h4,p1,p2]
STOR <filename>
RETR <filename>
QUIT
HELP
NOOP
TYPE <t>
STRU <s>
MODE <m>
```

