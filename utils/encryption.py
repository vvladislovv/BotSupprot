import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

class TokenEncryption:

    
    _fernet = None
    
    @classmethod
    def _get_fernet(cls):
        """Получение экземпляра Fernet для шифрования"""
        if cls._fernet is None:

            encryption_key = os.getenv('ENCRYPTION_KEY')
            
            if not encryption_key:
                # Если ключа нет, генерируем его из пароля
                password = os.getenv('ENCRYPTION_PASSWORD', 'default_crm_bot_password_2024').encode()
                salt = os.getenv('ENCRYPTION_SALT', 'crm_bot_salt_2024').encode()
                
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password))
            else:
                key = encryption_key.encode()
            
            cls._fernet = Fernet(key)
        
        return cls._fernet
    
    @classmethod
    def encrypt_token(cls, token: str) -> str:

        try:
            if not token:
                return ""
            
            fernet = cls._get_fernet()
            encrypted_token = fernet.encrypt(token.encode())
            return base64.urlsafe_b64encode(encrypted_token).decode()
            
        except Exception as e:
            logger.error(f"Ошибка при шифровании токена: {e}")
            raise
    
    @classmethod
    def decrypt_token(cls, encrypted_token: str) -> str:

        try:
            if not encrypted_token:
                return ""
            
            fernet = cls._get_fernet()
            decoded_token = base64.urlsafe_b64decode(encrypted_token.encode())
            decrypted_token = fernet.decrypt(decoded_token)
            return decrypted_token.decode()
            
        except Exception as e:
            logger.error(f"Ошибка при дешифровании токена: {e}")
            raise
    
    @classmethod
    def is_token_encrypted(cls, token: str) -> bool:

        try:

            if ':' in token and token.split(':')[0].isdigit():
                return False  # Это обычный токен
            

            cls.decrypt_token(token)
            return True  # Успешно дешифровали
            
        except:

            return False
    
    @classmethod
    def migrate_token(cls, token: str) -> str:

        if cls.is_token_encrypted(token):
            return token  # Уже зашифрован
        else:
            return cls.encrypt_token(token)  # Шифруем
