import os
import requests
import sys
import logging
import time
from jsonschema import validate
from dotenv import load_dotenv
from telegram import Bot
import datetime as DT

load_dotenv()


PRACTICUM_TOKEN = os.environ['PRACTICUM_TOKEN']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

logging.basicConfig(
    format='%(asctime)s, %(name)s, %(levelname)s, %(message)s',
    filename='program.log',
    filemode='w',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

dt = DT.datetime.now()
dt = dt.replace(tzinfo=DT.timezone.utc)

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступа к переменным окружения."""
    if (
        PRACTICUM_TOKEN is not None
        and TELEGRAM_CHAT_ID is not None
        and TELEGRAM_TOKEN is not None
    ):
        return True
    else:
        logging.critical()
        return False


def send_message(bot, message):
    """Отправка статуса в чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        message = 'Удачная отправка сообщения!'
        logging.debug(message)
    except Exception as error:
        message = f'Сбой при попытке отправить сообщение: {error}'
        logging.error(message)


def get_api_answer(timestamp):
    """Обращение к эндпоинту, получение данных, форматирование данных."""
    try:
        payload = {'from_date': timestamp}
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload
        )
        if homework_statuses.status_code == 200:
            return homework_statuses.json()
        raise Exception
    except Exception as error:
        message = f'Сбой при попытке получения данных: {error}.'
        logging.critical(message)
        raise Exception


def check_response(response):
    """Проверка полученного json-ответа на соответствие документации."""
    try:
        schema_1 = {
            "type": "object",
            "properties": {
                "homeworks": {
                    "type": "array",
                },
                "current_date": {
                    "type": "number",
                }
            }
        }
        validate(response, schema_1)
        return response['homeworks'][0]
    except Exception as error:
        message = (
            f'Сбой при попытке проверить json-данные '
            f'на соответствие документации: {error}'
        )
        logger.error(message)
        raise TypeError


def parse_status(homework):
    """Подготовка сообщения о статусе работы."""
    try:
        homework_name = homework['homework_name']
        verdict = HOMEWORK_VERDICTS[homework['status']]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except Exception as error:
        message = f'Сбой при парсинге: {error}'
        logging.error(message)
        raise Exception


def main():
    """Основная логика работы бота."""
    try:
        check_tokens()
    except Exception as error:
        message = f'Некоторые переменные окружения недоступны: {error}'
        logging.critical(message)
        sys.exit()
    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(dt.timestamp() - RETRY_PERIOD)
    while True:
        try:
            GET_API_ANSWER = get_api_answer(timestamp)
            CHECK_RESPONSE = check_response(GET_API_ANSWER)
            PARSE_STATUS = parse_status(CHECK_RESPONSE)
            send_message(bot, PARSE_STATUS)
            time.sleep(RETRY_PERIOD)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.critical(message)
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
