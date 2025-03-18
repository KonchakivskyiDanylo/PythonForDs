from telethon import TelegramClient
import os

API_ID = "23618673"
API_HASH = "0d1689bb32d38ae5b4d40128a4e38340"

SESSION_NAME = "user_session"
if os.path.exists(f"{SESSION_NAME}.session"):
    os.remove(f"{SESSION_NAME}.session")

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# 🔹 Отримання ID каналу за юзернеймом
async def get_channel_id(channel_username):
    try:
        entity = await client.get_entity(channel_username)
        channel_id = entity.id
        print(f"🔹 ID каналу {channel_username}: {channel_id}")
        return channel_id
    except Exception as e:
        print(f"❌ Помилка отримання ID каналу: {e}")
        return None

# Функція для отримання та красивого виводу повідомлень
async def fetch_latest_messages(channel_id, limit=10):
    try:
        print("=" * 60)
        print(f"📢 Останні {limit} повідомлень з каналу")
        print("=" * 60)

        async for message in client.iter_messages(channel_id, limit=limit):
            if message.text:  # Пропускаємо пусті повідомлення
                print(f"📅 Дата: {message.date.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"👤 Відправник ID: {message.sender_id}")
                print(f"📝 Текст: {message.text}\n")
                print("-" * 60)
    except Exception as e:
        print(f"❌ Помилка отримання повідомлень: {e}")

# Основна функція
async def main():
    await client.start()  # Авторизація через особистий акаунт
    print("✅ Користувач успішно авторизований!")

    # 🔹 Отримуємо ID каналу
    channel_id = await get_channel_id("@DeepStateUA")
    if channel_id:
        await fetch_latest_messages(channel_id, 10)  # Останні 10 повідомлень

# Запуск
await main()
