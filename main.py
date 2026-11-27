"""
Точка входа GostBuilder: настраивает журналирование, сканирует ресурсы
(титульные листы и профили ГОСТ) и запускает главное окно.

``main.py --worker <имя> [аргументы]`` запускает рабочий подпроцесс
(pipeline, diagram, installer) без GUI — так воркеры работают и после
упаковки в exe (см. core/workers.py).
"""
import sys

# Проверка выполняется до импорта модулей проекта: на старом Python они
# упали бы с SyntaxError/TypeError без объяснения причины.
if sys.version_info < (3, 10):
    sys.exit("GostBuilder требует Python 3.10 или новее (сейчас %d.%d)." % sys.version_info[:2])

import logging


def main() -> None:
    """
    Запускает приложение.

    Пока окно не создано, предупреждения копятся в буфере; после создания окна
    они переносятся в консоль журнала GUI, а дальнейшие сообщения уровня
    WARNING и выше направляются туда напрямую. Консоль GUI дублирует каждое
    сообщение в stdout/stderr, поэтому вывод виден и в окне CMD.

    Наличие pandoc/pandoc-crossref здесь не проверяется: окно делегирует это
    tools/install_pandoc.py (см. gui/pandoc_setup.py).
    """
    # GUI импортируется здесь, а не на уровне модуля, чтобы воркеры,
    # запущенные через --worker, не загружали tkinter.
    from core.config import ProjectConfig
    from core.logging_utils import StartupLogBuffer
    from gui.components import LogHandler
    from gui.app import MainWindow

    startup_logs = StartupLogBuffer()
    logging.basicConfig(
        level=logging.WARNING,
        handlers=[startup_logs],
        force=True,
    )
    log_format = logging.Formatter("%(levelname)s: %(message)s")

    cfg = ProjectConfig()

    titles = [t.name  for t in cfg.scan_templates("titles")]
    styles = [profile.name for profile in cfg.scan_gost_profiles()]

    app = MainWindow(titles=titles, styles=styles, cfg=cfg)
    gui_log_handler = LogHandler(app.console)
    gui_log_handler.setLevel(logging.WARNING)
    gui_log_handler.setFormatter(log_format)

    # Подменяем буферный обработчик на консоль GUI и выводим в неё всё,
    # что успело накопиться во время сканирования ресурсов.
    root_logger = logging.getLogger()
    root_logger.removeHandler(startup_logs)
    root_logger.addHandler(gui_log_handler)
    for record in startup_logs.records:
        gui_log_handler.handle(record)
    startup_logs.records.clear()

    # Проверка pandoc запускается после отрисовки окна, чтобы при ошибке
    # пользователю сразу можно было предложить автоматическую или ручную установку.
    app.after(100, app.pandoc_setup.start_check)
    app.mainloop()


if __name__ == "__main__":
    from core.workers import WORKER_FLAG, run_worker

    if len(sys.argv) > 1 and sys.argv[1] == WORKER_FLAG:
        sys.exit(run_worker(sys.argv[2:]))
    main()
