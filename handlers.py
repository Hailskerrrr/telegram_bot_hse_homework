import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import io
from states import Form
import utils

import io
import matplotlib.pyplot as plt
from aiogram.types.input_file import BufferedInputFile  

from aiogram.types import InputFile

router = Router()
import matplotlib.pyplot as plt


user_data = {}  




def get_or_create_user(user_id: str) -> dict:
    if user_id not in user_data:
        user_data[user_id] = {
            "weight": 0.0,
            "height": 0.0,
            "age": 0,
            "activity": 0,
            "city": "",
            "water_goal": 0.0,
            "calorie_goal": 0.0,
            "logged_water": 0.0,
            "logged_calories": 0.0,
            "burned_calories": 0.0
        }
    return user_data[user_id]




@router.message(Command("start"))
async def start_message(message: Message):
    await message.answer(
        "Бот для расчёта нормы воды, калорий и трекинга активности.\n\n"
        "Используйте /set_profile для определения своего профиля.\n"
        "Если у вас уже есть данные, введите /get_profile.\n"
        "Список других команд: /log_water, /log_food, /log_workout, /check_progress."
    )





@router.message(Command("set_profile"))
async def cmd_set_profile(message: Message, state: FSMContext):
    """Начинаем диалог по настройке профиля (рост, вес, возраст, активность, город)."""
    await message.answer("Введи свой рост (в см):")
    await state.set_state(Form.height)

@router.message(Form.height)
async def process_height(message: Message, state: FSMContext):
    try:
        h = float(message.text)
    except ValueError:
        await message.reply("Пожалуйста, введите число (например, 180).")
        return
    await state.update_data(height=h)
    await message.reply("Введи свой вес (в кг):")
    await state.set_state(Form.weight)

@router.message(Form.weight)
async def process_weight(message: Message, state: FSMContext):
    try:
        w = float(message.text)
    except ValueError:
        await message.reply("Пожалуйста, введите число (например, 75).")
        return  
    await state.update_data(weight=w)
    await message.reply("Введи свой возраст (полных лет):")
    await state.set_state(Form.age)

@router.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    try:
        a = int(message.text)
    except ValueError:
        await message.reply("Пожалуйста, введите целое число (например, 30).")
        return
    await state.update_data(age=a)
    await message.reply("Сколько минут активности у вас в день?")
    await state.set_state(Form.action_level)

@router.message(Form.action_level)
async def process_action_level(message: Message, state: FSMContext):
    try:
        act = int(message.text)
    except ValueError:
        await message.reply("Пожалуйста, введите целое число (например, 45).")
        return
    await state.update_data(activity=act)
    await message.reply("В каком городе вы живёте? (Чтобы определить погоду)")
    await state.set_state(Form.city)

@router.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    city = message.text.strip()
    await state.update_data(city=city)

    data = await state.get_data()
    user_id = str(message.from_user.id)


    base_cal = utils.calculate_calorie_goal(
        weight=data["weight"],
        height=data["height"],
        age=data["age"],
        activity_minutes=data["activity"]
    )


    temperature = await utils.get_weather_temp(city)
    base_water = utils.calculate_water_goal(
        weight=data["weight"],
        activity_minutes=data["activity"],
        temperature=temperature
    )


    user = get_or_create_user(user_id)
    user["height"] = data["height"]
    user["weight"] = data["weight"]
    user["age"] = data["age"]
    user["activity"] = data["activity"]
    user["city"] = city
    user["calorie_goal"] = round(base_cal, 1)
    user["water_goal"] = round(base_water, 1)
    user["logged_water"] = 0.0
    user["logged_calories"] = 0.0
    user["burned_calories"] = 0.0

    await message.reply(
        f"Профиль обновлён!\n"
        f"Калорий в день: ~{user['calorie_goal']} ккал\n"
        f"Воды в день: ~{user['water_goal']} мл\n\n"
        "Если хотите скорректировать цель калорий вручную, введите её здесь (число), "
        "или напишите «нет» для подтверждения."
    )


    await state.set_state(Form.goal)

@router.message(Form.goal)
async def process_goal(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    user = get_or_create_user(user_id)

    text = message.text.lower().strip()

    if text == "нет":
        await message.reply(
            f"Хорошо, оставляем {user['calorie_goal']} ккал.\n"
            "Профиль сохранён! Можете использовать /check_progress."
        )
    else:

        try:
            custom_goal = float(text)
            user["calorie_goal"] = custom_goal
            await message.reply(
                f"Цель калорий обновлена на {custom_goal:.1f}.\n"
                "Профиль сохранён! Можете использовать /check_progress."
            )
        except ValueError:
            await message.reply("Не понял. Если не хотите менять цель, напишите «нет» или введите число.")
            return


    utils.save_data_to_json(user_data)

    await state.clear()




@router.message(Command("get_profile"))
async def cmd_get_profile(message: Message):
    print("DEBUG: cmd_log_workout was called with:", message.text)
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        await message.answer("Профиль не найден. Сначала введите /set_profile.")
        return

    user = user_data[user_id]
    text = (
        f"Ваш профиль:\n"
        f"Рост: {user['height']} см\n"
        f"Вес: {user['weight']} кг\n"
        f"Возраст: {user['age']}\n"
        f"Активность: {user['activity']} мин/день\n"
        f"Город: {user['city']}\n\n"
        f"Цель по калориям: {user['calorie_goal']:.1f} ккал\n"
        f"Цель по воде: {user['water_goal']:.1f} мл\n"
        f"Выпито воды: {user['logged_water']:.1f} мл\n"
        f"Потреблено калорий: {user['logged_calories']:.1f} ккал\n"
        f"Сожжено калорий: {user['burned_calories']:.1f} ккал\n"
    )
    await message.answer(text)




@router.message(Command("log_water"))
async def cmd_log_water(message: Message):
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        await message.answer("Сначала /set_profile для создания профиля.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Используйте: /log_water <кол-во мл>")
        return

    try:
        amount = float(args[1].replace(",", "."))
    except ValueError:
        await message.answer("Неверное число. Пример: /log_water 250")
        return

    user = user_data[user_id]
    user["logged_water"] += amount
    utils.save_data_to_json(user_data)

    remain = user["water_goal"] - user["logged_water"]
    if remain < 0:
        remain = 0
    await message.answer(
        f"Добавлено {amount} мл воды. Всего сегодня: {user['logged_water']} мл.\n"
        f"Осталось до нормы: {remain} мл."
    )





FOOD_LOG_STATE = {}

@router.message(Command("log_food"))
async def cmd_log_food(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        await message.answer("Сначала /set_profile для создания профиля.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Используйте: /log_food <название продукта> на английском")
        return

    product_name = args[1].strip()
    # Сохраняем название продукта в данные FSM
    await state.update_data(product_for_food=product_name)
    await message.answer(
        f"Вы указали продукт: {product_name}.\n"
        "Сколько граммов вы съели? (введите число)"
    )
    # Переводим пользователя в состояние, когда мы ожидаем ввод граммов
    await state.set_state(Form.food_grams)


@router.message(Form.food_grams)
async def handle_food_grams(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    data = await state.get_data()
    product_name = data.get("product_for_food")
    if not product_name:
        await message.answer("Ошибка: не найден продукт для логирования.")
        return

    try:
        grams = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число для граммов.")
        return

    # Получаем калорийность продукта (ккал на 100 г)
    kcal_100g = await utils.get_food_calories(product_name)
    kcal_total = (kcal_100g * grams) / 100.0

    user = get_or_create_user(user_id)
    # Обновляем суммарное количество потреблённых калорий
    user["logged_calories"] += kcal_total

    # Если в профиле ещё нет истории еды, создаём список
    if "food_log" not in user:
        user["food_log"] = []

    # Добавляем новую запись в историю еды
    user["food_log"].append({
        "product": product_name,
        "grams": grams,
        "kcal_total": kcal_total
    })

    # Сохраняем изменения в JSON
    utils.save_data_to_json(user_data)

    await message.answer(
        f"Записано: {product_name}, {grams} г.\n"
        f"~ {kcal_total:.1f} ккал добавлено к дневному рациону."
    )
    # Завершаем работу FSM для логирования еды
    await state.clear()





@router.message(Command("show_graph"))
async def cmd_show_graph(message: Message):
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        await message.answer("Сначала создайте профиль командой /set_profile")
        return

    user = user_data[user_id]
    water_goal = user.get("water_goal", 0)
    logged_water = user.get("logged_water", 0)
    cal_goal = user.get("calorie_goal", 0)
    logged_calories = user.get("logged_calories", 0)
    burned_calories = user.get("burned_calories", 0)

    fig, axs = plt.subplots(1, 2, figsize=(10, 4))

    # График по воде
    axs[0].bar(["Выпито", "Цель"], [logged_water, water_goal], color=["blue", "green"])
    axs[0].set_title("Прогресс по воде")
    axs[0].set_ylabel("Мл")

    # График по калориям
    axs[1].bar(["Потреблено", "Сожжено", "Цель"],
               [logged_calories, burned_calories, cal_goal],
               color=["orange", "red", "green"])
    axs[1].set_title("Прогресс по калориям")
    axs[1].set_ylabel("Ккал")

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)

    # Используем BufferedInputFile, передавая байты из буфера и имя файла
    photo = BufferedInputFile(buf.getvalue(), filename="graph.png")
    
    await message.answer_photo(photo, caption="Графики прогресса за сегодня")

@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "Доступные команды:\n\n"
        "/start - Начать работу с ботом и получить основную информацию\n"
        "/set_profile - Настроить или обновить профиль (рост, вес, возраст, активность, город)\n"
        "/get_profile - Показать текущий профиль\n"
        "/log_water <кол-во мл> - Зафиксировать количество выпитой воды\n"
        "/log_food <название продукта> - Зафиксировать прием пищи\n"
        "/log_workout <тип> <время(мин)> - Зафиксировать тренировку\n"
        "/check_progress - Показать прогресс по воде и калориям\n"
        "/show_graph - Показать графики прогресса по воде и калориям\n\n"
        "Если у вас возникнут вопросы – пишите /help."
    )
    await message.answer(help_text)



@router.message(Command("log_workout"))
async def cmd_log_workout(message: Message):
    print("DEBUG: cmd_log_workout was called with:", message.text)
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        await message.answer("Сначала /set_profile для создания профиля.")
        return

    args = message.text.split()
    if len(args) < 3:
        await message.answer("Используйте: /log_workout <тип> <время(мин)>\nНапример: /log_workout бег 30")
        return

    workout_type = args[1]
    try:
        duration = float(args[2])
    except ValueError:
        await message.answer("Неверное число минут. Пример: /log_workout бег 30")
        return



    if workout_type.lower() in ("бег", "run"):
        burned = 10.0 * duration
    elif workout_type.lower() in ("ходьба", "walk"):
        burned = 5.0 * duration
    else:
        burned = 7.0 * duration

    user = user_data[user_id]
    user["burned_calories"] += burned


    add_water = (int(duration) // 30) * 200
    user["logged_water"] += add_water

    utils.save_data_to_json(user_data)

    await message.answer(
        f"Тренировка: {workout_type}, {duration} мин.\n"
        f"Сожжено: ~{burned:.1f} ккал.\n"
        f"Рекомендуется дополнительно выпить {add_water} мл воды."
    )




@router.message(Command("check_progress"))
async def cmd_check_progress(message: Message):
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        await message.answer("Сначала /set_profile для создания профиля.")
        return

    user = user_data[user_id]
    water_goal = user["water_goal"]
    water_logged = user["logged_water"]
    cal_goal = user["calorie_goal"]
    cal_logged = user["logged_calories"]
    cal_burned = user["burned_calories"]
    balance = cal_logged - cal_burned  

    text = (
        f"📊 Прогресс:\n\n"
        f"Вода:\n"
        f" • Выпито: {water_logged:.1f} мл из {water_goal:.1f} мл.\n"
        f" • Осталось: {max(0, water_goal - water_logged):.1f} мл.\n\n"
        f"Калории:\n"
        f" • Потреблено: {cal_logged:.1f} ккал из {cal_goal:.1f} ккал.\n"
        f" • Сожжено: {cal_burned:.1f} ккал.\n"
        f" • Баланс (потребл.-сожж.): {balance:.1f} ккал."
    )
    await message.answer(text)
