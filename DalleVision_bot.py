from telegram.ext import Updater, CommandHandler, MessageHandler, ApplicationBuilder, CallbackContext, ContextTypes
from telegram.ext import filters as Filters
from asyncio import Queue
import os.path

# Name of files which bot uses (Названия файлов, используемые ботом)
scores_filename = 'scores_test.txt' #Scores file (Файл, содержащий количество очков)
admins_filename = 'admins.txt' #Administrator list file (Файл, содержащий список администраторов)
token_test_filename = 'token_test.txt' #Test bot token file (optional) (Файл, содержащий токен тестового бота, не обязательный)
token_filename = 'token.txt' #Bot token file (Файл, содержащий токен основного бота)


scores = {}
posts = {}
administrators = {}
my_queue = Queue()

def check_admins(get_admins, administrator_list):
  # Add and check admins list (Добавление и проверка администраторов)
  for admin in get_admins:
      administrator_list[admin.user.username] = 'admin'
  with open(admins_filename, 'w') as f:
    f.writelines(f"{item},{administrator_list[item]}\n" for item in administrator_list)

# Function for check new post and future parsing (Функция для проверки нового поста и дальнейшего парсинга)
async def check_new_post(update: Updater, context: CallbackContext):
    print(update.message.api_kwargs)
    
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
  # Get admins from channel (Получение списка администраторов канала)
  admins = await update.effective_chat.get_administrators()
  print(admins)
  check_admins(admins, administrators)
  # Who reply message (Кто ответил на сообщение)
  who_reply = update.message.from_user.username
  # Whose message has been replied (Чье сообщение было отвечено)
  from_who_reply = update.message.reply_to_message.from_user.username
  # Parse text in reply message (Текст сообщения в ответе)
  message = update.message.text
  # Find increase points message (Поиск сообщения о начислении очков)
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
    # Add and check admins (Добавление и проверка администраторов)
    admins = await update.effective_chat.get_administrators()
    scores = check_admins(admins, administrators)
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

# Function for postin top users (example, /top <count>)
async def top(update: Updater, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # args[0] should contain the count of users
        count = int(context.args[0])
        if count < 0:
            await update.effective_message.reply_text("Укажите пожалуйста целое число от 0 до ")
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

def main():
  
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
    scores_file = open(admins_filename, "w+")
    scores_file.close()

  # Add 'extra' admins/moderators
  administrators['DalleVision'] = 'owner'
  administrators['Channel_Bot'] = 'channel'
  administrators['Lov3lyD3ath'] = 'moderator'

  # Get main_bot token from 'token.txt'
  # token = open(token_filename, "r").readline().rstrip()
  # application = ApplicationBuilder().token(token).build()

  # Get test_bot token from 'token_test.txt'
  token_test = open(token_test_filename, "r").readline().rstrip()
  application = ApplicationBuilder().token(token_test).build()

  # Command /top X
  application.add_handler(CommandHandler("top", top))

  # Reply messages listener for counting points
  application.add_handler(MessageHandler(Filters.REPLY, count_points))

  # Forward messages listener for parsing channel post
  application.add_handler(MessageHandler(Filters.FORWARDED, check_new_post))

  # Polling bot
  application.run_polling()

if __name__ == '__main__':
    main()
