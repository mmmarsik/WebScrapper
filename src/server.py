import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import Response
from telethon import TelegramClient

from src.api import router
from src.api.endpoints import scrapper_api_router
from src.api.endpoints.bot_api.bot_updates import router as bot_updates_router
from src.bot.notification_sender.http_sender import HttpSender
from src.bot.scheduler import Scheduler
from src.bot.settings import BotSettings
from src.db.repositories.orm_repository.chat_repository import ORMChatRepository
from src.db.repositories.orm_repository.link_repository import ORMLinkRepository
from src.db.repositories.sql_repository.chat_repository import SQLChatRepository
from src.db.repositories.sql_repository.link_repository import SQLLinkRepository
from src.db.repositories.sql_repository.sql_pool_manager import SQLConnectionPool
from src.db.repositories.types import RepositoryAccessType
from src.db.settings import DBSettings
from src.scrapper.client import ScrapperAPIClient

if TYPE_CHECKING:
    from src.db.repositories.base import ChatRepositoryInterface, LinkRepositoryInterface

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> Response:
    """Handles request validation exceptions and logs the invalid request data.

    Args:
        request (Request): The incoming HTTP request.
        exc (RequestValidationError): The validation error exception.

    Returns:
        Response: The validation error response.

    """
    logger.exception("Invalid request data: %s", exc)
    return await request_validation_exception_handler(request, exc)


@asynccontextmanager
async def default_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages the application's startup and shutdown lifecycle.

    Initializes dependencies such as:
    - Thread pool executor
    - Bot settings
    - Repository manager
    - Scrapper API client
    - Telegram client
    - Scheduler

    Cleans up resources on application shutdown.
    """
    logger.debug("Starting application lifespan...")
    loop = asyncio.get_event_loop()
    loop.set_default_executor(ThreadPoolExecutor(max_workers=4))

    api_id: int = int(os.getenv("BOT_API_ID") or 0)
    api_hash: str = os.getenv("BOT_API_HASH") or ""
    bot_token: str = os.getenv("BOT_TOKEN") or ""

    app.state.bot_settings = BotSettings(api_id=api_id, api_hash=api_hash, token=bot_token)

    scrapper_client = ScrapperAPIClient(base_url="http://scrapper_api:8000")
    app.state.scrapper_client = scrapper_client

    telegram_client = TelegramClient(
        "fastapi_bot_session",
        app.state.bot_settings.api_id,
        app.state.bot_settings.api_hash,
    )

    await telegram_client.start(bot_token=app.state.bot_settings.token)

    app.state.tg_client = telegram_client

    user: str = os.getenv("POSTGRES_USER") or ""
    password: str = os.getenv("POSTGRES_PASSWORD") or ""
    db: str = os.getenv("POSTGRES_DB") or "postgres"
    host: str = os.getenv("POSTGRES_HOST") or ""
    access_type_str: str = os.getenv("POSTGRES_ACCESS_TYPE") or "ORM"
    access_type = RepositoryAccessType(access_type_str)
    pagination_batch_size: int = int(os.getenv("POSTGRES_PAGINATION_BATCH_SIZE", "100"))

    app.state.db_settings = DBSettings(
        db=db,
        user=user,
        password=password,
        host=host,
        access_type=access_type,
        pagination_batch_size=pagination_batch_size,
    )

    database_url = f"postgresql+psycopg://{user}:{password}@{host}/{db}"

    engine = create_async_engine(database_url, echo=True)
    async_session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    app.state.async_session_maker = async_session_maker

    sql_connection_string = f"postgresql://{user}:{password}@{host}/{db}"
    sql_connection_pool = SQLConnectionPool(sql_connection_string)
    app.state.sql_connection_pool = sql_connection_pool

    chat_repository: ChatRepositoryInterface
    link_repository: LinkRepositoryInterface

    if access_type == RepositoryAccessType.ORM:
        chat_repository = ORMChatRepository(async_session_maker)
        link_repository = ORMLinkRepository(async_session_maker)
        logger.info("Using ORM repos for Scheduler")
    else:
        await sql_connection_pool.initialize()
        chat_repository = SQLChatRepository(sql_connection_pool)
        link_repository = SQLLinkRepository(sql_connection_pool)
        logger.info("Using SQL repos for Scheduler")

    notification_sender = HttpSender(telegram_client)

    app.state.notification_sender = notification_sender

    scheduler = Scheduler(
        scrapper_client=scrapper_client,
        telegram_client=telegram_client,
        chat_repository=chat_repository,
        link_repository=link_repository,
        notification_sender=notification_sender,
        check_interval=60,
        batch_size=pagination_batch_size,
    )

    app.state.scheduler = scheduler
    scheduler_task = asyncio.create_task(scheduler.start())
    logger.info("Scheduler started.")

    try:
        yield
    finally:
        await scheduler.stop()
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            logger.info("Scheduler task canceled.")

        await sql_connection_pool.close()
        logger.info("SQL connection closed.")

        await scrapper_client.close()
        await telegram_client.disconnect()
        logger.info("Telegram client disconnected.")
        await engine.dispose()
        logger.info("Database engine disposed.")
        loop.run_until_complete(loop.shutdown_default_executor())
        loop.close()


app = FastAPI(
    title="Scrapper API",
    lifespan=default_lifespan,
)

# Register exception handlers
app.exception_handler(RequestValidationError)(validation_exception_handler)

# Register API routers
app.include_router(router=router, prefix="/api/v1")
app.include_router(router=scrapper_api_router)
app.include_router(router=bot_updates_router)

# Add middlewares
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    """
    Entry point for running the FastAPI application with Uvicorn.
    Logs application startup details and starts the server.
    """
    logger.info("Serving app on port: %d", 8000)
    logger.info("http://127.0.0.1:8000/docs")
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level=os.getenv("LOGGING_LEVEL", "info").lower(),
    )
