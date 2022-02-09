from Crypto.Cipher import AES
from Crypto.Util import Counter
import hashlib


def pad_message(msg):
    while len(msg) % 16 != 0:
        msg = msg + b'0'
    return msg


def encrypt(plain_text):
    password = "1234".encode()
    key = hashlib.sha256(password).digest()
    mode = AES.MODE_CBC
    IV = '0123456789ABCDEF'.encode()  # should be 16 bytes
    cipher = AES.new(key, mode, IV)
    # cipher = AES.new(key, mode, counter=Counter.new(128))
    padded_message = pad_message(plain_text.encode())
    encryped_message = cipher.encrypt(padded_message)
    return encryped_message


def decrypet(cipher_text):
    password = "1234".encode()
    key = hashlib.sha256(password).digest()
    mode = AES.MODE_CBC
    IV = '0123456789ABCDEF'.encode()  # should be 16 bytes
    cipher = AES.new(key, mode, IV)
    # cipher = AES.new(key, mode, counter=Counter.new(128))
    decrypted_text = cipher.decrypt(cipher_text)
    return decrypted_text.rstrip(b'0')


def file_encrypt(fileName):
    password = "1234".encode()
    key = hashlib.sha256(password).digest()
    mode = AES.MODE_CBC
    IV = '0123456789ABCDEF'.encode()  # should be 16 bytes

    cipher = AES.new(key, mode, IV)

    with open(fileName, 'rb') as f:
        file_text = f.read()

    padded_file = pad_message(file_text)
    enc_data = cipher.encrypt(padded_file)

    with open('dogEnc.jpg', 'wb') as e:
        e.write(enc_data)


def file_decrypt(enc_file):
    password = "1234".encode()
    key = hashlib.sha256(password).digest()
    mode = AES.MODE_CBC
    IV = '0123456789ABCDEF'.encode()  # should be 16 bytes
    cipher = AES.new(key, mode, IV)

    with open(enc_file, 'rb') as e:
        enc_data = e.read()

    dec_file_data = cipher.decrypt(enc_data)
    dec_file_data.rstrip(b'0')
    with open('dogDec.jpg', 'wb') as f:
        f.write(dec_file_data)


if __name__ == '__main__':
    text_message = 'this is my first message to encrypet with AES'
    print(f'orginal message \n{text_message}')
    cipherText = encrypt(text_message)
    print('Encrypted message')
    print(cipherText)
    back_to_text = decrypet(cipherText).decode()
    print('Decoded message')
    print(back_to_text)
    # file_encrypt('dog.jpg')
    # file_decrypt('dogEnc.jpg')

