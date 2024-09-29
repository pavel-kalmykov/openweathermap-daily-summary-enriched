import traceback


class WeatherServiceInputError(Exception):
    """Raised when there is an error in the weather service."""

    pass


class WeatherDataFetcherError(Exception):
    """Raised when there is an error in the weather service."""

    pass


def get_exception_traceback(exc: Exception) -> str:
    return "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)
    ).replace("\n", "\\n")
