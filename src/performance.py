"""Performance optimization utilities for production deployment"""

import functools
import time
import logging
import hashlib
import json
from typing import Any, Callable, Optional
import streamlit as st

logger = logging.getLogger(__name__)

def cache_with_expiry(seconds: int = 300):
    """Cache decorator with time-based expiry for streamlit sessions"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Create cache key from function name and arguments
            key_data = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Check if cached data exists and is fresh
            if cache_key in st.session_state:
                cache_entry = st.session_state[cache_key]
                age = time.time() - cache_entry['timestamp']
                if age < seconds:
                    logger.debug(f"Cache hit for {func.__name__} (age: {age:.1f}s)")
                    return cache_entry['value']
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}, executing...")
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            st.session_state[cache_key] = {
                'value': result,
                'timestamp': time.time()
            }
            
            logger.debug(f"{func.__name__} executed in {execution_time:.2f}s")
            return result
        
        return wrapper
    return decorator


def measure_performance(func: Callable) -> Callable:
    """Decorator to measure and log function execution time"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} completed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {str(e)}")
            raise
    
    return wrapper


def optimize_dataframe(df) -> None:
    """In-place dataframe memory optimization"""
    import pandas as pd
    import numpy as np
    
    for col in df.columns:
        col_type = df[col].dtype
        
        # Optimize numeric columns
        if col_type != 'object':
            c_min = df[col].min()
            c_max = df[col].max()
            
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
            else:
                if c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
        else:
            # Optimize object columns to category
            df[col] = df[col].astype("category")


def clear_session_cache(age_threshold: int = 600):
    """Clear old cached items from session state"""
    current_time = time.time()
    keys_to_remove = []
    
    for key, value in st.session_state.items():
        if isinstance(value, dict) and 'timestamp' in value:
            age = current_time - value['timestamp']
            if age > age_threshold:
                keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del st.session_state[key]
        logger.debug(f"Cleared expired cache entry: {key}")
    
    if keys_to_remove:
        logger.info(f"Cleared {len(keys_to_remove)} expired cache entries")


def get_memory_usage():
    """Get current memory usage in MB"""
    import psutil
    import os
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


@measure_performance
def optimize_chart_data(df, max_points: int = 2000):
    """Reduce data points for large datasets to optimize chart rendering"""
    import pandas as pd
    
    if len(df) <= max_points:
        return df
    
    # Calculate sampling rate
    step = len(df) // max_points
    sampled_df = df.iloc[::step].copy()
    
    # Ensure last point is included
    if len(df) > 0 and not df.index[-1].isin(sampled_df.index):
        sampled_df = pd.concat([sampled_df, df.iloc[[-1]]])
    
    logger.info(f"Reduced data points from {len(df)} to {len(sampled_df)}")
    return sampled_df.sort_index()


class PerformanceMonitor:
    """Context manager for performance monitoring"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if exc_type is None:
            logger.info(f"Completed operation: {self.operation_name} ({duration:.3f}s)")
        else:
            logger.error(f"Failed operation: {self.operation_name} ({duration:.3f}s): {exc_val}")
        return False
