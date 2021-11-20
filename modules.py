def getType(string):
    if string == "ico":
        return "image/x-icon"
    elif string == "js":
        return "text/javascript"

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
    