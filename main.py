import os
import re
from telethon.errors import PhoneNumberBannedError, PasswordHashInvalidError, UsernameInvalidError
from telethon.types import DocumentAttributeFilename, InputMediaUploadedPhoto
from telethon.sync import TelegramClient, events
from dotenv import load_dotenv

from config import Config
from src.utils import change_channel_signature, text_contain_banword, find_target_channel

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
    session = f"sessions/tg_{os.getenv('PHONE_NUMBER')}",
    api_id = int(os.getenv("API_ID")),
    api_hash = os.getenv("API_HASH"),
    device_model = os.getenv("DEVICE_MODEL"),
    system_version = os.getenv("SYSTEM_VERSION")
)

source_channels = (channel['source_channel_id'] for channel in Config.CHANNELS)


@client.on(events.NewMessage(chats=source_channels, forwards=Config.FORWARDS))
async def message_handler(event):
    """
    Обработка сообщений
    """
    print(event)
    if event.message.grouped_id is not None:
        print('scip album')
        return

    id = event.message.id
    caption = event.message.text
    spoiler = False
    web_preview = False

    try:
        if event.message.media.__dict__['spoiler'] is True:
            spoiler = True
    except AttributeError:
        pass
    except KeyError:
        pass

    try:
        if event.message.media.webpage.__dict__['url'] is not None:
            web_preview = True
    except AttributeError:
        pass
    except KeyError:
        pass

    gd_print(f"Получили сообщение {id}.")

    target_channel = await find_target_channel(event, Config.CHANNELS)
    caption = await change_channel_signature(event.message.text,
                                             target_channel.get('source_channel_signature'),
                                             target_channel.get('target_channel_signature'))
    if caption and await text_contain_banword(caption, Config.BAN_WARDS):
        return

    if event.message.photo and not web_preview:
        await client.download_media(event.message, f"temp_pics/pics_{id}.png")
        await client.send_file(target_channel.get('target_channel_id'),
                               InputMediaUploadedPhoto(await client.upload_file(f"temp_pics/pics_{id}.png"),
                                                       spoiler=spoiler), caption=caption)
        os.remove(f"temp_pics/pics_{id}.png")

    elif event.message.video:
        await client.download_media(event.message, f"temp_pics/pics_{id}.mp4")
        await client.send_file(target_channel.get('target_channel_id'), f"temp_pics/pics_{id}.mp4", caption=caption,
                               video_note=True)  # video_note позволяет отправлять кружки в виде кружков, однако из-за этого иногда GIF может ошибочно отправляться как кружок. Используйте video_note = False на своё усмотрение.
        os.remove(f"temp_pics/pics_{id}.mp4")

    elif event.message.document:
        file_name = next(
            (x.file_name for x in event.message.document.attributes if isinstance(x, DocumentAttributeFilename)), None)
        if event.message.document.mime_type == "audio/ogg":
            path = await client.download_media(event.message, f"temp_pics/{id}")
            await client.send_file(target_channel.get('target_channel_id'), path, voice_note=True)
            os.remove(path)
            return
        await client.download_media(event.message, f"temp_pics/{file_name}")
        await client.send_file(target_channel.get('target_channel_id'), f"temp_pics/{file_name}", caption=caption,
                               force_document=True)
        os.remove(f"temp_pics/{file_name}")

    else:
        try:
            await client.send_message(target_channel.get('target_channel_id'), caption)
        except Exception as e:
            bd_print(f"Ошибка при отправке сообщения: {e}")
            return

    gd_print(f"Скопировали и успешно отправили сообщение {id}.")


@client.on(events.Album(source_channels))
async def album_handler(event):
    print('Album', event)
    print(type(event))
    """
    Обработка альбомов
    """
    if Config.FORWARDS is True:
        if event.messages[0].fwd_from:
            pass
        else:
            return
    elif Config.FORWARDS is False:
        if event.messages[0].fwd_from:
            return

    media = []
    target_channel = await find_target_channel(event, Config.CHANNELS)
    caption = await change_channel_signature(event.messages[0].text,
                                             target_channel.get('source_channel_signature'),
                                             target_channel.get('target_channel_signature'))
    if caption and await text_contain_banword(caption, Config.BAN_WARDS):
        return
    force_document = False
    message_id = event.messages[0].id
    if message_id in last_id_message:
        last_id_message.clear()
        return # Album почему-то иногда получает ивент дважды на одно сообщение.
    last_id_message.append(id)

    caption = await check_caption(caption)

    gd_print(f"Получили альбом из {len(event)} сообщений.")

    for group_message in event.messages: # Да, spoiler для альбомов в теории можно реализовать, однако сделать это не так просто, как кажется. Плюсом занимало бы много времени на обработку.
        if group_message.photo:
            media.append(await client.download_media(group_message, f"temp_pics/{group_message.id}.png"))
        elif group_message.video:
            media.append(await client.download_media(group_message, f"temp_pics/{group_message.id}.mp4"))
        elif group_message.document:
            file_name = next((x.file_name for x in group_message.document.attributes if isinstance(x, DocumentAttributeFilename)), None)
            media.append(await client.download_media(group_message, f"temp_pics/{file_name}"))
            force_document = True
        else:
            return bd_print("Неизвестный тип сообщения")

    await client.send_file(target_channel.get('target_channel_id'), media, caption=caption, force_document=force_document)
    gd_print(f"Скопировали и успешно отправили альбом из {len(event)} сообщений.")

    for file in media:
        os.remove(file) # использование временной папки оказалось самым удобным способом.




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
