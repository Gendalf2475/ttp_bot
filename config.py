import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))

TOPIC_NEW_ID = int(os.getenv("TOPIC_NEW_ID"))
TOPIC_IN_WORK_ID = int(os.getenv("TOPIC_IN_WORK_ID"))
TOPIC_DECLINED_ID = int(os.getenv("TOPIC_DECLINED_ID"))
TOPIC_AWAIT_REVIEW_ID = int(os.getenv("TOPIC_AWAIT_REVIEW_ID"))
TOPIC_APPROVED_ID = int(os.getenv("TOPIC_APPROVED_ID"))

# Парсим список ID администраторов
admins_str = os.getenv("SUPER_ADMINS", "")
SUPER_ADMINS = [int(x) for x in admins_str.split(",") if x.strip().isdigit()]

# Парсим список ответственных
usernames_str = os.getenv("RESPONSIBLE_USERNAMES", "")
RESPONSIBLE_USERNAMES = [x.strip() for x in usernames_str.split(",") if x.strip()]

MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
