from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

EMAIL = "25ds1000066@ds.study.iitm.ac.in"

ALLOWED_ORIGINS = [
    "https://app-qz9758.example.com",
    "https://exam.sanand.workers.dev",
]

RATE_LIMIT = 13
WINDOW = 10

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

client_requests = {}


@app.middleware("http")
async def request_context(request: Request, call_next):

    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


@app.middleware("http")
async def rate_limit(request: Request, call_next):

    if request.method == "OPTIONS":
        return await call_next(request)

    client = request.headers.get("X-Client-Id")

    if client is None:
        return await call_next(request)

    now = time.time()

    if client not in client_requests:
        client_requests[client] = []

    client_requests[client] = [
        t for t in client_requests[client]
        if now - t < WINDOW
    ]

    if len(client_requests[client]) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )

    client_requests[client].append(now)

    return await call_next(request)


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }