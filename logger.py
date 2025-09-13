"""
Comprehensive logging system for the Code Chat application.
Provides structured logging with console output and rotating file logging.
"""
import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class LogContext:
    """Context information for structured logging."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    request_id: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    additional_data: Optional[Dict[str, Any]] = None


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process
        }
        
        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add structured context if present
        if hasattr(record, 'context') and record.context:
            log_data["context"] = asdict(record.context)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in log_data and not key.startswith('_'):
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                              'pathname', 'filename', 'module', 'exc_info', 'exc_text',
                              'stack_info', 'lineno', 'funcName', 'created', 'msecs',
                              'relativeCreated', 'thread', 'threadName', 'processName',
                              'process', 'message', 'context']:
                    log_data["extra"] = log_data.get("extra", {})
                    log_data["extra"][key] = value
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """Custom formatter for human-readable console output."""
    
    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record for console output with colors."""
        # Add color if terminal supports it
        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            color = self.COLORS.get(record.levelname, '')
            reset = self.COLORS['RESET']
        else:
            color = reset = ''
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Build base message
        base_msg = f"{color}[{timestamp}] {record.levelname:8} {record.name:15} | {record.getMessage()}{reset}"
        
        # Add context information if present
        if hasattr(record, 'context') and record.context:
            context_parts = []
            ctx = record.context
            if ctx.component:
                context_parts.append(f"component={ctx.component}")
            if ctx.operation:
                context_parts.append(f"operation={ctx.operation}")
            if ctx.file_path:
                context_parts.append(f"file={Path(ctx.file_path).name}")
            
            if context_parts:
                base_msg += f" [{', '.join(context_parts)}]"
        
        # Add location information for errors and debug
        if record.levelno >= logging.ERROR or record.levelno == logging.DEBUG:
            base_msg += f" ({record.filename}:{record.lineno})"
        
        # Add exception information if present
        if record.exc_info:
            base_msg += f"\n{self.formatException(record.exc_info)}"
        
        return base_msg


class CodeChatLogger:
    """Main logger class for the Code Chat application."""
    
    def __init__(self, name: str = "minicli", log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
        
        self.context = LogContext()
    
    def _setup_handlers(self):
        """Set up logging handlers for console and file output."""
        
        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ConsoleFormatter())
        self.logger.addHandler(console_handler)
        
        # Rotating file handler for structured logs
        structured_log_file = self.log_dir / "structured.log"
        file_handler = logging.handlers.RotatingFileHandler(
            structured_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(file_handler)
        
        # Separate error log file
        error_log_file = self.log_dir / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(error_handler)
        
        # Performance log for timing operations
        perf_log_file = self.log_dir / "performance.log"
        perf_handler = logging.handlers.RotatingFileHandler(
            perf_log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.addFilter(lambda record: hasattr(record, 'performance'))
        perf_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(perf_handler)
    
    def set_context(self, **kwargs):
        """Set logging context for subsequent log messages."""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)
            else:
                if not self.context.additional_data:
                    self.context.additional_data = {}
                self.context.additional_data[key] = value
    
    def clear_context(self):
        """Clear the current logging context."""
        self.context = LogContext()
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log message with current context."""
        extra = kwargs.copy()
        extra['context'] = self.context
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        extra = kwargs.copy()
        extra['context'] = self.context
        self.logger.exception(message, extra=extra)
    
    def performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics."""
        extra = kwargs.copy()
        extra['context'] = self.context
        extra['performance'] = True
        extra['duration_ms'] = round(duration * 1000, 2)
        extra['operation'] = operation
        self.info(f"Performance: {operation} completed in {duration:.3f}s", **extra)
    
    def audit(self, action: str, resource: str, **kwargs):
        """Log audit trail information."""
        extra = kwargs.copy()
        extra['audit'] = True
        extra['action'] = action
        extra['resource'] = resource
        self.info(f"Audit: {action} on {resource}", **extra)
    
    def get_child_logger(self, name: str) -> 'CodeChatLogger':
        """Get a child logger with the same configuration."""
        child_name = f"{self.name}.{name}"
        child_logger = CodeChatLogger.__new__(CodeChatLogger)
        child_logger.name = child_name
        child_logger.log_dir = self.log_dir
        child_logger.logger = self.logger.getChild(name)
        child_logger.context = LogContext()
        return child_logger


class LoggerContextManager:
    """Context manager for temporary logging context."""
    
    def __init__(self, logger: CodeChatLogger, **context):
        self.logger = logger
        self.old_context = None
        self.new_context = context
    
    def __enter__(self):
        # Save current context
        self.old_context = LogContext(
            user_id=self.logger.context.user_id,
            session_id=self.logger.context.session_id,
            component=self.logger.context.component,
            operation=self.logger.context.operation,
            request_id=self.logger.context.request_id,
            file_path=self.logger.context.file_path,
            line_number=self.logger.context.line_number,
            additional_data=self.logger.context.additional_data.copy() if self.logger.context.additional_data else None
        )
        
        # Set new context
        self.logger.set_context(**self.new_context)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore old context
        self.logger.context = self.old_context


# Global logger instance
app_logger = CodeChatLogger()


def get_logger(name: str = None) -> CodeChatLogger:
    """Get a logger instance."""
    if name:
        return app_logger.get_child_logger(name)
    return app_logger


def with_context(**context):
    """Decorator for adding context to log messages within a function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with LoggerContextManager(app_logger, **context):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def log_performance(operation_name: str = None):
    """Decorator for logging function performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                app_logger.performance(op_name, duration)
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                app_logger.performance(f"{op_name} (failed)", duration, error=str(e))
                raise
        return wrapper
    return decorator


# Configure logging based on environment variables
def configure_logging():
    """Configure logging based on environment variables."""
    # Set log level from environment
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    if hasattr(logging, log_level):
        app_logger.logger.setLevel(getattr(logging, log_level))
        
        # Update console handler level
        for handler in app_logger.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.handlers.RotatingFileHandler):
                handler.setLevel(getattr(logging, log_level))
    
    # Set log directory from environment
    log_dir = os.getenv('LOG_DIR', 'logs')
    if log_dir != str(app_logger.log_dir):
        app_logger.log_dir = Path(log_dir)
        app_logger.log_dir.mkdir(exist_ok=True)


# Initialize logging configuration
configure_logging()