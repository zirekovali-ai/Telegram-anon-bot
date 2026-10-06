import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, ContextTypes, filters

CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

pending_messages = {}


async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.effective_user

    # Не принимаем сообщения от самого администратора
    if user.id == ADMIN_ID:
        return

    message_id = update.message.message_id

    pending_messages[message_id] = {
        "chat_id": update.message.chat_id,
        "message_id": message_id
    }

    keyboard = [[
        InlineKeyboardButton("✅ Опубликовать", callback_data=f"publish:{message_id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"reject:{message_id}")
    ]]

    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=update.message.chat_id,
        message_id=message_id
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text="Новое сообщение от подписчика:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    action, message_id = query.data.split(":")

    if message_id not in pending_messages:
        await query.edit_message_text("Сообщение уже обработано.")
        return

    data = pending_messages[message_id]

    if action == "publish":
        await context.bot.copy_message(
            chat_id=CHANNEL_ID,
            from_chat_id=data["chat_id"],
            message_id=data["message_id"]
        )
        await query.edit_message_text("✅ Опубликовано в канале.")

    elif action == "reject":
        await query.edit_message_text("❌ Отклонено.")

    del pending_messages[message_id]


async def main():
    token = os.getenv("BOT_TOKEN")

    app = Application.builder().token(token).build()

    app.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND,
        receive_message
    ))

    app.add_handler(CallbackQueryHandler(button_handler))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
