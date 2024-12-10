import typing


class BadArgument(Exception):
    def __init__(self, message):
        self.message = message


def convertToBool(input: typing.Union[str, int, bool]) -> bool:
    errormessage = f"Expected yes/no, true/false, 0/1. Got {input}"
    if isinstance(input, str):
        input = input.lower()
        if input == "yes":
            return True
        elif input == "no":
            return False
        else:
            raise BadArgument(errormessage)
    elif isinstance(input, int):
        if input == 0:
            return False
        elif input == 1:
            return True
        else:
            raise BadArgument(errormessage)
    else:
        return input
