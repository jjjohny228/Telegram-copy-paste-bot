class Config:
    CHANNELS = [{'source_channel_id': 121,
                 'source_channel_signature': 'some_signature',
                 'source_channel_name': 'Channel name',
                 'target_channel_id': 123,
                 'target_channel_signature': 'target_signature'},
                ]

    AUTO_DELETE_LINKS = False  # Удаление ссылок в описании (True - удалять ссылку вместе с её текстом, если таковая имеется, False - ничего не делать со ссылками, None - удалять только ссылку, оставляя её текст, str - заменить ссылку на указанную ссылку(например, "AUTO_DELETE_LINKS = "https://t.me/your_channel""))
    FORWARDS = None  # True - обрабатывать только пересланные сообщения, False - не обрабатывать пересланные сообщения, None - обрабатывать все сообщения.
    BAN_WARDS = ('реклама', 'розіграш',)