import traceback


class WeatherServiceInputError(Exception):
    """Raised when there is an error in the weather service."""


class WeatherDataFetcherError(Exception):
    """Raised when there is an error in the weather service."""


def get_exception_traceback(exc: Exception) -> str:
    return "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)
    ).replace("\n", "\\n")
