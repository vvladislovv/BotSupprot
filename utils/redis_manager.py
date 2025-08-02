import json
import logging
from typing import Optional, Any, Dict
import redis.asyncio as redis
from config import config

logger = logging.getLogger(__name__)

class RedisManager:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.connected = False

    async def connect(self):
        """Подключение к Redis"""
        try:
            self.redis = redis.from_url(
                config.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Проверяем соединение
            await self.redis.ping()
            self.connected = True
            logger.info("Успешно подключились к Redis")
            
        except Exception as e:
            logger.error(f"Ошибка подключения к Redis: {e}")
            self.connected = False
            self.redis = None

    async def disconnect(self):
        """Отключение от Redis"""
        if self.redis:
            await self.redis.close()
            self.connected = False
            logger.info("Отключились от Redis")

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Установка значения в Redis"""
        if not self.connected or not self.redis:
            logger.warning("Redis не подключен")
            return False
        
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            await self.redis.set(key, value, ex=expire)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка записи в Redis: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из Redis"""
        if not self.connected or not self.redis:
            logger.warning("Redis не подключен")
            return None
        
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            
            # Пытаемся распарсить JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"Ошибка чтения из Redis: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """Удаление ключа из Redis"""
        if not self.connected or not self.redis:
            logger.warning("Redis не подключен")
            return False
        
        try:
            result = await self.redis.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Ошибка удаления из Redis: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Проверка существования ключа"""
        if not self.connected or not self.redis:
            return False
        
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Ошибка проверки существования ключа: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """Установка времени жизни ключа"""
        if not self.connected or not self.redis:
            return False
        
        try:
            return await self.redis.expire(key, seconds)
        except Exception as e:
            logger.error(f"Ошибка установки TTL: {e}")
            return False

    async def hset(self, name: str, mapping: Dict[str, Any]) -> bool:
        """Установка hash значений"""
        if not self.connected or not self.redis:
            return False
        
        try:
            # Конвертируем значения в строки
            str_mapping = {}
            for k, v in mapping.items():
                if isinstance(v, (dict, list)):
                    str_mapping[k] = json.dumps(v, ensure_ascii=False)
                else:
                    str_mapping[k] = str(v)
            
            await self.redis.hset(name, mapping=str_mapping)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка записи hash в Redis: {e}")
            return False

    async def hget(self, name: str, key: str) -> Optional[Any]:
        """Получение значения из hash"""
        if not self.connected or not self.redis:
            return None
        
        try:
            value = await self.redis.hget(name, key)
            if value is None:
                return None
            
            # Пытаемся распарсить JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"Ошибка чтения hash из Redis: {e}")
            return None

    async def hgetall(self, name: str) -> Dict[str, Any]:
        """Получение всех значений из hash"""
        if not self.connected or not self.redis:
            return {}
        
        try:
            data = await self.redis.hgetall(name)
            result = {}
            
            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    result[k] = v
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка чтения всех hash из Redis: {e}")
            return {}

    async def hdel(self, name: str, *keys: str) -> bool:
        """Удаление ключей из hash"""
        if not self.connected or not self.redis:
            return False
        
        try:
            result = await self.redis.hdel(name, *keys)
            return result > 0
        except Exception as e:
            logger.error(f"Ошибка удаления hash ключей: {e}")
            return False

    # Методы для кеширования данных бота
    async def cache_bot_data(self, bot_id: int, data: Dict[str, Any], expire: int = 3600):
        """Кеширование данных бота"""
        key = f"bot:{bot_id}"
        return await self.set(key, data, expire)

    async def get_cached_bot_data(self, bot_id: int) -> Optional[Dict[str, Any]]:
        """Получение кешированных данных бота"""
        key = f"bot:{bot_id}"
        return await self.get(key)

    async def cache_chat_data(self, chat_id: int, data: Dict[str, Any], expire: int = 1800):
        """Кеширование данных чата"""
        key = f"chat:{chat_id}"
        return await self.set(key, data, expire)

    async def get_cached_chat_data(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Получение кешированных данных чата"""
        key = f"chat:{chat_id}"
        return await self.get(key)

    async def cache_user_session(self, user_id: int, bot_id: int, data: Dict[str, Any], expire: int = 3600):
        """Кеширование пользовательской сессии"""
        key = f"session:{bot_id}:{user_id}"
        return await self.set(key, data, expire)

    async def get_cached_user_session(self, user_id: int, bot_id: int) -> Optional[Dict[str, Any]]:
        """Получение кешированной пользовательской сессии"""
        key = f"session:{bot_id}:{user_id}"
        return await self.get(key)

    async def clear_user_session(self, user_id: int, bot_id: int) -> bool:
        """Очистка пользовательской сессии"""
        key = f"session:{bot_id}:{user_id}"
        return await self.delete(key)

# Глобальный экземпляр Redis менеджера
redis_manager = RedisManager()