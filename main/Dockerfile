# Используем базовый образ Python
FROM python:3.8

# Устанавливаем необходимые библиотеки
RUN pip install requests beautifulsoup4 fake-useragent pyTelegramBotAPI

# Копируем все файлы из текущей директории в /app внутри контейнера
COPY . /app

# Устанавливаем рабочую директорию в /app
WORKDIR /app

# Команда для запуска вашего скрипта
CMD ["python", "run.py"]