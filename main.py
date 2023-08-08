from flask import Flask, render_template, request
from telegram import Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import sqlite3
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


# Telegram Bot token
bot_token = os.getenv("BOT_TOKEN")
bot = Bot(token=bot_token)

# Flask app setup
app = Flask(__name__)
updater = None

# SQLite database setup
def get_db_cursor():
    conn = sqlite3.connect('users.db')
    return conn, conn.cursor()

# Telegram Bot commands
def start_command(update, context):
    update.message.reply_text("Hello! Welcome to the Telegram Bot. Type /help for available commands.")


def help_command(update, context):
    update.message.reply_text("""Available Commands:
    /register - Register yourself
    /contact_us - Contact us for any query
    /services - To enquire about our services""")


def reg_process(update, context):
    update.message.reply_text("""Use register command to register yourself :

    register yourusername
    """)


def handle_message(update, context):
    chat_id = update.effective_chat.id
    text = update.effective_message.text

    if text.lower().startswith("register"):
        username = text.split()[1]  # Get the username after 'register' keyword

        conn, cursor = get_db_cursor()
        cursor.execute('SELECT username FROM users WHERE chat_id = ?', (chat_id,))
        result = cursor.fetchone()

        if result is not None:
            update.effective_message.reply_text(f"You're already registered with username {result[0]}")
            conn.close()
            return

        try:
            cursor.execute("INSERT INTO users VALUES (?, ?)", (username, chat_id))
            conn.commit()
            update.effective_message.reply_text(f"Registered as {username}")
        except sqlite3.IntegrityError:
            update.effective_message.reply_text(f"Username {username} is already taken")
        finally:
            conn.close()

    else:
        response = handle_response(text)
        update.message.reply_text(response)


def contact_us(update, context):
    update.message.reply_text("""You can contact us at:
    Mail - example@gmail.com
    Phone no. - 8102233445""")


def services_command(update, context):
    update.message.reply_text("Here's our website URL to reach us - www.google.com")


def send_message_command():
    conn, cursor = get_db_cursor()
    users = cursor.execute("SELECT * FROM users").fetchall()
    conn.close()

    return render_template("send_message.html", users=users)

def send_message_submit(form):
    selected_user = form.get("user")
    message = form.get("message")

    conn, cursor = get_db_cursor()

    for user in cursor.execute("SELECT * FROM users"):
        if user[0] == selected_user:
            chat_id = user[1]
            bot.send_message(chat_id=chat_id, text=message)
            return "Message sent successfully!"

    return "User not found."


# RESPONSES
def handle_response(text: str) -> str:
    # Create your own response logic
    processed: str = text.lower()

    if 'hello' in processed:
        return 'Hey there!'

    if 'hi' in processed:
        return 'Hi there!'

    if 'how are you' in processed:
        return 'I\'m good!'

    if 'nice to meet you' in processed:
        return 'Nice to meet you too!'

    return 'I don\'t understand'


# Flask web portal routes
@app.route('/')
def index():
    conn, cursor = get_db_cursor()
    users = cursor.execute("SELECT * FROM users").fetchall()
    conn.close()
    return render_template("index.html", users=users)

@app.route('/send_message', methods=['GET', 'POST'])
def send_message():
    if request.method == 'POST':
        return send_message_submit(request.form)
    else:
        return send_message_command()

def main():
    global updater
    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher

    # Register Telegram Bot commands
    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(CommandHandler('register', reg_process))
    dispatcher.add_handler(CommandHandler('contact_us', contact_us))
    dispatcher.add_handler(CommandHandler('services', services_command))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_message))

    # Start the Telegram bot
    updater.start_polling()

    # Start Flask web server
    app.run(debug=True)

if __name__ == '__main__':
    main()
