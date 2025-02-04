from telethon.events import NewMessage, Album


async def text_contain_banword(text: str, ban_words_list: list) -> bool:
    return any(word.lower() in text.lower() for word in ban_words_list)


async def change_channel_signature(text: str, source_channel_signature: str, target_channel_signature: str) -> str:
    new_text = text
    if target_channel_signature:
        if source_channel_signature:
            if source_channel_signature in text:
                new_text = text.replace(source_channel_signature, target_channel_signature)
        elif not source_channel_signature or source_channel_signature not in text:
            new_text += '\n\ntarget_channel_signature'
    else:
        if source_channel_signature in text:
            new_text = text.replace(source_channel_signature, '')
    return new_text

async def find_target_channel_for_single_message(event, all_channels: list) -> dict:
    source_channel_id = await channel_id_from_event(event)
    for channel in all_channels:
        if source_channel_id == channel['source_channel_id']:
            return channel

    raise ValueError('Channel not found')


async def find_target_channel_for_album(channel_id: int, all_channels: list) -> dict:
    source_channel_id = -1000000000000 - channel_id
    for channel in all_channels:
        if source_channel_id == channel['source_channel_id']:
            return channel

    raise ValueError('Channel not found')


async def channel_id_from_event(event):
    channel_id = int(event.message.peer_id.channel_id)
    if not channel_id:
        raise ValueError('Channel not found')
    converted_id = -1000000000000 - channel_id  # или
    # converted_id = -1002000000000 - channel_id  # для некоторых каналов
    return converted_id
