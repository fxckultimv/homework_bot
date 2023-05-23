import logging
import os
import sys
import telegram
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot, message):
    """Функция отправки сообщений от бота клиенту."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logger.info(f'Отправлено сообщение: {message}')
    except Exception:
        raise Exception('Не удалось отправить сообщение.')


def get_api_answer(current_timestamp):
    """Получение ответа от API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    status = response.status_code
    if status != HTTPStatus.OK:
        raise AssertionError(
            f'Недоступность эндпоинта {ENDPOINT}. Код ответа от API: {status}'
        )
    try:
        return response.json()
    except ValueError:
        ValueError('Ошибка преобразования к типам данных в Python.')


def check_response(response):
    """Проверка ответа от API."""
    if not isinstance(response, dict):
        raise TypeError('Ответ от API не является словарем.')
    hws = response.get('homeworks')
    cur_date = response.get('current_date')
    if (hws is None or cur_date is None):
        raise KeyError('Ошибка в получении значений словаря.')
    if not isinstance(hws, list):
        raise TypeError('Ответ от API не соответствует ожиданиям.')
    return hws


def parse_status(homework):
    """Проверка статуса парсинга."""
    homework_name = homework.get('homework_name')
    if not homework_name:
        raise KeyError(f'Пустое/отсутствует поле: {homework_name}')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError(f'Неизвестный статус: {homework_status}')
    verdict = HOMEWORK_STATUSES.get(homework_status)
    return f'Был изменён статус проверки задания "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика бота вынесена в эту функцию."""
    if not check_tokens():
        logger.critical('Отсутствует переменная окружения.')
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
            else:
                logger.debug('Новые статусы в ответе отсутствуют.')
            current_timestamp = response.get(
                'current_date',
                int(time.time()) - RETRY_TIME
            )
        except Exception as error:
            logger.error(error)
            message = f'Ошибка в работе программы: {error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
