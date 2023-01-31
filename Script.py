class script(object):
    START_TXT = """👋 Hello {},

I'm an advanced manual filter bot. 🤩

All you have to do is add me to a group and give me admin. 😌

I will take care of the rest. 😎"""

    MY_ABOUT_TXT = """★ Server: <a href=https://www.heroku.com>Heroku</a>
★ Database: <a href=https://www.mongodb.com>MongoDB</a>
★ Language: <a href=https://www.python.org>Python</a>
★ Library: <a href=https://pyrogram.org>Pyrogram</a>"""

    MY_OWNER_TXT = """★ Name: Hansaka Anuhas
★ Username: @Hansaka_Anuhas
★ ID: <code>5493832202</code>
★ Country: Sri Lanka 🇱🇰"""

    STATUS_TXT = """★ Total Users: <code>{}</code>
★ Total Groups: <code>{}</code>"""

    MANUAL_FILTER_TXT = """• /filter or /add - Add filter
• /filters or /viewfilters - List all filters
• /del - Delete filter
• /delall - Delete all filters"""
    
    CONNECTIONS_TXT = """• /connect - Connect PM
• /disconnect - Disconnect PM
• /connections - List all connections"""
    
    BUTTONS_TXT = """<b>URL Buttons:</b>
<code>[Button Text](buttonurl:https://t.me/{})</code>

<b>Alert Buttons:</b>
<code>[Button Text](buttonalert:Alert Message)</code>"""
    
    NEW_GROUP_TXT = """#NewGroup
★ Title: {}
★ ID: <code>{}</code>
★ Total Members: {}
★ Added by: {}"""

    NEW_USER_TXT = """#NewUser
★ Name: {}
★ ID: <code>{}</code>"""
