from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import logging

# ---------- تنظیمات ----------
TOKEN = "8974576730:AAGGO8ODO70RZMug94CE0MKwhtpL378MGmQ" # از @BotFather
GROUP_ID = -1003921357983  # آیدی گروه
YOUR_ID = 8893315184  # آیدی خودت

# ---------- دیکشنری ذخیره ریکشن‌ها ----------
user_reactions = {}  # {user_id: "emoji"}

# ---------- متن‌های قابل تنظیم ----------
TEXT_REPLY_FIRST = "⚠️ ابتدا روی فرد مورد نظر ریپلای کن ارباب!"
TEXT_SELECT_REACTION = "🎯 لطفاً ریکت مورد نظر رو انتخاب کن شاه:"
TEXT_REACTION_SET = "✅ ریکشن {emoji} برای کاربر تنظیم شد!"
TEXT_REACTION_REMOVED = "❌ ریکشن برای کاربر حذف شد!"
TEXT_ALL_REACTIONS_REMOVED = "🗑️ همه ریکشن‌ها حذف شدند!"
TEXT_CANCELLED = "❌ عملیات لغو شد!"
TEXT_START = """
🤖 **سگ درگاه شاهمیر**

📌 **دستورات:**
• `/set` + ریپلای روی کاربر → تنظیم ریکشن
• `/remove` + ریپلای روی کاربر → حذف ریکشن
• `/removeall` → حذف همه ریکشن‌ها

💡 روی پیام‌های خودت و دیگران کار میکنه!
"""

logging.basicConfig(level=logging.INFO)

# ---------- لیست ریکشن‌ها ----------
def get_reactions():
    return ["👍", "❤️", "🔥", "🤣", "😁", "👏", "🎉", "💯", "🥰", "🤔"]

# ---------- ساخت دکمه‌ها ----------
def create_reaction_buttons():
    buttons = []
    row = []
    for emoji in get_reactions():
        row.append(InlineKeyboardButton(emoji, callback_data=f"react_{emoji}"))
        if len(row) == 5:
            buttons.append(row.copy())
            row.clear()
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("❌ انصراف", callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)

# ---------- تنظیم ریکشن ----------
async def set_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # فقط خودت مجازی
    if user_id != YOUR_ID:
        await update.message.reply_text("🚫 تو کیرمی فقط حرف ارباب اصلی!")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text(TEXT_REPLY_FIRST)
        return
    
    target_user_id = update.message.reply_to_message.from_user.id
    
    if target_user_id == context.bot.id:
        await update.message.reply_text("⚠️ کصمیخ رو خودم نمیتونم ریکت بزنم!")
        return
    
    # ذخیره موقت
    context.user_data['target_user'] = target_user_id
    
    # ارسال دکمه‌ها
    await update.message.reply_text(
        TEXT_SELECT_REACTION,
        reply_markup=create_reaction_buttons()
    )

# ---------- حذف ریکشن انفرادی ----------
async def remove_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != YOUR_ID:
        await update.message.reply_text("🚫 شما اجازه این کار رو ندارید!")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text(TEXT_REPLY_FIRST)
        return
    
    target_user_id = update.message.reply_to_message.from_user.id
    
    if target_user_id in user_reactions:
        del user_reactions[target_user_id]
        await update.message.reply_text(TEXT_REACTION_REMOVED)
    else:
        await update.message.reply_text("ℹ️ این کاربر ریکشنی تنظیم شده ندارد!")

# ---------- حذف همه ریکشن‌ها ----------
async def remove_all_reactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != YOUR_ID:
        await update.message.reply_text("🚫 شما اجازه این کار رو ندارید!")
        return
    
    user_reactions.clear()
    await update.message.reply_text(TEXT_ALL_REACTIONS_REMOVED)

# ---------- کالبک دکمه‌ها ----------
async def reaction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id != YOUR_ID:
        await query.answer("❌ شما اجازه ندارید!", show_alert=True)
        return
    
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text(TEXT_CANCELLED)
        return
    
    emoji = query.data.replace("react_", "")
    target_user_id = context.user_data.get('target_user')
    
    if not target_user_id:
        await query.edit_message_text("❌ خطا! دوباره تلاش کن.")
        return
    
    user_reactions[target_user_id] = emoji
    await query.edit_message_text(
        TEXT_REACTION_SET.format(emoji=emoji)
    )
    
    context.user_data['target_user'] = None

# ---------- ریکشن خودکار (روی همه از جمله خودت) ----------
async def auto_react(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # فقط تو گروه مورد نظر
    if update.effective_chat.id != GROUP_ID:
        return
    
    # اگه پیام از خود ربات بود، نادیده بگیر
    if update.effective_user.id == context.bot.id:
        return
    
    # اگه کاربر توی دیکشنری هست (شامل خودت هم میشه)
    if update.effective_user.id in user_reactions:
        emoji = user_reactions[update.effective_user.id]
        try:
            await context.bot.set_message_reaction(
                chat_id=update.effective_chat.id,
                message_id=update.effective_message.message_id,
                reaction=emoji
            )
            print(f"✅ ریکشن {emoji} به پیام از {update.effective_user.id} زده شد!")
        except Exception as e:
            print(f"❌ خطا: {e}")

# ---------- استارت ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != YOUR_ID:
        await update.message.reply_text("🚫 شما اجازه ندارید!")
        return
    
    await update.message.reply_text(TEXT_START)

# ---------- اجرا ----------
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_reaction))
    app.add_handler(CommandHandler("remove", remove_reaction))
    app.add_handler(CommandHandler("removeall", remove_all_reactions))
    app.add_handler(CallbackQueryHandler(reaction_callback))
    app.add_handler(MessageHandler(filters.ALL & filters.Chat(GROUP_ID), auto_react))
    
    print("🤖 ربات روشن شد...")
    print(f"📍 گروه: {GROUP_ID}")
    print("📌 دستورات:")
    print("  /set + ریپلای → تنظیم ریکشن")
    print("  /remove + ریپلای → حذف ریکشن")
    print("  /removeall → حذف همه")
    print("✅ ریکشن روی خودت هم کار میکنه!")
    app.run_polling()

if __name__ == "__main__":
    main()