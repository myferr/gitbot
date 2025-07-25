import os
from cryptography.fernet import Fernet

class TokenHandler:
    def __init__(self, key: str = None):
        """
        Initialize the TokenHandler with the encryption key.
        If no key is provided, it reads from the ENCRYPTION_KEY env variable.
        """
        if key is None:
            key = os.getenv("ENCRYPTION_KEY")
            if not key:
                raise ValueError("ENCRYPTION_KEY environment variable is not set.")
        if isinstance(key, str):
            key = key.encode()
        self.fernet = Fernet(key)

    def encrypt(self, token: str) -> str:
        """
        Encrypts the token and returns a base64 encoded string.
        """
        token_bytes = token.encode()
        encrypted = self.fernet.encrypt(token_bytes)
        return encrypted.decode()

    def decrypt(self, encrypted_token: str) -> str:
        encrypted_bytes = encrypted_token.encode()
        decrypted = self.fernet.decrypt(encrypted_bytes)
        return decrypted.decode()

# Example usage:
# handler = TokenHandler()
# encrypted = handler.encrypt("my_github_token_here")
# decrypted = handler.decrypt(encrypted)
