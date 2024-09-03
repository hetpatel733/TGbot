import telebot
import random
from telebot import types

BOT_TOKEN = "7293635884:AAEEW9OtCn6tZsH9RfJuyTv3N8SXe8Vt_fQ"
bot = telebot.TeleBot(BOT_TOKEN)

users = {}  # Stores users and their gender
chats = {}  # Stores active chats between users
searching = {}  # Tracks users who are currently searching for a partner
from datetime import datetime, timedelta

vip_dict = {}


def add_vip(username, days):
    """Add a user as VIP with a specified number of days."""
    end_date = datetime.now() + timedelta(days=days)
    vip_dict[username] = end_date
    print(f"User '{username}' added as VIP until {end_date.strftime('%Y-%m-%d')}.")


def remove_vip(username):
    """Remove a user from VIP status."""
    if username in vip_dict:
        del vip_dict[username]
        print(f"User '{username}' removed from VIP status.")
    else:
        print(f"User '{username}' is not a VIP.")


def show_vips(message):
    username = message.from_user.username
    if is_admin(username):
        if vip_dict:
            vip_list = [
                f"{user}: {end_date.strftime('%Y-%m-%d')}"
                for user, end_date in vip_dict.items()
            ]
            vip_message = "\n".join(vip_list)
            bot.send_message(message.chat.id, f"VIP List:\n{vip_message}")
        else:
            bot.send_message(message.chat.id, "No VIP members found.")
    else:
        bot.send_message(message.chat.id, "You are not authorized to use this command.")


def process_add_vip(message):
    try:
        username, days = message.text.split()
        days = int(days)
        add_vip(username, days)
        bot.send_message(
            message.chat.id, f"VIP status added for {username} for {days} days."
        )
    except ValueError:
        bot.send_message(message.chat.id, "Invalid format. Please use 'username days'.")


def process_remove_vip(message):
    username = message.text
    remove_vip(username)
    bot.send_message(message.chat.id, f"VIP status removed for {username}.")


# Function to ask the user for gender selection
def ask_for_gender(user_id, welcome_message=True):
    markup = types.InlineKeyboardMarkup()
    btn_male = types.InlineKeyboardButton("Male", callback_data="gender_male")
    btn_female = types.InlineKeyboardButton("Female", callback_data="gender_female")
    markup.add(btn_male, btn_female)
    if welcome_message:
        msg = bot.send_message(
            user_id, "Welcome! Please select your gender:", reply_markup=markup
        )
    else:
        msg = bot.send_message(
            user_id, "Please select your new gender:", reply_markup=markup
        )
    return msg.message_id


# Welcome message and gender selection
@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id not in users:
        start_message_id = ask_for_gender(user_id)  # Ask for gender selection
        users[user_id] = {
            "gender": None,
            "partner": None,
            "start_message_id": start_message_id,
            "available": False,
        }
    else:
        bot.send_message(
            user_id,
            "Welcome back! Use the /new command to find a new partner.",
        )


# Handling gender selection
@bot.callback_query_handler(func=lambda call: call.data.startswith("gender_"))
def handle_gender(call):
    user_id = call.from_user.id
    gender = "Male" if call.data == "gender_male" else "Female"

    if user_id in users and users[user_id]["gender"] is None:
        users[user_id]["gender"] = gender
        users[user_id]["available"] = True  # Mark user as available
        bot.delete_message(
            user_id, users[user_id]["start_message_id"]
        )  # Delete initial gender selection message
        bot.delete_message(
            call.message.chat.id, call.message.message_id
        )  # Delete selection message
        bot.send_message(
            user_id, "Gender selected successfully. Use /new to find a partner."
        )
        find_partner(call.message)


@bot.message_handler(commands=["new"])
def new_partner(message):
    user_id = message.from_user.id
    if user_id in searching:
        bot.reply_to(
            message,
            "You are already searching for a partner. Please wait until the search is complete or use /leave to cancel.",
        )
    elif users[user_id]["partner"] is None:  # Only find a new partner if not in chat
        users[user_id]["available"] = True  # Mark user as available
        searching[user_id] = True
        find_partner(message)


# Handling /leave command to cancel search
@bot.message_handler(commands=["leave"])
def leave_search(message):
    user_id = message.from_user.id
    if user_id in searching:
        searching.pop(user_id, None)
        bot.reply_to(
            message,
            "Search canceled. Use /new to find a new partner.",
        )
    else:
        bot.reply_to(
            message,
            "You are not currently searching for a partner.",
        )


# Handling /settings command
@bot.message_handler(commands=["settings"])
def show_settings(message):
    user_id = message.from_user.id
    markup = types.InlineKeyboardMarkup()
    btn_change_gender = types.InlineKeyboardButton(
        "Change Gender", callback_data="change_gender"
    )

    # Display the Gender Preference option for all users
    btn_gender_preference = types.InlineKeyboardButton(
        "Partner Gender Preference", callback_data="gender_preference"
    )
    markup.add(btn_change_gender, btn_gender_preference)

    btn_vip = types.InlineKeyboardButton("VIP Info", callback_data="show_vip")
    markup.add(btn_vip)

    bot.send_message(
        message.chat.id, "Settings Menu: Choose an option below:", reply_markup=markup
    )

# Handling Gender Preference Selection
@bot.callback_query_handler(func=lambda call: call.data == "gender_preference")
def handle_gender_preference(call):
    user_id = call.from_user.id
    if user_id in vip_dict:  # Check if the user is a VIP
        markup = types.InlineKeyboardMarkup()
        btn_male_preference = types.InlineKeyboardButton(
            "Male", callback_data="preference_male"
        )
        btn_female_preference = types.InlineKeyboardButton(
            "Female", callback_data="preference_female"
        )
        markup.add(btn_male_preference, btn_female_preference)
        bot.send_message(
            user_id,
            "Select your preferred gender for partnership:",
            reply_markup=markup,
        )
        bot.delete_message(call.message.chat.id, call.message.message_id)  # Optionally delete the gender preference button message
    else:
        bot.send_message(
            user_id,
            "This option is available to VIP members only. Please purchase VIP status to unlock this feature. Contact @Tirthpatel1302 for more details."
        )

# Handling Selected Gender Preference
@bot.callback_query_handler(func=lambda call: call.data.startswith("preference_"))
def handle_selected_preference(call):
    user_id = call.from_user.id
    if user_id in vip_dict:  # VIP check
        preferred_gender = "Male" if call.data == "preference_male" else "Female"
        users[user_id]["preferred_gender"] = preferred_gender
        bot.send_message(user_id, f"Gender preference set to {preferred_gender}.")
        bot.delete_message(call.message.chat.id, call.message.message_id)  # Optionally delete the preference message
    else:
        bot.send_message(user_id, "This option is only available to VIP members.")

           

@bot.callback_query_handler(
    func=lambda call: call.data in ["change_gender", "show_vip"]
)
def handle_settings_callback(call):
    user_id = call.from_user.id
    if call.data == "change_gender":
        # Remove user data and ask for gender selection again
        users[user_id]["gender"] = None  # Reset gender
        users[user_id]["available"] = False  # Reset availability
        ask_for_gender(user_id, welcome_message=False)  # Ask for gender again
    elif call.data == "show_vip":
        bot.send_message(
            call.from_user.id,
            "Make payment here: 'patelhet@fam' and send Screenshot to @Tirthpatel1302",
        )


ADMIN_USERNAME = "Tirthpatel1302"


# Function to check if the user is an admin
def is_admin(username):
    return username == ADMIN_USERNAME


# Function to handle /admin command
@bot.message_handler(commands=["admin"])
def handle_admin_command(message):
    username = message.from_user.username
    if is_admin(username):
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        btn_add_vip = types.KeyboardButton("Add VIP")
        btn_remove_vip = types.KeyboardButton("Remove VIP")
        btn_show_vip = types.KeyboardButton("Show VIP")
        markup.add(btn_add_vip, btn_remove_vip, btn_show_vip)
        bot.send_message(
            message.chat.id, "Admin Menu: Choose an option below:", reply_markup=markup
        )
    else:
        bot.send_message(message.chat.id, "You are not authorized to use this command.")


# Function to handle admin menu options
@bot.message_handler(func=lambda msg: msg.text in ["Add VIP", "Remove VIP", "Show VIP"])
def handle_admin_menu(message):
    username = message.from_user.username
    if is_admin(username):
        if message.text == "Add VIP":
            bot.send_message(
                message.chat.id,
                "Please send the username and number of days for VIP status.",
            )
            bot.register_next_step_handler(message, process_add_vip)
        elif message.text == "Remove VIP":
            bot.send_message(
                message.chat.id, "Please send the username to remove from VIP status."
            )
            bot.register_next_step_handler(message, process_remove_vip)
        elif message.text == "Show VIP":
            bot.send_message(
                message.chat.id, "Enter Anything in the messeage and press enter"
            )
            bot.register_next_step_handler(message, show_vips)


def find_partner(message):
    user_id = message.from_user.id
    user_gender_preference = users.get(user_id, {}).get("preferred_gender", None)

    potential_partners = [
        uid
        for uid, info in users.items()
        if uid != user_id
        and info["partner"] is None
        and info["available"]
        and (
            user_gender_preference is None  # No preference, accept any gender
            or info["gender"] == user_gender_preference  # Match preferred gender
        )
    ]
    if potential_partners:
        partner_id = random.choice(potential_partners)
        users[user_id]["partner"] = partner_id
        users[partner_id]["partner"] = user_id
        users[user_id]["available"] = False
        users[partner_id]["available"] = False
        chats[user_id] = partner_id
        chats[partner_id] = user_id
        searching.pop(user_id, None)
        bot.send_message(
            user_id, "Your partner has been found! You can start chatting now."
        )
        bot.send_message(
            partner_id, "Your partner has been found! You can start chatting now."
        )
    else:
        bot.reply_to(message, "Finding a partner...")


def end_chat(user_id):
    if user_id in chats:
        partner_id = chats[user_id]
        bot.send_message(user_id, "You have left the chat.")
        bot.send_message(partner_id, "Your partner has left the chat.")

        # Clear chat and mark users as unavailable until they issue the /new command
        users[user_id]["partner"] = None
        users[partner_id]["partner"] = None
        users[user_id]["available"] = False
        users[partner_id]["available"] = False
        chats.pop(user_id, None)
        chats.pop(partner_id, None)

        # Notify both users they can start a new chat
        bot.send_message(
            user_id,
            "You can start a new chat by giving the /new command.",
        )
        bot.send_message(
            partner_id,
            "You can start a new chat by giving the /new command.",
        )


@bot.message_handler(func=lambda msg: msg.from_user.id in chats.keys())
def handle_chat(message):
    user_id = message.from_user.id
    if user_id in chats:
        partner_id = chats[user_id]

        if message.text.lower() == "/end":
            end_chat(user_id)
        elif message.text.lower() == "/new":
            bot.send_message(
                user_id,
                "You must leave the current chat first by using /end.",
            )
        else:
            user_gender = users[user_id]["gender"][0].upper()
            if user_gender == "F":
                user_gender = "🙍‍♀️"
            else:
                user_gender = "🙎‍♂️"
            formatted_message = f"{user_gender}: {message.text}"
            bot.send_message(partner_id, formatted_message)


@bot.message_handler(
    func=lambda msg: msg.from_user.id in chats.keys(),
    content_types=[
        "photo",
        "audio",
        "document",
        "video",
        "video_note",
        "voice",
        "animation",
    ],
)
def handle_media(message):
    user_id = message.from_user.id
    if user_id in chats:
        partner_id = chats[user_id]
        media_type = message.content_type

        # Send the media message directly to the partner
        if media_type == "photo":
            bot.send_photo(partner_id, message.photo[-1].file_id)
        elif media_type == "audio":
            bot.send_audio(partner_id, message.audio.file_id)
        elif media_type == "document":
            bot.send_document(partner_id, message.document.file_id)
        elif media_type == "video":
            bot.send_video(partner_id, message.video.file_id)
        elif media_type == "video_note":
            bot.send_video_note(partner_id, message.video_note.file_id)
        elif media_type == "voice":
            bot.send_voice(partner_id, message.voice.file_id)
        elif media_type == "animation":
            bot.send_animation(partner_id, message.animation.file_id)


@bot.message_handler(
    func=lambda msg: not (
        msg.text.lower() in ["/end", "/new", "/end", "/settings"]
        or msg.from_user.id in chats.keys()
    )
)
def handle_wrong_command(message):
    bot.reply_to(
        message,
        "Invalid command. Use /new to start a new chat or /end to end the current chat.",
    )


bot.infinity_polling()
