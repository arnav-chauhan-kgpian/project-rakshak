import threading
import queue
import time
from typing import Dict, Any, List

class StreamProcessor:
    """
    Handles continuous ingestion stream with buffering/batching logic.
    Decouples data arrival from processing to prevent backpressure issues.
    """
    def __init__(self, coordinator, batch_size: int = 5, flush_interval: float = 5.0):
        self.coordinator = coordinator
        self.queue = queue.Queue()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.running = False
        self.worker_thread = None
        self.processed_count = 0
        
    def start(self):
        """Starts the background worker thread."""
        if self.running: return
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.worker_thread.start()
        print(f"  [Stream] Background processor started (Batch: {self.batch_size}, Interval: {self.flush_interval}s)")

    def stop(self):
        """Gracefully stops the worker."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2.0)
            
    def ingest(self, incident_payload: Dict[str, Any]):
        """
        Public API to ingest an item into the stream.
        Thread-safe.
        """
        self.queue.put(incident_payload)
        
    def _process_loop(self):
        """Internal loop to consume queue and flush batches."""
        buffer = []
        last_flush = time.time()
        
        while self.running:
            try:
                # 1. Fetch from queue (blocking with timeout to allow flush checks)
                try:
                    item = self.queue.get(timeout=1.0)
                    buffer.append(item)
                except queue.Empty:
                    pass
                
                # 2. Check Flush Conditions
                time_since_flush = time.time() - last_flush
                is_full = len(buffer) >= self.batch_size
                is_timeout = len(buffer) > 0 and time_since_flush >= self.flush_interval
                
                # 3. Flush if needed
                if is_full or is_timeout:
                    self._flush_buffer(buffer)
                    buffer = []
                    last_flush = time.time()
                    
            except Exception as e:
                print(f"  [Stream] Loop Error: {e}")
                time.sleep(1) # Backoff

    def _flush_buffer(self, buffer: List[Dict[str, Any]]):
        """Process the buffered batch."""
        print(f"  [Stream] Flushing batch of {len(buffer)} items...")
        
        for item in buffer:
            try:
                # Extract args and run pipeline
                # Note: We assume the dict keys match process_new_incident args
                self.coordinator.process_new_incident(**item)
                self.processed_count += 1
            except Exception as e:
                print(f"  [Stream] Failed to process item: {e}")
