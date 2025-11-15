from typing import cast

import json
import os

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag


def generate_rsa_keypair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    return private_key, public_key


def generate_aes_key():
    return AESGCM.generate_key(bit_length=256)


def public_key_to_json(pubkey: rsa.RSAPublicKey):
    pem = pubkey.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    return json.dumps({"public_key": pem.decode("utf-8")})


def public_key_from_json(json_str):
    data = json.loads(json_str)
    pem_str = data["public_key"]

    pubkey = serialization.load_pem_public_key(pem_str.encode("utf-8"))
    return cast(rsa.RSAPublicKey, pubkey)


def rsa_encrypt(public_key: rsa.RSAPublicKey, message: bytes) -> bytes:
    ciphertext = public_key.encrypt(
        message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    return ciphertext


def rsa_decrypt(private_key: rsa.RSAPrivateKey, ciphertext: bytes) -> bytes:
    message = private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    return message


def aes_encrypt(key: bytes, plaintext: bytes) -> tuple[bytes, bytes]:
    aes = AESGCM(key)

    # GCM recommended nonce size is 12 bytes
    nonce = os.urandom(12)

    # ciphertext includes authentication tag
    ciphertext = aes.encrypt(nonce, plaintext, None)

    return nonce, ciphertext


def aes_decrypt(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    aes = AESGCM(key)

    try:
        plaintext = aes.decrypt(nonce, ciphertext, None)
        return plaintext
    except InvalidTag:
        raise ValueError(
            "Decryption failed: wrong key, wrong nonce, or corrupted ciphertext"
        )
