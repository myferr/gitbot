# Generate ENCRYPTION_KEY using
# 
# from cryptography.fernet import Fernet
# print(Fernet.generate_key().decode())
#
# That is very important.

import os
from cryptography.fernet import Fernet

class TokenHandler:
    def __init__(self):
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            raise ValueError("ENCRYPTION_KEY environment variable not set")
        self.fernet = Fernet(key.encode())

    def encrypt(self, token: str) -> str:
        encrypted_bytes = self.fernet.encrypt(token.encode())
        return encrypted_bytes.decode()

    def decrypt(self, encrypted_token: str) -> str:
        """Decrypt a previously encrypted token string back to plaintext."""
        decrypted_bytes = self.fernet.decrypt(encrypted_token.encode())
        return decrypted_bytes.decode()
