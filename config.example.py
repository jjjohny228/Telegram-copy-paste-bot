class Config:
    CHANNELS = [{'source_channel_id': 121,
                 'source_channel_signature': 'some_signature',
                 'source_channel_name': 'Channel name',
                 'target_channel_id': 123,
                 'target_channel_signature': 'target_signature'},
                ]

    AUTO_DELETE_LINKS = False  # Deleting links in description (True - delete link with its text, if any exists, False - do nothing with links, None - delete only link, leaving its text, str - replace link with specified link (for example, “AUTO_DELETE_LINKS = ”https://t.me/your_channel“”)).
    FORWARDS = None  # True - process only forwarded messages, False - do not process forwarded messages, None - process all messages.
    BAN_WARDS = ('реклама', 'розіграш',)