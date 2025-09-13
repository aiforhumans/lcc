"""
Logging configuration for Local Chat Companion.

Provides structured logging with support for console and file output.
"""

import logging
import logging.handlers
import sys
import time
from pathlib import Path
from typing import Optional

try:
    import structlog
    from rich.console import Console
    from rich.logging import RichHandler
except ImportError:
    # Fallback for basic logging if dependencies not installed
    structlog = None
    Console = None
    RichHandler = None

from .config import Config


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green  
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        """Format log record with colors."""
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(config: Config) -> structlog.BoundLogger:
    """
    Set up logging configuration based on application config.
    
    Args:
        config: Application configuration
        
    Returns:
        Configured structlog logger
    """
    # Ensure logs directory exists
    log_dir = Path(config.log_file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[]
    )
    
    # Console handler with Rich for pretty output
    console = Console(stderr=True)
    console_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=True,
        enable_link_path=True,
        markup=True,
        rich_tracebacks=True,
    )
    console_handler.setLevel(getattr(logging, config.log_level.upper()))
    
    # File handler with rotation
    if config.log_to_file:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=config.log_file_path,
            maxBytes=config.log_max_size_mb * 1024 * 1024,  # Convert MB to bytes
            backupCount=config.log_backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Add handlers to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
    
    # Add console handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)
    
    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="ISO"),
    ]
    
    if config.debug:
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    else:
        processors.extend([
            structlog.processors.JSONRenderer(),
        ])
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, config.log_level.upper())
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Create and return the main application logger
    logger = structlog.get_logger("local_chat_companion")
    
    # Log startup information
    logger.info(
        "Logging initialized",
        log_level=config.log_level,
        log_to_file=config.log_to_file,
        log_file=config.log_file_path if config.log_to_file else None,
        debug_mode=config.debug,
    )
    
    return logger


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return structlog.get_logger(name)


def log_function_call(logger: structlog.BoundLogger):
    """
    Decorator to log function calls with parameters and results.
    
    Args:
        logger: Logger instance to use
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(
                f"Calling {func.__name__}",
                args=args,
                kwargs=kwargs
            )
            try:
                result = func(*args, **kwargs)
                logger.debug(
                    f"{func.__name__} completed successfully",
                    result=str(result)[:200] if result else None
                )
                return result
            except Exception as e:
                logger.error(
                    f"{func.__name__} failed",
                    error=str(e),
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


def setup_request_logging(app, logger: structlog.BoundLogger):
    """
    Set up request logging for web applications.
    
    Args:
        app: FastAPI or similar app instance
        logger: Logger instance
    """
    @app.middleware("http")
    async def log_requests(request, call_next):
        """Log HTTP requests and responses."""
        start_time = time.time()
        
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            logger.info(
                "Request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=round(process_time, 3),
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            logger.error(
                "Request failed",
                method=request.method,
                url=str(request.url),
                error=str(e),
                process_time=round(process_time, 3),
                exc_info=True,
            )
            raise


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""
    
    @property
    def logger(self) -> structlog.BoundLogger:
        """Get a logger instance for this class."""
        return structlog.get_logger(self.__class__.__name__)