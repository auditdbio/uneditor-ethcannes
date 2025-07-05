from asyncio import Semaphore, Lock, sleep, get_running_loop
from os import getenv

class RLSemaphore(Semaphore):
    def __init__(self, value=None, min_interval=None, error_tolerance=0.05, slowdown_factor=1.2):
        
        if value is None:
            value = int(getenv("MAX_CONCURRENCY", "200"))
        
        if min_interval is None:
            min_interval = float(getenv("RATE_LIMIT_SECONDS", "0.2"))

        super().__init__(value)
        if min_interval < 0:
            raise ValueError("Rate limit interval 'min_interval' must be non-negative.")
        self.min_interval = min_interval
        self.rate_limit_lock = Lock()
        self.last_allowed_start_time = -float('inf')
        self.error_tolerance = error_tolerance
        self.slowdown_factor = slowdown_factor
        # slowdown_factor^error_tolerance * speedup_factor^(1-error_tolerance) = 1
        self.speedup_factor = slowdown_factor ** (-error_tolerance/(1.0 - error_tolerance))
        

    async def __aenter__(self):
        await super().acquire()
        sleep_needed = 0.0
        async with self.rate_limit_lock:
            current_actual_time = get_running_loop().time()
            target_start_time = max(current_actual_time, self.last_allowed_start_time + self.min_interval)
            sleep_needed = target_start_time - current_actual_time
            self.last_allowed_start_time = target_start_time
        
        if sleep_needed > 0:
            await sleep(sleep_needed)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.release()


    # equilibrium at 5% failed requests
    def slowdown(self):
        self.min_interval *= self.slowdown_factor

    def speedup(self):
        self.min_interval *= self.speedup_factor 