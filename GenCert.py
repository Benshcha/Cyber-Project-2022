import socket
import random, ssl
from OpenSSL import crypto
import random
from OpenSSL import crypto
import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import NameOID
import socket


def _gen_openssl(rootIssuer=None, commonName=socket.gethostname(), cakey=None):
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, 2048)

    x509 = crypto.X509()
    subject = x509.get_subject()
    subject.commonName = commonName
    if rootIssuer != None:
        x509.set_issuer(rootIssuer)
    else:
        x509.set_issuer(subject)
    x509.gmtime_adj_notBefore(0)
    x509.gmtime_adj_notAfter(5*365*24*60*60)
    x509.set_pubkey(pkey)
    x509.set_serial_number(random.randrange(100000))
    x509.set_version(2)
    if cakey == None:
        CA = 'CA:true'
    else:
        CA = 'CA:false'
    x509.add_extensions([
        crypto.X509Extension(b'subjectAltName', False,
            ','.join([
                'DNS:%s' % socket.gethostname(),
                'DNS:*.%s' % socket.gethostname(),
                'DNS:localhost',
                'DNS:*.localhost']).encode()),
        crypto.X509Extension(b"basicConstraints", True, CA.encode())])

    if cakey != None:
        x509.sign(cakey, 'SHA256')
    else:
        x509.sign(pkey, 'SHA256')

    return (crypto.dump_certificate(crypto.FILETYPE_PEM, x509),
        crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))

def _gen_cryptography(issuer, subject, cakey=None):
    one_day = datetime.timedelta(1, 0, 0)
    private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend())
    public_key = private_key.public_key()




    builder = x509.CertificateBuilder()
    builder = builder.subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject)]))
    builder = builder.issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, issuer)]))
    builder = builder.not_valid_before(datetime.datetime.today() - one_day)
    builder = builder.not_valid_after(datetime.datetime.today() + (one_day*365*5))
    builder = builder.serial_number(x509.random_serial_number())
    builder = builder.public_key(public_key)
    builder = builder.add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(socket.gethostname()),
            x509.DNSName('*.%s' % socket.gethostname()),
            x509.DNSName('localhost'),
            x509.DNSName('*.localhost'),
        ]),
        critical=False)
    builder = builder.add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)

    if cakey == None:
        certificate = builder.sign(
            private_key=private_key, algorithm=hashes.SHA256(),
            backend=default_backend())
    else:
        certificate = builder.sign(
            private_key=cakey, algorithm=hashes.SHA256(),
            backend=default_backend())

    return (certificate.public_bytes(serialization.Encoding.PEM),
        private_key.private_bytes(serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()))

def gen_self_signed_cert():
    '''
    Returns (cert, key) as ASCII PEM strings
    '''
    try:
        return _gen_openssl()
    except:
        try:
            return _gen_cryptography()
        except:
            return (None, None)
    return (None, None)

def generateServerCertificate(certPath, keyPath, rootCertPath, rootKeyPath):
    # Generate a server certificate signed by the root certificate
    # certPath: Path to the certificate file
    # keyPath: Path to the key file
    # rootCertPath: Path to the root certificate file
    # rootKeyPath: Path to the root key file

    # Load the root cert and key
    rootCert = crypto.load_certificate(crypto.FILETYPE_PEM, open(rootCertPath, "rb").read())
    rootKey = crypto.load_privatekey(crypto.FILETYPE_PEM, open(rootKeyPath, "rb").read())


    # Sign the server cert with the root cert
    server_cert, server_key = _gen_openssl(rootCert.get_subject(), "Gal's Server", rootKey)

    # Load the server certificate and key
    server_cert = crypto.load_certificate(crypto.FILETYPE_PEM, server_cert)
    server_key = crypto.load_privatekey(crypto.FILETYPE_PEM, server_key)

    # Write the cert and key files
    certOutFile = open(certPath, "wb")
    certOutFile.write(crypto.dump_certificate(crypto.FILETYPE_PEM, server_cert))
    certOutFile.close()
    keyOutFile = open(keyPath, "wb")
    keyOutFile.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, server_key))
    keyOutFile.close()


if __name__ == '__main__':
    # Save the cert and key to files

    cert, key = gen_self_signed_cert()

    with open('https/rootcert.pem', 'w') as f:
        f.write(cert.decode())
        
    with open('https/rootkey.pem', 'w') as f:
        f.write(key.decode())
    

    # generate the server cert
    generateServerCertificate('https/servercert.pem', 'https/serverkey.pem', 'https/rootcert.pem', 'https/rootkey.pem')

    # write the server cert and key to .cer file
    with open('https/servercert.cer', 'wb') as f:
        f.write(open('https/servercert.pem', 'rb').read())
        f.write(open('https/serverkey.pem', 'rb').read())

    # write the root cert and key to .cer file
    with open('https/rootcert.cer', 'wb') as f:
        f.write(open('https/rootcert.pem', 'rb').read())
        f.write(open('https/rootkey.pem', 'rb').read())

