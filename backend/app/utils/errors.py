CLIENT_ERROR_MESSAGE = "Service temporarily unavailable"


class ConsulateError(Exception):
    pass


class ProviderError(ConsulateError):
    pass


class SessionLimitError(ConsulateError):
    pass


class ModelNotFoundError(ConsulateError):
    pass
