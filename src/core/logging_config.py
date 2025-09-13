"""
Logging configuration for Local Chat Companion.

Provides structured logging with support for console and file output.
"""

import logging
import logging.handlers
import sys
import time
from pathlib import Path
from typing import Optional, Union, Any

try:
    import structlog
    from rich.console import Console
    from rich.logging import RichHandler
    STRUCTLOG_AVAILABLE = True
    RICH_AVAILABLE = True
except ImportError:
    # Fallback for basic logging if dependencies not installed
    structlog = None
    Console = None
    RichHandler = None
    STRUCTLOG_AVAILABLE = False
    RICH_AVAILABLE = False

from .config import Config

# Type aliases for logger compatibility
if STRUCTLOG_AVAILABLE:
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        import structlog
        BoundLoggerType = structlog.BoundLogger
    else:
        BoundLoggerType = Any
else:
    BoundLoggerType = logging.Logger


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


def setup_logging(config: Config) -> Union[Any, logging.Logger]:
    """
    Set up logging configuration based on application config.
    
    Args:
        config: Application configuration
        
    Returns:
        Configured logger (structlog if available, else standard logger)
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
    
    # Console handler with Rich for pretty output if available
    if RICH_AVAILABLE:
        console = Console(stderr=True)
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=True,
            enable_link_path=True,
            markup=True,
            rich_tracebacks=True,
        )
    else:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    
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
    
    # Configure structlog if available
    if STRUCTLOG_AVAILABLE:
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
            structlog_available=True
        )
        
        return logger
    else:
        # Fallback to standard logging
        logger = logging.getLogger("local_chat_companion")
        logger.info(
            f"Logging initialized (fallback mode) - Level: {config.log_level}, "
            f"File: {config.log_file_path if config.log_to_file else 'None'}, "
            f"Debug: {config.debug}"
        )
        return logger


def get_logger(name: str) -> Union[Any, logging.Logger]:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance (structlog if available, else standard logger)
    """
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)


def log_function_call(logger: Union[Any, logging.Logger]):
    """
    Decorator to log function calls with parameters and results.
    
    Args:
        logger: Logger instance to use
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if hasattr(logger, 'debug'):
                logger.debug(
                    f"Calling {func.__name__}",
                    args=args,
                    kwargs=kwargs
                )
            try:
                result = func(*args, **kwargs)
                if hasattr(logger, 'debug'):
                    logger.debug(
                        f"{func.__name__} completed successfully",
                        result=str(result)[:200] if result else None
                    )
                return result
            except Exception as e:
                if hasattr(logger, 'error'):
                    logger.error(
                        f"{func.__name__} failed",
                        error=str(e),
                        exc_info=True
                    )
                raise
        return wrapper
    return decorator


def setup_request_logging(app, logger: Union[Any, logging.Logger]):
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
        
        if hasattr(logger, 'info'):
            logger.info(
                "Request started",
                method=request.method,
                url=str(request.url),
                client_ip=request.client.host if request.client else None,
            )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            if hasattr(logger, 'info'):
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
            
            if hasattr(logger, 'error'):
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
    def logger(self) -> Union[Any, logging.Logger]:
        """Get a logger instance for this class."""
        if STRUCTLOG_AVAILABLE:
            return structlog.get_logger(self.__class__.__name__)
        else:
            return logging.getLogger(self.__class__.__name__)
    
    def log_with_context(self, level: str, message: str, **kwargs):
        """Log a message with context, handling both structlog and standard logging."""
        logger = self.logger
        
        try:
            if STRUCTLOG_AVAILABLE and hasattr(logger, 'bind'):
                # Use structlog with keyword arguments
                getattr(logger, level.lower())(message, **kwargs)
            else:
                # Handle special logging keywords for standard logger
                special_kwargs = {}
                context_kwargs = kwargs.copy()
                
                # Extract known logging arguments
                if 'exc_info' in context_kwargs:
                    special_kwargs['exc_info'] = context_kwargs.pop('exc_info')
                if 'extra' in context_kwargs:
                    special_kwargs['extra'] = context_kwargs.pop('extra')
                if 'stack_info' in context_kwargs:
                    special_kwargs['stack_info'] = context_kwargs.pop('stack_info')
                
                # Format remaining kwargs as part of the message
                if context_kwargs:
                    context_str = ", ".join(f"{k}={v}" for k, v in context_kwargs.items())
                    formatted_message = f"{message} - {context_str}"
                else:
                    formatted_message = message
                
                # Call logger with only supported kwargs
                getattr(logger, level.lower())(formatted_message, **special_kwargs)
        except Exception as e:
            # Fallback to simple logging if there's any issue
            try:
                getattr(logger, level.lower())(f"{message} - {str(kwargs)}")
            except:
                # Last resort - use print
                print(f"LOGGING ERROR: {level.upper()}: {message} - {kwargs}")