import sys
import threading
import traceback
import logging
import os
from datetime import datetime

LOG_FILE = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), "YouTubeMusicPro", "logs", "error.log")

_app_instance = None

def set_app_instance(app):
    global _app_instance
    _app_instance = app

def setup_global_error_handling():
    # Налаштовуємо теку для логів
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    # Конфігурація модуля logging
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Обробка для головного потоку
    def global_excepthook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logging.error(f"Uncaught Exception (Main Thread):\n{err_msg}")
        _trigger_error_dialog("Критична помилка програми", err_msg)

    # Обробка для фонових потоків (наприклад завантаження пісні)
    def thread_excepthook(args):
        err_msg = "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
        thread_name = args.thread.name if args.thread else "Unknown Thread"
        logging.error(f"Uncaught Exception (Thread: {thread_name}):\n{err_msg}")
        _trigger_error_dialog("Помилка у фоновому процесі", err_msg)

    sys.excepthook = global_excepthook
    threading.excepthook = thread_excepthook

def _trigger_error_dialog(title, error_details):
    from ui.error_dialog import show_error_window
    global _app_instance
    
    # Якщо головне вікно ще існує і працює, викликаємо безпечно через after()
    if _app_instance and hasattr(_app_instance, 'after'):
        _app_instance.after(0, lambda: show_error_window(title, error_details, LOG_FILE))
    else:
        # Якщо головного вікна ще немає або воно вмерло
        show_error_window(title, error_details, LOG_FILE, is_standalone=True)
