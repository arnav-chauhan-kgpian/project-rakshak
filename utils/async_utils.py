
import time
import functools
import concurrent.futures
from typing import Callable, Any, Dict, List

def retry_with_backoff(retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0):
    """
    Decorator for exponential backoff retries.
    
    Args:
        retries: Maximum number of retries before failing.
        initial_delay: Initial wait time in seconds.
        backoff_factor: Multiplier for wait time after each failure.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == retries:
                        print(f"    ❌ Final attempt failed for {func.__name__}: {e}")
                        raise last_exception
                    
                    print(f"    ⚠ Attempt {attempt+1}/{retries} failed for {func.__name__}: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= backoff_factor
            
            raise last_exception
        return wrapper
    return decorator

def run_parallel_tasks(tasks: Dict[str, Callable]) -> Dict[str, Any]:
    """
    Execute multiple callable tasks in parallel using threads.
    
    Args:
        tasks: Dictionary mapping task_name -> callable (function with no args, usually lambda)
        
    Returns:
        Dictionary mapping task_name -> result
    """
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        # Submit all tasks
        future_to_name = {executor.submit(func): name for name, func in tasks.items()}
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_name):
            name = future_to_name[future]
            try:
                data = future.result()
                results[name] = data
            except Exception as e:
                print(f"    ⚠ Parallel task '{name}' generated an exception: {e}")
                results[name] = None  # Fail gracefully
                
    return results
