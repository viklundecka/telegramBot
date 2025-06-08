import json
import aiofiles
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class JSONStorage:
    def __init__(self, file_path: str = "storage/user_data.json"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(exist_ok=True)

        if not self.file_path.exists():
            self._create_empty_storage()

    def _create_empty_storage(self):
        initial_data = {
            "users": {},
            "favorites": {},
            "banned_users": {},
            "statistics": {
                "total_users": 0,
                "total_requests": 0,
                "bot_started": str(datetime.now())
            }
        }
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=2)

    async def load_data(self) -> Dict:
        try:
            async with aiofiles.open(self.file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)

                if "banned_users" not in data:
                    data["banned_users"] = {}

                return data
        except Exception as e:
            logger.error(f"Ошибка загрузки данных: {e}")
            self._create_empty_storage()
            return await self.load_data()

    async def save_data(self, data: Dict):
        try:
            async with aiofiles.open(self.file_path, 'w', encoding='utf-8') as f:
                content = json.dumps(data, ensure_ascii=False, indent=2)
                await f.write(content)
        except Exception as e:
            logger.error(f"Ошибка сохранения данных: {e}")

    async def add_user(self, user_id: int, username: str = None):
        data = await self.load_data()

        if str(user_id) not in data["users"]:
            data["users"][str(user_id)] = {
                "username": username,
                "first_seen": str(datetime.now()),
                "last_activity": str(datetime.now()),
                "request_count": 0
            }
            data["statistics"]["total_users"] += 1
            await self.save_data(data)
            logger.info(f"Добавлен новый пользователь: {user_id}")

    async def update_user_activity(self, user_id: int):
        data = await self.load_data()
        user_str = str(user_id)

        if user_str in data["users"]:
            data["users"][user_str]["last_activity"] = str(datetime.now())
            data["users"][user_str]["request_count"] += 1
            data["statistics"]["total_requests"] += 1
            await self.save_data(data)

    async def add_favorite(self, user_id: int, item: str):
        data = await self.load_data()
        user_str = str(user_id)

        if user_str not in data["favorites"]:
            data["favorites"][user_str] = []

        if item not in data["favorites"][user_str]:
            data["favorites"][user_str].append(item)
            await self.save_data(data)
            return True
        return False

    async def get_favorites(self, user_id: int) -> List[str]:
        data = await self.load_data()
        return data["favorites"].get(str(user_id), [])

    async def remove_favorite(self, user_id: int, item: str) -> bool:
        data = await self.load_data()
        user_str = str(user_id)

        if user_str in data["favorites"] and item in data["favorites"][user_str]:
            data["favorites"][user_str].remove(item)
            await self.save_data(data)
            return True
        return False

    async def get_statistics(self) -> Dict:
        data = await self.load_data()
        return data.get("statistics", {})

    async def get_all_users(self) -> List[int]:
        data = await self.load_data()
        return [int(user_id) for user_id in data["users"].keys()]

    async def ban_user(self, user_id: int, reason: str = "Нарушение правил", admin_id: int = None) -> bool:
        data = await self.load_data()
        user_str = str(user_id)

        if user_str not in data["banned_users"]:
            data["banned_users"][user_str] = {
                "reason": reason,
                "banned_at": str(datetime.now()),
                "banned_by": admin_id
            }
            await self.save_data(data)
            logger.info(f"Пользователь {user_id} заблокирован админом {admin_id}. Причина: {reason}")
            return True
        return False

    async def unban_user(self, user_id: int, admin_id: int = None) -> bool:
        data = await self.load_data()
        user_str = str(user_id)

        if user_str in data["banned_users"]:
            del data["banned_users"][user_str]
            await self.save_data(data)
            logger.info(f"Пользователь {user_id} разблокирован админом {admin_id}")
            return True
        return False

    async def is_user_banned(self, user_id: int) -> bool:
        data = await self.load_data()
        return str(user_id) in data.get("banned_users", {})

    async def get_ban_info(self, user_id: int) -> Optional[Dict]:
        data = await self.load_data()
        return data.get("banned_users", {}).get(str(user_id))

    async def get_banned_users(self) -> Dict:
        data = await self.load_data()
        return data.get("banned_users", {})

    async def get_user_info(self, user_id: int) -> Optional[Dict]:
        data = await self.load_data()
        return data.get("users", {}).get(str(user_id))