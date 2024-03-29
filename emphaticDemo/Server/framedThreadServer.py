#! /usr/bin/env python3
import sys, os, socket, params, time
from threading import Thread, Lock
from framedSock import FramedStreamSock

switchesVarDefaults = (
    (('-l', '--listenPort') ,'listenPort', 50001),
    (('-d', '--debug'), "debug", False), # boolean (set if present)
    (('-?', '--usage'), "usage", False), # boolean (set if present)
    )

progname = "echoserver"
paramMap = params.parseParams(switchesVarDefaults)

debug, listenPort = paramMap['debug'], paramMap['listenPort']

if paramMap['usage']:
    params.usage()

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # listener socket
bindAddr = ("127.0.0.1", listenPort)
lsock.bind(bindAddr)
lsock.listen(5)
print("listening on:", bindAddr)

class ServerThread(Thread):
    requestCount = 0            # one instance / class
    mutex = Lock()
    def __init__(self, sock, debug):
        Thread.__init__(self, daemon=True)
        self.fsock, self.debug = FramedStreamSock(sock, debug), debug
        self.start()
    def run(self):
        state = "nameCheck"
        fileName = ""
        while True:
            ServerThread.mutex.acquire()
            try:
                msg = self.fsock.receivemsg()
                if not msg:
                    if self.debug: print(self.fsock, "server thread done")
                    return
                requestNum = ServerThread.requestCount
                #time.sleep(0.001)
                ServerThread.requestCount = requestNum + 1
                #msg = ("%s! (%d)" % (msg, requestNum)).encode()
                #self.fsock.sendmsg(msg)
                
                if state == "nameCheck":
                    fileName = msg.decode()
                    print(fileName)
                    state = "firstRun"
                    self.fsock.sendmsg(msg)
                
                #In this state the file overwrites the file if it already exists in the server directory 
                elif state == "firstRun":
                    f = open(fileName, 'wb+')
                    f.write(msg)
                    state = "continue"
                    self.fsock.sendmsg(msg)
                
                #This state appends after the firstRun state changes so that the data is added to the new file
                else:
                    #If the payload is not None then it will continue append otherwise it will close the child
                    if msg != None:
                        f = open(fileName, 'ab+')
                        f.write(msg)
                        state = "continue"
                        self.fsock.sendmsg(msg)
                    else:
                        print("File Received")
                        f.close()
                        sys.exit(0)
            finally:
                ServerThread.mutex.release()

while True:
    sock, addr = lsock.accept()
    ServerThread(sock, debug)
