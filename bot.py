import sqlite3
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ChatJoinRequestHandler, filters, ContextTypes

TOKEN = "8691445919:AAFe4oAVsaugRQ80hCgsYpNUQVkPddm5SXM"
ADMIN_ID = 8446411026

# DATABASE
db = sqlite3.connect("bot.db")
cursor = db.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,name TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT)")
db.commit()


# DATABASE FUNCTIONS

def add_user(user):
    cursor.execute("INSERT OR IGNORE INTO users VALUES(?,?)",(user.id,user.full_name))
    db.commit()

def get_users():
    cursor.execute("SELECT user_id FROM users")
    return [x[0] for x in cursor.fetchall()]

def total_users():
    cursor.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0]

def set_setting(k,v):
    cursor.execute("INSERT OR REPLACE INTO settings VALUES(?,?)",(k,v))
    db.commit()

def get_setting(k):
    cursor.execute("SELECT value FROM settings WHERE key=?",(k,))
    r=cursor.fetchone()
    return r[0] if r else None


# START

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    add_user(user)

    # ADMIN ALERT
    try:
        await context.bot.send_message(
            ADMIN_ID,
            f"🔔 New User Found\n\n"
            f"👤 Name : {user.full_name}\n"
            f"🆔 ID : {user.id}\n"
            f"📊 Total Users : {total_users()}"
        )
    except:
        pass

    await update.message.reply_text("👋 Bot Active")


# ADMIN PANEL

async def admin(update:Update,context):

    if update.effective_user.id!=ADMIN_ID:
        return

    keyboard=[
        [
            InlineKeyboardButton("🟢 Approve System",callback_data="approve"),
            InlineKeyboardButton("📢 Broadcast",callback_data="broadcast")
        ],
        [
            InlineKeyboardButton("👋 Set Greeting",callback_data="setgreet"),
            InlineKeyboardButton("👀 Preview Greeting",callback_data="preview")
        ],
        [
            InlineKeyboardButton("📊 Stats",callback_data="stats")
        ]
    ]

    await update.message.reply_text(
        "⚙️ ADMIN PANEL",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# BUTTON HANDLER

async def button(update:Update,context):

    q=update.callback_query
    await q.answer()

    if q.data=="approve":

        keyboard=[
            [
                InlineKeyboardButton("🟢 ON",callback_data="approve_on"),
                InlineKeyboardButton("🔴 OFF",callback_data="approve_off")
            ]
        ]

        await q.edit_message_text(
            "Approve System",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif q.data=="approve_on":

        set_setting("approve","on")
        await q.edit_message_text("🟢 Auto Approve Enabled")

    elif q.data=="approve_off":

        set_setting("approve","off")
        await q.edit_message_text("🔴 Auto Approve Disabled")

    elif q.data=="stats":

        await q.edit_message_text(
            f"📊 Total Users : {total_users()}"
        )

    elif q.data=="broadcast":

        await q.message.reply_text("📢 Send message for broadcast")
        context.user_data["broadcast"]=True

    elif q.data=="setgreet":

        await q.message.reply_text(
            "👋 Send Greeting Message\n(Text / Photo / Video supported)"
        )
        context.user_data["setgreet"]=True

    elif q.data=="preview":

        gtype=get_setting("greet_type")
        gtext=get_setting("greet_text")
        gfile=get_setting("greet_file")
        gurl=get_setting("greet_url")

        keyboard=[[InlineKeyboardButton("🔗 Advertisement Link",url=gurl)]]

        if gtype=="photo":

            await context.bot.send_photo(
                ADMIN_ID,
                gfile,
                caption=gtext,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif gtype=="video":

            await context.bot.send_video(
                ADMIN_ID,
                gfile,
                caption=gtext,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        else:

            await context.bot.send_message(
                ADMIN_ID,
                gtext,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )


# MESSAGE HANDLER

async def messages(update:Update,context):

    user=update.effective_user
    add_user(user)

    msg=update.message

    # SET GREETING
    if context.user_data.get("setgreet"):

        if msg.photo:

            set_setting("greet_type","photo")
            set_setting("greet_file",msg.photo[-1].file_id)
            set_setting("greet_text",msg.caption)

        elif msg.video:

            set_setting("greet_type","video")
            set_setting("greet_file",msg.video.file_id)
            set_setting("greet_text",msg.caption)

        else:

            set_setting("greet_type","text")
            set_setting("greet_text",msg.text)

        await msg.reply_text("🔗 Now Send Advertisement URL")

        context.user_data["seturl"]=True
        context.user_data["setgreet"]=False
        return


    # SET URL
    if context.user_data.get("seturl"):

        set_setting("greet_url",msg.text)

        await msg.reply_text("✅ Greeting Saved")

        context.user_data["seturl"]=False
        return


    # BROADCAST
    if context.user_data.get("broadcast") and user.id==ADMIN_ID:

        users=get_users()

        sent=0
        failed=0

        progress=await msg.reply_text("📡 Broadcasting...")

        for uid in users:

            try:
                await context.bot.copy_message(
                    uid,
                    msg.chat.id,
                    msg.message_id
                )
                sent+=1

            except:
                failed+=1

            if sent%50==0:

                await progress.edit_text(
                    f"📢 Broadcast Progress\n\n"
                    f"Sent : {sent}\n"
                    f"Failed : {failed}"
                )

                await asyncio.sleep(0.05)

        await progress.edit_text(
            f"✅ Broadcast Done\n\n"
            f"Sent : {sent}\n"
            f"Failed : {failed}"
        )

        context.user_data["broadcast"]=False


# JOIN REQUEST

async def join(update:Update,context):

    user=update.chat_join_request.from_user
    add_user(user)

    # ADMIN ALERT
    try:
        await context.bot.send_message(
            ADMIN_ID,
            f"🔔 New User Found (Join Request)\n\n"
            f"👤 Name : {user.full_name}\n"
            f"🆔 ID : {user.id}\n"
            f"📊 Total Users : {total_users()}"
        )
    except:
        pass


    approve=get_setting("approve")

    if approve=="on":

        await context.bot.approve_chat_join_request(
            update.chat_join_request.chat.id,
            user.id
        )


    gtype=get_setting("greet_type")
    gtext=get_setting("greet_text")
    gfile=get_setting("greet_file")
    gurl=get_setting("greet_url")

    keyboard=[[InlineKeyboardButton("🔗 Advertisement Link",url=gurl)]]

    try:

        if gtype=="photo":

            await context.bot.send_photo(
                user.id,
                gfile,
                caption=gtext,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif gtype=="video":

            await context.bot.send_video(
                user.id,
                gfile,
                caption=gtext,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        else:

            await context.bot.send_message(
                user.id,
                gtext,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    except:
        pass


# MAIN

def main():

    app=Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("admin",admin))

    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.ALL,messages))
    app.add_handler(ChatJoinRequestHandler(join))

    print("Bot Running...")

    app.run_polling()

if __name__ == "__main__":
    main()
