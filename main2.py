from collections import defaultdict
import asyncio
import os
import re
from telethon.errors import PhoneNumberBannedError, PasswordHashInvalidError, UsernameInvalidError
from telethon.types import DocumentAttributeFilename, InputMediaUploadedPhoto
from telethon.sync import TelegramClient, events
from dotenv import load_dotenv

from config import Config
from src.utils import change_channel_signature, text_contain_banword, find_target_channel
# Dictionary to store grouped messages temporarily
grouped_messages = defaultdict(list)

load_dotenv()

logo = """
█▀▀ █▀█ █▀█ █▄█ ▄▄ █▀█ ▄▀█ █▀ ▀█▀ █▀▀   █▄▄ █▀█ ▀█▀|ᵇʸ ᵈᵉˡᵃᶠᵃᵘˡᵗ
█▄▄ █▄█ █▀▀ ░█░ ░░ █▀▀ █▀█ ▄█ ░█░ ██▄   █▄█ █▄█ ░█░"""

last_id_message = []
# CHANNEL_PASTE = -1002327107376
def gd_print(value):
    green_color = '\033[32m'
    reset_color = '\033[0m'
    result = f"\n>{green_color} {value} {reset_color}\n"
    print(result)

def bd_print(value):
    red_color = '\033[31m'
    reset_color = '\033[0m'
    result = f"\n>{red_color} {value} {reset_color}\n"
    print(result)

async def check_caption(caption):
    if Config.AUTO_DELETE_LINKS is False:
        return caption
    elif Config.AUTO_DELETE_LINKS is True:
        return re.sub(r'<a\s[^>]*>.*?</a>', '', caption)
    elif Config.AUTO_DELETE_LINKS is None:
        return re.sub(r'<a\s[^>]*>(.*?)</a>', r'\1', caption)
    elif Config.AUTO_DELETE_LINKS not in [True, False, None]:
        return re.sub(r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"(?:[^>]*)>(.*?)</a>', rf'<a href="{Config.AUTO_DELETE_LINKS}">\2</a>', caption)

client = TelegramClient(
    session = f"tg_{os.getenv('PHONE_NUMBER')}",
    api_id = int(os.getenv("API_ID")),
    api_hash = os.getenv("API_HASH"),
    device_model = os.getenv("DEVICE_MODEL"),
    system_version = os.getenv("SYSTEM_VERSION")
)

source_channels = (channel['source_channel_id'] for channel in Config.CHANNELS)


@client.on(events.NewMessage(chats=source_channels, forwards=Config.FORWARDS))
async def message_handler(event):
    # try:
        # Check if the message is part of an album
    if event.message.grouped_id is not None:
        grouped_id = event.message.grouped_id
        grouped_messages[grouped_id].append(event)

        # Wait for a short delay to collect all messages in the group
        await asyncio.sleep(2)  # Adjust the delay as needed

        # If no new messages have been added to the group, process the album
        if grouped_id in grouped_messages and len(grouped_messages[grouped_id]) > 1:
            await process_album(grouped_messages[grouped_id])
            del grouped_messages[grouped_id]  # Clear the group after processing
    else:
        # Process single messages
        await process_single_message(event)
    # except Exception as e:
    #     bd_print(f"Error in message handler: {e}")

async def process_album(messages):
    """
    Process a group of messages (album).
    """
    # try:
    print(*messages, sep='\n')
    media = []
    target_channel = await find_target_channel(messages[0], Config.CHANNELS)
    caption = await change_channel_signature(messages[0].text,
                                             target_channel.get('source_channel_signature'),
                                             target_channel.get('target_channel_signature'))
    if caption and await text_contain_banword(caption, Config.BAN_WARDS):
        return

    force_document = False
    caption = await check_caption(caption)

    gd_print(f"Received album with {len(messages)} messages.")

    for message in messages:
        if message.photo:
            print('phototo')
            media.append(await client.download_media(message, f"temp_pics/{message.id}.png"))
        elif message.video:
            media.append(await client.download_media(message, f"temp_pics/{message.id}.mp4"))
        elif message.document:
            file_name = next((x.file_name for x in message.document.attributes if isinstance(x, DocumentAttributeFilename)), None)
            media.append(await client.download_media(message, f"temp_pics/{file_name}"))
            force_document = True
        else:
            bd_print("Unknown message type in album")
            return
    print(media)
    await client.send_file(target_channel.get('target_channel_id'), media, caption=caption, force_document=force_document)
    gd_print(f"Copied and forwarded album with {len(messages)} messages.")

    # for file in media:
    #     os.remove(file)  # Clean up temporary files
    # except Exception as e:
    #     bd_print(f"Error processing album: {e}")

async def process_single_message(message):
    """
    Process a single message.
    """
    # try:
    id = message.id
    caption = message.text
    spoiler = False
    web_preview = False

    try:
        if message.media.__dict__['spoiler'] is True:
            spoiler = True
    except (AttributeError, KeyError):
        pass

    try:
        if message.media.webpage.__dict__['url'] is not None:
            web_preview = True
    except (AttributeError, KeyError):
        pass

    gd_print(f"Received single message {id}.")

    target_channel = await find_target_channel(message, Config.CHANNELS)
    caption = await change_channel_signature(message.text,
                                             target_channel.get('source_channel_signature'),
                                             target_channel.get('target_channel_signature'))
    if caption and await text_contain_banword(caption, Config.BAN_WARDS):
        return

    if message.photo and not web_preview:
        await client.download_media(message, f"temp_pics/pics_{id}.png")
        await client.send_file(target_channel.get('target_channel_id'), InputMediaUploadedPhoto(await client.upload_file(f"temp_pics/pics_{id}.png"), spoiler=spoiler), caption=caption)
        os.remove(f"temp_pics/pics_{id}.png")

    elif message.video:
        await client.download_media(message, f"temp_pics/pics_{id}.mp4")
        await client.send_file(target_channel.get('target_channel_id'), f"temp_pics/pics_{id}.mp4", caption=caption, video_note=True)
        os.remove(f"temp_pics/pics_{id}.mp4")

    elif message.document:
        file_name = next((x.file_name for x in message.document.attributes if isinstance(x, DocumentAttributeFilename)), None)
        if message.document.mime_type == "audio/ogg":
            path = await client.download_media(message, f"temp_pics/{id}")
            await client.send_file(target_channel.get('target_channel_id'), path, voice_note=True)
            os.remove(path)
            return
        await client.download_media(message, f"temp_pics/{file_name}")
        await client.send_file(target_channel.get('target_channel_id'), f"temp_pics/{file_name}", caption=caption, force_document=True)
        os.remove(f"temp_pics/{file_name}")

    else:
        try:
            await client.send_message(target_channel.get('target_channel_id'), caption)
        except Exception as e:
            bd_print(f"Error sending message: {e}")
            return

    gd_print(f"Copied and forwarded single message {id}.")
    # except Exception as e:
    #     bd_print(f"Error processing single message: {e}")


if __name__ == "__main__":
    try:
        client.start(phone=os.getenv('PHONE_NUMBER'))
        os.system('cls' if os.name == 'nt' else 'clear')
        print(logo)
        gd_print(f"Успешно вошли в аккаунт {os.getenv('PHONE_NUMBER')}.")
        client.parse_mode = "html"

        client.run_until_disconnected()
        gd_print(f"Сессия {os.getenv('PHONE_NUMBER')} завершена.")
    except PhoneNumberBannedError:
        bd_print(f"Аккаунт {os.getenv('PHONE_NUMBER')} заблокирован.")
    except PasswordHashInvalidError:
        bd_print(f"Неверный пароль для аккаунта {os.getenv('PHONE_NUMBER')}.")
    except UsernameInvalidError:
        pass
    except Exception as e:
        bd_print(f"Неизвестная ошибка: {e}")