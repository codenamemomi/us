class ServiceError(Exception):
    def __init__(self, detail: str, status_code: int) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class InvalidInviteCodeError(ServiceError):
    def __init__(self) -> None:
        super().__init__("Invalid invite code", 400)


class CoupleFullError(ServiceError):
    def __init__(self) -> None:
        super().__init__("This couple already has two members", 409)


class EmailAlreadyRegisteredError(ServiceError):
    def __init__(self) -> None:
        super().__init__("Email is already registered", 409)


class InvalidCredentialsError(ServiceError):
    def __init__(self) -> None:
        super().__init__("Invalid email or password", 401)