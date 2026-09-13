import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Імпорт автоінструментації Datadog (вимога методички)
from ddtrace import patch_all

# Активація моніторингу
patch_all()

# Налаштування системного логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_logger")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware для логування вхідних HTTP-запитів
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = f"{process_time:.2f}ms"
    
    logger.info(
        f"Path: {request.url.path} | Method: {request.method} | "
        f"Status: {response.status_code} | Duration: {formatted_process_time}"
    )
    
    return response

# Реєстрація маршрутів
from routes.readers import readers_router 
from routes.books import books_router
from routes.borrowings import borrowings_router
from routes.auth import router
from routes.analytics import analytics_router

app.include_router(readers_router)
app.include_router(books_router)
app.include_router(borrowings_router)
app.include_router(router)
app.include_router(analytics_router)