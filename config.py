import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MAIN_BOT_TOKEN = os.getenv('MAIN_BOT_TOKEN')
    DATABASE_URL = os.getenv('DATABASE_URL')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Настройки шифрования
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    ENCRYPTION_PASSWORD = os.getenv('ENCRYPTION_PASSWORD', 'default_crm_bot_password_2024')
    ENCRYPTION_SALT = os.getenv('ENCRYPTION_SALT', 'crm_bot_salt_2024')
    
    # Статусы и эмодзи
    STATUS_WAITING = 'waiting'
    STATUS_ANSWERED = 'answered'
    STATUS_HOLD = 'hold'
    STATUS_BANNED = 'banned'
    STATUS_ENDED = 'ended'
    
    STATUS_EMOJIS = {
        STATUS_WAITING: '⏳',
        STATUS_ANSWERED: '✅',
        STATUS_HOLD: '🟡',
        STATUS_BANNED: '🔒',
        STATUS_ENDED: '❌'
    }
    
    # Тексты по умолчанию
    DEFAULT_WELCOME_RU = "👋 Добро пожаловать! Напишите ваш вопрос, и мы свяжемся с вами в ближайшее время."
    DEFAULT_WELCOME_EN = "👋 Welcome! Write your question and we will contact you soon."
    DEFAULT_INFO_RU = "ℹ️ Это бот поддержки. Вы можете задать любой вопрос, и наши операторы ответят вам."
    DEFAULT_INFO_EN = "ℹ️ This is a support bot. You can ask any question and our operators will answer you."

config = Config()
