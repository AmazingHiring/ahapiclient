
class AHBaseException(Exception):
    pass

class AHException(AHBaseException):
    pass

class AHUnauthorizedException(AHBaseException):
    pass

class AHBadRequestException(AHBaseException):
    pass
