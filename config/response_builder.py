from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ErrorDetail

def response_ok(message="ok", status=status.HTTP_200_OK):
    if not isinstance(message, dict):
        message = {"message": message}
    return Response(message, status=status)

def response_error(errors):
    message = extract_message(errors)
    if not message:
        message = "unknown error."
    return Response(
        {"message": message},
        status=extract_status(errors)
    )
    
def response_error(custom_validation_error):
    error_type = custom_validation_error.error_type
    return Response(
        {"message": error_type.message},
        status=error_type.status
    )

def extract_status(errors):
    for key, value in errors.items():
        if key == "status":
            if isinstance(value, ErrorDetail):
                return str(value)
            elif isinstance(value, list) and isinstance(value[0], ErrorDetail):
                return str(value[0])
        elif isinstance(value, dict):  # 중첩된 dict 처리
            return extract_status(value)  # 재귀 호출
    return None

def extract_message(errors):
    parsed_messages = {
        key: value for key, value in errors.items()
    }
    return {k: v for k, v in parsed_messages.items()}
