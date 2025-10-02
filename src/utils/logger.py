"""Logging utilities using Loguru"""

import sys
from pathlib import Path

from loguru import logger

from src.utils.config import settings


def setup_logger():
    """Configure the logger with proper settings"""
    
    # Remove default handler
    logger.remove()
    
    # Console handler with color
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
    )
    
    # File handler for all logs
    log_dir = settings.project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
    )
    
    # Error file handler
    logger.add(
        log_dir / "errors_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="90 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
    )
    
    return logger


# Initialize logger
app_logger = setup_logger()
