from collections.abc import Callable
from typing import TypeVar

from PyQt6.QtCore import QObject, QThread, pyqtSignal

T = TypeVar("T")


class _Worker(QObject):
    result_ready = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, fn: Callable[[], object]) -> None:
        super().__init__()
        self._fn = fn

    def run(self) -> None:
        try:
            self.result_ready.emit(self._fn())
        except Exception as exc:  # surfaced to the GUI thread via signal
            self.error.emit(str(exc))


class TaskRunner(QObject):
    """Runs callables on background threads. Results return via callbacks on
    the GUI thread (cross-thread signal connections are queued automatically).
    Only callbacks may touch widgets — never the callable itself."""

    def __init__(self) -> None:
        super().__init__()
        self._active: list[tuple[QThread, _Worker]] = []

    def start(
        self,
        fn: Callable[[], T],
        on_result: Callable[[T], None],
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        thread = QThread()
        worker = _Worker(fn)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.result_ready.connect(lambda value: on_result(value))
        if on_error is not None:
            worker.error.connect(on_error)
        worker.result_ready.connect(lambda *_: self._cleanup(thread, worker))
        worker.error.connect(lambda *_: self._cleanup(thread, worker))
        self._active.append((thread, worker))
        thread.start()

    def _cleanup(self, thread: QThread, worker: _Worker) -> None:
        thread.quit()
        thread.wait()
        self._active = [pair for pair in self._active if pair != (thread, worker)]
