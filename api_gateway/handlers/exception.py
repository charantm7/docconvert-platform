class AppError(Exception):

    "Base Exception for all application errors"

    def __init__(self, message: str, stage: str = None, extra: dict = None):
        self.message = message
        self.stage = stage
        self.extra = extra or {}
        super().__init__(message)


class UserAlreadyExistsError(AppError): pass
class UserCreationError(AppError): pass
class TokenGenerationError(AppError): pass
class EmailSchedulingError(AppError): pass