import os
import asyncio
import random
import string
import gspread
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import re

# Загрузка переменных окружения из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Подключение к Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("root/ptp-llc-15ee6d9cbfd6.json", scope)
gc = gspread.authorize(credentials)
spreadsheet = gc.open("payment_table")
worksheet = spreadsheet.worksheet("Orders")

# Словарь для хранения временных данных пользователя
user_data = {}

# Доступные языки и локализация
LANGUAGES = {
    "en": {
        "welcome": "👋 Welcome! Please select a service:",
        "main_menu": "⬅️ Return to Main Menu",
        "first_name": "Please enter your **First Name** (in Latin letters):",
        "last_name": "Please enter your **Last Name**:",
        "birth_date": "Please enter your **Date of Birth** (format: YYYY-MM-DD):",
        "pesel": "Please enter your **PESEL**:",
        "residence": "Please enter your **Place of Residence**:",
        "start_date": "Please enter the **Start Date** of Usprawidliwienie (YYYY-MM-DD):",
        "end_date": "Please enter the **End Date** of Usprawidliwienie (YYYY-MM-DD):",
        "select_payment": "Please select a payment method:",
        "thank_you": "Thank you for your order! ✅",
        "payment_details_cash": "Payment on delivery. Our team will contact you via Telegram.",
        "payment_details_online": "Please complete the payment by visiting <a href='https://buy.stripe.com/aEU4gnflHc5z9Co4gg'>this link</a>. Include your <b>Request Key</b>: {request_key} in the payment description. Our team will contact you after confirmation.",
        "feature_in_development": "Sorry, this feature is still under development. Please check back later.",
        "menu1": "📝 Document Preparation",
        "menu2": "📚 Academic Assistance",
        "menu3": "💼 Other Services",
        "available_docs": "Please select a document service:",
        "usprawidliwienie": "Usprawidliwienie lekarskie"
    },
    "pl": {
        "welcome": "👋 Witaj! Wybierz usługę:",
        "main_menu": "⬅️ Powrót do głównego menu",
        "first_name": "Proszę wprowadzić swoje **Imię** (w literach łacińskich):",
        "last_name": "Proszę wprowadzić swoje **Nazwisko**:",
        "birth_date": "Proszę wprowadzić swoją **Datę urodzenia** (format: YYYY-MM-DD):",
        "pesel": "Proszę wprowadzić swój **PESEL**:",
        "residence": "Proszę wprowadzić swoje **Miejsce zamieszkania**:",
        "start_date": "Proszę wprowadzić **Datę początkową** usprawiedliwienia (YYYY-MM-DD):",
        "end_date": "Proszę wprowadzić **Datę końcową** usprawiedliwienia (YYYY-MM-DD):",
        "select_payment": "Proszę wybrać metodę płatności:",
        "thank_you": "Dziękujemy za zamówienie! ✅",
        "payment_details_cash": "Płatność przy odbiorze. Nasz zespół skontaktuje się z Tobą przez Telegram.",
        "payment_details_online": "Proszę dokonać płatności, odwiedzając <a href='https://buy.stripe.com/aEU4gnflHc5z9Co4gg'>ten link</a>. Wprowadź <b>Klucz zapytania</b>: {request_key} w opisie płatności. Nasz zespół skontaktuje się po potwierdzeniu płatności.",
        "feature_in_development": "Przepraszamy, ta funkcja jest nadal w trakcie opracowywania. Proszę sprawdzić później.",
        "menu1": "📝 Przygotowanie dokumentów",
        "menu2": "📚 Pomoc akademicka",
        "menu3": "💼 Inne usługi",
        "available_docs": "Proszę wybrać usługę dokumentu:",
        "usprawidliwienie": "Usprawiedliwienie lekarskie"
    },
    "uk": {
        "welcome": "👋 Вітаємо! Будь ласка, виберіть послугу:",
        "main_menu": "⬅️ Повернутися до головного меню",
        "first_name": "Будь ласка, введіть своє **Ім'я** (латинськими літерами):",
        "last_name": "Будь ласка, введіть своє **Прізвище**:",
        "birth_date": "Будь ласка, введіть свою **Дату народження** (формат: YYYY-MM-DD):",
        "pesel": "Будь ласка, введіть свій **PESEL**:",
        "residence": "Будь ласка, введіть своє **Місце проживання**:",
        "start_date": "Будь ласка, введіть **Початкову дату** (YYYY-MM-DD):",
        "end_date": "Будь ласка, введіть **Кінцеву дату** (YYYY-MM-DD):",
        "select_payment": "Будь ласка, виберіть спосіб оплати:",
        "thank_you": "Дякуємо за ваше замовлення! ✅",
        "payment_details_cash": "Оплата при доставці. Наша команда зв’яжеться з вами через Telegram.",
        "payment_details_online": "Будь ласка, зробіть оплату за <a href='https://buy.stripe.com/aEU4gnflHc5z9Co4gg'>цим посиланням</a>. Введіть <b>Ключ запиту</b>: {request_key} в описі оплати. Наша команда зв’яжеться після підтвердження оплати.",
        "feature_in_development": "Вибачте, ця функція все ще в розробці. Будь ласка, перевірте пізніше.",
        "menu1": "📝 Підготовка документів",
        "menu2": "📚 Академічна допомога",
        "menu3": "💼 Інші послуги",
        "available_docs": "Будь ласка, виберіть послугу документа:",
        "usprawidliwienie": "Usprawidliwienie lekarskie"
    }
}

# Глобальный словарь для хранения выбранного языка пользователя
user_language = {}

def get_main_menu(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LANGUAGES[lang]["menu1"])],
            [KeyboardButton(text=LANGUAGES[lang]["menu2"])],
            [KeyboardButton(text=LANGUAGES[lang]["menu3"])]
        ],
        resize_keyboard=True
    )

def get_document_menu(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LANGUAGES[lang]["usprawidliwienie"])],
            [KeyboardButton(text=LANGUAGES[lang]["main_menu"])]
        ],
        resize_keyboard=True
    )

payment_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💵 Cash"), KeyboardButton(text="💰 Online Payment")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def select_language(message: Message):
    await message.answer("🌐 Please select your language / Wybierz swój język / Виберіть мову:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇬🇧 English"), KeyboardButton(text="🇵🇱 Polski"), KeyboardButton(text="🇺🇦 Українська")]
        ],
        resize_keyboard=True
    ))

@dp.message(lambda message: message.text in ["🇬🇧 English", "🇵🇱 Polski", "🇺🇦 Українська"])
async def set_language(message: Message):
    if message.text == "🇬🇧 English":
        user_language[message.from_user.id] = "en"
    elif message.text == "🇵🇱 Polski":
        user_language[message.from_user.id] = "pl"
    elif message.text == "🇺🇦 Українська":
        user_language[message.from_user.id] = "uk"

    lang = user_language[message.from_user.id]
    await message.answer(LANGUAGES[lang]["welcome"], reply_markup=get_main_menu(lang))

@dp.message(lambda message: message.text in [lang_dict["menu1"] for lang_dict in LANGUAGES.values()] + 
                                     [lang_dict["menu2"] for lang_dict in LANGUAGES.values()] +
                                     [lang_dict["menu3"] for lang_dict in LANGUAGES.values()])
async def handle_service_selection(message: Message):
    lang = user_language.get(message.from_user.id, "en")
    selected_service = message.text

    if selected_service == LANGUAGES[lang]["menu1"]:  # Document Preparation
        await message.answer(LANGUAGES[lang]["available_docs"], reply_markup=get_document_menu(lang))
    elif selected_service == LANGUAGES[lang]["menu2"] or selected_service == LANGUAGES[lang]["menu3"]:  # Academic Assistance or Other Services
        await message.answer(LANGUAGES[lang]["feature_in_development"], reply_markup=get_main_menu(lang))

@dp.message(lambda message: message.text in [lang_dict["usprawidliwienie"] for lang_dict in LANGUAGES.values()])
async def document_preparation_menu(message: Message):
    lang = user_language.get(message.from_user.id, "en")
    await message.answer(LANGUAGES[lang]["first_name"])
    user_data[message.from_user.id] = {"step": "first_name"}

@dp.message(lambda message: message.text == LANGUAGES['en']['main_menu'] or message.text == LANGUAGES['pl']['main_menu'] or message.text == LANGUAGES['uk']['main_menu'])
async def return_to_main_menu(message: Message):
    lang = user_language.get(message.from_user.id, "en")
    await message.answer(LANGUAGES[lang]["welcome"], reply_markup=get_main_menu(lang))

@dp.message(lambda message: message.from_user.id in user_data)
async def collect_user_data(message: Message):
    user_id = message.from_user.id
    current_step = user_data[user_id].get("step")
    lang = user_language.get(user_id, "en")

    if current_step == "first_name":
        user_data[user_id]["first_name"] = message.text
        await message.answer(LANGUAGES[lang]["last_name"])
        user_data[user_id]["step"] = "last_name"

    elif current_step == "last_name":
        user_data[user_id]["last_name"] = message.text
        await message.answer(LANGUAGES[lang]["birth_date"])
        user_data[user_id]["step"] = "birth_date"

    elif current_step == "birth_date":
        user_data[user_id]["birth_date"] = message.text
        await message.answer(LANGUAGES[lang]["pesel"])
        user_data[user_id]["step"] = "pesel"

    elif current_step == "pesel":
        user_data[user_id]["pesel"] = message.text
        await message.answer(LANGUAGES[lang]["residence"])
        user_data[user_id]["step"] = "residence"

    elif current_step == "residence":
        user_data[user_id]["residence"] = message.text
        await message.answer(LANGUAGES[lang]["start_date"])
        user_data[user_id]["step"] = "start_date"

    elif current_step == "start_date":
        user_data[user_id]["start_date"] = message.text
        await message.answer(LANGUAGES[lang]["end_date"])
        user_data[user_id]["step"] = "end_date"

    elif current_step == "end_date":
        user_data[user_id]["end_date"] = message.text
        request_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        user_data[user_id]["request_key"] = request_key
        await message.answer(LANGUAGES[lang]["select_payment"], reply_markup=payment_menu)
        user_data[user_id]["step"] = "payment_method"

    elif current_step == "payment_method":
        username = f"@{message.from_user.username}" if message.from_user.username else "N/A"

        if message.text == "💵 Cash":
            payment_method = "Cash"
            payment_details = LANGUAGES[lang]["payment_details_cash"]
        elif message.text == "💰 Online Payment":
            payment_method = "Online Payment"
            payment_details = LANGUAGES[lang]["payment_details_online"].format(request_key=user_data[user_id]["request_key"])
        else:
            await message.answer("Invalid option. Please select a valid payment method.")
            return

        save_to_google_sheets(user_data[user_id], username, payment_method)
        await message.answer(
            f"{payment_details}\n\n{LANGUAGES[lang]['thank_you']}",
            reply_markup=get_main_menu(lang),
            parse_mode="HTML"
        )
        user_data.pop(user_id)

def save_to_google_sheets(data, username, payment_method):
    headers = ["First Name", "Last Name", "Date of Birth", "PESEL", "Place of Residence", "Start Date", "End Date", "Request Key", "Payment Method", "Telegram Username"]
    values = [
        data["first_name"], data["last_name"], data["birth_date"], data["pesel"], data["residence"],
        data["start_date"], data["end_date"], data["request_key"], payment_method, username
    ]
    if worksheet.row_count == 1:
        worksheet.append_row(headers)
    worksheet.append_row(values)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())