import os
import asyncio
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant

from config import API_ID, API_HASH, BOT_TOKEN, FORCE_MSG, START_MSG, ADMINS, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON, PROTECT_CONTENT
from database.database import add_user, del_user, full_userbase, present_user
from helper_func import encode, decode, get_messages

# ✅ Replace with your actual Telegram channel usernames (WITHOUT @)
CHANNEL_1 = "attack_on_titan_tamildub1"
CHANNEL_2 = "solo_levelingseason2_t"

# Initialize Bot
Bot = Client("FileStoreBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def is_subscribed(client, user_id):
    try:
        await client.get_chat_member(CHANNEL_1, user_id)
        await client.get_chat_member(CHANNEL_2, user_id)
        return True
    except UserNotParticipant:
        return False

@Bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id

    # Check if user is subscribed to both channels
    if not await is_subscribed(client, user_id):
        buttons = [
            [InlineKeyboardButton("⚡ Join Channel 1", url=f"https://t.me/{CHANNEL_1}")],
            [InlineKeyboardButton("⚡ Join Channel 2", url=f"https://t.me/{CHANNEL_2}")],
            [InlineKeyboardButton("✅ I Joined", callback_data="checksub")]
        ]
        await message.reply_text(
            text=FORCE_MSG,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
        return

    # Add user to database if not already present
    if not await present_user(user_id):
        await add_user(user_id)

    # Handle file access if user starts with a file ID
    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
            string = await decode(base64_string)
            file_ids = [int(x) for x in string.split("-")[1:]]
        except:
            return
        
        temp_msg = await message.reply("📥 Retrieving file... Please wait.")
        try:
            messages = await get_messages(client, file_ids)
        except:
            await message.reply_text("❌ Error: Could not retrieve the file.")
            return
        await temp_msg.delete()

        for msg in messages:
            caption = CUSTOM_CAPTION.format(filename=msg.document.file_name) if msg.document else msg.caption
            reply_markup = None if DISABLE_CHANNEL_BUTTON else msg.reply_markup

            try:
                await msg.copy(
                    chat_id=user_id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
                await asyncio.sleep(0.5)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await msg.copy(chat_id=user_id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            except:
                pass
    else:
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("😊 About Me", callback_data="about"),
             InlineKeyboardButton("🔒 Close", callback_data="close")]
        ])
        await message.reply_text(
            text=START_MSG.format(first=message.from_user.first_name),
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

@Bot.on_callback_query(filters.regex("checksub"))
async def check_subscription(client: Client, query: CallbackQuery):
    user_id = query.from_user.id

    # Recheck subscription
    if await is_subscribed(client, user_id):
        await query.message.edit_text("✅ You have successfully joined the required channels. Enjoy!")
    else:
        await query.answer("❌ You haven't joined both channels yet. Please join and try again.", show_alert=True)

# Start bot
Bot.run()
