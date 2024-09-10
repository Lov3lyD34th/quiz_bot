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

# Function for check new post and future parsing (Функция для проверки нового поста и дальнейшего парсинга)
async def check_new_post(update: Updater, context: CallbackContext):
  if (update.channel_post) :
    print("It's channel post\n")
  else:
    return

# Function for scoring points (Функция начисления баллов)
def scoring(points, trash, user, scores_list):
  try:
    # Delete 'trash' from message (Вычленяем очки из сообщения администратора)
    points = int(points.lower().strip(trash))
    # Update or create note for user points (Обновляем или создаем запись для пользователя)
    if user in scores_list:
      scores_list[user] += points
    else:
      scores_list[user] = points
    return scores_list
  except (IndexError, ValueError):
    return False


# Function for check increase/decrease points (need to fix) (Функция для поиска начисления/)
async def count_points(update: Updater, context: CallbackContext):
  global scores
  # Who reply message (Кто ответил на сообщение)
  if (update.message.from_user.is_bot == False):
    who_reply = update.message.from_user.id
  else:
    who_reply = update.message.sender_chat.id
  # Whose message has been replied (Чье сообщение было отвечено)
  if (update.message.reply_to_message.from_user.is_bot == False):
    from_who_reply = str(update.message.reply_to_message.from_user.id) + '@' + update.message.reply_to_message.from_user.username
  else: from_who_reply = str(update.message.reply_to_message.sender_chat.id) + '@' + update.message.reply_to_message.sender_chat.username
  # Parse text in reply message (Текст сообщения в ответе)
  message = update.message.text
  # Find increase points message (Поиск сообщения о начислении очков)
  # return
  if ('Верно!' in message):
    # Handling of increase points message if who_reply in admin list (Обработка начисления очков, если пользователь администратор)
    if (who_reply in administrators):
      fstring= 'верно!баллов ' #formatted string for clean 'trash' symbols and leave only points (Форматированная строка для последующей очистки сообщения от "мусора")
      if (scoring(message, fstring, from_who_reply, scores) == False):
        await update.message.reply_text('Ошибка! В вашем сообщении не найдёно количество начисленных (отнятых) баллов')
      else: 
        await update.message.reply_text(f"{from_who_reply} заработал баллов. \nБаланс: {scores[from_who_reply]} баллов!")
        with open(scores_filename, 'w') as f:
          f.writelines(f"{item},{scores[item]}\n" for item in scores)
    else:
      await update.message.reply_text("Только администраторы могут начислять баллы")
  # Found decrease point message (Поиск сообщения о вычитании очков)
  if ('Читер!' in message):
    # Handling of decrease points message if who_reply in admin list (Обработка сообщения вычитания очков, если пользователь администратор)
    if (who_reply in administrators):
      fstring= 'читер!баллов ' #formatted string for clean 'trash' symbols and leave only points (форматированная строка для последующей очистки сообщения от "мусора")
      scoring(message, fstring, from_who_reply, scores)
      if (scoring(message, fstring, from_who_reply, scores) == False):
        await update.message.reply_text('Ошибка! В вашем сообщении не найдёно количество начисленных (отнятых) баллов')
      else: 
        await update.message.reply_text(f"{from_who_reply} наказан и теряет баллы. \nБаланс: {scores[from_who_reply]} баллов!")
        with open(scores_filename, 'w') as f:
          f.writelines(f"{item},{scores[item]}\n" for item in scores)
    else:
      await update.message.reply_text("Только администраторы могут наказывать читеров")

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
    for i, (username, points) in enumerate(top_players, start=1):
      message += f"{i}. @{username}: {points} баллов\n"
    await update.message.reply_text(message)
  except (IndexError, ValueError):
    await update.effective_message.reply_text("Используйте: /top <количество>")

# Function for postin top users (example, /top <count>)
async def reset_points(update: Updater, context: ContextTypes.DEFAULT_TYPE) -> None:
  if (update.message.from_user.id in administrators):
    scores = {}
    f = open(scores_filename, 'w')
    f.close()
    await update.effective_message.reply_text("Все баллы были сброшены")
  else:
    await update.effective_message.reply_text("Только администраторы могут сбрасывать баллы")

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
  response_channel_id = requests.get(f'https://api.telegram.org/bot{TOKEN}/getChat?chat_id=@{channel_username}')
  contents = json.loads(response_channel_id.text)
  # Check 'OK' answer without mistakes
  if contents['ok'] == True:
    channel_id = contents['result']['id']
    # Add channel in list of administrators (for discussion)
    administrators[channel_id] = 'channel'
  else: return

  # Get administrators list of channel (Bot needed to be admin on this channel) and update admins file
  response_admins = requests.get(f'https://api.telegram.org/bot{TOKEN}/getChatAdministrators?chat_id=@{channel_username}')
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

  # Forward messages listener for parsing channel post
  application.add_handler(MessageHandler(Filters.ALL, check_new_post))

  # Polling bot
  application.run_polling()

if __name__ == '__main__':
    main()
