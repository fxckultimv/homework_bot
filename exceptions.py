class Error(Exception):
    """Базовый класс для исключений."""


class ExceptionSendMessageError(Error):
    """Исключение при сбое при отправки сообщения."""

    def __init__(self, message):
        self.message = message


class ExceptionStatusError(Exception):
    """Исключение при некорректном статусе ответа."""

    def __init__(self, message):
        self.message = message


class ExceptionGetAPYError(Exception):
    """Исключение при ошибке запроса к API."""

    def __init__(self, message):
        self.message = message