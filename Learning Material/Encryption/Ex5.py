# %%

import hashlib
from Crypto.Cipher import AES
from Crypto.Util import Counter

def EncryptFile(filename, key):
    with open(filename, 'rb') as file:
        data = file.read()
    encrypted = EncryptCTR(data, key)
    with open(".".join(filename.split('.')[:-1]) + '.enc', 'wb') as file:
        file.write(encrypted)

def EncryptCTR(data:bytes, key:bytes):
    mode = AES.MODE_CTR
    cipher = AES.new(key, mode, counter=Counter.new(128))
    encryptedMSG = cipher.encrypt(data)
    return encryptedMSG

def DecryptCTR(cipherText, key):
    mode = AES.MODE_CTR
    cipher = AES.new(key, mode, counter=Counter.new(128))
    decryptedMSG = cipher.decrypt(cipherText)
    return decryptedMSG

def DecryptFile(EncryptedFile, key):
    with open(EncryptedFile, 'rb') as file:
        data = file.read()
    decrypted = DecryptCTR(data, key)
    with open(".".join(EncryptedFile.split('.')[:-1]) + 'dec.jpg', 'wb') as file:
        file.write(decrypted)

# %%
if __name__ == "__main__":
    key = hashlib.sha256(b'YELLOW SUBMARINE').digest()
    EncryptFile('Secret Message.jpg', key)


# %% [markdown]
# # 1 + 2

# %%

if __name__ == "__main__":
    DecryptFile('Secret Message.enc', key)

# %% [markdown]
# # 3

# In the file "Ex5_Server.py, Ex5_Client.py"

# %%

def RecievePacket(sock) -> bytes:
    bufferSize = 4086
    add = b""
    data = b""
    while True:
        add = sock.recv(bufferSize)
        data += add
        if len(add) < bufferSize:
            break
    return data

# %%

def generatePrimeNumbers(n):
    primes = []
    i = 2
    while len(primes) < n:
        isPrime = True
        for j in primes:
            if i%j == 0:
                isPrime = False
                break
        if isPrime:
            primes.append(i)
        i += 1
    return primes

def GCD(a, b):
    while b != 0:
        a, b = b, a % b
    return a

import numpy as np
primes = generatePrimeNumbers(1000)


def modInverse(e, phi):
    while True:
        k = np.random.randint(1, 200)
        d = pow(e, -1, phi) + k * phi
        
        if d%1 == 0:
            return int(d)


def generateKeys():
    while True:
        p, q = np.random.choice(primes, 2)
        p = int(p)
        q = int(q)
        if p != q and int(np.log10(p)) == int(np.log10(q)):

            break
    n = p * q
    phi = (p - 1) * (q - 1)
    while True:
        e = int(np.random.choice(range(2, phi), 1)[0])
        if GCD(e, phi) == 1 and GCD(e, n) == 1:
            break

    d = modInverse(e, phi)

    return e, d, n
