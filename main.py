from fastapi import FastAPI, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi import Request, File, UploadFile
from boto3.s3.transfer import TransferConfig
import boto3
from tempfile import NamedTemporaryFile
import shutil

from api.common import *
from custom_response import *
from api.upload import upload_router
from api.filters import filter_router
from api.search import search_router
from api.download import download_router

from core.databases import database

app = FastAPI(default_response_class=CustomJSONResponse, openapi_url=None)

app.router.redirect_slashes = False

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.exception_handler(HTTPException2)
async def HTTPException2Handler(request: Request, exception: HTTPException2):
    content = {
        "detail": exception.detail
    }
    return JsonResponse2(status_code=exception.status_code, content=json.dumps(content))


app.router.redirect_slashes = False

app.include_router(upload_router, prefix='/files', tags=['upload'])
app.include_router(filter_router, prefix='/api', tags=['filter'])
app.include_router(search_router, prefix='/api', tags=['search'])
app.include_router(download_router, prefix='/files', tags=['download'])

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
    "https://facialoracle.com"
]

app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
async def read_root():
    return {"detail": "Upload API Service"}


@app.get("/ip")
async def read_ip(request: Request):
    # return {"detail": request.client.host}
    # 사용자 IP를 가져온다.
    ip = request.headers.get(
        'X-Forwarded-For', request.client.host).split(',')[0]
    return {"detail": ip}

def check_ip(request):
    return TransferConfig

@app.get("/openapi.json")
async def get_openapi_json(request: Request):
    if check_ip(request):
        return JSONResponse(get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
            servers=app.servers,
        ))
    raise HTTPException2(status_code=401, detail="Unauthorized request.")

@app.get("/docs")
async def get_swagger_documentation(request: Request):
    if check_ip(request):
        return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")
    raise HTTPException2(status_code=401, detail="Unauthorized request.")