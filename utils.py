import logging
import os
import json
import aiohttp


DATA_FILE = "user_data.json"

def load_data_from_json(file_path=DATA_FILE) -> dict:
    
    if not os.path.exists(file_path):
        logging.info("JSON-файл не найден, возвращаем пустой словарь.")
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logging.error(f"Ошибка чтения JSON: {e}")
        return {}

def save_data_to_json(data: dict, file_path=DATA_FILE):
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info("Данные успешно сохранены в JSON.")
    except Exception as e:
        logging.error(f"Ошибка записи в JSON: {e}")



def calculate_water_goal(weight: float, activity_minutes: int, temperature: float) -> float:

    base = weight * 30
    extra_for_activity = (activity_minutes // 30) * 500
    extra_for_heat = 0
    if temperature > 25:
        extra_for_heat = 500  # или 1000, на ваш выбор
    return base + extra_for_activity + extra_for_heat

def calculate_calorie_goal(weight: float, height: float, age: float, activity_minutes: int) -> float:

    base = 10 * weight + 6.25 * height - 5 * age
    if activity_minutes > 30:
        return base + 300
    else:
        return base + 100


OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")  # Поместите реальный ключ в .env

async def get_weather_temp(city: str) -> float:

    if not city or not OPENWEATHER_API_KEY:
        return 0.0

    url = (
        f"http://api.openweathermap.org/data/2.5/weather?"
        f"q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    )
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                data = await resp.json()
                return data["main"]["temp"]
    except Exception as e:
        logging.error(f"Ошибка при запросе погоды: {e}")
        return 0.0


async def get_food_calories(product_name: str) -> float:
    
    if not product_name:
        return 0.0

    url = (
        "https://world.openfoodfacts.org/cgi/search.pl"
        f"?search_terms={product_name}"
        "&search_simple=1&action=process&json=1&page_size=1"
    )
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                data = await resp.json()
                products = data.get("products", [])
                if not products:
                    return 0.0
                nutriments = products[0].get("nutriments", {})
                kcal = (
                    nutriments.get("kcal_100g")
                    or nutriments.get("energy-kcal_100g")
                    or 0
                )
                return float(kcal)
    except Exception as e:
        logging.error(f"Ошибка при запросе OpenFoodFacts: {e}")
        return 0.0
