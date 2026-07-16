import os
import random
import json
import sqlite3
import google.generativeai as genai
from telebot import TeleBot, types
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Настраиваем Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = TeleBot(BOT_TOKEN)

# Поддерживаемые языки
LANGUAGE_NAMES = {
    "english": "🇬🇧 Английский",
    "spanish": "🇪 Испанский",
    "german": "🇩🇪 Немецкий",
    "korean": "🇰🇷 Корейский",
    "french": "🇷 Французский",
    "japanese": "🇯🇵 Японский",
    "italian": "🇹 Итальянский",
    "chinese": "🇨 Китайский"
}

# ===== БАЗА ДАННЫХ =====
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            language TEXT DEFAULT 'english',
            difficulty TEXT DEFAULT 'beginner',
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
    learned = user[3] if user[3] else ''
    if word not in learned.split(','):
        learned = f"{learned},{word}" if learned else word
        update_user(user_id, learned_words=learned)

def add_answer(user_id, correct):
    user = get_user(user_id)
    correct_count = user[4] + (1 if correct else 0)
    total_count = user[5] + 1
    update_user(user_id, correct_answers=correct_count, total_answers=total_count)

# ===== AI ФУНКЦИЯ =====
def get_ai_words(language, difficulty="beginner", count=5):
    """Генерирует слова через Google Gemini"""
    lang_names = {
        "english": "English", "spanish": "Spanish", "german": "German", 
        "korean": "Korean", "french": "French", "japanese": "Japanese",
        "italian": "Italian", "chinese": "Chinese (Mandarin)"
    }
    lang_name = lang_names.get(language, "English")
    
    diff_names = {
        "beginner": "A1-A2 (начальный, базовые слова)", 
        "intermediate": "B1-B2 (средний, повседневные темы)", 
        "advanced": "C1-C2 (продвинутый, редкие и сложные слова)"
    }
    diff_name = diff_names.get(difficulty, "beginner")

    prompt = f"""
    Act as a professional language teacher. 
    Generate exactly {count} useful {lang_name} words for a learner at {diff_name} level.
    Return ONLY a valid JSON array of objects. Do not write any markdown, no ```json, just the raw array.
    Format:
    [
        {{"word": "word_in_target_language", "translation": "перевод_на_русский", "example": "простой пример предложения с этим словом на целевом языке"}}
    ]
    Make sure the JSON is valid and parseable.
    """
    
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        words = json.loads(clean_text)
        return words
    except Exception as e:
        print(f"AI Error: {e}")
        return None

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
        "👋 Привет! Я **WordMaster Pro AI** 🤖\n\n"
        "Я использую искусственный интеллект Gemini, чтобы подбирать для тебя слова любого уровня сложности!\n\n"
        "✨ **Возможности:**\n"
        "- AI генерирует слова под твой уровень\n"
        "- 8 языков на выбор\n"
        "- Адаптивное обучение\n\n"
        "Выбери язык для изучения:",
        reply_markup=markup,
        parse_mode='Markdown'
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
                f"🎯 Твой текущий уровень: 🟢 Начальный\n\n"
                f"**Команды:**\n"
                "/learn — AI подберет новое слово\n"
                "/quiz — тест из 5 вопросов от AI\n"
                "/difficulty — изменить уровень сложности\n"
                "/stats — твоя статистика\n"
                "/help — помощь",
                reply_markup=types.ReplyKeyboardRemove(),
                parse_mode='Markdown'
            )
            break

@bot.message_handler(commands=['difficulty'])
def set_difficulty(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🟢 Начальный (A1-A2)", callback_data="diff_beginner"),
        types.InlineKeyboardButton("🟡 Средний (B1-B2)", callback_data="diff_intermediate"),
        types.InlineKeyboardButton("🔴 Продвинутый (C1-C2)", callback_data="diff_advanced")
    )
    bot.send_message(message.chat.id, "Выбери свой текущий уровень:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('diff_'))
def handle_difficulty(call):
    user_id = call.message.chat.id
    level = call.data.split('_')[1]
    update_user(user_id, difficulty=level)
    
    level_names = {"beginner": "🟢 Начальный", "intermediate": "🟡 Средний", "advanced": "🔴 Продвинутый"}
    bot.answer_callback_query(call.id, f"Уровень изменен на {level_names[level]}")
    bot.edit_message_text(
        f"✅ Твой уровень установлен: {level_names[level]}\n\n"
        f"Теперь AI будет подбирать слова соответственно!", 
        call.message.chat.id, 
        call.message.message_id,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['learn'])
def learn(message):
    user_id = message.chat.id
    user = get_user(user_id)
    lang = user[1]
    difficulty = user[2]
    
    wait_msg = bot.send_message(user_id, " AI подбирает для тебя идеальное слово...")
    
    words = get_ai_words(lang, difficulty, count=1)
    
    if words and len(words) > 0:
        word_data = words[0]
        add_learned_word(user_id, word_data["word"])
        
        bot.delete_message(wait_msg.chat.id, wait_msg.message_id)
        
        bot.send_message(
            user_id,
            f" **Новое слово** ({difficulty}):\n\n"
            f"🔹 *{word_data['word']}*\n"
            f"📝 Перевод: {word_data['translation']}\n"
            f" Пример: _{word_data['example']}_\n\n"
            f"Используй /quiz чтобы проверить знания!",
            parse_mode='Markdown'
        )
    else:
        bot.delete_message(wait_msg.chat.id, wait_msg.message_id)
        bot.send_message(user_id, "❌ AI временно недоступен. Попробуй через минуту.")

@bot.message_handler(commands=['quiz'])
def start_quiz(message):
    user_id = message.chat.id
    user = get_user(user_id)
    
    wait_msg = bot.send_message(user_id, " AI генерирует тест из 5 вопросов...")
    
    words = get_ai_words(user[1], user[2], count=5)
    
    if not words or len(words) < 5:
        bot.delete_message(wait_msg.chat.id, wait_msg.message_id)
        bot.send_message(user_id, "❌ Не удалось сгенерировать тест. Попробуй позже.")
        return
    
    bot.delete_message(wait_msg.chat.id, wait_msg.message_id)
    
    if not hasattr(bot, 'active_quizzes'):
        bot.active_quizzes = {}
        
    bot.active_quizzes[user_id] = {
        "questions": words,
        "current": 0,
        "correct": 0
    }
    send_quiz_question(message, user_id)

def send_quiz_question(message, user_id):
    quiz = bot.active_quizzes[user_id]
    if quiz["current"] >= len(quiz["questions"]):
        finish_quiz(message, user_id)
        return
    
    q = quiz["questions"][quiz["current"]]
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Создаем варианты ответа (1 правильный + 3 неправильных)
    correct_word = q["word"]
    # Генерируем неправильные варианты
    wrong_words = get_ai_words(quiz["questions"][0].get("lang", "english"), "beginner", count=3)
    options = [correct_word]
    if wrong_words:
        for w in wrong_words[:3]:
            options.append(w["word"])
    else:
        options.extend(["apple", "book", "house"])
    
    random.shuffle(options)
    
    for option in options:
        markup.add(types.InlineKeyboardButton(
            option, 
            callback_data=f"quiz_ans_{option}_{correct_word}"
        ))
    
    bot.send_message(
        user_id,
        f"🧠 **Вопрос {quiz['current'] + 1}/5**\n\n"
        f"Как переводится: *{q['word']}*?",
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('quiz_ans_'))
def handle_quiz_answer(call):
    user_id = call.message.chat.id
    if user_id not in getattr(bot, 'active_quizzes', {}):
        return
        
    parts = call.data.split('_')
    chosen = parts[2]
    correct = parts[3]
    
    quiz = bot.active_quizzes[user_id]
    
    if chosen == correct:
        quiz["correct"] += 1
        bot.answer_callback_query(call.id, "✅ Правильно!")
    else:
        bot.answer_callback_query(call.id, f" Нет. Правильно: {correct}")
    
    quiz["current"] += 1
    send_quiz_question(call.message, user_id)

def finish_quiz(message, user_id):
    quiz = bot.active_quizzes[user_id]
    accuracy = (quiz["correct"] / 5 * 100)
    
    add_answer(user_id, quiz["correct"] >= 3)
    
    emoji = "🏆" if quiz["correct"] >= 4 else "👍" if quiz["correct"] >= 3 else "📚"
    
    bot.send_message(
        user_id,
        f"{emoji} **Тест завершен!**\n\n"
        f"✅ Правильных: {quiz['correct']}/5\n"
        f"🎯 Точность: {accuracy:.0f}%\n\n"
        f"{'Отличный результат!' if quiz['correct'] >= 4 else 'Продолжай учиться!'}",
        parse_mode='Markdown'
    )
    del bot.active_quizzes[user_id]

@bot.message_handler(commands=['stats'])
def stats(message):
    user_id = message.chat.id
    user = get_user(user_id)
    learned = len(user[3].split(',')) if user[3] else 0
    total = user[5]
    correct = user[4]
    accuracy = (correct / total * 100) if total > 0 else 0
    
    level_emoji = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}
    
    bot.send_message(
        user_id,
        f"📊 **Твоя статистика:**\n\n"
        f"🌐 Язык: {LANGUAGE_NAMES.get(user[1], 'Не выбран')}\n"
        f"📈 Уровень: {level_emoji.get(user[2], '🟢')} {user[2].capitalize()}\n"
        f"📚 Выучено слов: {learned}\n"
        f"✅ Правильных ответов: {correct}\n"
        f"📝 Всего ответов: {total}\n"
        f"🎯 Точность: {accuracy:.1f}%",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(
        message.chat.id,
        "📖 **Справка:**\n\n"
        "/start — начать и выбрать язык\n"
        "/learn — получить новое слово от AI\n"
        "/quiz — пройти тест (5 вопросов)\n"
        "/difficulty — изменить уровень сложности\n"
        "/stats — посмотреть статистику\n"
        "/help — эта справка\n\n"
        "Бот использует Google Gemini AI для генерации слов!"
    )

@bot.message_handler(commands=['reset'])
def reset(message):
    user_id = message.chat.id
    update_user(user_id, learned_words='', correct_answers=0, total_answers=0)
    bot.send_message(user_id, "🔄 Прогресс сброшен! Начинаем заново.")

# ===== ЗАПУСК =====
if __name__ == "__main__":
    print(" WordMaster Pro AI запущен...")
    print("Используется Google Gemini API")
    bot.infinity_polling()
