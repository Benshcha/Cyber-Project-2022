"""
Module for managing HTML functions and classes
"""
from dataclasses import dataclass, field
import logging
import sys, json, os
from typing import Union, Any
import urllib.parse
from xml.etree.ElementInclude import include

# create a color dictionary for console text
colorDict = {
    'red': '\033[91m',
    'blue': '\033[94m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'white': '\033[0m',
    'cyan': '\033[96m',
    'bold': '\033[1m',
    'underline': '\033[4m',
    'end': '\033[0m'
}

# Color text according to the color dictionary
def colorText(text: str, color: str) -> str:
    """
    # Color text according to the color dictionary
    
    ## Args:
    
        text (str): the text to color
        color (str): the color to use
    
    ## Returns:
    
        **text**: str = the text colored according to the color dictionary
    """
    return colorDict[color] + text + colorDict['end']

LevelColor = {"INFO": "cyan", "WARNING": "yellow", "ERROR": "red", "DEBUG": 'green'}
def ColorLevel(text):
    return  colorText(text, LevelColor[text.upper()])


class LoggerFormatter(logging.Formatter):
    def __init__(self, *args, use_color=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_color = use_color

    def format(self, record):
        levelName = record.levelname
        if self.use_color and levelName in LevelColor:
            record.levelname = ColorLevel(levelName)

        return logging.Formatter.format(self, record)

class myLogger(logging.Logger):
    def __init__(self, name: str, level:str = ...) -> None:
        super().__init__(name)
        self.setLevel(logging.DEBUG)
        formatter = LoggerFormatter('%(asctime)s | %(levelname)s | %(message)s', 
                                    '%m-%d-%Y %H:%M:%S', use_color=True, style="%")

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.setFormatter(formatter)

        file_handler = logging.FileHandler('logs/logs.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        self.addHandler(file_handler)
        self.addHandler(stdout_handler)  
   
class Packet:
    """Class for a general Packet

    Headers: dict = dict
    Payload: Any Stringable = ""
    command: str = ""
    filename: str = ""
    overflow: str = ""
    status: str = ""
    bytePayload: bytes = b""
    """
    
    def __init__(self, Payload: str = "", Headers: dict = {}, command: str = "", filename: str = "", overflow: str = "", status: str = "200 OK", attr: dict = {}, bytePayload: bytes = b'', includePayload: bool=True, dataType: str = ...) -> None:
        self.Headers = Headers
        self.command = command
        self.filename = filename
        self.overflow = overflow
        self.status = status
        self.attr = attr
        self.bytePayload = bytePayload
        self.dataType = dataType
        
        if includePayload:
            if not isinstance(Payload, str):
                if isinstance(Payload, dict):
                    self.Payload = json.dumps(Payload)
                else:
                    self.Payload = str(Payload)
            else:
                self.Payload = Payload            
        else:
            self.Payload = ""
            
        if self.Payload != None and self.Payload != "":
            self.Headers['Content-Length'] = len(self.Payload)

        try:
            if self.dataType == ...:
                self.dataType = self.filename.split(".")[-1]

            self.Headers['Content-Type'] = self.dataType
        except AttributeError:
            pass

    def getHeader(self, header:str) -> Any:
        if header in self.Headers:
            return self.Headers[header]
        return None
            
    def toBytes(self) -> bytes:
        packetString = ""
        if self.command != "":
            packetString += f"{self.command} {self.filename} "
        packetString += f"HTTP/1.1 {self.status}"
        
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
    
    def setPayload(self, payload):
        self.Payload = payload
        self.Headers['Content-Length'] = len(payload)
    
    def __str__(self):
        bytesObj = self.toBytes()
        try:
            return bytesObj.decode()
        except Exception as e:
            return e + "\n" + str(bytesObj)   
    
typeDict = {"html": "text/html",
            "ico": "image/x-icon",
            "js": "text/javascript",
            "css": "text/css",
            "json": "text/json"
            }  
class GeneralClient:
    
    def __init__(self, clientStream, addr: tuple[str]) -> None:
        global typeDict
        self.stream = clientStream
        self.addr = addr
    
    def SendPacket(self, packet: Packet):
        byteString = packet.toBytes()
        self.stream.send(byteString)
        return byteString

    @staticmethod
    def getType(string):
        if string in typeDict:
            return typeDict[string]
        else:
            return string

    def FileResponsePacket(self, filePath, includePayload=True):
        with open(filePath, 'rb') as FILE:
            fileData = FILE.read()
        fileType = self.getType(filePath.split('.')[-1])
        resp = Packet()
        resp.status = "200 OK"
        resp.Headers["Content-Length"] = len(fileData)
        resp.Headers["Content-Type"] = fileType
        if includePayload:
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
    
    def Recieve(self) -> bytes:
        bufSize = 4096
        data = b''
        while True:
            try:
                part = self.stream.recv(bufSize)
                data += part
                
                if len(part) < bufSize:
                    break
            except Exception as e:
                raise(e)
            
        return data
    
class ParsingError(Exception):
    def __init__(self, e: Exception) -> None:
        super().__init__(e)

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
    try:
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
        
        return Packet(msgPayload, msgHeader, command, file, overflow, status=status, attr=attr)
    except Exception as e:
        raise ParsingError(e)

