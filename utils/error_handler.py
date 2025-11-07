# utils/error_handler.py
from .logger import log_info as log_error  # aliasujemy log_info na log_error


def handle_exception(e):
    """
    Centralna funkcja obsługi błędów.
    - loguje do pliku
    - wypisuje w konsoli
    """
    log_error(f"{type(e).__name__}: {e}")