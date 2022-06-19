import socket
import os
import threading
import time
# Basheq Tarifi (1696842)
# Setting up server address details
PORT = 21
HOST = socket.gethostbyname(socket.gethostname())
SERVER_ADDR = (HOST, PORT)

# Set defaults
DEFAULT_DTP_PORT = 20
DEFAULT_DTP_HOST = HOST
DEFAULT_ERROR = '550 Requested action not taken.'
DEFAULT_TYPE = 'A'
DEFAULT_MODE = 'S'
DEFAULT_STRU = 'F'

# Communication standards
BUFFER = 1024
FORMAT = 'utf-8'

# Setting to maintain state
clientSettings = {}

# Dictionary for efficient access of replies
replies = {
    125: '125 Data connection already open; transfer starting.',
    150: '150 File status okay; about to open data connection.',
    200: '200 Command okay.',
    220: '220 Service ready for new user.',
    221: '221 Service closing control connection.',
    226: '226 Closing data connection; requested file action successful.',
    230: '230 User logged in, proceed.',
    332: '332 Need account.',
    425: '425 Can\'t open data connection.',
    450: '450 Requested file action not taken.',
    500: '500 Syntax error.',
    501: '501 Syntax error in parameters.',
    502: '502 Command not implemented.',
    504: '504 Command not implemented for that parameter.',
    530: '530 Not logged in.',
    550: '550 Requested action not taken.'
}

# Function Handlers
def user(args, conn, addr, threadName):
    username = args[1].lower()
    baseDir = os.getcwd()

    # Check user exists
    if username not in users:
        # Request new user
        reply(332, conn)
        input = conn.recv(BUFFER).decode(FORMAT)
        newUser = input.split()[0]
        if newUser not in users:
            users.append(newUser)

            print(f'[{threadName}>NEW USER] new user {newUser} created')

            reply(220, conn)
            newFolder = os.path.join(baseDir, newUser) 
            # Create new folder for user
            if not os.path.isdir(newFolder):
                os.mkdir(newFolder)
        else:
            reply(230, conn)

        username = newUser
    else:
        reply(230, conn)

    print(f'[{threadName}>LOGGED IN] {username} logged in')
    print(f'[{threadName}>DIRECTORY] {username}/')

    # Set log in and current directory for client
    loggedIn = True
    currentDir = os.path.join(baseDir, username)
    clientSettings[threadName]['currentDir'] = currentDir
    clientSettings[threadName]['user'] = username
    return loggedIn

# Port 
def port(args, conn, addr, threadName):

    # Parse input
    hp = args[1].split(',')
    clientDataHost = f'{hp[0]}.{hp[1]}.{hp[2]}.{hp[3]}'
    clientDataPort = int(hp[4])*256 + int(hp[5])

    # Set host and port for client
    clientSettings[threadName]['host'] = clientDataHost
    clientSettings[threadName]['port'] = clientDataPort

    print(f'[{threadName}>PORT] Data transfer HOST:PORT set to {clientDataHost}:{clientDataPort}')
    reply(200, conn)
    return

# Quit
def quit(args, conn, addr, threadName):

    # Flush client details
    clientSettings[threadName]['currentDir'] = os.getcwd()
    clientSettings[threadName]['host'] = ''
    clientSettings[threadName]['username'] = ''
    clientSettings[threadName]['port'] = 0
    reply(221, conn)
    print(f'[{threadName}>DISCONNECT] {addr} disconnected on {threadName}.')
    return

# Structure
def stru(args, conn, addr, threadName):
    # Check default
    if (args[1] == DEFAULT_STRU):
        reply(200, conn, 'Default File structure.')
    else:
        # Reply negative
        reply(504, conn, 'Only File structure available on server.')
    return

# Type
def type(args, conn, addr, threadName):
    newType = args[1]
    # Check valid
    if (newType == 'I' or newType == 'A'):
        clientSettings[threadName]['type'] = newType
        reply(200, conn)
        print(f'[{threadName}>TYPE] Changed to \'{newType}\'')
    else:
    # Reply negative
        reply(504, conn, 'Only types A and I available on server.')
    return

def mode(args, conn, addr, threadName):
    if (args[1] == DEFAULT_MODE):
        reply(200, conn, 'Default Stream mode.')
    else:
        reply(504, conn, 'Only Stream mode available on server.')
    return

def stor(args, conn, addr, threadName):
    fileName = args[1]
    try:
        reply(150, conn)
        print(f'[{threadName}>STOR] Preparing to receive \'{fileName}\'.')
        
        # Create server DTP
        serverDTP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # State details
        currentDir = clientSettings[threadName]['currentDir']
        clientDataHost = clientSettings[threadName]['host']
        clientDataPort = clientSettings[threadName]['port']
        currentType = clientSettings[threadName]['type']

        # Connect to client DTP 
        clientDtpAddr = (clientDataHost, clientDataPort)
        serverDTP.connect(clientDtpAddr)

        # Get file size
        fileSize = int(serverDTP.recv(BUFFER).decode(FORMAT))
        
        # Configure write type
        writeType = 'w'
        if currentType=='I':
            writeType = 'wb'

        outputFile = open(os.path.join(currentDir,fileName), writeType)

        serverDTP.send('OK'.encode())

        start_time = time.time()
        # Receive datas
        bytesRecv = 0
        while bytesRecv < fileSize:
            chunk = serverDTP.recv(BUFFER)
            if currentType=='A':
                chunk = chunk.decode()
            outputFile.write(chunk)
            bytesRecv += BUFFER
        outputFile.close()


        serverDTP.send('OK'.encode())
        serverDTP.send(str(time.time() - start_time).encode(FORMAT))
        print(f'[{threadName}>STOR] File \'{fileName}\' received successfully')
        reply(226, conn)
        serverDTP.close()
    except:
        reply(450, conn, 'Error during file store.')
    return

def retr(args, conn, addr, threadName):

    currentDir = clientSettings[threadName]['currentDir']
    clientDataHost = clientSettings[threadName]['host']
    clientDataPort = clientSettings[threadName]['port']
    currentType = clientSettings[threadName]['type']

    fileName = args[1]
    if not os.path.isfile(os.path.join(currentDir,fileName)):
        reply(450, conn)
        print(f'[{threadName}>RETR] File \'{fileName}\' not found')
        return
    
    try:
        reply(150, conn)
        print(f'[{threadName}>RETR] Preparing to send \'{fileName}\'')

        clientDtpAddr = (clientDataHost, clientDataPort)
        serverDTP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverDTP.connect(clientDtpAddr)
        filePath = os.path.join(currentDir,fileName)
        fileSize = os.path.getsize(filePath)
        serverDTP.send(str(fileSize).encode())

        serverDTP.recv(BUFFER)

        readType = 'r'
        if currentType=='I':
            readType = 'rb'

        fileContent = open(filePath, readType)

        start_time = time.time()
        chunk = fileContent.read(BUFFER)
        while chunk:
            if currentType=='A':
                chunk = chunk.encode()
            serverDTP.send(chunk)
            chunk = fileContent.read(BUFFER)
        
        fileContent.close()

        serverDTP.recv(BUFFER)
        serverDTP.send(str(time.time() - start_time).encode(FORMAT))
        print(f'[{threadName}>RETR] FIle \'{fileName}\' sent successfully')
        reply(226, conn)
    except:
        reply(450, conn, 'Error during file retrieval.')
    return

def noop(args, conn, addr, threadName):
    reply(200, conn)
    return

def help(args, conn, addr, threadNum):
    helpMessage = 'The server implements the following commands:\n\n'
    helpMessage += 'USER <username> \t Sign in with a new or existing user.\n'
    helpMessage += 'PORT [h1,h2,h3,h4,p1,p2] \t Change the data connection port. Omitting the argument will set the default port.'
    helpMessage += 'h1 to h4 are the four 8 bit numbers of the IP and p1,p2 are the higher and lower 8 bit numbers of the port.\n'
    helpMessage += 'RETR <filename> \t Download a file from the server.\n'
    helpMessage += 'STOR <filename> \t Upload a file to the server.\n'
    helpMessage += 'TYPE <type> \t Change the data type - implemented for A and I.\n'
    helpMessage += 'MODE <mode> \t Change the transmission mode - implemented for S.\n'
    helpMessage += 'STRU <structure> \t Change the file structure - implemented for F.\n'
    helpMessage += 'QUIT \t Logout and exit the FTP Client.\n'
    helpMessage += 'NOOP \t Ping the server.\n'
    helpMessage += 'HELP \t View this help message.\n'

    msgSize = len(helpMessage)
    conn.send(str(msgSize).encode(FORMAT))
    conn.sendall(helpMessage.encode(FORMAT))
    
    reply(200, conn)
    return

def reply(code, conn, optMsg = ''):
    replyMsg = replies.get(code, DEFAULT_ERROR)
    if (not optMsg == ''):
        replyMsg += " " + optMsg

    conn.send(replyMsg.encode(FORMAT))
    return

def error(args, conn, addr, threadName):
    conn.send(DEFAULT_ERROR.encode(FORMAT))
    return

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

users = [f.name for f in os.scandir(os.getcwd()) if f.is_dir()] 

def handleClient(conn, addr):
    loggedIn = False
    threadName = threading.current_thread().getName()
    
    clientSettings[threadName] = {
        'currentDir': os.getcwd(),
        'username': '',
        'host': DEFAULT_DTP_HOST,
        'port': DEFAULT_DTP_PORT,
        'type': DEFAULT_TYPE,
        'stru': DEFAULT_STRU,
        'mode': DEFAULT_MODE
    }

    print(f"[NEW CONNECTION] {addr} on {threadName}")
    connectionOpen = True
    while connectionOpen:
        cmd = conn.recv(BUFFER).decode(FORMAT)
        if not cmd:
            break
        args = cmd.split()
        
        if (loggedIn or (args[0].upper() in ['NOOP', 'HELP', 'USER', 'QUIT'])):
            action = commands.get(args[0].upper(), lambda: error)
            if (args[0].upper() == 'USER'):
                loggedIn = action(args, conn, addr, threadName)
            else:
                action(args, conn, addr, threadName)
        else:
            reply(530, conn)
            continue

        if args[0].upper() == 'QUIT':
            loggedIn = False
            connectionOpen = False


# Actual start of program:

# Create server process interpreter socket
serverPI = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Bind to address and listen 
serverPI.bind(SERVER_ADDR)
serverPI.listen()

print(f'[STARTING] Server is starting up.')
online = True
print(f'[ONLINE] Server is listening on {HOST}, port {PORT}...')     

while online:
    connectedSocket, address = serverPI.accept()
    ftpRunner = threading.Thread(target=handleClient, args=(connectedSocket, address))
    ftpRunner.start()
    print(f"[ACTIVE CLIENTS] {threading.active_count() - 1}")

