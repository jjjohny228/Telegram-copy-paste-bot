import os

from telethon.errors import PhoneNumberBannedError, PasswordHashInvalidError, UsernameInvalidError
from telethon.types import DocumentAttributeFilename, InputMediaUploadedPhoto
from telethon.sync import TelegramClient, events
from loguru import logger
from dotenv import load_dotenv
from collections import defaultdict

from config import Config
from src.utils import (change_channel_signature, text_contain_banword, find_target_channel_for_single_message,
                       find_target_channel_for_album, check_caption)

load_dotenv()

# Setup logger
logger.add("logs/logs.log", format="{time} {level} {message}", rotation="10:00", compression="zip")

# Dictionary to store grouped messages temporarily
grouped_messages = defaultdict(list)

client = TelegramClient(
    session = f"sessions/tg_{os.getenv('PHONE_NUMBER')}",
    api_id = int(os.getenv("API_ID")),
    api_hash = os.getenv("API_HASH"),
    device_model = os.getenv("DEVICE_MODEL"),
    system_version = os.getenv("SYSTEM_VERSION")
)

source_channels = (channel['source_channel_id'] for channel in Config.CHANNELS)


@client.on(events.NewMessage(chats=source_channels, forwards=Config.FORWARDS))
async def message_handler(event):
    try:
        # Check if the message is part of an album
        if event.message.grouped_id is not None:
            grouped_id = event.message.grouped_id
            if grouped_id not in grouped_messages:
                grouped_messages.clear()
                grouped_messages[grouped_id] = []
            else:
                logger.info('Group id is already in use')
                return

            # Find all messages of the group
            messages = await client.get_messages(event.message.peer_id, min_id=event.message.id - 5,
                                                 max_id=event.message.id + 5)
            album_messages = [message for message in messages if message.grouped_id == event.message.grouped_id]
            album_messages.reverse()
            if not album_messages:
                return

            grouped_messages[grouped_id] = album_messages

            # If no new messages have been added to the group, process the album
            if grouped_id in grouped_messages and len(grouped_messages.get(grouped_id)) > 1:
                await process_album(grouped_messages[grouped_id])
        else:
            # Process single messages
            await process_single_message(event)
    except Exception as e:
        logger.error(f"Error in message handler: {e}")


async def process_album(messages):
    """
    Process a group of messages (album).
    """
    try:
        media = []
        target_channel = await find_target_channel_for_album(messages[0].peer_id.channel_id, Config.CHANNELS)
        caption = await change_channel_signature(messages[0].message,
                                                 target_channel.get('source_channel_signature'),
                                                 target_channel.get('target_channel_signature'))
        if caption and await text_contain_banword(caption, Config.BAN_WARDS):
            return

        force_document = False
        caption = await check_caption(caption)

        logger.info(f"Received album with {len(messages)} messages.")

        for message in messages:
            if message.photo:
                media.append(await client.download_media(message, f"temp_pics/{message.id}.png"))
            elif message.video:
                media.append(await client.download_media(message, f"temp_pics/{message.id}.mp4"))
            elif message.document:
                file_name = next((x.file_name for x in message.document.attributes if isinstance(x, DocumentAttributeFilename)), None)
                media.append(await client.download_media(message, f"temp_pics/{file_name}"))
                force_document = True
            else:
                logger.info("Unknown message type in album")
                return
        await client.send_file(target_channel.get('target_channel_id'), media, caption=caption, force_document=force_document)
        logger.info(f"Copied and forwarded album with {len(messages)} messages.")

        for file in media:
            os.remove(file)  # Clean up temporary files
    except Exception as e:
        logger.error(f"Error processing album: {e}")

async def process_single_message(message):
    """
    Process a single message.
    """
    try:
        message_id = message.message.id
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

        logger.info(f"Received single message {message_id}.")

        target_channel = await find_target_channel_for_single_message(message, Config.CHANNELS)
        caption = await change_channel_signature(message.text,
                                                 target_channel.get('source_channel_signature'),
                                                 target_channel.get('target_channel_signature'))
        if caption and await text_contain_banword(caption, Config.BAN_WARDS):
            return

        if message.photo and not web_preview:
            await client.download_media(message.message, f"temp_pics/pics_{message_id}.png")
            await client.send_file(target_channel.get('target_channel_id'), InputMediaUploadedPhoto(await client.upload_file(f"temp_pics/pics_{message_id}.png"), spoiler=spoiler), caption=caption)
            os.remove(f"temp_pics/pics_{message_id}.png")

        elif message.video:
            await client.download_media(message.message, f"temp_pics/pics_{message_id}.mp4")
            await client.send_file(target_channel.get('target_channel_id'), f"temp_pics/pics_{message_id}.mp4", caption=caption, video_note=True)
            os.remove(f"temp_pics/pics_{message_id}.mp4")

        elif message.document:
            file_name = next((x.file_name for x in message.document.attributes if isinstance(x, DocumentAttributeFilename)), None)
            if message.document.mime_type == "audio/ogg":
                path = await client.download_media(message.message, f"temp_pics/{message_id}")
                await client.send_file(target_channel.get('target_channel_id'), path, voice_note=True)
                os.remove(path)
                return
            await client.download_media(message.message, f"temp_pics/{file_name}")
            await client.send_file(target_channel.get('target_channel_id'), f"temp_pics/{file_name}", caption=caption, force_document=True)
            os.remove(f"temp_pics/{file_name}")

        else:
            try:
                await client.send_message(target_channel.get('target_channel_id'), caption)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                return

        logger.success(f"Copied and forwarded single message {message_id}.")
    except Exception as e:
        logger.error(f"Error processing single message: {e}")


if __name__ == "__main__":
    try:
        client.start(phone=os.getenv('PHONE_NUMBER'))
        os.system('cls' if os.name == 'nt' else 'clear')
        logger.success(f"You successfully logged in account {os.getenv('PHONE_NUMBER')}.")
        client.parse_mode = "html"

        client.run_until_disconnected()
        logger.info(f"Session {os.getenv('PHONE_NUMBER')} has ended.")
    except PhoneNumberBannedError:
        logger.error(f"Account {os.getenv('PHONE_NUMBER')} is blocked.")
    except PasswordHashInvalidError:
        logger.error(f"Incorrect password for the account {os.getenv('PHONE_NUMBER')}.")
    except UsernameInvalidError:
        pass
    except Exception as e:
        logger.error(f"Unknown error: {e}")