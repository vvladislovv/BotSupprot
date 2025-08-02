from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from utils.encryption import TokenEncryption

Base = declarative_base()

class ConnectedBot(Base):
    __tablename__ = 'connected_bots'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    _encrypted_token = Column('bot_token', String(500), nullable=False, unique=True)  # Увеличили размер для зашифрованного токена
    bot_username = Column(String(50), nullable=False)
    bot_id = Column(BigInteger, nullable=False)
    group_id = Column(BigInteger, nullable=True)
    is_active = Column(Boolean, default=True)
    welcome_text_ru = Column(Text, nullable=True)
    welcome_text_en = Column(Text, nullable=True)
    info_text_ru = Column(Text, nullable=True)
    info_text_en = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    chats = relationship("Chat", back_populates="bot")
    
    @property
    def bot_token(self):
        """Получение расшифрованного токена"""
        try:
            if not self._encrypted_token:
                return ""
            

            if TokenEncryption.is_token_encrypted(self._encrypted_token):
                return TokenEncryption.decrypt_token(self._encrypted_token)
            else:

                return self._encrypted_token
        except Exception as e:

            return self._encrypted_token
    
    @bot_token.setter
    def bot_token(self, value):
        """Установка токена с автоматическим шифрованием"""
        if not value:
            self._encrypted_token = ""
            return
        
        try:

            self._encrypted_token = TokenEncryption.encrypt_token(value)
        except Exception as e:

            self._encrypted_token = value
    
    def migrate_token_encryption(self):
        """Миграция токена к зашифрованному виду"""
        try:
            if self._encrypted_token and not TokenEncryption.is_token_encrypted(self._encrypted_token):
                # Токен не зашифрован, шифруем его
                plain_token = self._encrypted_token
                self._encrypted_token = TokenEncryption.encrypt_token(plain_token)
                return True
        except Exception as e:
            pass
        return False

class Chat(Base):
    __tablename__ = 'chats'
    
    id = Column(Integer, primary_key=True)
    bot_id = Column(Integer, ForeignKey('connected_bots.id'), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    username = Column(String(50), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    topic_id = Column(Integer, nullable=True)
    status = Column(String(20), default='waiting')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    

    bot = relationship("ConnectedBot", back_populates="chats")
    messages = relationship("Message", back_populates="chat")

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id'), nullable=False)
    message_id = Column(Integer, nullable=False)
    from_user = Column(Boolean, nullable=False)  # True - от пользователя, False - от оператора
    content = Column(Text, nullable=True)
    message_type = Column(String(20), default='text')
    created_at = Column(DateTime, default=datetime.utcnow)
    

    chat = relationship("Chat", back_populates="messages")

class BannedUser(Base):
    __tablename__ = 'banned_users'
    
    id = Column(Integer, primary_key=True)
    bot_id = Column(Integer, ForeignKey('connected_bots.id'), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    banned_at = Column(DateTime, default=datetime.utcnow)
    

    bot = relationship("ConnectedBot")
