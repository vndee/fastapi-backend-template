import logging
import time
import traceback
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, Generator, Optional

from opentelemetry import trace

REQUEST_ID: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
USER_ID: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class LogLevel(Enum):
    """Standardized log levels"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """Log categories for better organization"""

    AUTH = "auth"
    API = "api"
    DATABASE = "database"
    BUSINESS = "business"
    SECURITY = "security"
    PERFORMANCE = "performance"
    SYSTEM = "system"


@dataclass
class LogContext:
    """Structured log context"""

    operation: str
    category: LogCategory
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    duration_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, filtering None values and converting enums to strings"""
        result = {}
        for k, v in asdict(self).items():
            if v is not None:
                # Convert LogCategory enum to string value for OpenTelemetry compatibility
                if k == "category" and isinstance(v, LogCategory):
                    result[k] = v.value
                else:
                    result[k] = v
        return result


class SensitiveDataFilter:
    """Filter sensitive data from logs"""

    SENSITIVE_KEYS = {
        "password",
        "token",
        "secret",
        "key",
        "authorization",
        "cookie",
        "session",
        "credentials",
        "auth",
        "jwt",
        "refresh_token",
        "access_token",
        "api_key",
    }

    @classmethod
    def filter_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively filter sensitive data from dictionary"""
        if not isinstance(data, dict):
            return data

        filtered: Dict[str, Any] = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in cls.SENSITIVE_KEYS):
                filtered[key] = "[FILTERED]"
            elif isinstance(value, dict):
                filtered[key] = cls.filter_dict(value)
            elif isinstance(value, (list, tuple)):
                filtered[key] = [
                    cls.filter_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                filtered[key] = value
        return filtered


class Logger:
    """Enhanced logger with industry-standard features"""

    def __init__(self, name: str, category: LogCategory = LogCategory.SYSTEM):
        self.logger = logging.getLogger(name)
        self.category = category
        self.name = name

    def _should_log(self, level: LogLevel) -> bool:
        """Check if we should log at this level (performance optimization)"""
        return self.logger.isEnabledFor(getattr(logging, level.value))

    def _get_trace_context(self) -> Dict[str, str]:
        """Get OpenTelemetry trace context"""
        current_span = trace.get_current_span()
        if current_span.is_recording():
            span_context = current_span.get_span_context()
            return {
                "trace_id": f"{span_context.trace_id:032x}",
                "span_id": f"{span_context.span_id:016x}",
            }
        return {"trace_id": "0", "span_id": "0"}

    def _build_log_context(self, operation: str, **kwargs: Any) -> LogContext:
        """Build structured log context"""
        trace_ctx = self._get_trace_context()

        return LogContext(
            operation=operation,
            category=self.category,
            request_id=REQUEST_ID.get(),
            user_id=USER_ID.get(),
            trace_id=trace_ctx["trace_id"],
            span_id=trace_ctx["span_id"],
            metadata=SensitiveDataFilter.filter_dict(kwargs) if kwargs else None,
        )

    def _log(
        self, level: LogLevel, message: str, context: LogContext, exc_info: bool = False
    ) -> None:
        """Internal logging method"""
        if not self._should_log(level):
            return

        log_data = context.to_dict()
        log_data.update({"logger": self.name, "level": level.value})

        self.logger.log(
            getattr(logging, level.value), message, extra=log_data, exc_info=exc_info
        )

    # Public logging methods
    def info(self, message: str, operation: str, **kwargs: Any) -> None:
        """Log info message with structured context"""
        context = self._build_log_context(operation, **kwargs)
        self._log(LogLevel.INFO, message, context)

    def warning(self, message: str, operation: str, **kwargs: Any) -> None:
        """Log warning message with structured context"""
        context = self._build_log_context(operation, **kwargs)
        self._log(LogLevel.WARNING, message, context)

    def error(
        self,
        message: str,
        operation: str,
        error: Optional[Exception] = None,
        **kwargs: Any,
    ) -> None:
        """Log error message with structured context and exception details"""
        context = self._build_log_context(operation, **kwargs)

        if error:
            if context.metadata is None:
                context.metadata = {}
            context.metadata.update(
                {"error_type": type(error).__name__, "error_message": str(error)}
            )

        self._log(LogLevel.ERROR, message, context, exc_info=bool(error))

    def debug(self, message: str, operation: str, **kwargs: Any) -> None:
        """Log debug message with structured context"""
        if not self._should_log(LogLevel.DEBUG):
            return
        context = self._build_log_context(operation, **kwargs)
        self._log(LogLevel.DEBUG, message, context)

    def critical(
        self,
        message: str,
        operation: str,
        error: Optional[Exception] = None,
        **kwargs: Any,
    ) -> None:
        """Log critical message with structured context"""
        context = self._build_log_context(operation, **kwargs)

        if error:
            if context.metadata is None:
                context.metadata = {}
            context.metadata.update(
                {
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "traceback": traceback.format_exc() if error else None,
                }
            )

        self._log(LogLevel.CRITICAL, message, context, exc_info=bool(error))


class TimedLogger:
    """Logger with timing capabilities"""

    def __init__(self, logger: Logger):
        self.logger = logger
        self.start_time: Optional[float] = None
        self.operation: Optional[str] = None
        self.metadata: Dict[str, Any] = {}

    def start(self, operation: str, **metadata: Any) -> "TimedLogger":
        """Start timing an operation"""
        self.start_time = time.time()
        self.operation = operation
        self.metadata = metadata
        return self

    def stop(
        self,
        message: str,
        level: LogLevel = LogLevel.INFO,
        error: Optional[Exception] = None,
    ) -> float:
        """Stop timing and log result"""
        if self.start_time is None:
            raise ValueError("Timer not started")

        duration_ms = (time.time() - self.start_time) * 1000

        log_kwargs = {**self.metadata, "duration_ms": duration_ms}

        if level == LogLevel.ERROR and error:
            self.logger.error(
                message, self.operation or "unknown", error=error, **log_kwargs
            )
        elif level == LogLevel.WARNING:
            self.logger.warning(message, self.operation or "unknown", **log_kwargs)
        elif level == LogLevel.INFO:
            self.logger.info(message, self.operation or "unknown", **log_kwargs)
        elif level == LogLevel.DEBUG:
            self.logger.debug(message, self.operation or "unknown", **log_kwargs)

        return duration_ms


@contextmanager
def log_context(
    request_id: Optional[str] = None, user_id: Optional[str] = None
) -> Generator[None, None, None]:
    """Context manager for setting correlation IDs"""
    if request_id is None:
        request_id = str(uuid.uuid4())

    # Set context variables
    request_token = REQUEST_ID.set(request_id)
    user_token = USER_ID.set(user_id) if user_id else None

    try:
        yield
    finally:
        # Reset context variables
        REQUEST_ID.reset(request_token)
        if user_token:
            USER_ID.reset(user_token)


@contextmanager
def timed_operation(
    logger: Logger, operation: str, **metadata: Any
) -> Generator[TimedLogger, None, None]:
    """Context manager for timed operations with logging"""
    timed_logger = TimedLogger(logger).start(operation, **metadata)
    try:
        yield timed_logger
        timed_logger.stop(f"Completed {operation}", level=LogLevel.INFO)
    except Exception as e:
        timed_logger.stop(f"Failed {operation}", LogLevel.ERROR, error=e)
        raise


def get_auth_logger() -> Logger:
    """Get enhanced logger for authentication operations"""
    return Logger("auth", LogCategory.AUTH)


def get_api_logger() -> Logger:
    """Get enhanced logger for API operations"""
    return Logger("api", LogCategory.API)


def get_db_logger() -> Logger:
    """Get enhanced logger for database operations"""
    return Logger("database", LogCategory.DATABASE)


def get_business_logger() -> Logger:
    """Get enhanced logger for business logic operations"""
    return Logger("business", LogCategory.BUSINESS)


def get_security_logger() -> Logger:
    """Get enhanced logger for security operations"""
    return Logger("security", LogCategory.SECURITY)


def get_performance_logger() -> Logger:
    """Get enhanced logger for performance monitoring"""
    return Logger("performance", LogCategory.PERFORMANCE)


def get_logger(name: str, category: LogCategory = LogCategory.SYSTEM) -> Logger:
    """Get enhanced logger for any module"""
    return Logger(name, category)
