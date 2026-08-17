import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paths import BASE_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(BASE_DIR, 'scanbot.log'),
                            encoding='utf-8'),
    ]
)

def main():
    from main_widnow import MainWindow
    app = MainWindow()

    config_path = os.path.join(BASE_DIR, 'config.json')
    if not os.path.exists(config_path):
        logging.info('Первый запуск показывается окно настроек')
        from setup_window import show_setup_window
        success = show_setup_window(app.root)
        if not success:
            logging.info('Настройки не сохранены, выходим')
            app.root.destroy()
            return
    app.run()

if __name__ == '__main__':
    main()