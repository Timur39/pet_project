FROM python

RUN mkdir "telegram-bot"

WORKDIR /telegram-bot

COPY requirements.txt ./


RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY .env .env

WORKDIR src

CMD ["/bin/bash", "-c", "python main.py"]
