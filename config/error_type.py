from enum import Enum
from rest_framework import status


class ErrorType(Enum):
    # user
    INVALID_VERIFICATION_CODE = (status.HTTP_400_BAD_REQUEST, "Invalid verification code.")
    VERIFICATION_CODE_EXPIRED = (status.HTTP_400_BAD_REQUEST, "The verification code has expired.")
    VALIDATION_ERROR = (status.HTTP_400_BAD_REQUEST, "One or more fields failed validation. Please check the input values.")
    USER_ID_NOT_FOUND = (status.HTTP_400_BAD_REQUEST, "The user_id parameter is missing in the request URL.")
    
    INVALID_CREDENTIALS = (status.HTTP_401_UNAUTHORIZED, "Invalid credentials.")
    INVALID_PASSWORD = (status.HTTP_401_UNAUTHORIZED, "Invalid password.")
    
    RECEPTION_FULL = (status.HTTP_403_FORBIDDEN, "The reception is full.")
    NO_RECEPTION = (status.HTTP_403_FORBIDDEN, "No reception.")
    NOT_ONLINE = (status.HTTP_403_FORBIDDEN, "Your friend is not online.")
    TOURNAMENT_FULL = (status.HTTP_403_FORBIDDEN, "The tournament is full.")
    TOURNAMENT_NOT_FULL = (status.HTTP_403_FORBIDDEN, "Tournament is not full.")
    ALREADY_EXISTS = (status.HTTP_403_FORBIDDEN, "User already joined tournament.")
    TOURNAMENT_NOT_WAITING = (status.HTTP_403_FORBIDDEN, "Tournament is not in waiting state.")
    PERPISSON_DENIED = (status.HTTP_403_FORBIDDEN, "You do not have permission to start this tournament.")
    
    USER_NOT_FOUND = (status.HTTP_404_NOT_FOUND, "User not found.")
    RECEPTION_NOT_FOUND = (status.HTTP_404_NOT_FOUND, "Reception not found.")
    
    NICKNAME_ALREADY_EXISTS = (status.HTTP_409_CONFLICT, "This nickname is already in use.")
    EMAIL_ALREADY_EXISTS = (status.HTTP_409_CONFLICT, "This email is already in use.")

    # 기타 추가된 코드들은 자바 코드와 동일하게 추가 가능

    def __init__(self, status, message):
        self.status = status
        self.message = message

    def to_dict(self):
        return {
            "status": self.status,
            "message": self.message
        }

    @staticmethod
    def find_by_message(message):
        for error in ErrorType:
            if error.message == message:
                return error
        return None