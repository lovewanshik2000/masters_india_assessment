from rest_framework.response import Response
from rest_framework import status


def api_response(success=True, message="", data=None, status_code=status.HTTP_200_OK):
    response_data = {"status": success, "message": message}
    if data is not None:
        response_data["data"] = data
    return Response(response_data, status=status_code)
