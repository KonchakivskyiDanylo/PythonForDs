from telegram.ext import Application, ContextTypes, CommandHandler, ConversationHandler, filters, CallbackQueryHandler, \
    MessageHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import os
from dotenv import load_dotenv
import pymongo
import requests
import asyncio
import pandas as pd
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
API_TOKEN = os.getenv("API_TOKEN")
FLASK_API_URL = os.getenv("FLASK_API_URL")
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["PythonForDs"]
users_collection = db["users"]
predict_collection = db["prediction"]
REGIONS = ['Vinnytsia', 'Lutsk', 'Dnipro', 'Donetsk',
           'Zhytomyr', 'Uzhgorod', 'Zaporozhye', 'Ivano-Frankivsk', 'Kyiv',
           'Kropyvnytskyi', 'Lviv', 'Mykolaiv', 'Odesa', 'Poltava',
           'Rivne', 'Sumy', 'Ternopil', 'Kharkiv', 'Kherson', 'Khmelnytskyi',
           'Cherkasy', 'Chernivtsi', 'Chernihiv', 'Kyivska']
regions = pd.read_csv("data/regions.csv")
PREDICT_BUTTON = 0


def get_prediction(region):
    response = requests.post(f"{FLASK_API_URL}/predict", json={"region": region, "token": API_TOKEN})
    if response.status_code == 200:
        data = response.json()
        predictions = data.get(region, [])
        result = []
        for prediction in predictions:
            datetime_str = prediction.get('datetime')
            datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S")
            formatted_datetime = datetime_obj.strftime("%d.%m %H:%M")
            value = "yes" if prediction.get('prediction') == 1 else "no"

            result.append(f"{formatted_datetime} : {value}")
        return "\n".join(result)
    return "Error: Unable to get prediction."


def get_alarms():
    response = requests.get(f"{FLASK_API_URL}/alarms")
    if response.status_code == 200:
        return response.json()
    return "Error: Unable to get active alarms."


def get_location():
    response = requests.get(f"{FLASK_API_URL}/location")
    if response.status_code == 200:
        return response.text
    return "Error: Unable to get location."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_location = get_location()

    user_data = {
        "user_id": user_id,
        "user_name": update.message.from_user.username,
        "region": user_location,
        "active_alert": user_location in get_alarms()
    }

    if users_collection.find_one({"user_id": user_id}) is None:
        users_collection.insert_one(user_data)
        await update.message.reply_text(
            "Welcome!\n\n"
            "- Type /predict and choose a region to view predictions for the next 24 hours.\n"
            "- Type /alarms to view active alarms.\n"
        )
    else:
        await update.message.reply_text("You are already registered.")


async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = []
    row = []
    for i, region in enumerate(REGIONS):
        row.append(InlineKeyboardButton(region, callback_data=f"predict_{region}"))
        if (i + 1) % 3 == 0:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please select a region:", reply_markup=reply_markup)
    return PREDICT_BUTTON


async def show_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    region = query.data.split("_")[1]
    if region != "Kyiv" and region != "Kyivska":
        predict_region = regions.loc[regions["center_city_en"] == region, "region"].values[0]
    elif region == "Kyiv":
        predict_region = "Київ"
    else:
        predict_region = "Kyivska"
    prediction = get_prediction(predict_region)
    await query.edit_message_text(text=f"Prediction for {region}:\n\n{prediction}")
    return ConversationHandler.END


async def alarms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    active_alarms = get_alarms()
    formatted_alarms = '\n'.join(active_alarms)
    await update.message.reply_text(f"Active alarms:\n{formatted_alarms}")
    return ConversationHandler.END


async def send_daily_predictions(app: Application):
    users = users_collection.find()
    for user in users:
        user_id = user["user_id"]
        region = user["region"]

        prediction = get_prediction(region)
        print(prediction)

        await app.bot.send_message(user_id, f"Daily Prediction for {region}:\n\n{prediction}")


async def check_and_update_alarms(app: Application):
    users = users_collection.find()
    active_alarms = get_alarms()

    for user in users:
        user_id = user["user_id"]
        region = user["region"]
        active_alert = user["active_alert"]

        if not active_alert and region in active_alarms:
            await app.bot.send_message(user_id, f"ALERT: There is an active alarm in your region ({region})!")
            users_collection.update_one({"user_id": user_id}, {"$set": {"active_alert": True}})

        elif active_alert and region not in active_alarms:
            await app.bot.send_message(user_id, f"ALARM FINISHED: The alarm in your region ({region}) has ended.")
            users_collection.update_one({"user_id": user_id}, {"$set": {"active_alert": False}})


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Try again")
    return ConversationHandler.END


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Update {update} caused error {context.error}")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("predict", predict)],
        states={
            PREDICT_BUTTON: [
                CallbackQueryHandler(show_prediction, pattern=f"^predict_.+$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    app.add_handler(CommandHandler("alarms", alarms))
    scheduler = BackgroundScheduler()
    loop = asyncio.get_event_loop()
    scheduler.add_job(lambda: loop.call_soon_threadsafe(lambda: asyncio.create_task(send_daily_predictions(app))),
                      'cron', hour=12, minute=0)
    scheduler.add_job(lambda: loop.call_soon_threadsafe(lambda: asyncio.create_task(check_and_update_alarms(app))),
                      'interval', minutes=1)
    scheduler.start()
    app.add_error_handler(error)
    app.run_polling(poll_interval=0.1)


if __name__ == "__main__":
    main()
