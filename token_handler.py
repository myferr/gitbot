# Generate ENCRYPTION_KEY using:
#
# from cryptography.fernet import Fernet
# print(Fernet.generate_key().decode())
#
# Store this securely in your environment as ENCRYPTION_KEY.

import os
from cryptography.fernet import Fernet

class TokenHandler:
    def __init__(self):
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            raise ValueError("ENCRYPTION_KEY environment variable not set")
        self.fernet = Fernet(key.encode())

    def encrypt(self, token: str) -> str:
        return self.fernet.encrypt(token.encode()).decode()

    def decrypt(self, encrypted_token: str) -> str:
        return self.fernet.decrypt(encrypted_token.encode()).decode()
