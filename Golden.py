import telebot
import random
import re
import time
import threading
from flask import Flask

# Flask setup for Render
app = Flask('')
@app.route('/')
def home(): return "Bot is alive!"
def run_flask(): app.run(host='0.0.0.0', port=8080)

# --- Bot Configuration ---
API_TOKEN = '8784926429:AAEr77qoSzhNC9uos9277nrxOOHcthMzN-0'
OWNER_ID = 6738268096
GROUP_CHAT_ID = "@EarnMaster009"

bot = telebot.TeleBot(API_TOKEN)

# Data Storage
user_data = {'demos': {}}
# ১০টি লুপের জন্য কন্ট্রোল ইভেন্ট
loop_controls = {i: threading.Event() for i in range(1, 11)}

def get_seconds(delay_input):
    unit = delay_input[-1].upper()
    value = int(re.search(r'\d+', delay_input).group())
    return value * 60 if unit == 'M' else value

def smart_z_replace(text):
    lines = text.split('\n')
    processed_lines = []
    for line in lines:
        if "Country" in line or "Service" in line:
            processed_lines.append(line)
        else:
            processed_line = re.sub(r'z+', lambda m: ''.join([str(random.randint(0, 9)) for _ in range(len(m.group(0)))]), line, flags=re.IGNORECASE)
            processed_lines.append(processed_line)
    
    final_output = [f"**{p[0].strip()}:** `{p[1].strip()}`" if ':' in l and (p := l.split(':', 1)) else f"**{l}**" for l in processed_lines]
    return "\n".join(final_output)

# --- Keyboard Generator (Updated for 10 Loops) ---
def get_admin_markup():
    markup = telebot.types.InlineKeyboardMarkup()
    for i in range(1, 11): # ১০টি লুপের রেঞ্জ
        if loop_controls[i].is_set(): status = "🟢"
        elif i in user_data['demos']: status = "🟡"
        else: status = "⚪"
        
        btn_setup = telebot.types.InlineKeyboardButton(f"🛠️ L-{i} {status}", callback_data=f"setup_{i}")
        btn_del = telebot.types.InlineKeyboardButton(f"❌", callback_data=f"del_{i}")
        markup.row(btn_setup, btn_del)
    
    markup.add(telebot.types.InlineKeyboardButton("🚀 START ALL PROCESS", callback_data="start_all"))
    markup.add(telebot.types.InlineKeyboardButton("🛑 STOP ALL", callback_data="stop_all"))
    return markup

@bot.message_handler(commands=['start_demo'])
def admin_panel(message):
    if message.from_user.id != OWNER_ID: return
    bot.send_message(message.chat.id, "⚙️ **Admin Control Panel**", reply_markup=get_admin_markup(), parse_mode="Markdown")

@bot.message_handler(commands=['start_view'])
def view_status(message):
    if message.from_user.id != OWNER_ID: return
    if not user_data['demos']:
        bot.reply_to(message, "কোনো লুপ সেট করা নেই।")
        return
    
    status_text = "📊 **Bot Live Status**\n\n"
    for i, data in user_data['demos'].items():
        remaining = data['total'] - data['sent']
        active_tag = "➡️ " if loop_controls[i].is_set() else ""
        
        status_text += f"{active_tag}**Loop {i}:**\n"
        status_text += f"⏱️ Delay: {data['delay']}s | 🔢 Total: {data['total']}\n"
        status_text += f"✅ Sent: {data['sent']} | ⏳ Remaining: {remaining}\n"
        
        demo_preview = smart_z_replace(data['text'])
        status_text += f"{demo_preview}\n\n"
        status_text += "------------------------\n"
    
    bot.send_message(message.chat.id, status_text, parse_mode="Markdown")

# --- Timing Fixed Loop Worker ---
def individual_loop_worker(loop_id):
    while loop_controls[loop_id].is_set():
        data = user_data['demos'].get(loop_id)
        if not data or data['sent'] >= data['total']:
            loop_controls[loop_id].clear()
            break
        
        # মেসেজ পাঠানোর সঠিক সময় হিসাব করা
        start_time = time.time()
        
        final_msg = smart_z_replace(data['text'])
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("Chanel 💸", url="https://t.me/EarnMaster007"),
                   telebot.types.InlineKeyboardButton("📱 Number", url="https://t.me/EarnMasterSmsbot"))
        
        try:
            bot.send_message(GROUP_CHAT_ID, final_msg, reply_markup=markup, parse_mode="Markdown")
            user_data['demos'][loop_id]['sent'] += 1
        except: pass
        
        # টাইমিং ফিক্স: প্রসেসিং টাইম বাদ দিয়ে ডিলে ক্যালকুলেট করা
        elapsed_time = time.time() - start_time
        sleep_time = max(0.1, data['delay'] - elapsed_time)
        time.sleep(sleep_time)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data.startswith("setup_"):
        loop_id = int(call.data.split("_")[1])
        msg = bot.send_message(call.message.chat.id, f"Loop {loop_id} ডেমো দিন (শেষে 1M.1000 দিন):")
        bot.register_next_step_handler(msg, save_loop_data, loop_id)
    
    elif call.data.startswith("del_"):
        loop_id = int(call.data.split("_")[1])
        loop_controls[loop_id].clear()
        if loop_id in user_data['demos']: del user_data['demos'][loop_id]
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_admin_markup())

    elif call.data == "start_all":
        started_any = False
        for lid in user_data['demos']:
            if not loop_controls[lid].is_set():
                loop_controls[lid].set()
                threading.Thread(target=individual_loop_worker, args=(lid,), daemon=True).start()
                started_any = True
        if started_any:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_admin_markup())
        else: bot.answer_callback_query(call.id, "সবগুলো অলরেডি চলছে।")

    elif call.data == "stop_all":
        for i in range(1, 11): loop_controls[i].clear()
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=get_admin_markup())
        bot.send_message(call.message.chat.id, "🛑 সব প্রসেস বন্ধ।")

def save_loop_data(message, loop_id):
    try:
        text = message.text
        last_line = text.split('\n')[-1]
        parts = last_line.split('.')
        delay_sec = get_seconds(parts[0])
        total_count = int(parts[1])
        clean_text = "\n".join(text.split('\n')[:-1])
        
        user_data['demos'][loop_id] = {'text': clean_text, 'delay': delay_sec, 'total': total_count, 'sent': 0}
        bot.send_message(message.chat.id, f"✅ Loop {loop_id} সেভ হয়েছে।")
        admin_panel(message)
    except:
        bot.send_message(message.chat.id, "❌ ফরম্যাট ভুল! শেষে `1M.1000` দিন।")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
