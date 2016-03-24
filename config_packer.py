#!/usr/bin/env python3
import getpass
import sys
import base64

import Crypto.Random
from Crypto.Cipher import AES
import hashlib


# salt size in bytes
SALT_SIZE = 16
NUMBER_OF_ITERATIONS = 20

# the size multiple required for AES
AES_MULTIPLE = 16


def generate_key(password, salt, iterations):
    assert iterations > 0
    key = password + salt
    for i in range(iterations):
        key = hashlib.sha256(key).digest()
    return key


def pad_text(text, multiple):
    extra_bytes = len(text) % multiple
    padding_size = multiple - extra_bytes
    padding = bytes([padding_size]) * padding_size
    padded_text = text + padding
    return padded_text


def unpad_text(padded_text):
    padding_size = padded_text[-1]
    text = padded_text[:-padding_size]
    return text


def encrypt(plaintext, password):
    salt = Crypto.Random.get_random_bytes(SALT_SIZE)
    key = generate_key(password, salt, NUMBER_OF_ITERATIONS)
    cipher = AES.new(key, AES.MODE_ECB)
    padded_plaintext = pad_text(plaintext, AES_MULTIPLE)
    ciphertext = cipher.encrypt(padded_plaintext)
    ciphertext_with_salt = salt + ciphertext
    return base64.b64encode(ciphertext_with_salt)


def decrypt(ciphertext, password):
    ciphertext = base64.b64decode(ciphertext)
    salt = ciphertext[0:SALT_SIZE]
    ciphertext_sans_salt = ciphertext[SALT_SIZE:]
    key = generate_key(password, salt, NUMBER_OF_ITERATIONS)
    cipher = AES.new(key, AES.MODE_ECB)
    padded_plaintext = cipher.decrypt(ciphertext_sans_salt)
    plaintext = unpad_text(padded_plaintext)
    return plaintext


def help():
    print("Usage: {} (encrypt|decrypt) filename".format(sys.argv[0]))


if __name__ == "__main__":
    try:
        mode = sys.argv[1]
        filename = sys.argv[2]
    except IndexError:
        help()
        sys.exit()

    method = None
    if mode == 'encrypt':
        method = encrypt
    elif mode == 'decrypt':
        method = decrypt
    else:
        help()
        sys.exit()

    passphrase = getpass.getpass(prompt='passphrase> ').encode()
    data = open(filename, 'rb').read()
    print(method(data, passphrase).decode())
