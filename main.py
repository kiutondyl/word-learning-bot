import os
import random
import sqlite3
from telebot import TeleBot, types
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(BOT_TOKEN)

# ===== СЛОВАРИ СЛОВ =====
WORDS = {
    "english": [
        {"word": "apple", "translation": "яблоко", "example": "I eat an apple every day."},
        {"word": "book", "translation": "книга", "example": "This book is very interesting."},
        {"word": "house", "translation": "дом", "example": "My house is big."},
        {"word": "water", "translation": "вода", "example": "I drink water."},
        {"word": "friend", "translation": "друг", "example": "He is my best friend."},
        {"word": "time", "translation": "время", "example": "I don't have time."},
        {"word": "work", "translation": "работа", "example": "I go to work."},
        {"word": "day", "translation": "день", "example": "Today is a good day."},
        {"word": "love", "translation": "любовь", "example": "Love is beautiful."},
        {"word": "life", "translation": "жизнь", "example": "Life is good."},
        {"word": "world", "translation": "мир", "example": "The world is big."},
        {"word": "year", "translation": "год", "example": "This year is special."},
        {"word": "people", "translation": "люди", "example": "People are kind."},
        {"word": "way", "translation": "путь", "example": "This is the right way."},
        {"word": "city", "translation": "город", "example": "I live in a city."},
    ],
    "spanish": [
        {"word": "hola", "translation": "привет", "example": "¡Hola! ¿Cómo estás?"},
        {"word": "gracias", "translation": "спасибо", "example": "Muchas gracias."},
        {"word": "amigo", "translation": "друг", "example": "Él es mi amigo."},
        {"word": "casa", "translation": "дом", "example": "Mi casa es tu casa."},
        {"word": "agua", "translation": "вода", "example": "Necesito agua."},
        {"word": "comida", "translation": "еда", "example": "La comida está buena."},
        {"word": "familia", "translation": "семья", "example": "Mi familia es grande."},
        {"word": "trabajo", "translation": "работа", "example": "Tengo mucho trabajo."},
        {"word": "amor", "translation": "любовь", "example": "El amor es importante."},
        {"word": "tiempo", "translation": "время", "example": "No tengo tiempo."},
    ],
    "german": [
        {"word": "hallo", "translation": "привет", "example": "Hallo, wie geht's?"},
        {"word": "danke", "translation": "спасибо", "example": "Vielen Dank!"},
        {"word": "haus", "translation": "дом", "example": "Das Haus ist groß."},
        {"word": "wasser", "translation": "вода", "example": "Ich trinke Wasser."},
        {"word": "freund", "translation": "друг", "example": "Er ist mein Freund."},
        {"word": "arbeit", "translation": "работа", "example": "Ich gehe zur Arbeit."},
        {"word": "liebe", "translation": "любовь", "example": "Liebe ist schön."},
        {"word": "zeit", "translation": "время", "example": "Ich habe keine Zeit."},
        {"word": "buch", "translation": "книга", "example": "Das Buch ist gut."},
        {"word": "stadt", "translation": "город", "example": "Die Stadt ist schön."},
    ]
        "korean": [
        {"word": "annyeong", "translation": "привет", "example": "Annyeong! Chineseyo?"},
        {"word": "gamsahabnida", "translation": "спасибо", "example": "Gamsahabnida!"},
        {"word": "chingu", "translation": "друг", "example": "Nae chingu."},
        {"word": "jip", "translation": "дом", "example": "Jip-i keoyo."},
        {"word": "mul", "translation": "вода", "example": "Mul juseyo."},
        {"word": "gongbu", "translation": "учеба", "example": "Gongbu haeyo."},
        {"word": "sarang", "translation": "любовь", "example": "Saranghae!"},
        {"word": "hakgyo", "translation": "школа", "example": "Hakgyo-e gayo."},
        {"word": "chik", "translation": "работа", "example": "Chik-e gaseyo."},
        {"word": "il", "translation": "день", "example": "Oneul-eun joheun il."},
    ]

}

LANGUAGE_NAMES = {
    "english": "🇧 Английский",
    "spanish": "🇪 Испанский",
    "german": "🇩🇪 Немецкий",
    "korean": "🇰🇷 Корейский"

}

# ===== БАЗА ДАННЫХ =====
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            language TEXT DEFAULT 'english',
            learned_words TEXT DEFAULT '',
            correct_answers INTEGER DEFAULT 0,
            total_answers INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,))
        conn.commit()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
    return user

def update_user(user_id, **kwargs):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    for key, value in kwargs.items():
        cursor.execute(f'UPDATE users SET {key} = ? WHERE user_id = ?', (value, user_id))
    conn.commit()
    conn.close()

def add_learned_word(user_id, word):
    user = get_user(user_id)
    learned = user[2] if user[2] else ''
    if word not in learned.split(','):
        learned = f"{learned},{word}" if learned else word
        update_user(user_id, learned_words=learned)

def add_answer(user_id, correct):
    user = get_user(user_id)
    correct_count = user[3] + (1 if correct else 0)
    total_count = user[4] + 1
    update_user(user_id, correct_answers=correct_count, total_answers=total_count)

# ===== ИНИЦИАЛИЗАЦИЯ =====
init_db()

# ===== КОМАНДЫ =====
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for lang_code, lang_name in LANGUAGE_NAMES.items():
        markup.add(types.KeyboardButton(lang_name))
    
    bot.send_message(
        user_id,
        "👋 Привет! Я бот для изучения иностранных слов.\n\n"
        "Выбери язык для изучения:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text in LANGUAGE_NAMES.values())
def select_language(message):
    user_id = message.chat.id
    for lang_code, lang_name in LANGUAGE_NAMES.items():
        if message.text == lang_name:
            update_user(user_id, language=lang_code)
            bot.send_message(
                user_id,
                f"✅ Отлично! Ты выбрал: {lang_name}\n\n"
                f"Используй команды:\n"
                f"/learn — выучить новое слово\n"
                f"/quiz — пройти тест\n"
                f"/stats — твоя статистика\n"
                f"/reset — сбросить прогресс",
                reply_markup=types.ReplyKeyboardRemove()
            )
            break

@bot.message_handler(commands=['learn'])
def learn(message):
    user_id = message.chat.id
    user = get_user(user_id)
    lang = user[1]
    learned = user[2].split(',') if user[2] else []
    
    available = [w for w in WORDS[lang] if w["word"] not in learned]
    
    if not available:
        bot.send_message(user_id, "🎉 Ты выучил все слова! Используй /reset чтобы начать заново.")
        return
    
    word_data = random.choice(available)
    add_learned_word(user_id, word_data["word"])
    
    bot.send_message(
        user_id,
        f" Новое слово:\n\n"
        f" *{word_data['word']}*\n"
        f"📝 Перевод: {word_data['translation']}\n"
        f" Пример: _{word_data['example']}_\n\n"
        f"Используй /quiz чтобы проверить знания!",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['quiz'])
def quiz(message):
    user_id = message.chat.id
    user = get_user(user_id)
    lang = user[1]
    
    word_data = random.choice(WORDS[lang])
    correct_word = word_data["word"]
    
    other_words = [w["word"] for w in WORDS[lang] if w["word"] != correct_word]
    options = random.sample(other_words, min(3, len(other_words)))
    options.append(correct_word)
    random.shuffle(options)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for option in options:
        markup.add(types.InlineKeyboardButton(option, callback_data=f"quiz_{option}_{correct_word}"))
    
    bot.send_message(
        user_id,
        f"🧠 Тест!\n\n"
        f"Как будет: *{word_data['translation']}*?",
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('quiz_'))
def handle_quiz(call):
    parts = call.data.split('_')
    chosen = parts[1]
    correct = parts[2]
    user_id = call.message.chat.id
    
    is_correct = chosen == correct
    add_answer(user_id, is_correct)
    
    if is_correct:
        bot.answer_callback_query(call.id, "✅ Правильно!")
        bot.edit_message_text(
            f"✅ Правильно!\n\nСлово: *{correct}*",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
    else:
        bot.answer_callback_query(call.id, "❌ Неправильно")
        bot.edit_message_text(
            f"❌ Неправильно!\n\nПравильный ответ: *{correct}*",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )

@bot.message_handler(commands=['stats'])
def stats(message):
    user_id = message.chat.id
    user = get_user(user_id)
    lang = user[1]
    learned = len(user[2].split(',')) if user[2] else 0
    total = user[4]
    correct = user[3]
    accuracy = (correct / total * 100) if total > 0 else 0
    
    bot.send_message(
        user_id,
        f"📊 Твоя статистика:\n\n"
        f"🌐 Язык: {LANGUAGE_NAMES[lang]}\n"
        f"📚 Выучено слов: {learned}\n"
        f"✅ Правильных ответов: {correct}\n"
        f"📝 Всего ответов: {total}\n"
        f"🎯 Точность: {accuracy:.1f}%"
    )

@bot.message_handler(commands=['reset'])
def reset(message):
    user_id = message.chat.id
    update_user(user_id, learned_words='', correct_answers=0, total_answers=0)
    bot.send_message(user_id, "🔄 Прогресс сброшен! Начинаем заново.")

# ===== ЗАПУСК =====
if __name__ == "__main__":
    print("🤖 Бот для изучения слов запущен...")
    bot.infinity_polling()
