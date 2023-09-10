# pylint: disable=unused-argument, import-error
# This program is dedicated to the public domain under the CC0 license.
import logging
import subprocess
import time

from telegram import InlineKeyboardButton, \
    InlineKeyboardMarkup, \
    ReplyKeyboardMarkup, \
    ReplyKeyboardRemove, \
    Update, Bot, ChatPhoto
import telegram
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)
from my_token import TOKEN

BEGIN_ROUTE, SETTINGS_ROUTE, AVA_ROUTE, PROGRESS_ROUTE = range(4)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    keyboard = [[
        InlineKeyboardButton("Персонаж", callback_data="Chel"),
        InlineKeyboardButton("В путь", callback_data="GO")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text="Здравствуйте, я ваш гид. Вы можете создать своего персонажа и начать увлекательное путешествие по Казани!",
        reply_markup=reply_markup
    )
    return BEGIN_ROUTE


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [[
        InlineKeyboardButton("Мой персонаж", callback_data="Chel"),
        InlineKeyboardButton("В путь", callback_data="GO")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Здравствуйте, я ваш гид. Вы можете создать своего персонажа и начать увлекательное путешествие по Казани!",
        reply_markup=reply_markup
    )
    return BEGIN_ROUTE


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Задать внешность", callback_data="Ava"),
            InlineKeyboardButton("Показать внешность", callback_data="ShowAva"),
        ],
        [
            InlineKeyboardButton("Выйти", callback_data="MainMenu"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Тут вы работаете с вашим персонажем...", reply_markup=reply_markup
    )
    return SETTINGS_ROUTE


async def ava_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Не могли бы Вы выслать вашу фотографию?")
    return AVA_ROUTE


async def set_ava(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    file = await context.bot.get_file(update.message.document)
    # await file.download_to_drive("images/file_name.png")
    await file.download_to_drive("images/chel.png")
    await context.bot.send_message(chat_id=context._chat_id, text="Ожидайте...")
    # Тут вообще ужас, пришлось на скорую руку хоть что-то предпринять. Поддержки многих пользователей, как видите, нет.
    # Сам алгоритм выполняет свою задачу долго, можно предринять некоторые модификации (например, использовать заливку по BFS)
    subprocess.run(["python", "tatarizator.py"]) # <-- Так писать нельзя
    await context.bot.send_photo(chat_id=context._chat_id, photo="images/result.png")
    keyboard = [[
        InlineKeyboardButton("Вернуться", callback_data="Chel")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Готово!", reply_markup=reply_markup)
    return BEGIN_ROUTE


async def get_ava(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_photo(chat_id=context._chat_id, photo="images/result.png")
    keyboard = [[
        InlineKeyboardButton("Вернуться", callback_data="Chel")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Готово!", reply_markup=reply_markup)
    return BEGIN_ROUTE


async def lets_goo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await context.bot.send_location(context._chat_id, 55.796129, 49.106414)
    await context.bot.send_audio(context._chat_id, audio="audio/coin.ogg")
    keyboard = [[
        InlineKeyboardButton("Итак, начнём наш путь!", callback_data="c0")
    ]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="И мы готовы...", reply_markup=reply_markup
    )
    return PROGRESS_ROUTE

# Добавили бы здесь sqlite с sqlalchemy, но что есть то есть :(
tmp_coordinates: list[tuple[float, float]] = [
    (55.778062, 49.119344),
    (55.779872, 49.117916),
    (55.781484, 49.123308),
    (55.787343, 49.121643),
    (55.788094, 49.120130),
    (55.788273, 49.119400),
    (55.790893, 49.114511),
    (55.793599, 49.116367),
    (55.792183, 49.112341),
    (55.796238, 49.108983),
    (55.796238, 49.108983),
    (55.798379, 49.105238),
    (55.799842, 49.105944),
    (55.800501, 49.105184)
]
tmp_names: list[str] = [
    "Апанаевская мечеть", "Мечеть Марджани", "Озеро Кабан", "Часы на улице Баумана",
    "Улица Баумана", "Богоявленская колокольня", "Нулевой меридиан", "Чернояровский пассаж",
    "Памятник Коту Казанскому", "Кем же был Джек Потрошитель", "Площадь первого мая",
    "Мечеть Кул Шариф", "Благовещенский Собор", "Башня Сююмбике"
]

# Первая идея, что в голову пришла, мне больно на этот код смотреть :/
async def chain(update: Update, context: ContextTypes.DEFAULT_TYPE, number: int) -> None:
    keyboard = [[
        f"Пункт {number + 1}/14"
    ]]
    await context.bot.send_message(context._chat_id,
                                   text=tmp_names[number],
                                   reply_markup=ReplyKeyboardMarkup(
                                       keyboard,
                                       one_time_keyboard=True
                                   )
                                   )
    await context.bot.send_location(context._chat_id, *tmp_coordinates[number])
    await context.bot.send_photo(context._chat_id, photo=f"images/{number + 1}.jpg")
    await context.bot.send_audio(context._chat_id, audio=f"audio/{number + 1}.m4a")


async def c0(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await chain(update, context, 0)
    return PROGRESS_ROUTE


async def c1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await chain(update, context, 1)
    return PROGRESS_ROUTE


async def c2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await chain(update, context, 2)
    return PROGRESS_ROUTE


async def c3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await chain(update, context, 3)
    return PROGRESS_ROUTE


async def c4(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await chain(update, context, 4)
    return PROGRESS_ROUTE


async def c5(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await chain(update, context, 5)
    return PROGRESS_ROUTE


async def c6(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await chain(update, context, 6)
    return PROGRESS_ROUTE


async def c7(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await chain(update, context, 7)
    return PROGRESS_ROUTE


async def c8(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await chain(update, context, 8)
    return PROGRESS_ROUTE


async def c9(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await chain(update, context, 9)
    return PROGRESS_ROUTE


async def c10(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await chain(update, context, 10)
    return PROGRESS_ROUTE


async def c11(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await chain(update, context, 11)
    return PROGRESS_ROUTE


async def c12(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await chain(update, context, 12)
    return PROGRESS_ROUTE


async def c13(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_message(context._chat_id, text=tmp_names[13])
    await context.bot.send_location(context._chat_id, *tmp_coordinates[13])
    await context.bot.send_photo(context._chat_id, photo="images/14.jpg")
    await context.bot.send_audio(context._chat_id, audio="audio/14.m4a")
    keyboard = [[
        InlineKeyboardButton("GO BACK GO BAK", callback_data=f"MainMenu")
    ]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text="I'm done", reply_markup=reply_markup
    )
    return BEGIN_ROUTE


def main() -> None:
    application = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            BEGIN_ROUTE: [
                CallbackQueryHandler(start, pattern="^MainMenu$"),
                CallbackQueryHandler(settings, pattern="^Chel$"),
                CallbackQueryHandler(lets_goo, pattern="^GO$")
            ],
            SETTINGS_ROUTE: [
                CallbackQueryHandler(ava_message, pattern="^Ava$"),
                CallbackQueryHandler(start, pattern="^MainMenu$"),
                CallbackQueryHandler(get_ava, pattern="^ShowAva$"),
            ],
            AVA_ROUTE: [
                MessageHandler(filters.Document.IMAGE, set_ava),
            ],
            PROGRESS_ROUTE: [
                # Я всё уже про это сказал
                CallbackQueryHandler(c0, pattern="^c0$"),
                MessageHandler(filters.Regex("^Пункт 1/14$"), c1),
                MessageHandler(filters.Regex("^Пункт 2/14$"), c2),
                MessageHandler(filters.Regex("^Пункт 3/14$"), c3),
                MessageHandler(filters.Regex("^Пункт 4/14$"), c4),
                MessageHandler(filters.Regex("^Пункт 5/14$"), c5),
                MessageHandler(filters.Regex("^Пункт 6/14$"), c6),
                MessageHandler(filters.Regex("^Пункт 7/14$"), c7),
                MessageHandler(filters.Regex("^Пункт 8/14$"), c8),
                MessageHandler(filters.Regex("^Пункт 9/14$"), c9),
                MessageHandler(filters.Regex("^Пункт 10/14$"), c10),
                MessageHandler(filters.Regex("^Пункт 11/14$"), c11),
                MessageHandler(filters.Regex("^Пункт 12/14$"), c12),
                MessageHandler(filters.Regex("^Пункт 13/14$"), c13),
            ]
        },
        fallbacks=[CommandHandler("start", start_command)]
    )

    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
