import datetime as DT
import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from jsonschema import validate
from telegram import Bot, TelegramError

from exceptions import InvalidStatusCode, GetDataError, ParsingError

load_dotenv()

PRACTICUM_TOKEN = os.environ['PRACTICUM_TOKEN']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

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
    return all([
        PRACTICUM_TOKEN is not None,
        TELEGRAM_CHAT_ID is not None,
        TELEGRAM_TOKEN is not None
    ])


def send_message(bot, message):
    """Отправка статуса в чат."""
    try:
        message = f'Начало отправки сообщения {message} в тг-чат.'
        logging.debug(message)
        bot.send_message(TELEGRAM_CHAT_ID, message)
        message = 'Удачная отправка сообщения!'
        logging.debug(message)
    except TelegramError as error:
        message = f'Сбой при попытке отправить сообщение: {error}'
        logging.error(message)


def get_api_answer(timestamp):
    """Обращение к эндпоинту, получение данных, форматирование данных."""
    try:
        payload = {'from_date': timestamp}
        message = (
            f'Обращение к эндпоинту {ENDPOINT}'
            f'Данные заголовка: {HEADERS}'
            f'Параметры: {payload}'
            'Начато обращение к эндпоинту.'
        )
        logging.debug(message)
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload
        )
        if HTTPStatus.OK == homework_statuses.status_code:
            return homework_statuses.json()
        raise InvalidStatusCode('Статус-код отличается от 200!')
    except requests.RequestException as error:
        message = f'Сбой при попытке получения данных: {error}.'
        raise GetDataError(message)


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
        return response['homeworks']
    except Exception as error:
        message = (
            f'Сбой при попытке проверить json-данные '
            f'на соответствие документации: {error}'
        )
        raise TypeError(message)


def parse_status(homework):
    """Подготовка сообщения о статусе работы."""
    try:
        homework_name = homework['homework_name']
        verdict = HOMEWORK_VERDICTS[homework['status']]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except Exception as error:
        message = f'Сбой при парсинге: {error}'
        raise ParsingError(message)


def main():
    """Основная логика работы бота."""
    if check_tokens():
        message = 'Все переменные окружения доступны и проверены.'
        logging.debug(message)
    else:
        message = 'Некоторые переменные окружения недоступны!'
        logging.critical(message)
        sys.exit()
    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(dt.timestamp() - RETRY_PERIOD)
    while True:
        try:
            get_data = get_api_answer(timestamp)
            homeworks_list = check_response(get_data)
            if homeworks_list:
                message = parse_status(homeworks_list[0])
                send_message(bot, message)
        except ParsingError as error:
            message = f'Сбой при парсинге: {error}'
            logging.error(message)
        except TypeError as error:
            message = (
                'Сбой при попытке проверить json-данные '
                f'на соответствие документации: {error}'
            )
            logger.error(message)
        except GetDataError as error:
            message = f'Сбой при попытке получения данных: {error}.'
            logging.error(message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s, %(name)s, %(levelname)s, %(message)s',
        filename='program.log',
        filemode='w',
        level=logging.INFO,
    )
    main()
