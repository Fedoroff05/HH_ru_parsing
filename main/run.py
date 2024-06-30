import requests
from bs4 import BeautifulSoup
import fake_useragent
import time
import telebot
import sqlite3
import threading

API_KEY = "7245919525:AAHKGwnDkmB6FxvN4wpOYH7WsZH0tAmsnJ0"

local_data = threading.local()

def get_cursor():
    if not hasattr(local_data, 'connection'):
        local_data.connection = sqlite3.connect('search_resume.db')
    if not hasattr(local_data, 'cursor'):
        local_data.cursor = local_data.connection.cursor()
    return local_data.cursor

cursor = get_cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS search_resume (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT,
        user_id INTEGER,
        name TEXT,
        salary TEXT,
        work TEXT,
        tags TEXT
        
    )
''')


def save_resume(user_id, query, resume):
    cursor = get_cursor()

    name = resume.get('name', '')
    salary = resume.get('salary', '')
    work = resume.get('work', '')
    tags = ', '.join(resume.get('tags', []))

    cursor.execute(
        "INSERT INTO search_resume (user_id, query, name, salary, work, tags) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, query, name, salary, work, tags)
    )
    local_data.connection.commit()

def get_links(text):
    ua = fake_useragent.UserAgent()
    data = requests.get(
        url=f"https://hh.ru/search/resume?text={text}&area=1&isDefaultArea=true&exp_period=all_time&logic=normal&pos=full_text&page=1",
        headers={"user-agent":ua.random}
    )
    if data.status_code != 200:
        return
    soup = BeautifulSoup(data.content, "lxml")
    try:
        page_count = int(soup.find("div", attrs={"class":"pager"}).find_all("span",recursive=False)[-1].find("a").find("span").text)
    except:
        return
    for page in range(page_count):
        try:
            data = requests.get(
                url=f"https://hh.ru/search/resume?text={text}&area=1&isDefaultArea=true&exp_period=all_time&logic=normal&pos=full_text&page={page}",
                headers={"user-agent": ua.random}
            )
            if data.status_code != 200:
                continue
            soup = BeautifulSoup(data.content, "lxml")
            for a in soup.find_all("a",attrs={"class":"bloko-link"}):
                yield f"https://hh.ru{a.attrs['href'].split('?')[0]}"
        except Exception as e:
            print(f"{e}")
        time.sleep(1)


def get_resume(link):
    ua = fake_useragent.UserAgent()
    data = requests.get(
        url=link,
        headers={"user-agent":ua.random}
    )
    if data.status_code != 200:
        return
    soup = BeautifulSoup(data.content, "lxml")
    try:
        name = soup.find(attrs={"class":"resume-block__title-text"}).text
    except:
        name = ""

    try:
        salary = soup.find(attrs={"class":"resume-block__salary"}).text.replace("\u2009","").replace("\xa0", " ")
    except:
        salary = ""

    try:
        work = soup.find(attrs={"class":"bloko-header-2 bloko-header-2_lite"}).text
    except:
        work = ""

    try:
        tags = [tag.text for tag in soup.find(attrs={"class":"bloko-tag-list"}).find_all(attrs={"class":"bloko-tag__section_text"})]
    except:
        tags = []

    resume = {
        "name":name,
        "salary":salary,
        "tags":tags,
        "work":work
    }
    return resume

bot = telebot.TeleBot(API_KEY)

running = False


@bot.message_handler(commands=['start'])
def send_start_message(message):
    global running
    running = True
    bot.send_message(message.chat.id, "Доброго времени суток! Введите запрос, по которому будем искать резюме, и количество резюме (например, Python developer 5)")

@bot.message_handler(commands=['stop'])
def stop_bot(message):
    global running
    running = False
    bot.send_message(message.chat.id, "Бот остановлен. Для повторного запуска введите /start.")

@bot.message_handler(commands=['restart'])
def restart_bot(message):
    global running
    running = True
    bot.send_message(message.chat.id, "Бот перезапущен и готов вновь искать резюме.")


@bot.message_handler(func=lambda message: running)
def search_resumes(message):
    search_text = message.text.split()
    user_id = message.from_user.id
    query = message.text

    if len(search_text) < 2:
        bot.send_message(message.chat.id, "Пожалуйста, введите как минимум запрос и количество резюме.")
        return

    query = " ".join(search_text[:-1])
    try:
        num_resumes = int(search_text[-1])
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное число для количества резюме.")
        return

    save_resume(user_id, query, {})

    for link in get_links(query):
        if not running or num_resumes <= 0:
            break
        resume = get_resume(link)

        if not all(resume.values()):
            continue

        text = f"Название вакансии: {resume['name']}\nЗарплата: {resume['salary']}\n{resume['work']}\nНавыки: {', '.join(resume['tags'])}\nСсылка на резюме: {link}"
        bot.send_message(message.chat.id, text)

        save_resume(user_id, query, resume)

        num_resumes -= 1
        time.sleep(2)

    if num_resumes <= 0:
        bot.send_message(message.chat.id,
            "Поиск завершен. Все запрошенные резюме найдены. Для нового запроса о резюме, нажмите, пожалуйста, на кнопку /restart")

bot.polling()