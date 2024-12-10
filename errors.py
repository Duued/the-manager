class InvalidTypeException(Exception):
    def __init__(self, message):
        self.message = message

        super().__init__(message)

    pass


class ApiError(Exception):
    def __init__(self, message):
        self.message = message

        super().__init__(message)

    pass
