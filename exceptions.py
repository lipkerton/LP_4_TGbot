class InvalidStatusCode(Exception):
    """Используется когда код статуса отличается от 200."""

    pass


class GetDataError(Exception):
    """Ошибка возникает при попытке получить данные из API."""

    pass


class ParsingError(Exception):
    """Ошибка возникает при неудачном парсинге."""

    pass
