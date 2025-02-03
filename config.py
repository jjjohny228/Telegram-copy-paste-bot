class Config:
    CHANNELS = [{'source_channel_id': -1001779418608,
                 'source_channel_signature': '<strong>\n</strong>🎬<a href="https://t.me/kino_redakciya">Киноредакция</a>',
                 'source_channel_name': 'Киноредакция',
                 'target_channel_id': -1002327107376,
                 'target_channel_signature': '\nКинокопия 🙈'},
                {'source_channel_id': -1001564859362,
                 'source_channel_signature': '<strong>\n🐈‍⬛ </strong><a href="https://t.me/kinokityk/"><strong>Кінокітик</strong></a>',
                 'source_channel_name': 'Кинокот',
                 'target_channel_id': -1002336863781,
                 'target_channel_signature': '\nКинокопия 🙈'},
                {'source_channel_id': -1002326888427,
                 'source_channel_signature': '<strong>\n🐈‍⬛ </strong><a href="https://t.me/kinokityk/"><strong>Кінокітик</strong></a>',
                 'source_channel_name': 'Кинокот',
                 'target_channel_id': -1002336863781,
                 'target_channel_signature': '\nКинокопия 🙈'}
                ]

    AUTO_DELETE_LINKS = False  # Удаление ссылок в описании (True - удалять ссылку вместе с её текстом, если таковая имеется, False - ничего не делать со ссылками, None - удалять только ссылку, оставляя её текст, str - заменить ссылку на указанную ссылку(например, "AUTO_DELETE_LINKS = "https://t.me/your_channel""))
    FORWARDS = None  # True - обрабатывать только пересланные сообщения, False - не обрабатывать пересланные сообщения, None - обрабатывать все сообщения.
    BAN_WARDS = ('реклама', 'розіграш',)