import aiohttp
import asyncio
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WeatherstackAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://api.weatherstack.com/current"
        self.cache = {}
        self.cache_ttl = 300  # 5 минут

    def _is_cache_valid(self, city: str) -> bool:
        if city not in self.cache:
            return False

        cache_time = self.cache[city]['timestamp']
        return datetime.now() - cache_time < timedelta(seconds=self.cache_ttl)

    async def get_weather(self, city: str) -> Optional[Dict]:
        city_lower = city.lower()

        if self._is_cache_valid(city_lower):
            logger.info(f"Возвращаем данные из кэша для города: {city}")
            return self.cache[city_lower]['data']

        params = {
            'access_key': self.api_key,
            'query': city,
            'units': 'm'
        }

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        if 'error' in data:
                            error_code = data['error'].get('code')
                            error_info = data['error'].get('info', 'Неизвестная ошибка')

                            if error_code == 615:  # Location not found
                                logger.warning(f"Город не найден: {city}")
                                return None
                            else:
                                logger.error(f"Ошибка API: {error_info}")
                                return None

                        self.cache[city_lower] = {
                            'data': data,
                            'timestamp': datetime.now()
                        }

                        logger.info(f"Получены данные о погоде для города: {city}")
                        return data
                    else:
                        logger.error(f"API вернул статус {response.status}")
                        return None

        except asyncio.TimeoutError:
            logger.error(f"Таймаут при запросе погоды для города: {city}")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка клиента при запросе погоды: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при запросе погоды: {e}")
            return None


class CatFactsAPI:
    def __init__(self):
        self.base_url = "https://catfact.ninja/fact"
        self.cache = {}
        self.cache_ttl = 60

    async def get_cat_fact(self) -> Optional[str]:
        if 'last_fact' in self.cache:
            cache_time = self.cache['last_fact']['timestamp']
            if datetime.now() - cache_time < timedelta(seconds=self.cache_ttl):
                return self.cache['last_fact']['data']

        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.base_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        fact = data.get('fact', 'Факт не найден')

                        self.cache['last_fact'] = {
                            'data': fact,
                            'timestamp': datetime.now()
                        }

                        return fact
                    else:
                        logger.error(f"Cat Facts API вернул статус {response.status}")
                        return None

        except asyncio.TimeoutError:
            logger.error("Таймаут при запросе факта о котах")
            return None
        except Exception as e:
            logger.error(f"Ошибка при запросе факта о котах: {e}")
            return None
