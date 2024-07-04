FROM python:3.8

RUN pip install requests beautifulsoup4 fake-useragent pyTelegramBotAPI

COPY . /app

WORKDIR /app

CMD ["python", "run.py"]
