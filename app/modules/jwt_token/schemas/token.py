from enum import Enum


class TokenTypes(str, Enum):
    ACCESS = 'access'
    REFRESH = 'refresh'
    RESET_PASSWORD = 'reset_password'
    EMAIL_VERIFICATION = 'email_verification'


class ExpiryTokenMinutes:
    ACCESS = 1440  # 1 day
    REFRESH = 1440  # 1 day
    RESET_PASSWORD = 10  # 10 minutes
    EMAIL_VERIFICATION = 60  # 1 hour
