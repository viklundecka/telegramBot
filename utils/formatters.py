from datetime import datetime
def format_weather_message(weather_data: dict) -> str:
    location = weather_data.get('location', {})
    current = weather_data.get('current', {})

    city = location.get('name', 'Неизвестный город')
    country = location.get('country', '')
    region = location.get('region', '')

    temp = current.get('temperature', 'N/A')
    feels_like = current.get('feelslike', 'N/A')
    description = ', '.join(current.get('weather_descriptions', ['Нет описания']))
    humidity = current.get('humidity', 'N/A')
    wind_speed = current.get('wind_speed', 'N/A')
    wind_dir = current.get('wind_dir', 'N/A')
    pressure = current.get('pressure', 'N/A')
    uv_index = current.get('uv_index', 'N/A')
    visibility = current.get('visibility', 'N/A')

    location_str = city
    if region and region != city:
        location_str += f", {region}"
    if country:
        location_str += f", {country}"

    return f"""
🌤 **Погода в {location_str}**

🌡 **Температура:** {temp}°C (ощущается как {feels_like}°C)
📝 **Описание:** {description}
💧 **Влажность:** {humidity}%
💨 **Ветер:** {wind_speed} км/ч, {wind_dir}
🗜 **Давление:** {pressure} мб
☀️ **УФ-индекс:** {uv_index}
👁 **Видимость:** {visibility} км

📅 **Время запроса:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""


def format_user_list(users: list) -> str:
    if not users:
        return "📭 Список пуст"

    formatted_list = []
    for i, user in enumerate(users, 1):
        formatted_list.append(f"{i}. {user}")

    return "📋 Список:\n" + "\n".join(formatted_list)