from fastapi import  Response
from starlette.responses import JSONResponse
import typing
import json

class HTTPException2(Exception):
    def __init__(self, status_code:int, detail: str):
        self.status_code = status_code
        self.detail = detail

class CustomJSONResponse(JSONResponse):
    def render(self, content: typing.Any) -> bytes:
        return json.dumps(content).encode("utf-8")

class JsonResponse2(Response):
    media_type = "application/json"        