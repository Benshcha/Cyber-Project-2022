"""
Module for managing HTML functions and classes
"""
from dataclasses import dataclass
import logging
import sys

class myLogger(logging.Logger):
    def __init__(self, name: str, level:str = ...) -> None:
        super().__init__(name)
        self.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', 
                                    '%m-%d-%Y %H:%M:%S')

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.setFormatter(formatter)

        file_handler = logging.FileHandler('logs/logs.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        self.addHandler(file_handler)
        self.addHandler(stdout_handler)      

@dataclass
class Packet:
    Headers: dict
    Payload: str
    command: str
    filename: str
    overflow: str

def getType(string):
    if string == "ico":
        return "image/x-icon"
    elif string == "js":
        return "text/javascript"
    elif string == "css":
        return "text/css"

def FileResponse(filePath):
    with open(filePath, 'rb') as FILE:
        fileData = FILE.read()
    fileType = getType(filePath.split('.')[-1])
    resp = "HTTP/1.1 200 OK\r\n"
    resp += f"Content-Length: {len(fileData)}\r\n"
    resp += f"Content-Type: {fileType}\r\n\r\n"
    resp = resp.encode()
    resp += fileData
    return resp

def FileNotFoundMsg(filePath):
    with open('errors/404.html', 'rb') as FILE:
        FileNotFoundData = FILE.read()
    resp = "HTTP/1.1 404\r\n"
    resp += f"Content-Length: {len(FileNotFoundData)}\r\n"
    resp += f"Content-Type: error\r\n\r\n"
    resp = resp.encode()
    resp += FileNotFoundData
    return resp 

def extractDataFromPacket(packet: str) -> Packet:
    """
    # Convert string to packet data
    
    ## Args:
    
        packet (str): the packet as a string
        
    ## Returns:
    
        **msgHeader**: dict = a dictionary of all the headers and their values
        **msgPayload**: str = the payload of the packet as a string
        **command**: str = the command of the payload if exists
        **file**: str = the file path refered to in the first line
        **overflow**: list = a list of overflow objects in the first line
    """
    
    msgHeaderPayloadList = packet.split("\r\n\r\n")
    msgHeaderString = msgHeaderPayloadList[0].split("\r\n")
    
    msgPayload = None
    if len(msgHeaderPayloadList) > 1:
        msgPayload = msgHeaderPayloadList[1].split("\r\n")
    
    commandLine = msgHeaderString[0]
    
    HeaderNamesAndAttr = [Header.split(": ") for Header in msgHeaderString[1:]]
    msgHeader = {h[0]: h[1] for h in HeaderNamesAndAttr[1:]}
    
    resp =  commandLine.split()
    command, file, overflow = None, None, None
    if len(resp) >= 1:
        command = resp[0]
        if len(resp) >= 2:
            file = resp[1]
            overflow = resp[2:]
    
    return Packet(msgHeader, msgPayload, command, file, overflow)