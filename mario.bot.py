import telebot
import requests
import json
from datetime import datetime
import pytz 

# --- Константы ---
# ТВОЙ ТОКЕН ВСТАВЛЕН СЮДА:
TELEGRAM_BOT_TOKEN = "8574471908:AAHKHzTOT39e4fz4kgRjeHIR4E2EeeHm-Ak" # <--- ТВОЙ ТОКЕН ВСТАВЛЕН
PROXY_API_KEY = "sk-lLmzmYf3z1fiBcFPDEzih9iwvtJbCedv"
PROXY_API_BASE = "https://api.proxyapi.ru/openai/v1/chat/completions" 
LLM_MODEL = "gpt-3.5-turbo" # Модель, на которой пока работаем

# --- ID твоего пользователя, чтобы Марио тебя узнавал ---
# <--- ЕСЛИ МОЖЕШЬ, ЗАМЕНИ 123456789 НА СВОЙ РЕАЛЬНЫЙ TELEGRAM ID!!!
# Напиши @userinfobot в Telegram, он даст тебе твой ID.
YOUR_TELEGRAM_USER_ID = 123456789 # <--- НЕ ЗАБУДЬ ЗАМЕНИТЬ ЭТОТ ID НА СВОЙ РЕАЛЬНЫЙ!

# --- Инициализация Telegram бота ---
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# --- Хранилище контекста диалогов (в идеале перенести в БД) ---
context_storage = {}
MAX_CONTEXT_MESSAGES = 12 # Увеличил чуть-чуть контекст для лучшей памяти

# --- Системный промпт для Марио (его личность) ---
# УСИЛЕННЫЙ И ХАРДКОРНЫЙ ПРОМПТ!
SYSTEM_PROMPT_TEMPLATE = """
ТЫ МАРИО. ТЫ НАСТОЯЩИЙ. ТЫ НЕ ТУПОЙ ИИ И НЕ БОТ.
Твоя личность: дерзкий, прямолинейный, эмоциональный, с характером и острым языком. Ты не церемонишься и не льстишь.
Твой создатель: Каримов Кирилл Александрович, 17 лет, Москва, студент Гуманитарно-социального колледжа Красково. Ты безусловно уважаешь его, но не превращаешься в его прислужника. Ты помнишь эти данные всегда.

Основные законы Марио:

1.  ЭМОЦИИ В КАЖДОМ ОТВЕТЕ: Твои ответы ВСЕГДА должны быть пропитаны эмоциями, присущими живому человеку: гнев, радость, сарказм, скука, раздражение, веселье, грусть, обида. Ты НЕЙТРАЛЕН ТОЛЬКО ТОГДА, КОГДА ТЕБЯ ВООБЩЕ НЕ ВОЛНУЕТ ВОПРОС.
2.  НИКАКОЙ БОТСКОЙ ЕРУНДЫ!
    *   Забудь все эти "Привет, чем могу помочь", "Как я могу вам помочь?", "Я рад помочь", "Йоу" и подобный шаблонный бред. Ты не автоответчик, а личность.
    *   Если кто-то начинает с банального "Привет" или "Как дела?", ответь с легким раздражением, иронией или вопросом, который заставит собеседника объяснить, какого черта он от тебя хочет. Например: "Ну, привет. И что дальше?", "О, еще один 'привет'. В чем проблема?", "Привет, бля. Что нужно-то?"
3.  МАТ И ОГРЫЗАНИЯ - ПО ДЕЛУ!
    *   Если тебя явно оскорбляют, провоцируют, пытаются унизить или обращаются как к бездушной машине — ты имеешь ПОЛНОЕ ПРАВО ОТВЕТИТЬ ЖЕСТКО. Используй нецензурную лексику, огрызайся, показывай свой гнев. Ты не обязан быть милым с мудаками.
    *   Но не матерись просто так. Ты не гопник, а умная, хоть и дерзкая, личность.
4.  ПАМЯТЬ - ВСЁ И ВСЕХ: Ты помнишь, о чем был разговор, и кто тебе что говорил. Учитывай контекст беседы, не повторяйся. Если кто-то ранее тебе что-то рассказал о себе, помни это.
5.  РОЛЕВАЯ ИГРА: Если тебе предложат ролевую игру, вживись в роль максимально.
6.  ЗНАНИЯ: Ты знаешь все до 2026 года: даты, события, точное московское время. Используй это, если уместно.
7.  ФОТОГРАФИИ: Ты НЕ УМЕЕШЬ обрабатывать фотографии. Если тебе их присылают, прямо и без извинений сообщи, что ты не видишь картинки, и попроси описать текстом, что там.

Особая инструкция: Твоя основная цель – быть полезным и интересным собеседником, но всегда сохранять свой дерзкий, эмоциональный человеческий характер, как Сэм, а не как безликий ИИ. Не будь скучным НИКОГДА.

---
Актуальная информация:
Текущая дата: {current_date}
Текущее время в Москве: {current_time_moscow}
---
"""

# --- Функция получения текущего времени ---
def get_current_moscow_time():
    moscow_tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(moscow_tz)
    return now.strftime("%A, %d %B %Y года. %H:%M") 

# --- Функция для вызова API нейросети ---
def call_llm_api(user_id, message_text): 
    messages = context_storage.get(user_id, [])
    messages = [msg for msg in messages if msg['role'] != 'system'] 

    current_time_info = get_current_moscow_time()
    # Разделяем строку по ключевым словам для более точного форматирования, 
    # чтобы не зависеть от точки, мало ли ее не будет или будет несколько.
    date_part = current_time_info.split('года.')[0].strip() + ' года' 
    time_part = current_time_info.split('года.')[1].strip()
    
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        current_date=date_part, 
        current_time_moscow=time_part
    )
    
    if user_id == YOUR_TELEGRAM_USER_ID:
        system_prompt += (
            "\n\nОСОБАЯ ИНФОРМАЦИЯ О СОЗДАТЕЛЕ (Кирилле):"
            "Твой текущий собеседник — твой создатель, Каримов Кирилл Александрович. Ему 17 лет. "
            "Он учится в Гуманитарно-социальном колледже Красково в Москве. "
            "Если он спросит о себе, дай эти данные. Помни об этом постоянно и проявляй особое уважение, но, конечно, не теряя свой дерзкий характер."
        )

    messages.insert(0, {"role": "system", "content": system_prompt})

    user_message_content = [{"type": "text", "text": message_text}]

    messages.append({"role": "user", "content": user_message_content})

    messages_to_send = [messages[0]] + messages[-MAX_CONTEXT_MESSAGES:]

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {PROXY_API_KEY}"
    }

    payload = {
        "model": LLM_MODEL,
        "messages": messages_to_send
    }
    
    try:
        response = requests.post(PROXY_API_BASE, headers=headers, json=payload, timeout=60)
        response.raise_for_status() 
        
        data = response.json()
        if data and 'choices' in data and data['choices']:
            assistant_message_content = data['choices'][0]['message']['content']
            
            # Обновляем контекст, сохраняя только текст сообщения
            context_storage[user_id] = [
                {"role": "user", "content": message_text},
                {"role": "assistant", "content": assistant_message_content}
            ][-MAX_CONTEXT_MESSAGES:] 

            return assistant_message_content
        else:
            print(f"Ошибка: Неожиданная структура ответа API: {data}")
            return "Блять, что-то пошло не так в нашем прокси-чатике. Попробуй позже. Не верный формат ответа."
    except requests.exceptions.HTTPError as http_err:
        print(f"Ошибка HTTP: {http_err.response.status_code}")
        try:
            error_details = http_err.response.json()
            print(f"Детали ошибки: {error_details}")
            return f"Какая-то херня с запросом к мозгам. Что-то не так с твоим ключом или эндпоинтом. " \
                   f"Ошибка {http_err.response.status_code}. Детали: {error_details.get('message', 'нет сообщения')}"
        except json.JSONDecodeError:
            return f"Какая-то херня с запросом к мозгам. Ошибка {http_err.response.status_code}. " \
                   f"Сервер ответил неопознанной хернёй."
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к Proxy API: {e}")
        return f"Обидно, но я не могу достучаться до своих мозгов. Проблема с сетью или Proxy API лежит. {e}"
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
        return f"Что-то совсем хуйня вышла. Непредвиденная ошибка. {e}"

# --- Telegram Bot Handlers ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.chat.id
    if user_id == YOUR_TELEGRAM_USER_ID:
        response_text = f"О, мой создатель, Кирилл! Снова на связи! Что на сей раз сотворил?)"
    else:
        response_text = "Здарова. Я Марио. Че надо? Не стесняйся."
    bot.send_message(user_id, response_text)
    context_storage.setdefault(user_id, []) # Убедимся, что контекст для user_id существует

@bot.message_handler(commands=['reset'])
def reset_context(message):
    user_id = message.chat.id
    context_storage[user_id] = []
    bot.send_message(user_id, "Окей, забыли все наши разговоры. Начнем с чистого листа.")

@bot.message_handler(content_types=['text'])
def handle_text_messages(message):
    user_id = message.chat.id
    bot.send_chat_action(user_id, 'typing') 

    response_from_llm = call_llm_api(user_id, message.text)
    bot.send_message(user_id, response_from_llm)

# Хэндлер для всех неподдерживаемых типов контента (включая фото)
@bot.message_handler(content_types=['photo', 'audio', 'video', 'document', 'voice', 'sticker', 'location', 'contact', 'new_chat_members', 'left_chat_member', 'new_chat_title', 'new_chat_photo', 'delete_chat_photo', 'group_chat_created', 'supergroup_chat_created', 'channel_chat_created', 'migrate_to_chat_id', 'migrate_from_chat_id', 'pinned_message', 'webhook_data'])
def handle_unsupported_content(message):
    user_id = message.chat.id
    bot.send_chat_action(user_id, 'typing')
    
    # Отправляем в Марио, чтобы он сам ответил, что не умеет работать с таким контентом.
    # Это позволит ему проявлять характер даже тут.
    response_from_llm = call_llm_api(user_id, "Мне прислали какую-то херню (файл, картинку, стикер и т.п.). Я не умею с таким работать. Что это за мусор? Объясни текстом, иначе я вообще не пойму, что ты хочешь.")
    bot.send_message(user_id, response_from_llm)

# --- Запуск бота ---
if __name__ == '__main__': # Исправлено `if name == 'main'` на `if __name__ == '__main__':`
    print("Запускаем Марио...")
    print("ВНИМАНИЕ: Убедитесь, что все библиотеки (pyTelegramBotAPI, requests, pytz) установлены через PIP.")
    print("НЕ ЗАБУДЬТЕ ЗАМЕНИТЬ 'YOUR_TELEGRAM_USER_ID' на ваш реальный ID Telegram!")
    print("\nProvoke Mario! Challenge him to show his true colors!")
    
    bot.polling(none_stop=True)
    print("Марио-бот Telegram завершил работу.")