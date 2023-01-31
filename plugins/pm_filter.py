import random
import asyncio
import re
import ast
import math
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import ADMINS, SUPPORT_CHAT, \
    MANUAL_FILTER
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid, ChatAdminRequired
from utils import is_subscribed, temp, get_settings, save_group_settings
from database.users_chats_db import db
from database.filters_mdb import (
    del_all,
    find_filter,
    get_filters,
)
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


@Client.on_message(filters.group & filters.text & filters.incoming)
async def give_filter(client, message):
    settings = await get_settings(message.chat.id)
    if settings["manual_filter"]:
        await manual_filters(client, message)
    else:
        k = await message.reply_text('Manual Filter Off! ❌')
        await asyncio.sleep(5)
        await k.delete()
        try:
            await message.delete()
        except:
            pass


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        try:
            user = query.message.reply_to_message.from_user.id
            if int(user) != 0 and query.from_user.id != int(user):
                return await query.answer(f"Hello {query.from_user.first_name},\nThis Is Not For You!", show_alert=True)
            await query.answer("Closed!")
            await query.message.delete()
            try:
                await query.message.reply_to_message.delete()
            except:
                pass
        except:
            await query.answer("Closed!")
            await query.message.delete()
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure i'm present in your group!", quote=True)
                    return
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups",
                    quote=True
                )
                return

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.ADMINISTRATOR) or (st.status == enums.ChatMemberStatus.OWNER):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("This Is Not For You!", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.ADMINISTRATOR) or (st.status == enums.ChatMemberStatus.OWNER):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("This Is Not For You!", show_alert=True)
    elif "groupcb" in query.data:

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name: **{title}**\nGroup ID: `{group_id}`",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return
    elif "connectcb" in query.data:

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connected to **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text('Some error occurred!', parse_mode=enums.ParseMode.MARKDOWN)
        return
    elif "disconnect" in query.data:

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Disconnected from **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return
    elif "deletecb" in query.data:

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return
    elif query.data == "backcb":

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections! Connect to some groups first.",
            )
            return
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details:\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)

    elif query.data == "start":
        await query.answer('Welcome!')
        buttons = [[
            InlineKeyboardButton("➕ Add Me To Your Group ➕", url=SUPPORT_CHAT)
        ],[
            InlineKeyboardButton('❓ Help ❓', callback_data='help')
        ],[
            InlineKeyboardButton('👑 My Owner 👑', callback_data='my_owner'),
            InlineKeyboardButton('ℹ️ My About ℹ️', callback_data='my_about')
        ],[
            InlineKeyboardButton('❌ Close ❌', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "my_about":
        buttons = [[
            InlineKeyboardButton('🏠 Home 🏠', callback_data='start'),
            InlineKeyboardButton('Report Bugs and Feedback', url='https://t.me/SL_Filters_Bot_Support')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.MY_ABOUT_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True
        )
    elif query.data == "my_owner":
        buttons = [[
            InlineKeyboardButton('🏠 Home 🏠', callback_data='start'),
            InlineKeyboardButton('Contact', url='https://t.me/Hansaka_Anuhas')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.MY_OWNER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('Manual Filter', callback_data='manual_filter'),
            InlineKeyboardButton('Connections', callback_data='connections')
        ],[
            InlineKeyboardButton('🏠 Home 🏠', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text='Help',
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "manual_filter":
        buttons = [[
            InlineKeyboardButton('◀️ Back', callback_data='help'),
            InlineKeyboardButton('Buttons', callback_data='buttons')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.MANUAL_FILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "connections":
        buttons = [[
            InlineKeyboardButton('◀️ Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CONNECTIONS_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "buttons":
        buttons = [[
            InlineKeyboardButton('◀️ Back', callback_data='manual_filter')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.BUTTONS_TXT.format(temp.U_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        
    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))
        userid = query.from_user.id if query.from_user else None
        st = await client.get_chat_member(grp_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            await query.answer("This Is Not For You!", show_alert=True)
            return

        if str(grp_id) != str(grpid):
            await query.message.edit("I'm not connected to this group! Check /connections or /connect to this group.")
            return

        if status == "True":
            await save_group_settings(grpid, set_type, False)
        else:
            await save_group_settings(grpid, set_type, True)

        settings = await get_settings(grpid)

        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('Manual Filter',
                                         callback_data=f'setgs#manual_filter#{settings["manual_filter"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ On' if settings["manual_filter"] else '❌ Off',
                                         callback_data=f'setgs#manual_filter#{settings["manual_filter"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('❌ Close ❌', callback_data='close_data')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.answer("Changed!")
            await query.message.edit_reply_markup(reply_markup)


async def manual_filters(client, message, text=False):
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                reply_to_message_id=reply_id)
                        else:
                            button = eval(btn)
                            await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                    elif btn == "[]":
                        await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                    else:
                        button = eval(btn)
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
