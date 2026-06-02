import sys
import threading
import time

VERBOSITY = 0
_current_phase = None
_step_count = 0
_last_step_name = None
_spinner_active = False


def set_verbosity(level: int):
    global VERBOSITY
    VERBOSITY = level


class Spinner:
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str):
        self._message = message
        self._stop = threading.Event()
        self._thread = None
        self._start_time = None
        self._failed = False

    def __enter__(self):
        global _spinner_active
        if VERBOSITY == 0:
            _spinner_active = True
            self._start_time = time.time()
            self._thread = threading.Thread(target=self._spin, daemon=True)
            self._thread.start()
        else:
            print(f"  → {self._message}...", flush=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _spinner_active
        self._stop.set()
        if self._thread:
            self._thread.join()
        if VERBOSITY == 0:
            _spinner_active = False
            elapsed = int(time.time() - self._start_time)
            if exc_type or self._failed:
                sys.stdout.write(f"\r  ✗ {self._message} ({elapsed}s)\n")
            else:
                sys.stdout.write(f"\r  ✓ {self._message} ({elapsed}s)\n")
            sys.stdout.flush()

    def fail(self):
        self._failed = True

    def _spin(self):
        i = 0
        while not self._stop.is_set():
            frame = self.FRAMES[i % len(self.FRAMES)]
            elapsed = int(time.time() - self._start_time)
            sys.stdout.write(f"\r  {frame} {self._message} ({elapsed}s)")
            sys.stdout.flush()
            i += 1
            self._stop.wait(0.1)


def log_phase(phase_name: str):
    global _current_phase, _step_count, _last_step_name
    _current_phase = phase_name
    _step_count = 0
    _last_step_name = None
    print(f"\n{'='*60}")
    print(f"  {phase_name}")
    print(f"{'='*60}")


def log_step(step_name: str):
    global _step_count, _last_step_name
    _step_count += 1
    _last_step_name = step_name
    if VERBOSITY >= 1:
        print(f"  [{_step_count}] {step_name}")


def log_substep(step_name: str):
    if VERBOSITY >= 1:
        print(f"    → {step_name}...")


def log_detail(message: str):
    if VERBOSITY >= 2:
        print(f"      {message}")


def log_info(message: str):
    if VERBOSITY >= 1:
        print(f"      {message}")


def log_success(message: str):
    if VERBOSITY >= 1:
        print(f"    ✅ {message}")


def log_warning(message: str):
    if _spinner_active:
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()
    print(f"    ⚠️  {message}")


def log_error(message: str):
    if _spinner_active:
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()
    print(f"    ❌ {message}")


def log_phase_complete(summary: str = None):
    if summary:
        print(f"  ✅ {summary}")
