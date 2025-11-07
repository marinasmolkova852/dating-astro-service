from aiogram.types import Message, FSInputFile, InputMediaPhoto, InputMediaVideo, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, PreCheckoutQuery, LabeledPrice, WebAppInfo
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums.parse_mode import ParseMode
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatAction
from aiogram.filters import Command
from async_controller import db
from tabulate import tabulate
import datetime as dt
import asyncio
import aiohttp
import logging
import random
import socket
import desc
import re
import os


BOT_TOKEN = os.getenv('BOT_TOKEN')
PAYMENT_TOKEN = os.getenv('PAYMENT_TOKEN')


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Хранилище для астро-чатов пользователей
astro_chat = {}
user_requests = {}

# Хранилище для альбомов (медиа-групп)
album_storage = {}  # {media_group_id: {"media": [], "caption": str, "timer": asyncio.Task}}

# Хранилище для отправленных сообщений
sent_messages = {} # Формат: {user_id: [{"message_id": int, "type": "text"|"media"}, ...]}


class SendMedia(StatesGroup):
    waiting_media = State()
    confirm = State()

class EditState(StatesGroup):
    waiting_new_text = State()

class AstroChat(StatesGroup):
    active_mode = State()

class Partners(StatesGroup):
    name = State()
    description = State()
    photo = State()
    promocode = State()
    discount = State()
    preview = State()


def length_control(table, max_length):
    if (len(table) > max_length):
        start_pos = 0
        table_list = []

        while (len(table[start_pos:]) > max_length):
            end_pos = start_pos + [m.end() for m in re.finditer(r':\d{2}\n',table[start_pos:start_pos+max_length])][-1]
            table_list.append(table[start_pos:end_pos])
            start_pos = end_pos

        if (len(table[start_pos:]) <= max_length):
            table_list.append(table[start_pos:])
        
        return table_list
    else:
        return [table]


def split_message(text, max_length=4096):
    """Разбивает текст на части длиной до max_length символов"""
    parts = []
    while len(text) > max_length:
        # Ищем последнее новое предложение или пробел перед лимитом
        split_pos = text.rfind('\n', 0, max_length)
        if split_pos == -1:
            split_pos = text.rfind(' ', 0, max_length)
        if split_pos == -1:
            split_pos = max_length
        parts.append(text[:split_pos].strip())
        text = text[split_pos:].strip()
    parts.append(text)
    return parts


async def get_ai_reply(chat_history):
    """Принимает запрос и возвращает ответ от нейросети для астро-чата"""
    url = os.getenv("AI_SERVICE_URL")
    payload = {"messages": chat_history}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("content", "Извините, не удалось получить ответ")
                else:
                    return f"Ошибка сервиса AI: {response.status}"
    except Exception as e:
        return f"Ошибка при подключении к AI сервису: {str(e)}"


def format_telegram_html(text: str) -> str:
    # Заменяем ###, ** и *
    text = re.sub(r"^###\s*(.+)", r"<b>\1</b>", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)

    return text


@dp.message(Command(commands="start"))
async def command_start(message: Message, state: FSMContext):
    tg_id =  message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    logging.info(f'Запуск бота /start: {tg_id} - {username}')
    photo = FSInputFile("img/header.jpg")
    
    text = f'<b>{first_name}, добро пожаловать в ASTRO-LOVE❤️‍🔥</b>\n\n'\
        'Здесь звезды сводят сердца, а твоя идеальная пара уже ждет тебя ✨\n\n'\
        'Сделай первый шаг навстречу судьбе — зарегистрируйся в нашем приложении!'
    
    menu_btns = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔥 АСТРО ЧАТ 💭"), KeyboardButton(text="🎟️ ПРОМОКОД 🎟️")],
            [KeyboardButton(text="💎 ТАРИФЫ 💎"), KeyboardButton(text="🐷 КОПИЛКА 🐽")],
            [KeyboardButton(text="⭐️ ПАРТНЁРСКАЯ ПРОГРАММА ⭐️")],
            [KeyboardButton(text="📚 ИНСТРУКЦИИ"), KeyboardButton(text="🛠 ТЕХ. ПРОБЛЕМЫ")],
            [KeyboardButton(text="📲 ОБРАТНАЯ СВЯЗЬ")]
        ], 
        resize_keyboard=True
    )
    
    await bot.send_photo(chat_id=message.chat.id, photo=photo, caption=text, reply_markup=menu_btns, parse_mode=ParseMode.HTML)
    

    text = "🔮 Тариф <b>«ЗНАКОМСТВО»</b> в подарок новым пользователям!\nВ бесплатном тарифе тебя ждёт:\n\n"\
        "❤️‍🔥 <b>2 мэтча</b> (твои первые совпадения по запросу)\n"\
        "❤️‍🔥 <b>2 «прокрутки»</b> любви в функции <b>«Сколько в тебе любви?»</b> (процент твоей внутренней любви + разбор чакр + инь/ян)\n"\
        "❤️‍🔥 <b>2 «прокрутки»</b> совместимости в функции <b>«Спидометр совместимости»</b> (любовь, семья, секс, дети, общая энергия пары)\n\n"\
        "<b>Скорее заходи и забирай свой подарок!</b>"
    
    await message.answer(text, parse_mode=ParseMode.HTML)
    
    text = "Жми кнопку <b>«СТАРТ»</b>, чтобы помочь Вселенной найти для тебя лучшего соулмейта 💫"
    
    start_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="СТАРТ", web_app=WebAppInfo(url='https://astro-love.online/profile'))]])
    # tg://miniapp?app_id=Astro_Love_bot
    await message.answer(text, reply_markup=start_btn, parse_mode=ParseMode.HTML)
    await state.clear()
    
    if not username:
        username = '-'
    # Получаем информацию о пользователе из базы данных
    user = await db.check_user(tg_id)
    
    if user:
        status = user.get('status')
        saved_username = user.get('username')
        if status == "blocked":
            await db.update_user_status(tg_id, "active")
        
        if username != saved_username:
            await db.update_user_info(tg_id, username)
    else:
        await db.add_new_user(tg_id, username)
    
    profile_details = await db.check_profile_details(tg_id)
    if not profile_details:
        await db.add_new_profile_details(tg_id)


@dp.message(Command(commands="test"))
async def command_start(message: Message):
    tg_id =  message.from_user.id
    admin = await db.check_admin(tg_id)
    
    if (admin):
        text = '<b>Модуль для тестирования страниц приложения</b>\n\nИспользуется режим изоляции, доступ предоставляется только по ссылке для администраторов и тестировщиков системы. Не предназначено для общего использования\n\n<b>Текущий шаблон:</b> test.html'
    
        open_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Открыть страницу через Telegram App", web_app=WebAppInfo(url='https://astro-love.online/test'))]])
        await message.answer(text, reply_markup=open_btn, parse_mode=ParseMode.HTML)


@dp.message(Command(commands="astrochat"))
async def command_start(message: Message, state: FSMContext):
    tg_id =  message.from_user.id
    first_name = message.from_user.first_name
    
    astro_chat[tg_id] = [
        {
            "role": "system", 
            "content": desc.PROMPT
        }
    ]
    
    text = f"<b>Добро пожаловать, {first_name}! 🚀️</b>\n\n"\
            "<i>Астро-чат — твой личный проводник в мире астрологии и знакомств 💖</i>\n\n"\
            "<b>Я помогу тебе:</b>\n"\
            "🧩 Узнать о совместимости по знакам зодиака\n"\
            "🔮 Получить персональный астрологический совет\n"\
            "🎭 Расшифровать послание звёзд на сегодня\n\n"\
            "<b>С чего начнем? Задавай вопрос!</b>\n"\
            "🌀 Используй команду /exit для выхода из чата"
    
    await message.answer(text, parse_mode=ParseMode.HTML)
    await state.set_state(AstroChat.active_mode)


@dp.message(Command(commands="exit"), AstroChat.active_mode)
async def exit_astro_chat(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    if tg_id in astro_chat:
        del astro_chat[tg_id]
    await state.clear()
    text = "<b>Астро-чат завершён! ❤️‍🔥</b>\n\n"\
           "Наша беседа подошла к концу, но помни: вселенная всегда на твоей стороне! 🪐\n\n"\
           "<i>Возвращайся за советом звёзд, когда:</i>\n"\
           "• Сердце замирает от новой встречи\n"\
           "• Хочется лучше понять того, кто рядом\n"\
           "• Нужен ориентир в мире знакомств\n\n"\
           "🧭 Твой космический компас ждёт по команде /astrochat"
    await message.answer(text, parse_mode=ParseMode.HTML)   
    

@dp.message(AstroChat.active_mode)
async def handle_astro_chat(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    username = message.from_user.username
    user_text = message.text
    
    # Получаем тариф пользователя
    user_details = await db.check_profile_details(tg_id)
    tariff_id = user_details.get('tariff_id')
    
    logging.info(f'Отправка запроса в астро-чат - ID аккаунта: {tg_id}, имя пользователя: {username}, ID тарифа: {tariff_id}\nЗапрос пользователя: {user_text}')
    
    # Проверяем лимит, если тариф ЗНАКОМСТВО или тариф не выбран
    if tariff_id in (1, 6):
        today = dt.datetime.now().date()
        user_data = user_requests.get(tg_id)

        if user_data:
            last_date, count = user_data['date'], user_data['count']
            # Обнуляем, если новый день
            if last_date != today:
                user_requests[tg_id] = {'date': today, 'count': 1}
            elif count >= 10:
                await message.answer(
                    "🚫 Достигнут лимит в 10 запросов на сегодня\n\n"
                    "⏳ Возвращайся завтра или обнови тариф для неограниченного доступа!",
                    parse_mode=ParseMode.HTML
                )
                return
            else:
                user_requests[tg_id]['count'] += 1
        else:
            user_requests[tg_id] = {'date': today, 'count': 1}
    
    astro_chat[tg_id].append({"role": "user", "content": user_text})
    
    # Отправляем начальное сообщение-заглушку
    thinking_message = await message.answer("<i>Анализирую твой вопрос.. 🧬</i>", parse_mode=ParseMode.HTML)
    
    # Задача для анимации заглушек
    async def thinking_animation():
        thinking_stages = [
            "<i>Думаю над ответом.. 💭</i>",
            "<i>Считываю вибрации космоса.. 📡</i>", 
            "<i>Компилирую звёздный код.. &lt;/&gt;</i>",
            "<i>Синтезирую формулу результата.. 🧪</i>"
        ]
        
        for stage in thinking_stages:
            await asyncio.sleep(3)
            await thinking_message.edit_text(stage, parse_mode=ParseMode.HTML)
    
    try:
        # Запускаем анимацию и AI запрос одновременно
        animation_task = asyncio.create_task(thinking_animation())
        ai_task = asyncio.create_task(get_ai_reply(astro_chat[tg_id]))
        
        # Ждем завершения обоих задач
        ai_reply = await ai_task
        await animation_task  # Ждем завершения анимации (она может быть прервана)
        
        # Добавляем ответ в историю
        astro_chat[tg_id].append({"role": "assistant", "content": ai_reply})
        # Показываем статус "печатает..."
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        edit_reply = format_telegram_html(ai_reply)
        # Отправляем финальный ответ
        await thinking_message.edit_text(edit_reply, parse_mode=ParseMode.HTML)
        
    except asyncio.CancelledError:
        # Если задача была отменена
        pass
    except Exception as e:
        logging.error(f'🚫 Ошибка при обработке запроса:\n{e}')
        await thinking_message.edit_text("Что-то пошло не так :(")


# @dp.message(AstroChat.active_mode)
# async def handle_astro_chat(message: Message, state: FSMContext):
#     tg_id = message.from_user.id
#     username = message.from_user.username
#     user_text = message.text
    
#     # Получаем тариф пользователя
#     user_details = await db.check_profile_details(tg_id)
#     tariff_id = user_details.get('tariff_id')
    
#     logging.info(f'Отправка запроса в астро-чат - ID аккаунта: {tg_id}, имя пользователя: {username}, ID тарифа: {tariff_id}\nЗапрос пользователя: {user_text}')
#     # Проверяем лимит, если тариф ЗНАКОМСТВО или тариф не выбран
#     if tariff_id in (1, 6):
#         today = dt.datetime.now().date()
#         user_data = user_requests.get(tg_id)

#         if user_data:
#             last_date, count = user_data['date'], user_data['count']
#             # Обнуляем, если новый день
#             if last_date != today:
#                 user_requests[tg_id] = {'date': today, 'count': 1}
#             elif count >= 10:
#                 await message.answer(
#                     "🚫 Достигнут лимит в 10 запросов на сегодня\n\n"
#                     "⏳ Возвращайся завтра или обнови тариф для неограниченного доступа!",
#                     parse_mode=ParseMode.HTML
#                 )
#                 return
#             else:
#                 user_requests[tg_id]['count'] += 1
#         else:
#             user_requests[tg_id] = {'date': today, 'count': 1}
    
#     astro_chat[tg_id].append({"role": "user", "content": user_text})
    
#     # Отправляем сообщение-заглушку
#     thinking_message = await message.answer("<i>Анализирую твой вопрос.. 🧬</i>", parse_mode=ParseMode.HTML)
#     await asyncio.sleep(2)
#     await thinking_message.edit_text("<i>Думаю над ответом.. 💭</i>", parse_mode=ParseMode.HTML)
#     await asyncio.sleep(2)
#     await thinking_message.edit_text("<i>Считываю вибрации космоса.. 📡</i>", parse_mode=ParseMode.HTML)
#     await asyncio.sleep(2)
#     await thinking_message.edit_text("<i>Компилирую звёздный код.. &lt;/&gt;</i>", parse_mode=ParseMode.HTML)
#     await asyncio.sleep(2)
#     await thinking_message.edit_text("<i>Синтезирую формулу результата.. 🧪</i>", parse_mode=ParseMode.HTML)
#     await asyncio.sleep(2)
    
#     # Показываем статус "печатает..."
#     await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    
#     try:
#         ai_reply = await get_ai_reply(astro_chat[tg_id])
#         astro_chat[tg_id].append({"role": "assistant", "content": ai_reply})
#         # ai_reply = await get_ai_reply(message.text)
#         await message.answer(str(ai_reply), parse_mode=ParseMode.HTML)

        
#         # edit_reply = format_telegram_html(ai_reply)
#         # if len(edit_reply) > 4096:
#         #     parts = split_message(edit_reply)
#         #     await thinking_message.edit_text(parts[0], parse_mode=ParseMode.HTML)
        
#         #     for part in parts[1:]:
#         #         await message.answer(part, parse_mode=ParseMode.HTML)
#         # else:
#         #     await thinking_message.edit_text(edit_reply, parse_mode=ParseMode.HTML)
            
#     except Exception as e:
#         logging.error(f'🚫 Ошибка при обработке запроса:\n{e}')
#         await thinking_message.edit_text(f"Что-то пошло не так :(")
    

@dp.message(Command(commands="menu"))
async def command_open_menu(message: Message):
    menu_btns = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔥 АСТРО ЧАТ 💭"),KeyboardButton(text="🎟️ ПРОМОКОД 🎟️")],
            [KeyboardButton(text="💎 ТАРИФЫ 💎"), KeyboardButton(text="🐷 КОПИЛКА 🐽")],
             [KeyboardButton(text="⭐️ ПАРТНЁРСКАЯ ПРОГРАММА ⭐️")],
            [KeyboardButton(text="📚 ИНСТРУКЦИИ"), KeyboardButton(text="🛠 ТЕХ. ПРОБЛЕМЫ")],
            [KeyboardButton(text="📲 ОБРАТНАЯ СВЯЗЬ")]
        ], 
        resize_keyboard=True
    )
    
    await message.answer("💟 <b>Системное уведомление</b> 💟\nВыберите пункт меню", reply_markup=menu_btns, parse_mode=ParseMode.HTML)


@dp.message(F.text.in_(["🔥 АСТРО ЧАТ 💭", "🎟️ ПРОМОКОД 🎟️", "💎 ТАРИФЫ 💎", "🐷 КОПИЛКА 🐽", "📚 ИНСТРУКЦИИ", "🛠 ТЕХ. ПРОБЛЕМЫ", "📲 ОБРАТНАЯ СВЯЗЬ", "⭐️ ПАРТНЁРСКАЯ ПРОГРАММА ⭐️", "⚜️ НАШИ ПАРТНЁРЫ ⚜️", "🔱 КАК СТАТЬ ПАРТНЁРОМ 🔱"]))
async def menu_handler(message: Message):
    tg_id = message.from_user.id
    username = message.from_user.username
    
    if message.text == "🔥 АСТРО ЧАТ 💭":
        photo = FSInputFile("img/menu/astrochat.png")
        text = "<i>Астро-чат эволюционирует! Теперь это не просто умный собеседник, а ваш личный гид по вселенной отношений. Мы научили его анализировать вашу уникальную ситуацию и энергетику, чтобы давать еще более точные и персонализированные советы ✨</i>\n\n"\
               "Почему выбирают Астро-чат:\n"\
               "🔮 Анализ совместимости: Откройте сильные стороны вашей пары и возможные «подводные камни»\n"\
               "💞 Объяснение поведения: Он внезапно охладел? Она замкнулась? Найдём астрологическую причину и подскажем, как на это реагировать\n"\
               "🪐 Персональный прогноз: Определите лучшие дни для важных шагов в отношениях\n"\
               "✨ Всегда в режиме онлайн: Ответы на ваши вопросы 24/7"
        
        await bot.send_photo(chat_id=message.chat.id, photo=photo, caption=text, parse_mode=ParseMode.HTML)
        
        text = "💸 <b>10 запросов в день</b> — если вы бесплатный пользователь\n"\
               "💎 <b>Неограниченное количество запросов в день</b> — если вы платный пользователь"
               
        tariffs_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Купить тариф", web_app=WebAppInfo(url='https://astro-love.online/tariffs'))]])
        await message.answer(text, reply_markup=tariffs_btn, parse_mode=ParseMode.HTML)
        
        text = "<b>🚀 Запустите Астро-чат и откройте новые грани ваших отношений!</b>\n\n"\
               "Через команду:\n"\
               "/astrochat - запуск Астро-чата\n"\
               "/exit - для выхода из Астро-чата\n"
        await message.answer(text, parse_mode=ParseMode.HTML)
        
    if message.text == "🎟️ ПРОМОКОД 🎟️":
        photo = FSInputFile("img/menu/promocode.jpg")
        text = "Промокод в АСТРО-ЛЮБОВЬ — твой ключ к выгоде и заработку!💰❤️‍🔥\n\n"\
               "Что дает?\n"\
               "✨Делись своим персональным промокодом с друзьями и знакомыми! — они получают скидку\n"\
               "🪐 Зарабатывай деньги! — приглашай друзей и получай вознаграждение за их покупки\n"\
               "🔮 Вывод средств —  осуществляется от 1000₽ без комиссий\n\n"\
               "Для пользователей:\n"\
               "❗️Ваш личный промокод дает <b>5% скидки</b> Вашему другу и(или) знакомому при оплате любого тарифа\n"\
               "❗️Вы <b>зарабатываете 5%</b> от покупки вашим другом и(или) знакомым любого тарифа\n"\
               "❓Если вы хотите больший % - становитесь нашим «партнером»"
        await bot.send_photo(chat_id=message.chat.id, photo=photo, caption=text, parse_mode=ParseMode.HTML)
        
        if not username:
            username = "User"
        referral = await db.check_ref(tg_id)
        if referral:
            promocode = referral.get('promocode')
            await message.answer(f'Ваш персональный промокод: <code>{promocode}</code>', parse_mode=ParseMode.HTML)
        else:
            number = random.randint(10, 10000)
            promocode = f'AL{username}{number}'.upper()
            await db.add_new_ref(tg_id, promocode)
            await message.answer(f'Ваш персональный промокод был успешно сгенерирован!\nПромокод: <code>{promocode}</code>', parse_mode=ParseMode.HTML)
    
    elif message.text == "💎 ТАРИФЫ 💎":
        photo = FSInputFile("img/menu/tariff.jpg")
        text = "<b>🔮 Выберите подходящий тариф</b>\n\n"\
               "Хотите увеличить шансы найти свою идеальную пару? Выберите любой тариф из представленных ниже вариантов!\n\n"\
               "<i>💡 Чем выше тариф — тем больше возможностей для знакомства!</i>"
        
        await bot.send_photo(chat_id=message.chat.id, photo=photo, caption=text, parse_mode=ParseMode.HTML)
        
        tariff_btns = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="💡 Тариф «СТАРТ»")], 
                [KeyboardButton(text="🔮 Тариф «БАЗОВЫЙ»")],
                [KeyboardButton(text="💳 Тариф «VIP»")], 
                [KeyboardButton(text="💎 Тариф «SUPER VIP»")],
                [KeyboardButton(text="Назад ⏪")]
            ], 
            resize_keyboard=True
        )
        await message.answer("💟 <b>Системное уведомление</b> 💟\nВыберите тариф", reply_markup=tariff_btns, parse_mode=ParseMode.HTML)
    
    elif message.text ==  "🐷 КОПИЛКА 🐽":
        photo = FSInputFile("img/menu/wallet.jpg")
        text = "Копилка в АСТРО-ЛЮБОВЬ — твой звёздный финансовый помощник!❤️‍🔥🐷\n\n"\
               "В данном разделе отражен твой баланс!\n"\
               "Следующим сообщением⬇️\n\n"\
               "Как можно использовать баланс?\n"\
               "🌟 Выводить напрямую на свой счет от 1000₽ — просто пиши @heroineVM\n"\
               "💎Оплачивать свой тариф — прям внутри приложения\n"\
               "💡Использовать внутри приложения — скоро расскажем!\n"
        await bot.send_photo(chat_id=message.chat.id, photo=photo, caption=text, parse_mode=ParseMode.HTML)
    
        referral = await db.check_ref(tg_id)
        if referral:
            earned_money = referral.get('earned_money')
            await message.answer(f'<b>🐷 КОПИЛКА 🐽</b>\n\nБаланс: {earned_money} рублей', parse_mode=ParseMode.HTML)
        else:
            await message.answer(f'Для того чтобы у Вас появилась копилка необходимо сгенерировать свой персональный промокод.\nДля его создания воспользуйтесь разделом <b>🎟️ ПРОМОКОД 🎟</b>', parse_mode=ParseMode.HTML)
    
    elif message.text == "📚 ИНСТРУКЦИИ":
        photo = FSInputFile("img/menu/instructions.jpg")
        help_btns = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✍️ Создание анкеты")],
                [KeyboardButton(text="🎟️ Генерация промокода")],
                [KeyboardButton(text="🐽 Копилка"), KeyboardButton(text="💎 Тарифы и оплата")],
                [KeyboardButton(text="♻️ Восстановление доступа")],
                [KeyboardButton(text="Назад ⏪")]
            ],
            resize_keyboard=True
        )
        
        await bot.send_photo(chat_id=message.chat.id, photo=photo, caption="💟 <b>Системное уведомление</b> 💟\nВыберите раздел", reply_markup=help_btns, parse_mode=ParseMode.HTML)
    
    elif message.text == "🛠 ТЕХ. ПРОБЛЕМЫ":
        photo = FSInputFile("img/menu/tech_problems.jpg")
        
        cache_clear_btns = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Очистка кэша - ANDROID")],
                [KeyboardButton(text="📱 Очистка кэша - IOS")],
                [KeyboardButton(text="Назад ⏪")]
            ], 
            resize_keyboard=True
        )
        
        await bot.send_photo(chat_id=message.chat.id, photo=photo, caption="Если у Вас возникла проблема при работе с Telegram-ботом или приложением и Вы не смогли найти решение в представленных инструкциях, пожалуйста, сообщите нам об этом!\n\nВ данном разделе рассмотрены возможные способы решения распространённых проблем, которые возникают при взаимодействии с Telegram-ботом и приложением.", parse_mode=ParseMode.HTML)
        await message.answer("💟 <b>Системное уведомление</b> 💟\nВыберите категорию", reply_markup=cache_clear_btns, parse_mode=ParseMode.HTML)
    
    elif message.text == "📲 ОБРАТНАЯ СВЯЗЬ":
        first_name = message.from_user.first_name
        photo = FSInputFile("img/menu/feedback.jpg")
        text = f"Здравствуйте, {first_name}! 🌟\n\n"\
                "Спасибо, что проявили интерес — приятно познакомиться! Все ли понравилось или есть моменты, которые можно улучшить?\n\n"\
                "Ваше мнение очень важно для нас — поможете сделать «АСТРО-ЛЮБОВЬ❤️‍🔥» еще лучше? 💫\n\n"\
                "Мы можем обсудить это лично или просто оставьте короткий отзыв здесь.\n"\
                "Будем рады услышать любые мысли!\n\n"\
                "С уважением,\n"\
                "Команда АСТРО-ЛЮБОВЬ❤️‍🔥"
            
        msg_btns = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📩 Написать сообщение", callback_data="leave_msg")],
                [InlineKeyboardButton(text="📲 Связаться напрямую", url="tg://resolve?domain=heroineVM")]
            ],
            resize_keyboard=True
        )
        await bot.send_photo(chat_id=message.chat.id, photo=photo, caption=text, reply_markup=msg_btns, parse_mode=ParseMode.HTML)
    
    elif message.text == "⭐️ ПАРТНЁРСКАЯ ПРОГРАММА ⭐️":
        photo = FSInputFile("img/menu/partners.jpg")
        part_btns = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⚜️ НАШИ ПАРТНЁРЫ ⚜️")],
                # [KeyboardButton(text="🥇 СПИСОК НАШИХ ПАРТНЕРОВ 🥇")],
                [KeyboardButton(text="🔱 КАК СТАТЬ ПАРТНЁРОМ 🔱")],
                [KeyboardButton(text="Назад ⏪")]
            ],
            resize_keyboard=True
        )
        await bot.send_photo(chat_id=message.chat.id, photo=photo, caption="💟 <b>Системное уведомление</b> 💟\nВыберите категорию", reply_markup=part_btns, parse_mode=ParseMode.HTML)
    
    elif message.text == "⚜️ НАШИ ПАРТНЁРЫ ⚜️":
        text = "Наши партнёры — друзья, которые делают ASTRO-LOVE❤️‍🔥 ярче!\n\n"\
               "Вместе мы создаём магию любви и доверия💫\n"\
               "Благодаря нашим партнёрам тысячи людей найдут свою гармонию!\n\n"\
               "Пользователи, которые купили любой платный тариф «АСТРО-ЛЮБОВЬ»❤️‍🔥,\n"\
               "имеют доступ к привилегиями от наших партнеров🙌🏻\n"\
               "О том, как стать нашим партнером смотри в другом разделе меню:\n<b>🔱 СТАТЬ НАШИМ ПАРТНЁРОМ 🔱</b>"
        await message.answer(text, parse_mode=ParseMode.HTML)
    
    elif message.text == "🔱 КАК СТАТЬ ПАРТНЁРОМ 🔱":
        text = "Стань партнёром ASTRO-LOVE❤️‍🔥 — зарабатывай на любви и звёздах! 🌟💘\n\n"\
               "Хочешь получать доход, помогая людям находить любовь через астрологию? Присоединяйся к нашей партнёрской программе!\n\n"\
               "<b>Кому подходит? Кем нужно быть?</b>\n"\
               "📲 Медийной личностью, блогером, лидером мнений\n"\
               "🎤 Специалистом в своей сфере , которая может быть интересна нашим пользователям (ведущий свадеб, фотограф и т.д.)\n"\
               "💒 Предпринимателем, владельцам бизнеса\n"\
               "(цветочные, кофейни, рестораны и т.д.)\n\n"\
               "<b>Почему это выгодно?</b>\n"\
               "🔥 Высокие проценты – твой доход растёт, обговариваем лично\n"\
               "✨ Готовые материалы – баннеры, посты, тексты для рекламы.\n"\
               "💬 Поддержка 24/7– помогаем на всех этапах\n"\
               "💯 Выплачиваем деньгами , а не баллами!\n\n"\
               "<b>Как это работает?</b>\n"\
               "1️⃣ Оставляешь заявку → @heroineVM\n"\
               "2️⃣ Получаешь ссылку/промокод → размещаешь в своих соц.сетях или на предприятии\n"\
               "3️⃣ Привлекаешь клиентов → через соцсети, блог, знакомых.\n"\
               "4️⃣ Зарабатываешь → с каждой продажи или лида!\n\n\n"\
               "Крути колесо фортуны в свою пользу — начни прямо сейчас!💫🚀"
            
        msg_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📩 Пиши", url="tg://resolve?domain=heroineVM")]])
        await message.answer(text, reply_markup=msg_btn, parse_mode=ParseMode.HTML)


@dp.message(F.text.in_(["💡 Тариф «СТАРТ»", "🔮 Тариф «БАЗОВЫЙ»", "💳 Тариф «VIP»", "💎 Тариф «SUPER VIP»"]))
async def tariff_handler(message: Message):
    if message.text == "💡 Тариф «СТАРТ»":
        description = "💡 <b>Тариф «СТАРТ»</b> — 599₽\n\n"\
                      "✨️ 5 мэтчей\n"\
                      "✨️ 5 прокруток «Сколько в тебе любви»\n"\
                      "✨️ 5 прокруток «Спидометра совместимости»\n"\
                      "✨️ Срок действия: 30 дней\n"\
                      "✨️ Подбор мэтчей в порядке очереди\n"\
                      "✨️ Совместимость по астрологии"
        buy_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Купить сейчас", callback_data="buy_now_start")]])
    
    elif message.text == "🔮 Тариф «БАЗОВЫЙ»":
        description = "🔮 <b>Тариф «БАЗОВЫЙ»</b> — 999₽\n\n"\
                      "✨️ 10 мэтчей\n"\
                      "✨️ 10 прокруток «Сколько в тебе любви»\n"\
                      "✨️ 10 прокруток «Спидометра совместимости»\n"\
                      "✨️ Срок действия: 30 дней\n"\
                      "✨️ Подбор мэтчей в порядке очереди\n"\
                      "✨️ Совместимость по астрологии"
        buy_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Купить сейчас", callback_data="buy_now_base")]])
        
    elif message.text == "💳 Тариф «VIP»":
        description = "💳 <b>Тариф «VIP»</b> — 2 999₽\n\n"\
                      "✨️ Неограниченное количество мэтчей\n"\
                      "✨️ Неограниченное количество прокруток «Сколько в тебе любви»\n"\
                      "✨️ Неограниченное прокруток «Спидометра совместимости»\n"\
                      "✨️ Срок действия: 30 дней\n"\
                      "✨️ Подбор мэтчей вне очереди\n"\
                      "✨️ Совместимость по всем программам"
        buy_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Купить сейчас", callback_data="buy_now_vip")]])
    
    elif message.text == "💎 Тариф «SUPER VIP»":
        description = "💎 <b>Тариф «SUPER VIP»</b> — 9 999₽\n\n"\
                      "✨️ Неограниченное количество мэтчей\n"\
                      "✨️ Неограниченное количество прокруток «Сколько в тебе любви»\n"\
                      "✨️ Неограниченное прокруток «Спидометра совместимости»\n"\
                      "✨️ Срок действия:  1 год\n"\
                      "✨️ Подбор мэтчей вне очереди\n"\
                      "✨️ Совместимость по всем программам"
        buy_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Купить сейчас", callback_data="buy_now_supervip")]])
    
    await message.answer(text=description, reply_markup=buy_btn, parse_mode=ParseMode.HTML)


@dp.message(F.text.in_(["✍️ Создание анкеты", "🎟️ Генерация промокода", "🐽 Копилка", "💎 Тарифы и оплата", "Назад ⏪", "📱 Очистка кэша - ANDROID", "📱 Очистка кэша - IOS"]))
async def help_handler(message: Message):
    if message.text == "✍️ Создание анкеты":
        main_photo = FSInputFile("img/help/create_form/create.png")
        
        step_1 = FSInputFile("img/help/create_form/Шаг_1.png")
        step_2 = FSInputFile("img/help/create_form/Шаг_2.png")
        step_3 = FSInputFile("img/help/create_form/Шаг_3.png")
        step_4 = FSInputFile("img/help/create_form/Шаг_4.png")
        step_5 = FSInputFile("img/help/create_form/Шаг_5.png")
        step_6 = FSInputFile("img/help/create_form/Шаг_6.png")
        
        media = [
            InputMediaPhoto(media=step_1),
            InputMediaPhoto(media=step_2),
            InputMediaPhoto(media=step_3),
            InputMediaPhoto(media=step_4),
            InputMediaPhoto(media=step_5),
            InputMediaPhoto(media=step_6)
        ]
        
        await bot.send_photo(chat_id=message.chat.id, photo=main_photo, parse_mode=ParseMode.HTML)
        await bot.send_media_group(chat_id=message.chat.id, media=media)
    
    elif message.text == "🎟️ Генерация промокода":
        main_photo = FSInputFile("img/help/generate_promo/gen_promo.png")
        
        step_1 = FSInputFile("img/help/generate_promo/Шаг_1.png")
        step_2 = FSInputFile("img/help/generate_promo/Шаг_2.png")
        
        media = [InputMediaPhoto(media=step_1), InputMediaPhoto(media=step_2)]
        
        await bot.send_photo(chat_id=message.chat.id, photo=main_photo, parse_mode=ParseMode.HTML)
        await bot.send_media_group(chat_id=message.chat.id, media=media)
    
    elif message.text == "🐽 Копилка":
        main_photo = FSInputFile("img/help/wallet/wallet.png")
        
        step_1 = FSInputFile("img/help/wallet/Шаг_1.png")
        step_2 = FSInputFile("img/help/wallet/Шаг_2.png")
        
        media = [InputMediaPhoto(media=step_1), InputMediaPhoto(media=step_2)]
        
        await bot.send_photo(chat_id=message.chat.id, photo=main_photo, parse_mode=ParseMode.HTML)
        await bot.send_media_group(chat_id=message.chat.id, media=media)
    
    elif message.text == "💎 Тарифы и оплата":
        main_photo = FSInputFile("img/help/payment/payment.png")
        
        step_1 = FSInputFile("img/help/payment/Шаг_1.png")
        step_2 = FSInputFile("img/help/payment/Шаг_2.png")
        step_3 = FSInputFile("img/help/payment/Шаг_3.png")
        step_4 = FSInputFile("img/help/payment/Шаг_4.png")
        step_5 = FSInputFile("img/help/payment/Шаг_5.png")
        
        media = [
            InputMediaPhoto(media=step_1),
            InputMediaPhoto(media=step_2),
            InputMediaPhoto(media=step_3),
            InputMediaPhoto(media=step_4),
            InputMediaPhoto(media=step_5)
        ]
        
        await bot.send_photo(chat_id=message.chat.id, photo=main_photo, parse_mode=ParseMode.HTML)
        await bot.send_media_group(chat_id=message.chat.id, media=media)
    
    elif message.text == "Назад ⏪":
        menu_btns = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔥 АСТРО ЧАТ 💭"), KeyboardButton(text="🎟️ ПРОМОКОД 🎟️")],
                [KeyboardButton(text="💎 ТАРИФЫ 💎"), KeyboardButton(text="🐷 КОПИЛКА 🐽")],
                [KeyboardButton(text="⭐️ ПАРТНЁРСКАЯ ПРОГРАММА ⭐️")],
                [KeyboardButton(text="📚 ИНСТРУКЦИИ"), KeyboardButton(text="🛠 ТЕХ. ПРОБЛЕМЫ")],
                [KeyboardButton(text="📲 ОБРАТНАЯ СВЯЗЬ")]
                
            ], 
            resize_keyboard=True
        )
    
        await message.answer("💟 <b>Системное уведомление</b> 💟\nВы вернулись в главное меню", reply_markup=menu_btns, parse_mode=ParseMode.HTML)
    
    elif message.text == "📱 Очистка кэша - ANDROID":
        step_1 = FSInputFile("img/help/tech_problems/cache_clear_android/Шаг_1.png")
        step_2 = FSInputFile("img/help/tech_problems/cache_clear_android/Шаг_2.png")
        step_3 = FSInputFile("img/help/tech_problems/cache_clear_android/Шаг_3.png")
        step_4 = FSInputFile("img/help/tech_problems/cache_clear_android/Шаг_4.png")
        step_5 = FSInputFile("img/help/tech_problems/cache_clear_android/Шаг_5.png")
        step_6 = FSInputFile("img/help/tech_problems/cache_clear_android/Шаг_6.png")
        step_7 = FSInputFile("img/help/tech_problems/cache_clear_android/Шаг_7.png")
        step_8 = FSInputFile("img/help/tech_problems/cache_clear_android/Шаг_8.png")
        step_9 = FSInputFile("img/help/tech_problems/cache_clear_android/Шаг_9.png")
        step_10 = FSInputFile("img/help/tech_problems/cache_clear_android/Шаг_10.png")
        
        media = [
            InputMediaPhoto(media=step_1),
            InputMediaPhoto(media=step_2),
            InputMediaPhoto(media=step_3),
            InputMediaPhoto(media=step_4),
            InputMediaPhoto(media=step_5),
            InputMediaPhoto(media=step_6),
            InputMediaPhoto(media=step_7),
            InputMediaPhoto(media=step_8),
            InputMediaPhoto(media=step_9),
            InputMediaPhoto(media=step_10)
        ]
        
        await bot.send_media_group(chat_id=message.chat.id, media=media)
        # await message.answer(text="При некорректной работе приложения Telegram (ограниченная функциональность, неработоспособность кнопок, отсутствие обновлений интерфейса)  может помочь очистка кэша на вашем устройстве.", reply_markup=None)
    elif message.text == "📱 Очистка кэша - IOS":
        step_1 = FSInputFile("img/help/tech_problems/cache_clear_ios/Шаг_1.png")
        step_2 = FSInputFile("img/help/tech_problems/cache_clear_ios/Шаг_2.png")
        step_3 = FSInputFile("img/help/tech_problems/cache_clear_ios/Шаг_3.png")
        step_4 = FSInputFile("img/help/tech_problems/cache_clear_ios/Шаг_4.png")
        step_5 = FSInputFile("img/help/tech_problems/cache_clear_ios/Шаг_5.png")
        step_6 = FSInputFile("img/help/tech_problems/cache_clear_ios/Шаг_6.png")
        step_7 = FSInputFile("img/help/tech_problems/cache_clear_ios/Шаг_7.png")
        step_8 = FSInputFile("img/help/tech_problems/cache_clear_ios/Шаг_8.png")
        step_9 = FSInputFile("img/help/tech_problems/cache_clear_ios/Шаг_9.png")

        media = [
            InputMediaPhoto(media=step_1),
            InputMediaPhoto(media=step_2),
            InputMediaPhoto(media=step_3),
            InputMediaPhoto(media=step_4),
            InputMediaPhoto(media=step_5),
            InputMediaPhoto(media=step_6),
            InputMediaPhoto(media=step_7),
            InputMediaPhoto(media=step_8),
            InputMediaPhoto(media=step_9)
        ]
        
        await bot.send_media_group(chat_id=message.chat.id, media=media)


@dp.message(Command(commands="cancel"))
async def command_cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("♻️ Действие было успешно отменено ")    


@dp.message(Command(commands="admin"))
async def command_admin(message: Message, state: FSMContext):
        tg_id =  message.from_user.id
        first_name = message.from_user.first_name
        
        admin = await db.check_admin(tg_id)
        if (admin):
            key_btns = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Включить режим рассылки", callback_data="admin_send")],
            [InlineKeyboardButton(text="💎 Тарифы", callback_data="admin_tariffs"),
             InlineKeyboardButton(text="🪙 Платежи", callback_data="admin_payments")],
            [InlineKeyboardButton(text="🎟 Реферальная система", callback_data="admin_referrals")],
            [InlineKeyboardButton(text="👤 Пользователи", callback_data="admin_user_list"), 
            InlineKeyboardButton(text="🚫 Чёрный список", callback_data="admin_black_list")],
            [InlineKeyboardButton(text="🎲 Администраторы", callback_data="admin_list")]], resize_keyboard=True)
            # [InlineKeyboardButton(text="Добавить в ЧС", callback_data="admin_ban_user"), 
            #  InlineKeyboardButton(text="Удалить из ЧС", callback_data="admin_unban_user")]
            
            await message.answer(f'<b>🥷 Панель администратора 🥷</b>', reply_markup=key_btns, parse_mode=ParseMode.HTML)


@dp.callback_query(F.data.startswith("admin_"))
async def admin_query(query: CallbackQuery, state: FSMContext):
    if (query.data == 'admin_send'):
        await query.message.answer("Для рассылки воспользуйтесь командой /send")
    elif (query.data == 'admin_user_list'): 
        user_list = await db.user_list()
        for user in user_list:
            user['Добавлен'] = user['Добавлен'].replace(' ', '\n', 1)
        table = tabulate(user_list, headers='keys', tablefmt="simple")

        table_message = length_control(table, 4096)
        for table in table_message:
            await query.message.answer(f'```Пользователи\n{table}```', parse_mode=ParseMode.MARKDOWN_V2)

    elif (query.data == 'admin_payments'):
        payments_list = await db.payment_list()
        for payment in payments_list:
            payment['Дата\nплатежа'] = payment['Дата\nплатежа'].replace(' ', '\n', 1)
        table = tabulate(payments_list, headers='keys', tablefmt="simple")
        await query.message.answer(f'```Платежи\n{table}```', parse_mode=ParseMode.MARKDOWN_V2)
        
    elif (query.data == 'admin_list'): 
        admin_list = await db.admin_send_list()
        for admin in admin_list:
            admin['Добавлен'] = admin['Добавлен'].replace(' ', '\n', 1)
        table = tabulate(admin_list, headers='keys', tablefmt="simple")
        await query.message.answer(f'```Администраторы\n{table}```', parse_mode=ParseMode.MARKDOWN_V2)
        
    elif (query.data == 'admin_referrals'): 
        key_btns = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Участники реферальной программы", callback_data="admin_ref_list")],
            # [InlineKeyboardButton(text="Воспользоваться SearchID", callback_data="admin_ref_search")],
            # [InlineKeyboardButton(text="Список партнёров программы", callback_data="admin_part_list")],
            [InlineKeyboardButton(text="Добавить нового партнёра", callback_data="admin_add_part")]])
        await query.message.answer("⚙️ <i>Параметры реферальной системы</i>", reply_markup=key_btns, parse_mode=ParseMode.HTML)
    elif (query.data == 'admin_add_part'):
        await query.message.answer("Введите наименование организации")
        await state.set_state(Partners.name)
    elif (query.data == 'admin_ref_list'):
        ref_list =  await db.ref_list()
        table = tabulate(ref_list, headers='keys', tablefmt="simple")
        await query.message.answer(f'```Рефералы\n{table}```', parse_mode=ParseMode.MARKDOWN_V2)
    elif (query.data == 'admin_tariffs'):
        tariff_list = await db.tariff_list()
        table = tabulate(tariff_list, headers='keys', tablefmt="simple")
        await query.message.answer(f'```Тарифы\n{table}```', parse_mode=ParseMode.MARKDOWN_V2)

    elif (query.data == 'admin_black_list'):
        black_list = await db.black_list()
        if black_list:
            table = tabulate(black_list, headers='keys', tablefmt="simple")
            await query.message.answer(f'```Заблокированные\n{table}```', parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await query.message.answer(f'```Заблокированные\nЧёрный список пуст```', parse_mode=ParseMode.MARKDOWN_V2)

@dp.message(Command(commands="cancel"))
async def command_cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("♻️ Действие было успешно отменено ")
    
@dp.message(Partners.name, F.text)
async def partner_name(message: Message, state: FSMContext):
    name = message.text
    await state.update_data(name=name)  # Сохраняем отдельно как name
    await message.answer("Введите описание организации")
    await state.set_state(Partners.description)

@dp.message(Partners.description, F.text)
async def partner_description(message: Message, state: FSMContext):
    description = message.text
    await state.update_data(description=description)  # Сохраняем отдельно как description
    await message.answer("Загрузите фото")
    await state.set_state(Partners.photo)

@dp.message(Partners.photo, F.photo)
async def partner_photo(message: Message, state: FSMContext):
    photo = message.photo[-1].file_id
    await state.update_data(photo=photo)  # Сохраняем отдельно как photo
    await message.answer("Укажите промокод")
    await state.set_state(Partners.promocode)

@dp.message(Partners.promocode, F.text)
async def partner_promocode(message: Message, state: FSMContext):
    promocode = message.text.upper()
    await state.update_data(promocode=promocode)  # Сохраняем отдельно как promocode
    await message.answer("Укажите % скидки по промокоду")
    await state.set_state(Partners.discount)

@dp.message(Partners.discount, F.text)
async def partner_discount(message: Message, state: FSMContext):
    discount = message.text.replace('%', '').strip()  # Удаляем % если есть
    await state.update_data(discount=discount)  # Сохраняем отдельно как discount
    await message.answer("Проверьте данные в карточке парнёра")
    
    data = await state.get_data()
    name = data.get("name")
    description = data.get("description")
    promocode = data.get("promocode")
    discount = data.get("discount")
    photo = data.get("photo")
    key_btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Добавить", callback_data="add_partner_card")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_partner_card")]
    ])
    
    await bot.send_photo(
        chat_id=message.chat.id, 
        photo=photo, 
        caption=f"<b>{name}</b>\n\n<i>{description}</i>\n\n<b>Скидка {discount}% по промокоду:</b> <code>{promocode}</code>", 
        reply_markup=key_btn, parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data == "add_partner_card")
async def cancel_send(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    name = data.get("name")
    description = data.get("description")
    promocode = data.get("promocode")
    discount = data.get("discount")
    photo = data.get("photo")
    await db.add_new_partner(name, description, photo, promocode, discount)
    await callback.message.answer("Карточка партнера добавлена ✅")
    await state.clear()
    part_list =  await db.partner_list()
    table = tabulate(part_list, headers='keys', tablefmt="simple")
    await callback.message.answer(f'```Партнёры\n{table}```', parse_mode=ParseMode.MARKDOWN_V2)
    

@dp.callback_query(F.data == "cancel_partner_card")
async def cancel_send(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Добавление карточки было успешно отменено ❌")
    await state.clear()


@dp.message(Command("send"))
async def start_send(message: Message, state: FSMContext):
    tg_id =  message.from_user.id
    admin = await db.check_admin(tg_id)
    if (admin):
        await message.answer(
            "Режим рассылки активирован ✅\n\n"
            "Отправьте сообщение, фото или видео с подписью или без для рассылки всем пользователям ASTRO-LOVE❤️‍🔥"
        )
        await state.set_state(SendMedia.waiting_media)


# --- Альбом ---
@dp.message(SendMedia.waiting_media, F.media_group_id)
async def handle_album(message: Message, state: FSMContext):
    mg_id = message.media_group_id
    if mg_id not in album_storage:
        album_storage[mg_id] = {"media": [], "caption": None}
        album_storage[mg_id]["timer"] = asyncio.create_task(finalize_album(mg_id, message, state))

    if message.photo:
        album_storage[mg_id]["media"].append({"type": "photo", "file_id": message.photo[-1].file_id})
    elif message.video:
        album_storage[mg_id]["media"].append({"type": "video", "file_id": message.video.file_id})

    if not album_storage[mg_id]["caption"] and message.caption:
        album_storage[mg_id]["caption"] = message.caption


async def finalize_album(media_group_id: str, message: Message, state: FSMContext):
    await asyncio.sleep(1.0)
    data = album_storage.pop(media_group_id, None)
    if not data:
        return

    await state.update_data(media=data["media"], caption=data["caption"], type="media")
    await send_preview(message, state)


# --- Одиночное фото/видео ---
@dp.message(SendMedia.waiting_media, F.photo | F.video)
async def handle_single_media(message: Message, state: FSMContext):
    media_list = []
    caption = message.caption
    if message.photo:
        media_list.append({"type": "photo", "file_id": message.photo[-1].file_id})
    elif message.video:
        media_list.append({"type": "video", "file_id": message.video.file_id})

    await state.update_data(media=media_list, caption=caption, type="media")
    await send_preview(message, state)


# --- Только текст ---
@dp.message(SendMedia.waiting_media, F.text)
async def handle_text(message: Message, state: FSMContext):
    text = message.text
    await state.update_data(text=text, type="text")
    await send_preview(message, state)
    

# --- Предпросмотр ---
async def send_preview(message: Message, state: FSMContext):
    data = await state.get_data()
    tg_id = message.from_user.id

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить", callback_data="send_all")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")]
    ])

    if data.get("type") == "media":
        media_list = data["media"]
        caption = data.get("caption")
        media_group = []
        for idx, item in enumerate(media_list):
            if item["type"] == "photo":
                media = InputMediaPhoto(media=item["file_id"])
            else:
                media = InputMediaVideo(media=item["file_id"])
            if idx == 0 and caption:
                media.caption = caption
            media_group.append(media)

        await bot.send_media_group(chat_id=tg_id, media=media_group)
        await bot.send_message(
            chat_id=tg_id,
            text="⬆️ Предпросмотр содержимого для рассылки ⬆️\n\nОтправить всем пользователям ASTRO-LOVE❤️‍🔥?",
            reply_markup=kb
        )

    elif data.get("type") == "text":
        text = data.get("text")
        await bot.send_message(chat_id=tg_id, text=f"Предпросмотр текста для рассылки:\n\n{text}")
        await bot.send_message(chat_id=tg_id, text="Отправить всем пользователям ASTRO-LOVE❤️‍🔥?", reply_markup=kb)

    await state.set_state(SendMedia.confirm)


# --- Подтверждение отправки ---
@dp.callback_query(SendMedia.confirm, F.data == "send_all")
async def confirm_send(callback: CallbackQuery, state: FSMContext):
    progress_msg = await callback.message.edit_text("Подождите, идёт отправка сообщений...")
    data = await state.get_data()
    
    user_list = await db.user_send_list()
    user_ids = [user['tg_id'] for user in user_list] 
    admin_id = callback.from_user.id  # id администратора, который запустил рассылку

    success, fail = 0, 0

    for user_id in user_ids: 
        if user_id == admin_id:
            continue  # пропускаем отправку самому себе

        if data.get("type") == "media":
            media_list = data["media"]
            caption = data.get("caption")
            media_group = []
            for idx, item in enumerate(media_list):
                if item["type"] == "photo":
                    media = InputMediaPhoto(media=item["file_id"])
                else:
                    media = InputMediaVideo(media=item["file_id"])
                if idx == 0 and caption:
                    media.caption = caption
                media_group.append(media)
            try:
                msgs = await bot.send_media_group(chat_id=user_id, media=media_group)
                sent_messages.setdefault(user_id, []).extend(
                    [{"message_id": m.message_id, "type": "media"} for m in msgs]
                )
                success += 1
            except Exception as e:
                fail += 1
                await db.update_user_status(user_id, "blocked")
                logging.warning(f"Ошибка для {user_id}: {e}")
            await asyncio.sleep(0.05)

        elif data.get("type") == "text":
            text = data.get("text")
            try:
                msg = await bot.send_message(chat_id=user_id, text=text)
                sent_messages.setdefault(user_id, []).append({"message_id": msg.message_id, "type": "text"})
                success += 1
            except Exception as e:
                fail += 1
                await db.update_user_status(user_id, "blocked")
                logging.warning(f"Ошибка для {user_id}: {e}")
            await asyncio.sleep(0.05)
    
    edit_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать текст", callback_data="edit_all")],
        [InlineKeyboardButton(text="🗑 Удалить рассылку", callback_data="delete_all")]
    ])
    
    # Отправляем администратору уведомление:
    await progress_msg.edit_text(
        f"Рассылка отправлена ✅\n\n"
        f"Кол-во пользователей, которые успешно получили сообщения: {success}\n"
        f"Кол-во недоставленных сообщений: {fail}", 
        reply_markup=edit_kb
    )

    await state.clear()


# --- Отмена ---
@dp.callback_query(SendMedia.confirm, F.data == "cancel")
async def cancel_send(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Рассылка была отменена ❌")
    await state.clear()


# --- Удаление всех отправленных сообщений ---
@dp.callback_query(F.data == "delete_all")
async def delete_all_messages(callback: CallbackQuery):
    del_msg = await callback.message.edit_text("Подождите, идёт удаление сообщений...")
    deleted, failed = 0, 0

    for user_id, messages in sent_messages.items():
        deleted += 1
        for msg in messages:
            try:
                await bot.delete_message(chat_id=user_id, message_id=msg["message_id"]) 
            except Exception as e:
                failed += 1
                logging.warning(f"Ошибка удаления {msg['message_id']} для {user_id}: {e}")
    
    await del_msg.edit_text(
        f"Процесс удаления завершен ❎\n\nКол-во удаленных сообщений: {deleted}"
    )

    sent_messages.clear()


# --- Запрос нового текста для редактирования ---
@dp.callback_query(F.data == "edit_all")
async def ask_new_text(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Отправьте новый текст для изменения содержимого рассылки")
    await state.set_state(EditState.waiting_new_text)


# --- Применение редактирования ---
@dp.message(EditState.waiting_new_text)
async def apply_edit(message: Message, state: FSMContext):
    new_text = message.text
    edited_msgs, failed_msgs = 0, 0

    for user_id, messages in sent_messages.items():
        for idx, msg in enumerate(messages):
            try:
                if msg["type"] == "text":
                    await bot.edit_message_text(chat_id=user_id, message_id=msg["message_id"], text=new_text)
                    edited_msgs += 1
                elif msg["type"] == "media":
                    # Редактируем подпись только у первого сообщения медиагруппы
                    if idx == 0:
                        await bot.edit_message_caption(chat_id=user_id, message_id=msg["message_id"], caption=new_text)
                        edited_msgs += 1
                    # Для остальных сообщений медиагруппы пропускаем редактирование caption
            except Exception as e:
                failed_msgs += 1
                logging.warning(f"Ошибка редактирования {msg['message_id']} для {user_id}: {e}")

    await message.answer(
        f"Процесс редактирования завершен ✳️\n\n"
        f"Кол-во измененных сообщений: {edited_msgs}"
    )
    await state.clear()


# --- Покупка тарифов ---
@dp.callback_query(F.data.startswith("buy_now_"))
async def tariff_buy_query(query: CallbackQuery):
    date_invoice = f'{dt.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}'
    
    tariffs = {
        'buy_now_start': (599, 'СТАРТ', 'tariff_start'),
        'buy_now_base': (999, 'БАЗОВЫЙ', 'tariff_base'),
        'buy_now_vip': (2999, 'VIP', 'tariff_vip'),
        'buy_now_supervip': (9999, 'SUPER VIP', 'tariff_supervip')
    }

    if query.data in tariffs:
        price, tariff_name, payload_str = tariffs[query.data]
        
        await bot.send_invoice(
            chat_id=query.message.chat.id, 
            title=f'Покупка тарифа {tariff_name}',
            description=f'Создано ------ {date_invoice} ------ Счёт на оплату сформирован. Оплата осуществляется через Telegram.',
            payload=payload_str,
            provider_token=PAYMENT_TOKEN,
            currency='RUB',
            prices=[LabeledPrice(label='Стоимость выбранного тарифа', amount=price * 100)]
        )
        

# --- Процедура оплаты ---
@dp.pre_checkout_query(lambda query: True)
async def pre_checkout_query(pre_checkout: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)


# --- Успешный платёж ---
@dp.message(F.successful_payment)
async def successful_payment(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    username = message.from_user.username
    total_amount = message.successful_payment.total_amount // 100
    logging.info(f'Успешный платёж на сумму {total_amount}: {tg_id} - {username}')
    
    profile_details = await db.check_profile_details(tg_id)
    if not profile_details:
        await db.add_new_profile_details(tg_id)
        
    currency = message.successful_payment.currency
    description = message.successful_payment.invoice_payload
    
    payload = description.split('_')
    selected_tariff = payload[1]
    promocode = payload[2] if len(payload) == 3 else None
    
    tariffs = {
        "start": (2, 599, "СТАРТ"),
        "base": (3, 999, "БАЗОВЫЙ"),
        "vip": (4, 2999, "VIP"),
        "supervip": (5, 9999, "SUPER VIP"),
        "spinner": (7, 2999, "КРУЧУ ВЕРЧУ")
    }
    
    tariff_id, price, name = tariffs[selected_tariff]

    await db.update_user_details(tg_id, tariff_id)
    await db.add_new_payment(tg_id, description, total_amount, tariff_id)
    
    if promocode:
        ref_id = await db.check_ref_by_promo(promocode)
        earned_money = price - total_amount
        await db.update_earned_money(ref_id, earned_money)
        await db.add_new_invited(ref_id, tg_id)
    
    await message.answer(f'Оплата тарифа «{name}» на сумму {total_amount} {currency} прошла успешно!\nВаш тарифный план был изменён. Благодарим за покупку! ')



async def main():
    # Подключаемся к бд
    await db.connect()
    try:
        # Запускаем бота
        await dp.start_polling(bot)
    finally:
        # Закрываем соединение с бд при завершении
        await db.close()
        await bot.session.close()
        


if __name__ == "__main__":
    asyncio.run(main())





# @dp.message(Command(commands="start"))
# async def command_start(message: Message):
#     admin_list = await db.admin_list()
#     await message.answer("Запуск прошёл успешно!")
#     await message.answer(str(admin_list))


# @dp.message()
# async def echo_message(message: Message):
#     ai_response = await get_ai_reply(message.text)
#     await message.answer(str(ai_response), parse_mode=ParseMode.HTML)


