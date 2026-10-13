"""Production-grade error handling and logging"""

import logging
import sys
import traceback
from typing import Optional, Any
import streamlit as st
from datetime import datetime
import json
import os

# Configure logging
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'app.log')),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base exception for application"""
    def __init__(self, message: str, error_code: str = "APP_ERROR", details: Optional[dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)


class DataFetchException(AppException):
    """Exception for data fetching failures"""
    def __init__(self, source: str, message: str, details: Optional[dict] = None):
        super().__init__(
            f"Failed to fetch data from {source}: {message}",
            error_code="DATA_FETCH_ERROR",
            details={**(details or {}), "source": source}
        )


class ModelException(AppException):
    """Exception for ML model failures"""
    def __init__(self, model_name: str, message: str, details: Optional[dict] = None):
        super().__init__(
            f"Model {model_name} error: {message}",
            error_code="MODEL_ERROR",
            details={**(details or {}), "model": model_name}
        )


def handle_exception(exc: Exception, context: str = "Unknown operation") -> None:
    """
    Handle exceptions gracefully with logging and user-friendly messages
    
    Args:
        exc: The exception to handle
        context: Description of what was being done
    """
    logger.error(f"Error in {context}: {str(exc)}", exc_info=True)
    
    # Create error log entry
    error_entry = {
        'timestamp': datetime.now().isoformat(),
        'context': context,
        'error_type': type(exc).__name__,
        'message': str(exc),
        'traceback': traceback.format_exc()
    }
    
    # Log to file
    error_log_path = os.path.join(LOG_DIR, 'errors.json')
    try:
        if os.path.exists(error_log_path):
            with open(error_log_path, 'r') as f:
                errors = json.load(f)
        else:
            errors = []
        
        errors.append(error_entry)
        with open(error_log_path, 'w') as f:
            json.dump(errors[-100:], f, indent=2)  # Keep last 100 errors
    except Exception as e:
        logger.error(f"Failed to log error: {e}")
    
    # Show user-friendly error
    if isinstance(exc, AppException):
        st.error(f"{exc.message}\n\nError Code: {exc.error_code}")
    elif isinstance(exc, ConnectionError):
        st.error("Connection error: Unable to reach external services. Please check your internet connection.")
    elif isinstance(exc, ValueError):
        st.error(f"Invalid input: {str(exc)}")
    elif isinstance(exc, TimeoutError):
        st.error("Request timed out. Please try again or select a smaller date range.")
    else:
        st.error(f"An unexpected error occurred in {context}. Please try refreshing the page or contact support.")
    
    # Show technical details in expander for debugging
    with st.expander("Technical Details (click to expand)"):
        st.code(traceback.format_exc(), language="python")


@st.cache_resource
def get_logger(name: str = "app"):
    """Get or create logger instance"""
    return logging.getLogger(name)


def log_user_action(action: str, details: Optional[dict] = None) -> None:
    """Log user actions for audit trail"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'details': details or {}
    }
    logger.info(f"USER_ACTION: {json.dumps(log_entry)}")


def log_performance_metric(metric_name: str, value: float, unit: str = "ms") -> None:
    """Log performance metrics"""
    logger.info(f"PERFORMANCE: {metric_name}={value}{unit}")


def create_error_report() -> str:
    """Generate error report for support"""
    error_log_path = os.path.join(LOG_DIR, 'errors.json')
    
    report = f"""
    ERROR REPORT - {datetime.now().isoformat()}
    {'='*50}
    
    Python Version: {sys.version}
    Platform: {sys.platform}
    
    Recent Errors:
    """
    
    if os.path.exists(error_log_path):
        try:
            with open(error_log_path, 'r') as f:
                errors = json.load(f)
            for error in errors[-5:]:  # Last 5 errors
                report += f"\n{error['timestamp']}: {error['error_type']} - {error['message']}"
        except Exception as e:
            report += f"\nFailed to read error log: {e}"
    
    return report
