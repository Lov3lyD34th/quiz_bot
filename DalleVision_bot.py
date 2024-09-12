import re
from typing import Optional, Tuple
from telegram import ChatMember, ChatMemberUpdated, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, ApplicationBuilder, CallbackContext, ContextTypes, ChatMemberHandler
from telegram.ext import filters as Filters
from asyncio import Queue
import os.path
import requests
import json

# Name of files which bot uses (Названия файлов, используемые ботом)
scores_filename = 'scores_test.txt' #Scores file (Файл, содержащий количество очков)
admins_filename = 'admins.txt' #Administrator list file (Файл, содержащий список администраторов)
# token_test_filename = 'token_test.txt' Test bot token file (optional) (Файл, содержащий токен тестового бота, не обязательный)
token_filename = 'token.txt' #Bot token file (Файл, содержащий токен основного бота)


channel_id = ''
channel_username = 'DalleVision' #Main channel
channel_username_test = 'dallevision_test' #Testing channel
scores = {}
posts = {}
administrators = {}
my_queue = Queue()

# Function for checking if admin increase/decrease points
def scoring2(text):
  # Counter for increase/decrease points 
  count = 0
  start_position = 0
  points_result = 0
  # Take all numbers on message
  matches = re.findall(r"\d+", text)
  for numbers in matches:
    if (text[text.find(numbers, start_position) - 1] == '-') or (text[text.find(numbers, start_position) - 1] == '+'):
      count += 1
      points_result = points_result + int(text[text.find(numbers, start_position) -1] + numbers)
      start_position = text.find(numbers) + 1
  if count != 0: return points_result
  else: return False

# Function for update or create note for user points (Функция для проверки есть ли запись пользователя в базе)
def check_user_in_scores(user, scores_list, points):
  if user in scores_list:
    scores_list[user] += points
  else:
    scores_list[user] = points
  return scores_list

# Function for check increase/decrease points (need to fix) (Функция для поиска начисления/)
async def count_points(update: Updater, context: CallbackContext):
  global scores
  # Who reply message (Кто ответил на сообщение)
  if (update.message.from_user.is_bot == False):
    who_reply = update.message.from_user.id
  else:
    who_reply = update.message.sender_chat.id
  # Whose message has been replied (Чье сообщение было отвечено)
  if (update.message.reply_to_message.from_user.is_bot == False) and (update.message.reply_to_message.sender_chat.username != channel_username_test):
    from_who_reply = str(update.message.reply_to_message.from_user.id) + '@' + str(update.message.reply_to_message.from_user.username)
  else: from_who_reply = str(update.message.reply_to_message.sender_chat.id) + '@' + str(update.message.reply_to_message.sender_chat.username)
  # Parse text in reply message (Текст сообщения в ответе)
  message = update.message.text
  #Take username for display in message
  username_from_who_reply = from_who_reply.split('@')[1]
  if (who_reply in administrators) and (username_from_who_reply != channel_username_test):
    result_point = scoring2(message)
    if (result_point == False) and (str(result_point) != 0):
      return
    else:
      check_user_in_scores(from_who_reply, scores, result_point)
      if (result_point >= 0):
        await update.message.reply_text(f"@{username_from_who_reply} заработал {result_point} балл(ов). \nБаланс: {scores[from_who_reply]} балл(ов)!")
        with open(scores_filename, 'w') as f:
          f.writelines(f"{item},{scores[item]}\n" for item in scores)
      else:
        await update.message.reply_text(f"@{username_from_who_reply} наказан на {result_point} балл(ов). \nБаланс: {scores[from_who_reply]} балл(ов)!")
        with open(scores_filename, 'w') as f:
          f.writelines(f"{item},{scores[item]}\n" for item in scores)

# Function for posting top users (example, /top <count>)
async def top(update: Updater, context: ContextTypes.DEFAULT_TYPE) -> None:
  try:
    # args[0] should contain the count of users
    count = int(context.args[0])
    if count <= 0:
      await update.effective_message.reply_text("Укажите количество пользователей (Пример: /top 5) ")
      return
    if not scores:
      await update.message.reply_text("Пока нет участников с баллами.")
      return
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True) # Sorted users by points
    top_players = sorted_scores[:count]  # Get only 'counts' best users
    message = f"Топ {count} игроков:\n"
    for i, (user, points) in enumerate(top_players, start=1):
      username = user.split('@')[1]
      message += f"{i}. @{username}: {points} баллов\n"
    await update.message.reply_text(message)
  except (IndexError, ValueError):
    await update.effective_message.reply_text("Используйте: /top <количество>")

# Function for postin top users (example, /top <count>)
async def reset_points(update: Updater, context: ContextTypes.DEFAULT_TYPE) -> None:
  if (update.message.from_user.is_bot == False):
    who_reset = update.message.from_user.id
  else:
    who_reset = update.message.sender_chat.id
  if (who_reset in administrators):
    scores.clear()
    f = open(scores_filename, 'w')
    f.close()
    await update.effective_message.reply_text("Все баллы были сброшены")
  else:
    await update.effective_message.reply_text("Только администраторы могут сбрасывать баллы")


# Need comments
def extract_status_change(chat_member_update: ChatMemberUpdated) -> Optional[Tuple[bool, bool]]:
    status_change = chat_member_update.difference().get("status")
    member_id = chat_member_update.new_chat_member.user.id

    if status_change is None:
        return None

    old_status, new_status = status_change
    if (old_status in [ChatMember.MEMBER,ChatMember.LEFT,ChatMember.BANNED]) and (new_status in [ChatMember.OWNER,ChatMember.ADMINISTRATOR]):
      administrators[member_id] = new_status.lower()
      with open(admins_filename, 'w+') as f:
        f.writelines(f"{item},{administrators[item]}\n" for item in administrators)
      return f"Администратор id={member_id} добавлен в список администраторов канала"
    
    if (new_status in [ChatMember.MEMBER,ChatMember.LEFT,ChatMember.BANNED]) and (old_status in [ChatMember.OWNER,ChatMember.ADMINISTRATOR]):
      del administrators[member_id]
      with open(admins_filename, 'w+') as f:
        f.writelines(f"{item},{administrators[item]}\n" for item in administrators)
      return f"Администратор id={member_id} удален из списков администраторов канала"


async def track_chats(update: Updater, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tracks the chats the bot is in."""
    result = extract_status_change(update.chat_member)
    if result is None:
        return
    print(result)



def main():
  # Get main_bot token from 'token.txt'
  TOKEN = open(token_filename, "r").readline().rstrip()
  application = ApplicationBuilder().token(TOKEN).build()

  # Reading or creating points file
  if (os.path.exists(scores_filename)):
    with open(scores_filename, 'r') as scores_file:
      for line in scores_file:
        key, value = line.strip('\n').split(',')
        scores[key] = int(value)
  else: 
    scores_file = open(scores_filename, "w+")
    scores_file.close()

  # Reading or creating admins file
  if (os.path.exists(admins_filename)):
    with open(admins_filename, 'r') as admins_file:
      for line in admins_file:
        key, value = line.strip('\n').split(',')
        administrators[key] = value
  else: 
    admins_file = open(admins_filename, "w+")
    admins_file.close()

  # Get channel ID
  response_channel_id = requests.get(f'https://api.telegram.org/bot{TOKEN}/getChat?chat_id=@{channel_username_test}')
  contents = json.loads(response_channel_id.text)
  # Check 'OK' answer without mistakes
  if contents['ok'] == True:
    channel_id = contents['result']['id']
    # Add channel in list of administrators (for discussion)
    administrators[channel_id] = 'channel'
  else: return

  # Get administrators list of channel (Bot needed to be admin on this channel) and update admins file
  response_admins = requests.get(f'https://api.telegram.org/bot{TOKEN}/getChatAdministrators?chat_id=@{channel_username_test}')
  # print(response_admins.text)
  contents = json.loads(response_admins.text)
  # Check 'OK' answer without mistakes
  if contents['ok'] == True:
    for admin in contents['result']:
      administrators[admin['user']['id']] = admin['status']
    with open(admins_filename, 'w+') as f:
      f.writelines(f"{item},{administrators[item]}\n" for item in administrators)
  else: return

  # Command /top X
  application.add_handler(CommandHandler("top", top))

  # Command /reset
  application.add_handler(CommandHandler("reset", reset_points))

  # Reply messages listener for counting points
  application.add_handler(MessageHandler(Filters.REPLY, count_points))

  # Forward update status of chat member
  application.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.CHAT_MEMBER, channel_id))

  # Polling bot
  application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
