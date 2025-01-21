import json
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Load or initialize data
ASSIGNMENTS_FILE = "assignments.json"
INCOMPLETE_FILE = "incomplete_tasks.json"
ADMIN_ID = "123456789"  # Replace with the admin's Telegram ID

def load_json(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_json(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

# Command: /add <user> <room_number> (Admin only)
def add_user(update: Update, context: CallbackContext):
    if str(update.effective_user.id) != ADMIN_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return

    if len(context.args) != 2:
        update.message.reply_text("Usage: /add <user> <room_number>")
        return

    user, room = context.args
    assignments = load_json(ASSIGNMENTS_FILE)
    assignments[user] = room
    save_json(ASSIGNMENTS_FILE, assignments)

    update.message.reply_text(f"Assigned {user} to {room}.")

# Notify users of their assignments every Monday
def notify_users(context: CallbackContext):
    week_number = datetime.now().isocalendar()[1]
    assignments = load_json(ASSIGNMENTS_FILE)

    for user, room in assignments.items():
        context.bot.send_message(
            chat_id=user,
            text=f"Week {week_number}: Your assigned room is {room}. Please complete your tasks."
        )

# Command: /done (User marks task as complete)
def mark_done(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    assignments = load_json(ASSIGNMENTS_FILE)

    if user_id not in assignments:
        update.message.reply_text("You do not have any assigned tasks.")
        return

    incomplete_tasks = load_json(INCOMPLETE_FILE)
    if user_id in incomplete_tasks:
        del incomplete_tasks[user_id]
        save_json(INCOMPLETE_FILE, incomplete_tasks)

    update.message.reply_text("Task marked as complete. Thank you!")

# Command: /incomplete (Admin-only)
def list_incomplete(update: Update, context: CallbackContext):
    if str(update.effective_user.id) != ADMIN_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return

    incomplete_tasks = load_json(INCOMPLETE_FILE)
    if not incomplete_tasks:
        update.message.reply_text("No users with incomplete tasks.")
    else:
        response = "Users with incomplete tasks:\n" + "\n".join(
            [f"User: {user}, Room: {room}" for user, room in incomplete_tasks.items()]
        )
        update.message.reply_text(response)

# Check incomplete tasks at the start of each week
def check_incomplete(context: CallbackContext):
    assignments = load_json(ASSIGNMENTS_FILE)
    incomplete_tasks = load_json(INCOMPLETE_FILE)

    for user, room in assignments.items():
        if user not in incomplete_tasks:
            incomplete_tasks[user] = room

    save_json(INCOMPLETE_FILE, incomplete_tasks)

# Main function to set up the bot
def main():
    updater = Updater("YOUR_TELEGRAM_BOT_TOKEN")
    job_queue = updater.job_queue

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("add", add_user))
    dispatcher.add_handler(CommandHandler("done", mark_done))
    dispatcher.add_handler(CommandHandler("incomplete", list_incomplete))

    # Schedule weekly notifications and checks
    job_queue.run_daily(notify_users, time=datetime.time(9, 0))  # Notify at 9:00 AM every day
    job_queue.run_daily(check_incomplete, time=datetime.time(0, 0))  # Check incomplete tasks at midnight

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
