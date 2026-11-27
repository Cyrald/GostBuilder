"""
Команды запуска рабочих подпроцессов и единая точка входа ``--worker``.

Из исходников воркер запускается как скрипт: ``python tools/<воркер>.py``.
После упаковки PyInstaller/Nuitka ``sys.executable`` — это сам exe
приложения, а .py-файлов рядом нет, поэтому воркер запускается как
``<приложение>.exe --worker <имя> [аргументы]``; main.py распознаёт этот
аргумент до загрузки GUI и передаёт управление run_worker().
"""
import sys
from pathlib import Path
from typing import List, Sequence

WORKER_FLAG = "--worker"

_TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
_SCRIPTS = {
    "pipeline": _TOOLS_DIR / "_pipeline_worker.py",
    "diagram": _TOOLS_DIR / "_diagram_worker.py",
    "installer": _TOOLS_DIR / "install_pandoc.py",
}


def is_frozen() -> bool:
    """True, если программа собрана в exe (PyInstaller задаёт sys.frozen, Nuitka — __compiled__)."""
    return bool(getattr(sys, "frozen", False)) or "__compiled__" in globals()


def worker_command(name: str, *args: str, unbuffered: bool = False) -> List[str]:
    """
    Командная строка для запуска воркера *name* с аргументами *args*.
    unbuffered добавляет ``-u`` при запуске из исходников; в exe вместо
    него действует PYTHONUNBUFFERED из окружения.
    """
    if name not in _SCRIPTS:
        raise ValueError(f"Неизвестный воркер: {name!r}")
    if is_frozen():
        return [sys.executable, WORKER_FLAG, name, *args]
    interpreter = [sys.executable, "-u"] if unbuffered else [sys.executable]
    return [*interpreter, str(_SCRIPTS[name]), *args]


def run_worker(argv: Sequence[str]) -> int:
    """
    Выполняет воркер, указанный в argv[0], с остальными аргументами;
    возвращает код завершения. Неизвестное имя — код 2.
    """
    if not argv or argv[0] not in _SCRIPTS:
        known = ", ".join(sorted(_SCRIPTS))
        print(f"Использование: {WORKER_FLAG} {{{known}}} [аргументы]", file=sys.stderr)
        return 2
    name, rest = argv[0], list(argv[1:])
    if name == "installer":
        from tools import install_pandoc
        return install_pandoc.main(rest)
    sys.argv = [str(_SCRIPTS[name]), *rest]
    if name == "pipeline":
        from tools import _pipeline_worker
        _pipeline_worker.main()
    else:
        from tools import _diagram_worker
        _diagram_worker.main()
    return 0
