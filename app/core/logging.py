import logging

from app.core.config import settings

logger = logging.getLogger("uvicorn.error")
logger.setLevel(settings.log_level)
