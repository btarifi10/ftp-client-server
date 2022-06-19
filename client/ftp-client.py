import socket
import os
# Basheq Tarifi (1696842)
# Setting up server address details
# FTP Default port
SERVER_PORT = 21
SERVER_HOST = '192.168.1.22'
SERVER_ADDR = (SERVER_HOST, SERVER_PORT)
# Communication standards
BUFFER = 1024
FORMAT = 'utf-8'

# Default values
DEFAULT_DTP_HOST = socket.gethostbyname(socket.gethostname())
DEFAULT_DTP_PORT = 20
# current Values
currentType = 'A'
currentStru = 'F'
currentMode = 'S'
currentDataHost = DEFAULT_DTP_HOST
currentDataPort = DEFAULT_DTP_PORT

# Function Handlers
# User
def user(prompts):
    # Check input
    if (len(prompts.split()) < 2):
        print('Error: Please type in a username.')
        return
    
    # Send prompt
    clientPI.sendall(prompt.encode())
    reply = clientPI.recv(BUFFER).decode()
    print(reply)
    # Handle new user
    if reply[:3]=='332':
        newUser = input('Please type in a new username to create an account or an existing account> ')
        clientPI.send(newUser.encode())
        reply = clientPI.recv(BUFFER).decode()
        print(reply)
    return

# Validate host port input
def validHostPort(hostPort):
    nums = [int(x) for x in hostPort.split(',')]
    return all(x < 256 and x >=0 for x in nums)

# Port
def port(prompts):
    global currentDataHost
    global currentDataPort
    prompts = prompts.split()
    hostPort = ''
    # Check number of inputs
    # Use Default
    if (len(prompts) < 2): 
        host_ = ','.join(DEFAULT_DTP_HOST.split('.'))
        # Extract host and port
        highBitPort = DEFAULT_DTP_PORT // 256
        lowBitPort = DEFAULT_DTP_PORT - ( highBitPort * 256 )
        hostPort = f'{host_},{highBitPort},{lowBitPort}'
        currentDataHost = DEFAULT_DTP_HOST
        currentDataPort = DEFAULT_DTP_PORT
    # Use input
    elif (validHostPort(prompts[1])):
        hostPort = prompts[1]
        hp = hostPort.split(',')
        currentDataHost = f'{hp[0]}.{hp[1]}.{hp[2]}.{hp[3]}'
        currentDataPort = int(hp[4])*256 + int(hp[5])
    else:
        # Error
        print('Please input a valid port and host in the form <h1,h2,h3,h4,p1,p2> where'+
         'h1 to h4 are the four 8 bit numbers of the IP and p1,p2 are the higher and lower 8 bit numbers of the port.')
        return

    commandString = f'PORT {hostPort}'
    # Send to Server
    clientPI.sendall(commandString.encode())
    reply = clientPI.recv(BUFFER).decode()
    print(reply)
    return

# Quit
def quit(prompts):
    clientPI.send('QUIT'.encode())
    reply = clientPI.recv(BUFFER).decode()
    print(reply)
    return

# Structure
def stru(prompts):
    global currentStru
    if (prompts.split()[1] not in ['F', 'R', 'P']):
        print('Please input a valid structure: "F", "R" or "P".')
        return
    clientPI.send(prompts.encode())
    reply = clientPI.recv(BUFFER).decode()
    if (reply[:3] == '200'):
        currentStru = prompts.split()[1].upper()
    print(reply)
    return

# Type
def type(prompts):
    global currentType
    # Check if Type is valid
    if (prompts.split()[1].upper() not in ['A', 'E', 'I', 'L']):
        print('Please input a valid type: "A", "E", "I" or "L".')
        return

    # Send to server
    clientPI.send(prompts.upper().encode())
    reply = clientPI.recv(BUFFER).decode()
    if (reply[:3] == '200'):
        currentType = prompts.split()[1].upper()
    print(reply)
    return

# Mode
def mode(prompts):
    global currentMode
    # Check if Mode is valid
    if (prompts.split()[1].upper() not in ['S', 'B', 'C']):
        print('Please input a valid structure: "S", "B" or "C".')
        return
    
    # Send to server

    clientPI.send(prompts.upper().encode())
    reply = clientPI.recv(BUFFER).decode()
    if (reply[:3] == '200'):
        currentMode = prompts.split()[1].upper()
    print(reply)
    return

# Stor
def stor(prompts):
    fileName = prompts.split()[1]
    print (f'Uploading file: {fileName}')
    try:
        # Define read type
        readType = 'r'
        if currentType == 'I':
            readType = 'rb'

        # Check the file exists
        fileContent = open(fileName, readType)
    except:
        print('Error opening file. Ensure file name was entered correctly.')
        return
    try:
        # Request upload
        clientPI.send(f'STOR {fileName}'.encode())
    except:
        print('Error making requets. Restart the client if problem persists.')
        return
    try:
        # Wait for server
        reply = clientPI.recv(BUFFER).decode()
        print(reply)
        if (reply[:3] == '450'):
            return
        
        # Make client DTP
        clientDTP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientDTP.bind((currentDataHost, currentDataPort))
        clientDTP.listen(1)
        # Accept server connection
        connServer, serverAddr = clientDTP.accept()

        # Send file size
        fileSize = os.path.getsize(fileName)
        connServer.send(str(fileSize).encode(FORMAT))
        
        connServer.recv(BUFFER)
    except:
        print('Error sending file details. Please try again or restart the server.')
    try:
        chunk = fileContent.read(BUFFER)
        print('Sending file...')
        # Send file
        while chunk:
            if currentType=='A':
                chunk = chunk.encode()
            connServer.send(chunk)
            chunk = fileContent.read(BUFFER)
        fileContent.close()

        # Get rime taken
        connServer.recv(BUFFER)
        uploadTime = connServer.recv(BUFFER).decode()
        print(f'Sent file {fileName} in {uploadTime}s')
        reply = clientPI.recv(BUFFER).decode()
        print(reply)
        if (reply[:3] == '450'):
            return
    except:
        print('Error during file send, please retry.')
        return
    return

def retr(prompts):
    fileName = prompts.split()[1]

    try:
        # Make retrieve request
        clientPI.send(f'RETR {fileName}'.encode())
    except:
        print('Couldn\'t make server request. Make sure a connection has bene established.')
        return
    try:
        
        # Wait for server

        reply = clientPI.recv(BUFFER).decode()
        print(reply)
        
        if (reply[:3] == '450'):
            return

        # Make client DTP
        clientDTP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientDTP.bind((currentDataHost, currentDataPort))
        clientDTP.listen(1)
        # Accept server connection
        connServer, serverAddr = clientDTP.accept()

        # Receive file size 
        fileSize = int(connServer.recv(BUFFER).decode())

        # Configure write type
        writeType = 'w'
        if currentType=='I':
            writeType = 'wb'

        outputFile = open(fileName, writeType)

        connServer.send('OK'.encode())

        bytesRecv = 0
        while bytesRecv < fileSize:
            chunk = connServer.recv(BUFFER)
            if currentType=='A':
                chunk = chunk.decode()
            outputFile.write(chunk)
            bytesRecv += BUFFER
    
        outputFile.close()

        connServer.send('OK'.encode())
        downloadTime = connServer.recv(BUFFER).decode()
        print(f'Downloaded file {fileName} in {downloadTime}s')
        reply = clientPI.recv(BUFFER).decode()
        print(reply)
    except:
        print('Error during file download, please retry')
        return
    return

# Noop function
def noop(prompts):
    clientPI.send(prompts.encode())
    reply = clientPI.recv(BUFFER).decode()
    print(reply)
    return

# Help function
def help(prompts):
    clientPI.send('HELP'.encode())

    helpMsgSize = int(clientPI.recv(BUFFER).decode(FORMAT))
    bytesRecv = 0
    helpMsg = '' 
    while bytesRecv < helpMsgSize:
        helpMsg += clientPI.recv(BUFFER).decode(FORMAT)
        bytesRecv = len(helpMsg)
        
    print(helpMsg)

    reply = clientPI.recv(BUFFER).decode(FORMAT)
    print(reply)
    return

# Switch map
commands = {
    'USER': user,
    'PORT': port,
    'QUIT': quit,
    'STRU': stru,
    'TYPE': type,
    'MODE': mode,
    'RETR': retr,
    'STOR': stor,
    'NOOP': noop,
    'HELP': help
}

# Main code begins here
# Create PI socket
clientPI = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Connect to address via socket
clientPI.connect(SERVER_ADDR)

# Initially, socket is open
socketOpen = True
print('Welcome to the FTP Server! Please login to continue.')
while socketOpen:
    # Get input
    prompt = input('\nFTP> ')
    if prompt == "":
        continue
    
    # Extract action from switch map
    action = commands.get(prompt[:4].upper(), -1)
    if action == -1:
        print('Unrecognized command.')
        continue
    
    # Perform action
    action(prompt)

    if prompt[:4].upper() == 'QUIT':
        clientPI.close()
        socketOpen  = False
        break
    

    

