#! /usr/bin/env python3

# Echo client program
import socket, sys, re, os
import params
from framedSock import FramedStreamSock
from threading import Thread
import time

switchesVarDefaults = (
    (('-s', '--server'), 'server', "localhost:50001"),
    (('-d', '--debug'), "debug", False), # boolean (set if present)
    (('-?', '--usage'), "usage", False), # boolean (set if present)
    )


progname = "framedClient"
paramMap = params.parseParams(switchesVarDefaults)

server, usage, debug  = paramMap["server"], paramMap["usage"], paramMap["debug"]

if usage:
    params.usage()


try:
    serverHost, serverPort = re.split(":", server)
    serverPort = int(serverPort)
except:
    print("Can't parse server:port from '%s'" % server)
    sys.exit(1)

class ClientThread(Thread):
    def __init__(self, serverHost, serverPort, debug):
        Thread.__init__(self, daemon=False)
        self.serverHost, self.serverPort, self.debug = serverHost, serverPort, debug
        self.start()
    def run(self):
        s = None
        for res in socket.getaddrinfo(serverHost, serverPort, socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                print("creating sock: af=%d, type=%d, proto=%d" % (af, socktype, proto))
                s = socket.socket(af, socktype, proto)
            except socket.error as msg:
                print(" error: %s" % msg)
                s = None
                continue
            try:
                print(" attempting to connect to %s" % repr(sa))
                s.connect(sa)
            except socket.error as msg:
                print(" error: %s" % msg)
                s.close()
                s = None
                continue
            break

        if s is None:
            print('could not open socket')
            sys.exit(1)

        fs = FramedStreamSock(s, debug=debug)
        
        inputStr = input("Input your file's name: ")
        #If file does not exist it will keep prompting the user to send the name of an existing file
        while not os.path.exists(inputStr):
            print("Invalid File, Try Again")
            inputStr = input("Input your file's name: ")

        inFile = open(inputStr, 'rb')

        #Try catch block to handle errors while reading the file
        try:
            #File's name is sent first to create file on server side
            print("sending name: " + inputStr)
            fs.sendmsg(bytes(inputStr.rstrip("\n\r"), encoding='ascii'))
            print("received:", fs.receivemsg())
                
            #For every line in the file the client will send a message containing that line
            print("Sending...\n")
            l = inFile.read(100)
            while (l):
                print("sending: ")
                fs.sendmsg(l)
                print("received:", fs.receivemsg())
                time.sleep(0.001)
                l = inFile.read(100)
            
        except Exception as e:
            print(e)
            print("Error reading file")
            
for i in range(2):
    ClientThread(serverHost, serverPort, debug)

