from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="🌤 Погода", callback_data="weather")],
        [InlineKeyboardButton(text="🐱 Факт о котах", callback_data="cat_fact")],
        [InlineKeyboardButton(text="⭐ Избранное", callback_data="favorites")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_favorites_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="📋 Показать избранное", callback_data="show_favorites")],
        [InlineKeyboardButton(text="➕ Добавить город", callback_data="add_favorite")],
        [InlineKeyboardButton(text="🗑 Удалить город", callback_data="remove_favorite")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_button() -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_main")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="📊 Детальная статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [
            InlineKeyboardButton(text="🔧 Кэш", callback_data="admin_cache"),
            InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")
        ],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{action}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{action}")
        ],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_cache_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="🗑 Очистить кэш", callback_data="clear_cache")],
        [InlineKeyboardButton(text="🔄 Обновить информацию", callback_data="admin_cache")],
        [InlineKeyboardButton(text="⬅ Назад к админке", callback_data="back_to_admin")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_ban_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="🚫 Заблокировать", callback_data="ban_user"),
            InlineKeyboardButton(text="✅ Разблокировать", callback_data="unban_user")
        ],
        [InlineKeyboardButton(text="👥 Обновить список", callback_data="admin_users")],
        [InlineKeyboardButton(text="⬅ Назад к админке", callback_data="back_to_admin")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)