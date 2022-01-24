"""
Module for managing HTML functions and classes
"""
from dataclasses import dataclass, field
import logging
import sys
from typing import Union
import urllib.parse

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
    """Class for a general Packet

    Headers: dict = dict
    Payload: str = ""
    command: str = ""
    filename: str = ""
    overflow: str = ""
    status: str = ""
    bytePayload: bytes = b""
    """
    Headers: dict = field(default_factory=dict)
    Payload: str = ""
    command: str = ""
    filename: str = ""
    overflow: str = ""
    status: str = "200 OK"
    attr: dict = field(default_factory=dict)
    bytePayload: bytes = b''
    
    
    def toBytes(self) -> bytes:
        packetString = ""
        if self.command != "":
            packetString += f"{self.command} {self.filename} "
        packetString = f"HTTP/1.1"
        if self.status != "":
            packetString += f" {self.status}"
        
        for header in self.Headers:
            packetString += "\r\n" + header + ": " + str(self.Headers[header])
        
        packetString += "\r\n\r\n"
        if self.bytePayload != b"":
            packetString = packetString.encode()
            packetString += self.bytePayload
        else:
            packetString += self.Payload
            packetString = packetString.encode()
        return packetString
    
    def __str__(self):
        bytesObj = self.toBytes()
        try:
            return bytesObj.decode()
        except Exception as e:
            return e + "\n" + str(bytesObj)
    
    
class GeneralClient:
    def __init__(self, clientSocket, addr):
        global typeDict
        self.socket = clientSocket
        self.addr = addr
        typeDict = {"html": "text/html",
                    "ico": "image/x-icon",
                    "js": "text/javascript",
                    "css": "text/css",
                    "json": "text/json"
                    }
    
    
    def SendPacket(self, packet: Packet):
        byteString = packet.toBytes()
        self.socket.send(byteString)
        return byteString

    @staticmethod
    def getType(string):
        return typeDict[string]

    def FileResponsePacket(self, filePath):
        with open(filePath, 'rb') as FILE:
            fileData = FILE.read()
        fileType = self.getType(filePath.split('.')[-1])
        resp = Packet()
        resp.status = "200 OK"
        resp.Headers["Content-Length"] = len(fileData)
        resp.Headers["Content-Type"] = fileType
        resp.bytePayload = fileData
        return resp

    def FileNotFoundMsgPacket(self, filePath):
        with open('errors/404.html', 'rb') as FILE:
            FileNotFoundData = FILE.read()
        resp = Packet()
        resp.status = "404"
        resp.Headers['Content-Length'] = len(FileNotFoundData)
        resp.Headers["Content-Type"] = "error"
        resp.bytePayload = FileNotFoundData
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
        msgPayload = msgHeaderPayloadList[1]
    
    commandLine = msgHeaderString[0]
    
    HeaderNamesAndAttr = [Header.split(": ") for Header in msgHeaderString[1:]]
    msgHeader = {h[0]: h[1] for h in HeaderNamesAndAttr[1:]}
    
    commandLine = urllib.parse.unquote(commandLine)
    resp =  commandLine.split()
    command, file, overflow, attr, status = None, None, None, {}, ""
    if len(resp) >= 1:
        command = resp[0]
        if len(resp) >= 2:
            if "?" in resp[1]:
                file, attrStr = resp[1].split("?")
                for eq in attrStr.split("&"):
                    var, val = eq.split("=")
                    attr[var] = val
            else:
                file = resp[1]
            overflow = resp[2:]
    
    return Packet(msgHeader, msgPayload, command, file, overflow, status=status, attr=attr)
