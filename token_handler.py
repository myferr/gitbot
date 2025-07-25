import base64
from cryptography.fernet import Fernet

key = base64.urlsafe_b64encode(os.getenv("ENCRYPTION_KEY").encode())
fernet = Fernet(key)

encrypted_token = fernet.encrypt(access_token.encode()).decode()

decrypted_token = fernet.decrypt(encrypted_token.encode()).decode()

