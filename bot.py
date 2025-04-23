import asyncio
import random
import os
import json
import time
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from deep_translator import GoogleTranslator
from gtts import gTTS

# Log sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='bot.log'
)
logger = logging.getLogger(__name__)

TOKEN = "7912221774:AAEuffV84M855QMI3Cwo4FYmS_UKVC9RsR0"
bot = Bot(token=TOKEN)
dp = Dispatcher()
translator = GoogleTranslator(source='auto', target='en')

DATA_FILE = "user_data.json"

def load_user_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.info("user_data.json topilmadi, bo'sh ma'lumotlar yaratilmoqda.")
        return {}
    except Exception as e:
        logger.error(f"Ma'lumotlarni yuklashda xato: {e}")
        return {}

def save_user_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ma'lumotlarni saqlashda xato: {e}")

user_data = load_user_data()

def get_language_inline_markup(prefix="lang", include_uz=False):
    buttons = [
        [InlineKeyboardButton(text="🇬🇧 English", callback_data=f"{prefix}_en"),
         InlineKeyboardButton(text="🇷🇺 Русский", callback_data=f"{prefix}_ru")]
    ]
    if include_uz:
        buttons[0].append(InlineKeyboardButton(text="🇺🇿 O‘zbek", callback_data=f"{prefix}_uz"))
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Tarjima"), KeyboardButton(text="🎲 Quiz Test")],
            [KeyboardButton(text="⏳ Zamonlar"), KeyboardButton(text="📚 Grammatika")],
            [KeyboardButton(text="📖 Lug‘atim")],
            [KeyboardButton(text="📊 Statistikam"), KeyboardButton(text="🔄 Botni qayta yuklash")],
            [KeyboardButton(text="📩 Yordam")]
        ],
        resize_keyboard=True
    )

quiz_words = {
    "Animals": {
        "en": {"dog": "it", "cat": "mushuk", "bird": "qush", "horse": "ot", "fish": "baliq", "lion": "sher", "elephant": "fil", "tiger": "yo‘lbars", "bear": "ayiq", "wolf": "bo‘ri"},
        "ru": {"собака": "it", "кошка": "mushuk", "птица": "qush", "лошадь": "ot", "рыба": "baliq", "лев": "sher", "слон": "fil", "тигр": "yo‘lbars", "медведь": "ayiq", "волк": "bo‘ri"}
    },
    "Fruits": {
        "en": {"apple": "olma", "banana": "banan", "orange": "apelsin", "grape": "uzum", "mango": "mango", "pear": "nok", "peach": "shaftoli", "pineapple": "ananas", "watermelon": "tarvuz", "cherry": "gilos"},
        "ru": {"яблоко": "olma", "банан": "banan", "апельсин": "apelsin", "виноград": "uzum", "манго": "mango", "груша": "nok", "персик": "shaftoli", "ананас": "ananas", "арбуз": "tarvuz", "вишня": "gilos"}
    },
    "Colors": {
        "en": {"red": "qizil", "blue": "ko‘k", "green": "yashil", "yellow": "sariq", "black": "qora", "white": "oq", "purple": "siyohrang", "pink": "pushti", "brown": "jigar", "gray": "kulrang"},
        "ru": {"красный": "qizil", "синий": "ko‘k", "зеленый": "yashil", "желтый": "sariq", "черный": "qora", "белый": "oq", "фиолетовый": "siyohrang", "розовый": "pushti", "коричневый": "jigar", "серый": "kulrang"}
    },
    "Clothes": {
        "en": {"shirt": "ko‘ylak", "pants": "shim", "jacket": "kurtka", "shoes": "poyabzal", "hat": "shlyapa", "dress": "ko‘ylak (ayollar)", "socks": "paypoq", "skirt": "yubka", "tie": "galstuk", "belt": "kamar"},
        "ru": {"рубашка": "ko‘ylak", "брюки": "shim", "куртка": "kurtka", "обувь": "poyabzal", "шапка": "shlyapa", "платье": "ko‘ylak (ayollar)", "носки": "paypoq", "юбка": "yubka", "галстук": "galstuk", "ремень": "kamar"}
    },
    "Food": {
        "en": {"bread": "non", "meat": "go‘sht", "rice": "guruch", "soup": "sho‘rva", "fish": "baliq", "egg": "tuxum", "cheese": "pishloq", "milk": "sut", "cake": "tort", "salad": "salat"},
        "ru": {"хлеб": "non", "мясо": "go‘sht", "рис": "guruch", "суп": "sho‘rva", "рыба": "baliq", "яйцо": "tuxum", "сыр": "pishloq", "молоко": "sut", "торт": "tort", "салат": "salat"}
    }
}

quiz_topics = {
    "en": ["Animals", "Fruits", "Colors", "Clothes", "Food"],
    "ru": ["Животные", "Фрукты", "Цвета", "Одежда", "Еда"]
}

tense_examples = {
    "Present Simple": {
        "en": [
            ["I ___ to school every day.", "go", ["go", "went", "will go"]],
            ["She ___ TV in the evening.", "watches", ["watch", "watches", "watched"]],
            ["They ___ football on weekends.", "play", ["play", "played", "will play"]],
            ["He ___ coffee every morning.", "drinks", ["drink", "dr Watches", "drank"]],
            ["We ___ books in the library.", "read", ["read", "reads", "reading"]],
            ["The dog ___ in the yard.", "barks", ["bark", "barks", "barked"]],
            ["She ___ her homework daily.", "does", ["do", "does", "did"]],
            ["I ___ my room every week.", "clean", ["clean", "cleaned", "will clean"]],
            ["They ___ English well.", "speak", ["speak", "spoke", "speaking"]],
            ["He ___ to music every night.", "listens", ["listen", "listens", "listened"]]
        ],
        "ru": [
            ["Я ___ в школу каждый день.", "хожу", ["хожу", "ходил", "буду ходить"]],
            ["Она ___ телевизор вечером.", "смотрит", ["смотрю", "смотрит", "смотрела"]],
            ["Они ___ в футбол по выходным.", "играют", ["играют", "играли", "будут играть"]],
            ["Он ___ кофе каждое утро.", "пьет", ["пью", "пьет", "пил"]],
            ["Мы ___ книги в библиотеке.", "читаем", ["читаю", "читаем", "читали"]],
            ["Собака ___ во дворе.", "лает", ["лаю", "лает", "лаяла"]],
            ["Она ___ домашку каждый день.", "делает", ["делаю", "делает", "сделала"]],
            ["Я ___ комнату каждую неделю.", "убираю", ["убираю", "убрал", "буду убирать"]],
            ["Они ___ английский хорошо.", "говорят", ["говорю", "говорят", "говорили"]],
            ["Он ___ музыку каждую ночь.", "слушает", ["слушаю", "слушает", "слушал"]]
        ]
    },
    "Present Continuous": {
        "en": [
            ["I ___ a book now.", "am reading", ["read", "am reading", "will read"]],
            ["She ___ dinner at the moment.", "is cooking", ["cooks", "is cooking", "cooked"]],
            ["They ___ a movie right now.", "are watching", ["watch", "are watching", "watched"]],
            ["He ___ his homework now.", "is doing", ["does", "is doing", "did"]],
            ["We ___ in the park now.", "are playing", ["play", "are playing", "played"]],
            ["The cat ___ on the sofa.", "is sleeping", ["sleeps", "is sleeping", "slept"]],
            ["She ___ a letter now.", "is writing", ["writes", "is writing", "wrote"]],
            ["I ___ to you at the moment.", "am talking", ["talk", "am talking", "talked"]],
            ["They ___ the room now.", "are cleaning", ["clean", "are cleaning", "cleaned"]],
            ["He ___ TV right now.", "is watching", ["watches", "is watching", "watched"]]
        ],
        "ru": [
            ["Я ___ книгу сейчас.", "читаю", ["читаю", "читал", "буду читать"]],
            ["Она ___ ужин сейчас.", "готовит", ["готовлю", "готовит", "готовила"]],
            ["Они ___ фильм прямо сейчас.", "смотрят", ["смотрю", "смотрят", "смотрели"]],
            ["Он ___ домашку сейчас.", "делает", ["делаю", "делает", "сделал"]],
            ["Мы ___ в парке сейчас.", "играем", ["играю", "играем", "играли"]],
            ["Кот ___ на диване.", "спит", ["сплю", "спит", "спал"]],
            ["Она ___ письмо сейчас.", "пишет", ["пишу", "пишет", "писала"]],
            ["Я ___ с тобой сейчас.", "говорю", ["говорю", "говорил", "буду говорить"]],
            ["Они ___ комнату сейчас.", "убирают", ["убираю", "убирают", "убрали"]],
            ["Он ___ телевизор сейчас.", "смотрит", ["смотрю", "смотрит", "смотрел"]]
        ]
    },
    "Past Simple": {
        "en": [
            ["I ___ to school yesterday.", "went", ["go", "went", "will go"]],
            ["She ___ TV last night.", "watched", ["watch", "watched", "watches"]],
            ["They ___ football yesterday.", "played", ["play", "played", "playing"]],
            ["He ___ coffee this morning.", "drank", ["drink", "drank", "drinks"]],
            ["We ___ a book last week.", "read", ["read", "reads", "reading"]],
            ["The dog ___ in the yard.", "barked", ["bark", "barked", "barks"]],
            ["She ___ her homework yesterday.", "did", ["do", "did", "does"]],
            ["I ___ my room last weekend.", "cleaned", ["clean", "cleaned", "cleaning"]],
            ["They ___ English yesterday.", "spoke", ["speak", "spoke", "speaking"]],
            ["He ___ to music last night.", "listened", ["listen", "listened", "listening"]]
        ],
        "ru": [
            ["Я ___ в школу вчера.", "ходил", ["хожу", "ходил", "буду ходить"]],
            ["Она ___ телевизор вчера.", "смотрела", ["смотрю", "смотрела", "смотрит"]],
            ["Они ___ в футбол вчера.", "играли", ["играю", "играли", "играют"]],
            ["Он ___ кофе утром.", "пил", ["пью", "пил", "пьет"]],
            ["Мы ___ книгу на прошлой неделе.", "читали", ["читаю", "читали", "читаем"]],
            ["Собака ___ во дворе.", "лаяла", ["лаю", "лаяла", "лает"]],
            ["Она ___ домашку вчера.", "сделала", ["делаю", "сделала", "делает"]],
            ["Я ___ комнату на выходных.", "убрал", ["убираю", "убрал", "убирает"]],
            ["Они ___ английский вчера.", "говорили", ["говорю", "говорили", "говорят"]],
            ["Он ___ музыку вчера.", "слушал", ["слушаю", "слушал", "слушает"]]
        ]
    },
    "Past Continuous": {
        "en": [
            ["I ___ a book yesterday.", "was reading", ["read", "was reading", "will read"]],
            ["She ___ dinner at 7 PM.", "was cooking", ["cooks", "was cooking", "cooked"]],
            ["They ___ a movie last night.", "were watching", ["watch", "were watching", "watched"]],
            ["He ___ his homework yesterday.", "was doing", ["does", "was doing", "did"]],
            ["We ___ in the park yesterday.", "were playing", ["play", "were playing", "played"]],
            ["The cat ___ on the sofa.", "was sleeping", ["sleeps", "was sleeping", "slept"]],
            ["She ___ a letter yesterday.", "was writing", ["writes", "was writing", "wrote"]],
            ["I ___ to you last night.", "was talking", ["talk", "was talking", "talked"]],
            ["They ___ the room yesterday.", "were cleaning", ["clean", "were cleaning", "cleaned"]],
            ["He ___ TV last evening.", "was watching", ["watches", "was watching", "watched"]]
        ],
        "ru": [
            ["Я ___ книгу вчера.", "читал", ["читаю", "читал", "буду читать"]],
            ["Она ___ ужин в 7 вечера.", "готовила", ["готовлю", "готовила", "готовит"]],
            ["Они ___ фильм вчера ночью.", "смотрели", ["смотрю", "смотрели", "смотрят"]],
            ["Он ___ домашку вчера.", "делал", ["делаю", "делал", "делает"]],
            ["Мы ___ в парке вчера.", "играли", ["играю", "играли", "играем"]],
            ["Кот ___ на диване.", "спал", ["сплю", "спал", "спит"]],
            ["Она ___ письмо вчера.", "писала", ["пишу", "писала", "пишет"]],
            ["Я ___ с тобой вчера.", "говорил", ["говорю", "говорил", "буду говорить"]],
            ["Они ___ комнату вчера.", "убирали", ["убираю", "убирали", "убирают"]],
            ["Он ___ телевизор вчера вечером.", "смотрел", ["смотрю", "смотрел", "смотрит"]]
        ]
    },
    "Future Simple": {
        "en": [
            ["I ___ to school tomorrow.", "will go", ["go", "went", "will go"]],
            ["She ___ TV tonight.", "will watch", ["watch", "watched", "will watch"]],
            ["They ___ football tomorrow.", "will play", ["play", "played", "will play"]],
            ["He ___ coffee tomorrow.", "will drink", ["drink", "drank", "will drink"]],
            ["We ___ a book next week.", "will read", ["read", "reads", "will read"]],
            ["The dog ___ in the yard.", "will bark", ["bark", "barked", "will bark"]],
            ["She ___ her homework tomorrow.", "will do", ["do", "did", "will do"]],
            ["I ___ my room next weekend.", "will clean", ["clean", "cleaned", "will clean"]],
            ["They ___ English tomorrow.", "will speak", ["speak", "spoke", "will speak"]],
            ["He ___ to music tonight.", "will listen", ["listen", "listened", "will listen"]]
        ],
        "ru": [
            ["Я ___ в школу завтра.", "буду ходить", ["хожу", "ходил", "буду ходить"]],
            ["Она ___ телевизор сегодня вечером.", "будет смотреть", ["смотрю", "смотрела", "будет смотреть"]],
            ["Они ___ в футбол завтра.", "будут играть", ["играю", "играли", "будут играть"]],
            ["Он ___ кофе завтра.", "будет пить", ["пью", "пил", "будет пить"]],
            ["Мы ___ книгу на следующей неделе.", "будем читать", ["читаю", "читали", "будем читать"]],
            ["Собака ___ во дворе.", "будет лаять", ["лаю", "лаяла", "будет лаять"]],
            ["Она ___ домашку завтра.", "сделает", ["делаю", "сделала", "сделает"]],
            ["Я ___ комнату на следующих выходных.", "буду убирать", ["убираю", "убрал", "буду убирать"]],
            ["Они ___ английский завтра.", "будут говорить", ["говорю", "говорили", "будут говорить"]],
            ["Он ___ музыку сегодня вечером.", "будет слушать", ["слушаю", "слушал", "будет слушать"]]
        ]
    }
}

tenses = {
    "en": ["Present Simple", "Present Continuous", "Past Simple", "Past Continuous", "Future Simple"],
    "ru": ["Настоящее простое", "Настоящее продолженное", "Прошедшее простое", "Прошедшее продолженное", "Будущее простое"]
}

grammar_examples = {
    "Articles": {
        "en": [
            ["I see ___ cat.", "a", ["a", "an", "the", "no"]],
            ["She has ___ apple.", "an", ["a", "an", "the", "no"]],
            ["He is ___ teacher.", "a", ["a", "an", "the", "no"]],
            ["They live in ___ house.", "a", ["a", "an", "the", "no"]],
            ["This is ___ best day.", "the", ["a", "an", "the", "no"]]
        ],
        "ru": [
            ["Я вижу ___ кошку.", "нет", ["a", "an", "the", "нет"]],
            ["У нее есть ___ яблоко.", "нет", ["a", "an", "the", "нет"]],
            ["Он ___ учитель.", "нет", ["a", "an", "the", "нет"]],
            ["Они живут в ___ доме.", "нет", ["a", "an", "the", "нет"]],
            ["Это ___ лучший день.", "нет", ["a", "an", "the", "нет"]]
        ]
    },
    "Prepositions": {
        "en": [
            ["I live ___ London.", "in", ["in", "on", "at", "to"]],
            ["She goes ___ school every day.", "to", ["in", "on", "at", "to"]],
            ["The book is ___ the table.", "on", ["in", "on", "at", "to"]],
            ["He arrives ___ 5 PM.", "at", ["in", "on", "at", "to"]],
            ["We travel ___ car.", "by", ["in", "on", "by", "to"]]
        ],
        "ru": [
            ["Я живу ___ Лондоне.", "в", ["в", "на", "у", "к"]],
            ["Она ходит ___ школу каждый день.", "в", ["в", "на", "у", "к"]],
            ["Книга лежит ___ столе.", "на", ["в", "на", "у", "к"]],
            ["Он приезжает ___ 5 вечера.", "в", ["в", "на", "у", "к"]],
            ["Мы путешествуем ___ машине.", "на", ["в", "на", "у", "к"]]
        ]
    }
}

def create_audio(text, lang="en"):
    try:
        tts = gTTS(text=text, lang=lang if lang in ["en", "ru", "uz"] else "en")
        audio_dir = "C:/Users/Admin/Desktop/Qosimov Quvonch/audio_temp"
        os.makedirs(audio_dir, exist_ok=True)
        filename = os.path.join(audio_dir, f"temp_{int(time.time())}_{random.randint(1, 1000)}.mp3")
        tts.save(filename)
        if os.path.exists(filename):
            logger.info(f"Audio fayl yaratildi: {filename}")
            return filename
        logger.warning("Audio fayl yaratilmadi.")
        return None
    except Exception as e:
        logger.error(f"Audio yaratishda xato: {e}")
        return None

@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        user_data[user_id] = {"stats": {}, "vocab_list": {}, "last_lang": "en"}
    save_user_data(user_data)
    try:
        await message.answer("🌍 *Assalomu Alaykum!*\nQuvonchbek Qosimov yaratgan botga xush kelibsiz!", parse_mode="Markdown")
        await message.answer("✨ *Nima bilan yordam beray?*", parse_mode="Markdown", reply_markup=get_main_menu())
        logger.info(f"Foydalanuvchi {user_id} /start buyrug'ini yubordi.")
    except Exception as e:
        logger.error(f"/start buyrug'ida xato: {e}")
        await message.answer("❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring.")

@dp.message()
async def handle_menu(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        user_data[user_id] = {"stats": {}, "vocab_list": {}, "last_lang": "en"}
        save_user_data(user_data)
    
    try:
        if message.text == "🔄 Botni qayta yuklash":
            await start(message)
        elif message.text == "📩 Yordam":
            await message.answer("📩 *Yordam:*\n💬 Muammoni hal qilishga harakat qilaman.\n👤 Murojaat uchun: @quvonchbekqos1mov2006", parse_mode="Markdown")
            await bot.send_contact(chat_id=message.chat.id, phone_number="+998770830820", first_name="⚜️𝑸𝒖𝒗𝒐𝒏𝒄𝒉𝒃𝒆𝒌 𝑸𝒐𝒔𝒊𝒎𝒐𝒗⚜️")
        elif message.text == "📝 Tarjima":
            user_data[user_id]["mode"] = "translate"
            await message.answer("✍️ *Matn kiriting:*", parse_mode="Markdown", reply_markup=get_main_menu())
        elif message.text == "🎲 Quiz Test":
            user_data[user_id]["mode"] = "quiz"
            await message.answer("🌐 *Tilni tanlang:*", parse_mode="Markdown", reply_markup=get_language_inline_markup("quiz_lang"))
        elif message.text == "⏳ Zamonlar":
            user_data[user_id]["mode"] = "tense"
            await message.answer("🌐 *Tilni tanlang:*", parse_mode="Markdown", reply_markup=get_language_inline_markup("tense_lang"))
        elif message.text == "📚 Grammatika":
            user_data[user_id]["mode"] = "grammar"
            await message.answer("🌐 *Tilni tanlang:*", parse_mode="Markdown", reply_markup=get_language_inline_markup("grammar_lang"))
        elif message.text == "📖 Lug‘atim":
            user_data[user_id]["mode"] = "vocab"
            await message.answer("📖 *Lug‘at bilan nima qilmoqchisiz?*\n1. So‘z qo‘shish\n2. Test o‘tash\n3. Lug‘atlarim\nJavob raqamini yuboring:", parse_mode="Markdown")
        elif message.text == "📊 Statistikam":
            stats = user_data[user_id]["stats"]
            quiz_score = stats.get("quiz", 0)
            tense_score = stats.get("tense", 0)
            grammar_score = stats.get("grammar", 0)
            vocab_score = stats.get("vocab", 0)
            total_possible = 10 + 10 + 5 + 5
            total_score = quiz_score + tense_score + grammar_score + vocab_score
            overall_percent = (total_score / total_possible) * 100 if total_score > 0 else 0
            text = (
                f"📊 *Sizning statistikangiz:*\n\n"
                f"🎲 Quiz: {quiz_score}/10\n"
                f"⏳ Zamonlar: {tense_score}/10\n"
                f"📚 Grammatika: {grammar_score}/5\n"
                f"📖 Lug‘at testi: {vocab_score}/5\n\n"
                f"🏆 Umumiy muvaffaqiyat: {total_score}/{total_possible} ({overall_percent:.1f}%)"
            )
            await message.answer(text, parse_mode="Markdown")
        elif user_id in user_data and "mode" in user_data[user_id]:
            mode = user_data[user_id]["mode"]
            if mode == "translate":
                user_data[user_id]["content"] = message.text
                last_lang = user_data[user_id].get("last_lang", "en")
                await message.answer(
                    f"🌐 *Qaysi tilga tarjima qilay? (Oxirgi tanlangan: {last_lang})*",
                    parse_mode="Markdown",
                    reply_markup=get_language_inline_markup("translate_lang", include_uz=True)
                )
            elif mode == "vocab":
                if message.text == "1":
                    await message.answer("📖 *So‘z kiriting (masalan, 'dog - it'):*", parse_mode="Markdown")
                    user_data[user_id]["vocab_action"] = "add"
                elif message.text == "2":
                    if user_data[user_id]["vocab_list"]:
                        user_data[user_id].update({"score": 0, "question_count": 0, "used_words": set()})
                        await send_vocab_question(message, user_id)
                    else:
                        await message.answer("📖 *Lug‘atingiz bo‘sh!* Avval so‘z qo‘shing.", parse_mode="Markdown")
                elif message.text == "3":
                    vocab = user_data[user_id]["vocab_list"]
                    if vocab:
                        text = "📖 *Sizning lug‘atlaringiz:*\n" + "\n".join(f"{k} - {v}" for k, v in vocab.items())
                    else:
                        text = "📖 *Lug‘atingiz bo‘sh!*"
                    await message.answer(text, parse_mode="Markdown")
                elif user_data[user_id].get("vocab_action") == "add":
                    try:
                        word, translation = message.text.split(" - ")
                        user_data[user_id]["vocab_list"][word] = translation
                        save_user_data(user_data)
                        await message.answer(f"✅ *{word} - {translation} lug‘atga qo‘shildi!*", parse_mode="Markdown")
                    except ValueError:
                        await message.answer("❌ *Noto‘g‘ri format!* Masalan: 'dog - it'", parse_mode="Markdown")
        save_user_data(user_data)
    except Exception as e:
        logger.error(f"handle_menu da xato: {e}")
        await message.answer("❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring.")

@dp.callback_query(lambda c: c.data.startswith("translate_lang_"))
async def translate_content(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    if user_id not in user_data or "content" not in user_data[user_id]:
        await callback_query.message.edit_text("❌ Matn topilmadi. Iltimos, avval matn kiriting.")
        logger.warning(f"Foydalanuvchi {user_id} uchun matn topilmadi.")
        return
    
    lang = callback_query.data.split("_")[2]
    user_data[user_id]["last_lang"] = lang
    content = user_data[user_id]["content"]
    
    try:
        translated_text = GoogleTranslator(source='auto', target=lang).translate(content)
        if not translated_text:
            raise ValueError("Tarjima bo‘sh qaytdi.")
        
        current_text = callback_query.message.text or ""
        new_text = f"📖 *Tarjima:* \n{translated_text}"
        if current_text != new_text:
            await callback_query.message.edit_text(new_text, parse_mode="Markdown")
        
        audio_file = create_audio(translated_text, lang)
        if audio_file and os.path.exists(audio_file):
            try:
                await bot.send_audio(
                    chat_id=callback_query.message.chat.id,
                    audio=types.FSInputFile(audio_file),
                    title=f"Tarjima: {lang}",
                    performer="Grok Bot"
                )
                os.remove(audio_file)
                logger.info(f"Audio fayl yuborildi va o‘chirildi: {audio_file}")
            except Exception as e:
                logger.error(f"Audio yuborishda xato: {e}")
                await bot.send_message(
                    chat_id=callback_query.message.chat.id,
                    text=f"❌ Audio yuborishda xato yuz berdi: {str(e)}"
                )
        else:
            await bot.send_message(
                chat_id=callback_query.message.chat.id,
                text="❌ Audio faylni yaratishda xato yuz berdi."
            )
        
    except Exception as e:
        logger.error(f"Tarjima qilishda xato: {e}")
        await callback_query.message.edit_text(f"❌ Tarjima qilishda xato: {str(e)}")
    
    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text="✍️ *Matn kiriting:*",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )
    user_data[user_id]["mode"] = "translate"
    save_user_data(user_data)

@dp.callback_query(lambda c: c.data.startswith("quiz_lang_"))
async def quiz_language(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    lang = callback_query.data.split("_")[2]
    user_data[user_id] = {
        "mode": "quiz",
        "lang": lang,
        "stats": user_data[user_id].get("stats", {}),
        "vocab_list": user_data[user_id].get("vocab_list", {}),
        "last_lang": user_data[user_id].get("last_lang", "en")
    }
    save_user_data(user_data)
    try:
        markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=topic, callback_data=f"quiz_start_{topic}")] for topic in quiz_topics[lang]])
        current_text = callback_query.message.text or ""
        new_text = "📚 *Mavzuni tanlang:*"
        if current_text != new_text:
            await callback_query.message.edit_text(new_text, parse_mode="Markdown", reply_markup=markup)
        logger.info(f"Foydalanuvchi {user_id} quiz tilini tanladi: {lang}")
    except Exception as e:
        logger.error(f"quiz_language da xato: {e}")
        await callback_query.message.edit_text("❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring.")

@dp.callback_query(lambda c: c.data.startswith("quiz_start_"))
async def quiz_start(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    topic = callback_query.data.split("_")[2]
    user_data[user_id].update({"topic": topic, "score": 0, "question_count": 0, "used_words": set()})
    save_user_data(user_data)
    try:
        await send_quiz_question(callback_query.message, user_id)
        logger.info(f"Foydalanuvchi {user_id} quizni boshladi: {topic}")
    except Exception as e:
        logger.error(f"quiz_start da xato: {e}")
        await callback_query.message.edit_text("❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring.")

async def send_quiz_question(message, user_id):
    try:
        lang = user_data[user_id]["lang"]
        topic = user_data[user_id]["topic"]
        words = quiz_words[topic][lang]
        available_words = [w for w in words.keys() if w not in user_data[user_id]["used_words"]]
        if not available_words or user_data[user_id]["question_count"] >= 10:
            await finish_quiz(message, user_id)
            return
        word = random.choice(available_words)
        correct_answer = words[word]
        options = [correct_answer] + random.sample([v for v in words.values() if v != correct_answer], 3)
        random.shuffle(options)
        markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=opt, callback_data=f"quiz_ans_{opt}")] for opt in options])
        user_data[user_id]["correct_answer"] = correct_answer
        user_data[user_id]["current_word"] = word
        question_number = user_data[user_id]["question_count"] + 1
        new_text = f"❓ *Savol {question_number}/10: {word} - bu nima?*"
        current_text = message.text or ""
        if current_text != new_text:
            await message.edit_text(new_text, parse_mode="Markdown", reply_markup=markup)
        save_user_data(user_data)
        logger.info(f"Foydalanuvchi {user_id} uchun quiz savoli yuborildi: {word}")
    except Exception as e:
        logger.error(f"send_quiz_question da xato: {e}")
        await message.edit_text("❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring.")

@dp.callback_query(lambda c: c.data.startswith("quiz_ans_"))
async def quiz_answer(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    try:
        selected_answer = callback_query.data.split("_")[2]
        correct_answer = user_data[user_id]["correct_answer"]
        word = user_data[user_id]["current_word"]
        if selected_answer == correct_answer:
            user_data[user_id]["score"] += 1
        user_data[user_id]["used_words"].add(word)
        user_data[user_id]["question_count"] += 1
        save_user_data(user_data)
        await send_quiz_question(callback_query.message, user_id)
        logger.info(f"Foydalanuvchi {user_id} quiz javobini yubordi: {selected_answer}")
    except Exception as e:
        logger.error(f"quiz_answer da xato: {e}")
        await callback_query.message.edit_text("❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring.")

async def finish_quiz(message, user_id):
    try:
        score = user_data[user_id]["score"]
        user_data[user_id]["stats"]["quiz"] = score
        await message.edit_text(f"🏆 *Test yakunlandi!*\nNatija: {score}/10", parse_mode="Markdown")
        user_data[user_id] = {
            "stats": user_data[user_id]["stats"],
            "vocab_list": user_data[user_id]["vocab_list"],
            "last_lang": user_data[user_id].get("last_lang", "en")
        }
        save_user_data(user_data)
        logger.info(f"Foydalanuvchi {user_id} quizni yakunladi: {score}/10")
    except Exception as e:
        logger.error(f"finish_quiz da xato: {e}")
        await message.edit_text("❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring.")

@dp.callback_query(lambda c: c.data.startswith("tense_lang_"))
async def tense_language(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    lang = callback_query.data.split("_")[2]
    user_data[user_id] = {
        "mode": "tense",
        "lang": lang,
        "stats": user_data[user_id].get("stats", {}),
        "vocab_list": user_data[user_id].get("vocab_list", {}),
        "last_lang": user_data[user_id].get("last_lang", "en")
    }
    save_user_data(user_data)
    try:
        markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=tense, callback_data=f"tense_start_{tense}")] for tense in tenses[lang]])
        current_text = callback_query.message.text or ""
        new_text = "⏳ *Zamonni tanlang:*"
        if current_text != new_text:
            await callback_query.message.edit_text(new_text, parse_mode="Markdown", reply_markup=markup)
        logger.info(f"Foydalanuvchi {user_id} zamon tilini tanladi: {lang}")
    except Exception as e:
        logger.error(f"tense_language da xato: {e}")
        await callback_query.message.edit_text("❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring.")

@dp.callback_query(lambda c: c.data.startswith("tense_start_"))
async def tense_start(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    tense = callback_query.data.split("_")[2]
    user_data[user_id].update({"tense": tense, "score": 0, "question_count": 0, "used_questions": set()})
    save_user_data(user_data)
    try:
        await send_tense_question(callback_query.message, user_id)
        logger.info(f"Foydalanuvchi {user_id} zamon testini boshladi: {tense}")
    except Exception as e:
        logger.error(f"tense_start da xato: {e}")
        await callback_query.message.edit_text("❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring.")

async def send_tense_question(message, user_id):
    try:
        lang = user_data[user_id]["lang"]
        tense = user_data[user_id]["tense"]
        examples = tense_examples[tense][lang]
        available_questions = [i for i in range(len(examples)) if i not in user_data[user_id]["used_questions"]]
        if not available_questions or user_data[user_id]["question_count"] >= 10:
            await finish_tense(message, user_id)
            return
        question_idx = random.choice(available_questions)
        question, correct_answer, options = examples[question_idx]
        random.shuffle(options)
        markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=opt, callback_data=f"tense_ans_{opt}")] for opt in options])
        user_data[user_id]["correct_answer"] = correct_answer
        user_data[user_id]["current_question"] = question
        user_data[user_id]["used_questions"].add(question_idx)
        question_number = user_data[user_id]["question_count"] + 1
        new_text = f"❓ *Savol {question_number}/10: {question}*"
        current_text = message.text or ""
        if current_text != new_text:
            await message.edit_text(new_text, parse_mode="Markdown", reply_markup=markup)
        save_user_data(user_data)
        logger.info(f"Foydalanuvchi {user_id} uchun zamon savoli yuborildi: {question}")
    except Exception as e:
        logger.error(f"send_tense_question da xato: {e}")
        await message.edit_text("❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring.")

@dp.callback_query(lambda c: c.data.startswith("tense_ans_"))
async def tense_answer(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    try:
        selected_answer = callback_query.data.split("_")[2]
        correct_answer = user_data[user_id]["correct_answer"]
        if selected_answer == correct_answer:
            user_data[user_id]["score"] += 1
        user_data[user_id]["question_count"] += 1
        save_user_data(user_data)
        await send_tense_question(callback_query.message, user_id)
        logger.info(f"Foydalanuvchi {user_id} zamon javobini yubordi: {selected_answer}")
    except Exception as e:
        logger.error(f"tense_answer da xato: {e}")
        await callback_query.message.edit_text("❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring.")

async def finish_tense(message, user_id):
    try:
        score = user_data[user_id]["score"]
        user_data[user_id]["stats"]["tense"] = score
        await message.edit_text(f"🏆 *Test yakunlandi!*\nNatija: {score}/10", parse_mode="Markdown")
        user_data[user_id] = {
            "stats": user_data[user_id]["stats"],
            "vocab_list": user_data[user_id]["vocab_list"],
            "last_lang": user_data[user_id].get("last_lang", "en")
        }
        save_user_data(user_data)
        logger.info(f"Foydalanuvchi {user_id} zamon testini yakunladi: {score}/10")
    except Exception as e:
        logger.error(f"finish_tense da xato: {e}")
        await message.edit_text("❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring.")

@dp.callback_query(lambda c: c.data.startswith("grammar_lang_"))
async def grammar_language(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    lang = callback_query.data.split("_")[2]
    user_data[user_id] = {
        "mode": "grammar",
        "lang": lang,
        "stats": user_data[user_id].get("stats", {}),
        "vocab_list": user_data[user_id].get("vocab_list", {}),
        "last_lang": user_data[user_id].get("last_lang", "en")
    }
    save_user_data(user_data)
    try:
        topics = list(grammar_examples.keys())
        markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=topic, callback_data=f"grammar_start_{topic}")] for topic in topics])
        current_text = callback_query.message.text or ""
        new_text = "📚 *Mavzuni tanlang:*"
        if current_text != new_text:
            await callback_query.message.edit_text(new_text, parse_mode="Markdown", reply_markup=markup)
        logger.info(f"Foydalanuvchi {user_id} grammatika tilini tanladi: {lang}")
    except Exception as e:
        logger.error(f"grammar_language da xato: {e}")
        await callback_query.message.edit_text("❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring.")

@dp.callback_query(lambda c: c.data.startswith("grammar_start_"))
async def grammar_start(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    topic = callback_query.data.split("_")[2]
    user_data[user_id].update({"topic": topic, "score": 0, "question_count": 0, "used_questions": set()})
    save_user_data(user_data)
    try:
        await send_grammar_question(callback_query.message, user_id)
        logger.info(f"Foydalanuvchi {user_id} grammatika testini boshladi: {topic}")
    except Exception as e:
        logger.error(f"grammar_start da xato: {e}")
        await callback_query.message.edit_text("❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring.")

async def send_grammar_question(message, user_id):
    try:
        lang = user_data[user_id]["lang"]
        topic = user_data[user_id]["topic"]
        examples = grammar_examples[topic][lang]
        available_questions = [i for i in range(len(examples)) if i not in user_data[user_id]["used_questions"]]
        if not available_questions or user_data[user_id]["question_count"] >= 5:
            await finish_grammar(message, user_id)
            return
        question_idx = random.choice(available_questions)
        question, correct_answer, options = examples[question_idx]
        random.shuffle(options)
        markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=opt, callback_data=f"grammar_ans_{opt}")] for opt in options])
        user_data[user_id]["correct_answer"] = correct_answer
        user_data[user_id]["current_question"] = question
        user_data[user_id]["used_questions"].add(question_idx)
        question_number = user_data[user_id]["question_count"] + 1
        new_text = f"❓ *Savol {question_number}/5: {question}*"
        current_text = message.text or ""
        if current_text != new_text:
            await message.edit_text(new_text, parse_mode="Markdown", reply_markup=markup)
        save_user_data(user_data)
        logger.info(f"Foydalanuvchi {user_id} uchun grammatika savoli yuborildi: {question}")
    except Exception as e:
        logger.error(f"send_grammar_question da xato: {e}")
        await message.edit_text("❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring.")

@dp.callback_query(lambda c: c.data.startswith("grammar_ans_"))
async def grammar_answer(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    try:
        selected_answer = callback_query.data.split("_")[2]
        correct_answer = user_data[user_id]["correct_answer"]
        if selected_answer == correct_answer:
            user_data[user_id]["score"] += 1
        user_data[user_id]["question_count"] += 1
        save_user_data(user_data)
        await send_grammar_question(callback_query.message, user_id)
        logger.info(f"Foydalanuvchi {user_id} grammatika javobini yubordi: {selected_answer}")
    except Exception as e:
        logger.error(f"grammar_answer da xato: {e}")
        await callback_query.message.edit_text("❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring.")

async def finish_grammar(message, user_id):
    try:
        score = user_data[user_id]["score"]
        user_data[user_id]["stats"]["grammar"] = score
        await message.edit_text(f"🏆 *Test yakunlandi!*\nNatija: {score}/5", parse_mode="Markdown")
        user_data[user_id] = {
            "stats": user_data[user_id]["stats"],
            "vocab_list": user_data[user_id]["vocab_list"],
            "last_lang": user_data[user_id].get("last_lang", "en")
        }
        save_user_data(user_data)
        logger.info(f"Foydalanuvchi {user_id} grammatika testini yakunladi: {score}/5")
    except Exception as e:
        logger.error(f"finish_grammar da xato: {e}")
        await message.edit_text("❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring.")

async def send_vocab_question(message, user_id):
    try:
        words = user_data[user_id]["vocab_list"]
        available_words = [w for w in words.keys() if w not in user_data[user_id]["used_words"]]
        if not available_words or user_data[user_id]["question_count"] >= 5:
            await finish_vocab(message, user_id)
            return
        word = random.choice(available_words)
        correct_answer = words[word]
        options = [correct_answer] + random.sample([v for v in words.values() if v != correct_answer], min(3, len(words) - 1))
        random.shuffle(options)
        markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=opt, callback_data=f"vocab_ans_{opt}")] for opt in options])
        user_data[user_id]["correct_answer"] = correct_answer
        user_data[user_id]["current_word"] = word
        question_number = user_data[user_id]["question_count"] + 1
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"❓ *Savol {question_number}/5: {word} - bu qanday so‘z?*",
            parse_mode="Markdown",
            reply_markup=markup
        )
        save_user_data(user_data)
        logger.info(f"Foydalanuvchi {user_id} uchun lug‘at savoli yuborildi: {word}")
    except Exception as e:
        logger.error(f"send_vocab_question da xato: {e}")
        await bot.send_message(
            chat_id=message.chat.id,
            text="❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring."
        )

@dp.callback_query(lambda c: c.data.startswith("vocab_ans_"))
async def vocab_answer(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    try:
        selected_answer = callback_query.data.split("_")[2]
        correct_answer = user_data[user_id]["correct_answer"]
        word = user_data[user_id]["current_word"]
        if selected_answer == correct_answer:
            user_data[user_id]["score"] += 1
        user_data[user_id]["used_words"].add(word)
        user_data[user_id]["question_count"] += 1
        save_user_data(user_data)
        await send_vocab_question(callback_query.message, user_id)
        logger.info(f"Foydalanuvchi {user_id} lug‘at javobini yubordi: {selected_answer}")
    except Exception as e:
        logger.error(f"vocab_answer da xato: {e}")
        await callback_query.message.edit_text("❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring.")

async def finish_vocab(message, user_id):
    try:
        score = user_data[user_id]["score"]
        user_data[user_id]["stats"]["vocab"] = score
        await message.edit_text(f"🏆 *Lug‘at testi yakunlandi!*\nNatija: {score}/5", parse_mode="Markdown")
        user_data[user_id] = {
            "stats": user_data[user_id]["stats"],
            "vocab_list": user_data[user_id]["vocab_list"],
            "last_lang": user_data[user_id].get("last_lang", "en")
        }
        save_user_data(user_data)
        logger.info(f"Foydalanuvchi {user_id} lug‘at testini yakunladi: {score}/5")
    except Exception as e:
        logger.error(f"finish_vocab da xato: {e}")
        await message.edit_text("❌ Xato yuz berdi. Iltimos, qayta urinib ko‘ring.")

async def main():
    try:
        logger.info("Bot ishga tushmoqda...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot ishga tushishda xato: {e}")

if __name__ == "__main__":
    asyncio.run(main())