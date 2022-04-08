port = 443

# import global variables
from config import *

import socket, threading, ssl
from pprint import pprint, pformat
import modules as HTTP
from modules import colorText
from os.path import join
import os, sys
import json, random
import traceback, hashlib, time
import multiprocessing as mp
import xml.etree.ElementTree as ET
ET.register_namespace('', "http://www.w3.org/2000/svg")
    
class InvalidLoginAttempt(Exception):
    # ! Do not insert sensitive information in the exception message
    def __init__(self, msg: str):
        super().__init__(f"Invalid Login Attempt:\n{msg}")


class Client(HTTP.GeneralClient):
    def __init__(self, *args, UpdatePipe):
        super().__init__(*args)
        self.thread = threading.Thread(target=self.manage)
        self.UpdatePipe = UpdatePipe

    @staticmethod
    def getUserAuth(packet):
        if 'Cookie' in packet.Headers and 'user_auth' in packet.Headers['Cookie']:
            cookiesStr = [i.split("=") for i in packet.Headers['Cookie'].split(";")]
            cookies = {cookieStr[0]: cookieStr[1] for cookieStr in cookiesStr}
            username, password = tuple(json.loads(cookies['user_auth']).values())
        else:
            return None, None
            
        if "'" not in username and "'" not in password:
            return username, password
        else:
            raise InvalidLoginAttempt("Username or password contains invalid characters: '")
    
    def postResponse(self, packet: HTTP.Packet):
        file = packet.filename
        resp = None
        if file == "/SIGNUP":
            resp = self.SignUp(packet.Payload)
        elif file.startswith('/SAVENEWNB'):
            resp = self.NewNotebook(packet)
        elif file.startswith('/SAVE/'):
            resp = self.SaveNotebook(packet, file)
        elif file.startswith('/api/'):
            resp = self.APIPostResponse(packet)
        else:
            # TODO Add error response
            ...
        
        resp = json.dumps(resp)
        respPacket = HTTP.Packet()
        respPacket.Headers['Content-Type'] = "text/json"
        respPacket.setPayload(resp)
        self.SendPacket(respPacket)
        logger.debug(f"Sent response packet: {resp}") 

    # TODO: Add closing of a client using the open notebooks
    def close(self):
        ...

    @staticmethod
    def SavePrivateNotebook(user_auth, notebookID, changes):
        
        resp = SQL.DataQuery(*user_auth, "id", 'NotebookPath', 'currentGroupID', table="notebooks", userIDString='ownerID', where=f"id={notebookID}", singleton=True, returnUserID=True)
        
        id = resp['UserID']
        logger.info(f"User {id} is saving notebook {notebookID}...")
        
        if resp['code'] == 1:
            errMsg = f"User {id} doesn't own notebook {notebookID}"
            logger.error(errMsg)
            return {'code': 1, 'data': errMsg}
        elif resp['code'] == 0:
            groupID = int(resp['data']['currentGroupID'])
            for i, change in enumerate(changes):
                Notebook.ChangeNotebook(resp['data']['NotebookPath'], groupID, change, SQL)
                
            logger.info(f"Succesfully saved user {id}'s notebook {notebookID}")
        return {'code': 0, 'data': "Changes saved"}

    def SavePublicNotebook(self, notebookCode, changes):
        resp = SQL.Request('id', 'notebookPath', table="notebooks", where="code='%s'" % notebookCode, singleton=True)

        if len(resp) == 0:
            return {'code': 1, 'data': "Unknown notebook code"}
        else:
            self.UpdatePipe.send((*list(resp.values()), changes))
            return {'code': 0, 'data': "Changes saved"}

    def SaveNotebook(self, packet: HTTP.Packet, file: str = "") -> dict:
        user_auth = self.getUserAuth(packet)

        notebookCode = ""
        if 'nb' in packet.attr:
            notebookCode = packet.attr['nb']
        
        changes = json.loads(packet.Payload)
        if notebookCode == "":
            notebookID = file[6:]
            resp = self.SavePrivateNotebook(user_auth, notebookID, changes)
            return resp
        else:
            logger.debug(f"User {user_auth[0]} is saving public notebook {notebookCode}...")
            resp = self.SavePublicNotebook(notebookCode, changes)
            return resp

    def NewNotebook(self, packet: HTTP.Packet):
        user_auth = self.getUserAuth(packet)
        id = SQL.CheckAuth(*user_auth)
        
        if id != None:
            payloadDict = json.loads(packet.Payload)
            svgData = payloadDict['svgData']
            payloadDict.pop('svgData', None)
            payloadDict['ownerID'] = id
            
            try:
                insertResp = SQL.Insert('notebooks', **payloadDict)
                
                if insertResp['code'] != 0:
                    return insertResp
                
            except KeyError as e:
                logger.error("User request doesn't have enough data:")
                logger.error(e)
                return {'code': 1, 'data': f'Missing key: {e}'}
                
            notebookID = insertResp['inserted_id']
            
            # Create svg file:
            newPath = f'Protected/Notebooks/{notebookID}.svg'
            with open(newPath, 'w') as FILE:
                svgData = '<?xml version ="1.0"?>\n' + svgData
                FILE.write(svgData)
            
            # Update file path to DB
            updateResp = SQL.Update(table="notebooks", where=f'id={notebookID}', NotebookPath=newPath)

            if updateResp['code'] == 0:
                return SQL.DataQuery(*user_auth, "id", table="notebooks", userIDString="ownerID", singleton=True)
            else:
                return updateResp
        else:
            return {'code': 1, 'data': 'Authorization denied!'}
    
    def SignUp(self, payload: str):
        payloadDict = json.loads(payload)
        attemptUsername = payloadDict['username']
        attemptPassword = payloadDict['password']
        
        SQL.cursor.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE username='{attemptUsername}')")
        resp = SQL.cursor.fetchall()
        
        if resp[0][0] == 1:
            return {"code": 1, "description": "Username already exists!"}
        
        
        SQL.cursor.execute(f"INSERT INTO users (username, pass) VALUES ('{attemptUsername}', '{attemptPassword}')")
        SQL.mydb.commit()
        
        return {"code": 0, "description": "Signed Up successfuly"}
    
    def RequestData(self, packet: HTTP.Packet, *attr: tuple[str], table="", userIDString="id", where: str=None, **kwargs):
        """Request user's private data from the database.

        Args:
            packet (HTTP.Packet): the packet that contains the user's credentials.
            table (str, optional): the table from which to request the data. Defaults to "".
            userIDString (str, optional): the string which represents the owner id in the relevent table. Defaults to "id".
            where (str | None, optional): additional where sql commands. Defaults to None.

        Returns:
            dict: dictionary containing the error code and data 
            e.g: {'code': 0, 'data': somedata}.
        """
        try:
            user_auth = self.getUserAuth(packet)
            resp = SQL.DataQuery(*user_auth,  *attr, table=table, userIDString=userIDString, where=where, **kwargs)
        except KeyError as e:
            resp = {"code": 1, "data": "No cookie was sent"}

        return resp
    
    def LoginAttempt(self, packet, includePayload=True):
        # TODO: Make use of the "id" request
        try:
            resp = self.RequestData(packet, "id", table="users", userIDString="id")
            resp = json.dumps(resp)
            respPacket = HTTP.Packet()
            respPacket.Headers['Content-Type'] = "text/json"
            
            if includePayload:
                respPacket.setPayload(resp)
            else:
                respPacket.Headers['Content-Length'] = len(resp)
                
            self.SendPacket(respPacket)
            logger.debug(f"Sent login response packet: {resp}")
        except Exception as e:
            raise e
        
    def PublicResponse(self, file, includePayload=True):
        if file == '/':
            file = "/index.html"

        if not file.startswith('/node_modules'):
            filePath = "public/" + file
        else:
            filePath = file[1:]

        fileRespPacket = self.FileResponsePacket(filePath, includePayload=includePayload)
        sentBytes = self.SendPacket(fileRespPacket)
        
        msg = f"Sent {filePath} to {self.addr}"
        
        if not includePayload:
            if silentLog:
                return
            else:
                msg += " without payload"
        logger.info(msg)

    def SendNotebookList(self, packet, includePayload=True):
        notebookList = self.RequestData(packet, "id", "ownerID", "title", "description", table="notebooks", userIDString="ownerID")
                
        nbListPacket = HTTP.Packet(json.dumps(notebookList, indent=4), includePayload=includePayload)
        
        self.SendPacket(nbListPacket)
    
    def SendNotebook(self, packet, includePayload=True):
        isPublicNB = 'nb' in packet.attr
        
        if not isPublicNB:
            notebookID = packet.filename[10:]
                
            nbdatadict = self.RequestData(packet, "NotebookPath", "title", "currentGroupID", table="notebooks", userIDString="ownerID", where=f"id={notebookID}", singleton=True)
            
        else:
            code = packet.attr['nb']
            sqlReqResp = SQL.Request("NotebookPath", "title", 'id', "currentGroupID", table="notebooks", where=f"code='{code}'", singleton=True)
            nbdatadict = {'code': 0, 'data': sqlReqResp}

            notebookID = sqlReqResp['id']
        
        if 'code' in nbdatadict and nbdatadict['code'] == 0:
            filePath = nbdatadict['data'].pop('NotebookPath', None)
            with open(filePath) as FILE:
                nbdatadict['data']["NotebookData"] = FILE.read()

        nbdataPacket = HTTP.Packet(nbdatadict, includePayload=includePayload, dataType='text/json')
        self.SendPacket(nbdataPacket)
        logger.info(f'Sent notebook {notebookID} to {self.addr} with groupid: {nbdatadict["data"]["currentGroupID"]}')
    
    def APIPostResponse(self, APIpacket):
        notebookID = APIpacket.Payload
        authResp = self.RequestData(APIpacket, "code", table='notebooks', userIDString='ownerID', where=f"id={notebookID}", singleton=True)
        if authResp['code'] == 0:
            resp = self.UpdateNotebookCode(notebookID)
        return resp

    def getResponseManage(self, packet: HTTP.Packet, includePayload=True):
        try:
            file = packet.filename
            if file == "/LOGIN":
                self.LoginAttempt(packet, includePayload=includePayload)
            elif file.startswith("/NotebookList"):
                self.SendNotebookList(packet, includePayload=includePayload)
            elif file.startswith("/Notebook"):
                self.SendNotebook(packet, includePayload=includePayload)
            elif file.startswith('/api/'):
                apiRequest = file[5:]
                self.APIGetResponse(packet, apiRequest)
            else: # If file is public
                self.PublicResponse(file, includePayload=includePayload)
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                logger.error(f"404:\n{e}")
                errorPacket = self.FileNotFoundMsgPacket(str(e).split()[-1][1:-1])
                self.SendPacket(errorPacket)
            elif isinstance(e, ConnectionAbortedError):
                logger.debug(f"{self.addr} Aborted Connection")
            elif isinstance(e, SQLException):
                logger.error(f"SQL Error:\n{e}\n{traceback.format_exc()}")
                errorPacket = HTTP.Packet(json.dumps({"code": 1, "data": "Internal Server Error"}), status="500")
            elif isinstance(e, InvalidLoginAttempt):
                logger.error(f"{e}")
                errorPacket = HTTP.Packet({"code": 1, "data": f"invalid login attempt, {str(e)}"}, status="400")
            else:
                logger.error(f"{e}\n{traceback.format_exc()}")
                errorPacket = HTTP.Packet(f"Unknown Error: {e}", status="520")
            
            self.SendPacket(errorPacket)
    
    def getResponse(self, packet):
        self.getResponseManage(packet)
        
    def headResponse(self, packet):
        self.getResponseManage(packet, includePayload=False)
    
    def APIGetResponse(self, APIpacket: HTTP.Packet, apiUrl: str) :
        if apiUrl == "notebook/code":
            notebookID =  APIpacket.attr['nbID']
            # Verify the opener is the owner of the notebook
            authResp = self.RequestData(APIpacket, "code", table='notebooks', userIDString='ownerID', where=f"id={notebookID}", singleton=True)
            if authResp['code'] == 1:
                apiRespPacket = HTTP.Packet("Invalid credentials", filename=apiUrl, status="403")
            else:
                currentCode = authResp['data']['code']
                apiRespPacket = HTTP.Packet({'code': currentCode}, filename=apiUrl, dataType='text/json')
                
        
        self.SendPacket(apiRespPacket)

    def UpdateNotebookCode(self, notebookID):
        code = GenerateNotebookCode()
        updateResp = SQL.Update(table="notebooks", where=f"id={notebookID}", code=code)
        return {"code": code}

    def parseHttpPacket(self, packetByteData: bytes):
        packetStr = packetByteData.decode()
        packet = HTTP.extractDataFromPacket(packetStr)
        if packet.command == "POST":
            while len(packet.Payload) < int(packet.Headers['Content-Length']):
                # Since the length is already set there is no need to use .setPayload
                packet.Payload += self.Recieve().decode()
            
        return packet
    
    def manage(self):
        # Define all actions
        Actions = {"GET": self.getResponse, "POST": self.postResponse, "HEAD": self.headResponse}
        
        while True:
            try:
                packetByteData = self.Recieve()
                if packetByteData == b'':
                    logger.info(f'Recieved empty packet from {self.addr}. closing connection')
                    try:
                        self.stream.send(b'\r\n')
                        self.stream.close()
                    except Exception:
                        pass
                    break

                packet = self.parseHttpPacket(packetByteData)
                
                
                command = packet.command
                if command != None:
                    if command in Actions:
                        Actions[command](packet)
                        if packet.getHeader('Connection') != 'keep-alive':
                            self.stream.close()
                            break
                    else:
                        logger.error(f"command {command} is not supported!")
                else:
                    # print(packetStr)
                    ...
            except:
                try: 
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    
                    raise
                # except SQL.connector.Error as e:
                #     logger.error(f"sql line from {self.addr} was: {SQL.cursor.statement} ")
                except ConnectionAbortedError as e:
                    logger.error(f"connection aborted with {self.addr}!")
                    self.stream.close()
                    return 1
                except HTTP.ParsingError as e:
                    logger.error(f"{e}")

                except Exception as e:
                    eText = f"{self.addr}\n=========================\n\n\t" + traceback.format_exc().replace('\n', '\n\t') + f"\n----------------------\n\t{exc_obj}\n========================="
                    logger.error(eText)
                    # ! Generally dont need this, but it is here for debugging
                    # logger.debug("\n->->->->->->->->->->\n" + pformat(packetByteData) + '\n->->->->->->->->->->\n')          
            ...
                    
    def start(self):
        self.thread.start()

    def __str__(self):
        return f"{self.addr}"

class Notebook:
    def __init__(self, id: str, path: str, SQL: SQLClass) -> None:
        self.id = id
        self.path = path
        self.Queue = mp.Queue()
        self.UpdateThread = None
        self.SQL = SQL
    
    def addChanges(self, change: tuple):
        self.Queue.put(change)

    def UpdateNotebook(self):
        while True:
            if not self.Queue.empty():
                change = self.Queue.get()
                if change == "stop":
                    return
                sqlResp = self.SQL.Request("currentGroupID", table="notebooks", where=f"id={self.id}", singleton=True)
                currentGroupNumber = sqlResp['currentGroupID']
                self.ChangeNotebook(self.path, currentGroupNumber, change, self.SQL)

    ns = "{http://www.w3.org/2000/svg}"

    # TODO: Update notebooks using the xml package 
    @staticmethod
    def ChangeNotebook(path: str, currentGroupID: int, change: tuple, SQL: SQLClass):
        changeCMD = change[0]
        changeData = change[1]
        tree = ET.parse(path)
        root = tree.getroot()
        if changeCMD == 'a':
            newElement = ET.fromstring(changeData)
            root.append(newElement)
            currentGroupID += 1
            newElement.set('id', str(currentGroupID))
            SQL.Update('notebooks', 'NotebookPath=\'%s\'' % path, currentGroupID=currentGroupID)
        elif changeCMD == 'e':
            id = changeData['id']
            t = changeData['type']
            group = root.find(f".//{Notebook.ns + t}[@id='{id}']")
            if group != None: 
                root.remove(group)
        
        tree.write(path)

    def start(self):
        self.UpdateThread = threading.Thread(target=self.UpdateNotebook)
        self.UpdateThread.start()

def CodeEncryptionKey() -> str:
    key = 0
    while True:
        yield bytes(key) + str(time.time()).encode()
        key += 1

def GenerateNotebookCode() -> str:
    keys = CodeEncryptionKey()
    code = hashlib.md5(next(keys)).hexdigest()
    return code


def UpdateOpenNotebooksLoop(child_conn):
    # Main function for the update process
    OpenNotebooks = {}
    changesList = []

    # Connect to database
    logger.info("Connecting to database from update process")
    updateNBSQL = SQLClass()
    logger.info("Connected to database from update process")

    while True:
        try:
            changesList.append(child_conn.recv())

            for NotebookID, NotebookPath, NBchanges in changesList:
                if NotebookID not in OpenNotebooks:
                    newNotebook = Notebook(NotebookID, NotebookPath, updateNBSQL)
                    newNotebook.start()
                    for change in NBchanges:
                        newNotebook.addChanges(change)
                    OpenNotebooks[NotebookID] = newNotebook
                else:
                    for change in NBchanges:
                        OpenNotebooks[NotebookID].addChanges(change)

        except Exception as e:
            logger.error(e, exc_info=True)
        

if __name__ == "__main__":
    # Load SQL
    logger.info("Initializing Database from main thread...")
    SQL = SQLClass()
    SQL.initMainSQL()
    logger.info("Database initialized")

    def exitFunc(*args):
        SQL.exitHandler()
        os._exit(0)

    def removeUser(username):
        SQL.Remove('users', username)

    def removeNotebook(notebookID):
        SQL.Remove('notebooks', notebookID)

    def Remove(*args):
        if len(args) == 0:
            logger.warning("Did not recieve arguments!")
        elif len(args) == 1:
            removeUser(args[0])
        elif args[0] == "ID":
            removeNotebook(args[1])
        else:
            logger.warning("No such command: ")

    def toggleSilentHeaderLog():
        global silentLog
        silentLog = not silentLog

    def printClientList():
        logger.debug(f"Client List:\n{pformat(clients)}")

    actions = {"exit": exitFunc, "remove": Remove, "save": SQL.saveDBToJson, "silent": toggleSilentHeaderLog, "clients": printClientList}

    # Start console:
    def console():
        while True:
            try:
                cmdtxt = input()
            except EOFError as e:
                exitFunc()
                
            cmd, *args = cmdtxt.split()
            logger.info(f"Executing Server Command: {cmd}")
            try:
                actions[cmd](*args)
            except KeyError as e:
                logger.warning(f"No Such Command: {cmd}")

    consoleThread = threading.Thread(target=console)
    consoleThread.start()

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="https/cert.pem", keyfile="https/key.pem")

    bindSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ADDR = ('', port)
    bindSocket.bind(ADDR)
    bindSocket.listen()
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    child_conn, parent_conn = mp.Pipe()
    UpdateNotebook = mp.Process(target=UpdateOpenNotebooksLoop, args=(child_conn, ))
    UpdateNotebook.start()
    logger.info(f"[INIT] Server running on {local_ip, port, hostname = }")


    # ! Send SQL Module with the its global variables
    # parent_conn.send(SQL)

    clients = []
    while True:
        clientSocket, addr = bindSocket.accept()
        try:
            connStream = context.wrap_socket(clientSocket, server_side=True)
            myClient = Client(connStream, addr, UpdatePipe=parent_conn)
            clients.append(myClient)
            myClient.start()
        except ssl.SSLError as e:
            if isinstance(e, ssl.AlertDescription):
                logger.warning(e)
        except Exception as e:
            logger.error(f"{e}\n{traceback.format_exc()}\n\nClosing client {addr}")
            clientSocket.close()


    # clientSocket.settimeout(10*60)
