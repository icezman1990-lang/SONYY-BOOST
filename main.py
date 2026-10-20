import telebot
from telebot import types
import requests

# ---------------- CONFIG ----------------
BOT_TOKEN = "8881370310:AAEO41P1VCBbgsPzfHwOTsjM1yBgqNHzBdI"
API_KEY = "932685347700b63e7411f4b32d44b399"
API_URL = "https://bulkfollows.com/api/v2"
SERVICE_ID = 9878
ADMIN_USER_ID = 8498478182
# ----------------------------------------

bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}

def call_smm(action, data=None):
    payload = {'key': API_KEY, 'action': action}
    if data:
        payload.update(data)
    try:
        res = requests.post(API_URL, data=payload, timeout=20)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def get_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_order = types.InlineKeyboardButton("Order Bot Start", callback_data="order")
    btn_bal = types.InlineKeyboardButton("Check Balance", callback_data="bal")
    btn_status = types.InlineKeyboardButton("Check Status", callback_data="status")
    markup.add(btn_order)
    markup.add(btn_bal, btn_status)
    return markup

@bot.message_handler(commands=['start'])
def start_handler(message):
    if message.from_user.id != ADMIN_USER_ID:
        bot.reply_to(message, "Access Denied.")
        return
    bot.send_message(
        message.chat.id,
        "BulkFollows Service (ID: 9878)\n\nSelect an option:",
        reply_markup=get_menu()
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.from_user.id != ADMIN_USER_ID:
        return

    if call.data == "bal":
        res = call_smm("balance")
        bal = res.get("balance", "N/A")
        cur = res.get("currency", "USD")
        bot.send_message(call.message.chat.id, f"Balance: {bal} {cur}")
        bot.answer_callback_query(call.id)

    elif call.data == "order":
        user_states[call.from_user.id] = "LINK"
        bot.send_message(
            call.message.chat.id,
            "Send Target Link:\nExample: https://t.me/mybot?start=ref123"
        )
        bot.answer_callback_query(call.id)

    elif call.data == "status":
        user_states[call.from_user.id] = "STATUS"
        bot.send_message(call.message.chat.id, "Send Order ID:")
        bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: True)
def message_handler(message):
    if message.from_user.id != ADMIN_USER_ID:
        return

    state = user_states.get(message.from_user.id)

    if state == "LINK":
        user_states[f"{message.from_user.id}_link"] = message.text.strip()
        user_states[message.from_user.id] = "QTY"
        bot.send_message(message.chat.id, "Enter Quantity (e.g. 100):")

    elif state == "QTY":
        qty = message.text.strip()
        if not qty.isdigit():
            bot.send_message(message.chat.id, "Please enter numbers only.")
            return

        target_link = user_states.get(f"{message.from_user.id}_link")
        data = {
            'service': SERVICE_ID,
            'link': target_link,
            'quantity': int(qty)
        }
        res = call_smm("add", data)

        if "order" in res:
            bot.send_message(
                message.chat.id,
                f"Order Success!\n\nOrder ID: {res['order']}\nLink: {target_link}\nQty: {qty}",
                reply_markup=get_menu()
            )
        else:
            bot.send_message(
                message.chat.id,
                f"Order Failed: {res.get('error', 'Unknown Error')}",
                reply_markup=get_menu()
            )
        user_states.pop(message.from_user.id, None)

    elif state == "STATUS":
        order_id = message.text.strip()
        res = call_smm("status", {'order': order_id})
        if "status" in res:
            bot.send_message(
                message.chat.id,
                f"Order #{order_id}\n\nStatus: {res.get('status')}\nCharge: ${res.get('charge', '0')}\nRemains: {res.get('remains', '0')}",
                reply_markup=get_menu()
            )
        else:
            bot.send_message(message.chat.id, f"Check Failed: {res.get('error')}", reply_markup=get_menu())
        user_states.pop(message.from_user.id, None)

bot.infinity_polling()
