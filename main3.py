import time

from telethon import TelegramClient, events
import os
from dotenv import load_dotenv

load_dotenv()


client = TelegramClient(
    session = f"tg_{os.getenv('PHONE_NUMBER')}",
    api_id = int(os.getenv("API_ID")),
    api_hash = os.getenv("API_HASH"),
    device_model = os.getenv("DEVICE_MODEL"),
    system_version = os.getenv("SYSTEM_VERSION")
)

@client.on(events.NewMessage())
async def handler(event):
    print('New message')
    some = await client.download_media(event, f'temp_pics/{int(time.time())}.png')
    print(some)

with client:
    client.run_until_disconnected()