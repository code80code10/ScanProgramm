import time
import os
import logging

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from memory import add_correction
from parser import parse_document
from config import load_config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

stats = {
    'processed': 0,
    'auto_saved': 0,
    'need_check': 0
}

class ScanHandler(FileSystemEventHandler):

    def __init__(self, config, main_window=None):
      self.config = config
      self.processing = set()
      self.main_window = main_window
    def on_created(self, event):
        logging.info(f'СОБЫТИЕ: {event.event_type} - {event.src_path}')
        if event.is_directory:
            logging.info('Это папка, игнорируем')
            return
        file_path = event.src_path
        if not file_path.lower().endswith('.pdf'):
            logging.info(f'Пропускаем не-PDF: {file_path}')
            return
        filename = os.path.basename(file_path)
        if filename.startswith('~') or filename.startswith('.'):
            logging.info(f'Пропускаем временный файл: {filename}')
            return
        if file_path in self.processing:
            logging.info('Уже обрабатывается,игнориурем')
            return
        logging.info(f'Обнаружен новый PDF: {filename}')
        if not self._wait_for_file_ready(file_path):
            logging.warning(f'Файл не готов к обработке: {filename}')
            return
        self.processing.add(file_path)
        try:
            self._process_file(file_path)
        finally:
            self.processing.discard(file_path)

    def on_modified(self, event):
        logging.info(f'СОБЫТИЕ: {event.event_type} - {event.src_path}')

    def _wait_for_file_ready(self, file_path, timeout=10):
        last_size = -1
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                current_size = os.path.getsize(file_path)
                if current_size == last_size and current_size > 0:
                    time.sleep(1)
                    return True
                last_size = current_size
                time.sleep(0.5)
            except OSError:
                time.sleep(0.5)
        return False
    def _process_file(self, file_path):
        from ocr_engine import extract_text_from_pdf
        from gui import show_verification_window
        from parser import is_valid_document
        from memory import add_correction
        from notifier import show_notification

        logging.info(f'Начинаем обработку: {os.path.basename(file_path)}')
        try:
            text = extract_text_from_pdf(file_path)
            if not text:
                logging.error(f"Не удалось извлечь текст из {file_path}")
                return

            logging.info(f"Текст извлечён: {len(text)} символов")
            is_doc = is_valid_document(text)
            logging.info(f"is_valid_document: {is_doc}")
            if not is_doc:
                logging.warning(f"Файл не похож на документ")

                def open_verification():
                    logging.info(
                        "Открываю окно проверки для неподходящего файла")
                    empty_result = {
                        'company': None,
                        'number': None,
                        'date': None,
                        'confidence': 0,
                        'details': {
                            'company_source': 'not_found',
                            'company_score': 0,
                            'number_source': 'not_found',
                            'number_score': 0,
                            'date_source': 'not_found',
                            'date_score': 0,
                        }
                    }
                    def on_save(user_data):
                        if user_data.get('company') or user_data.get(
                                'number') or user_data.get('date'):
                            self._save_with_data(file_path, user_data)
                            if user_data.get('learn'):
                                self._learn_from_user(text, empty_result,
                                                      user_data)
                            logging.info(
                                f"Пользователь сохранил: {user_data}")

                        if self.main_window:
                            self.main_window.after(0,
                                                   self.main_window.update_stats,
                                                   1, 0, 1)

                    def on_skip():
                        logging.info(f"Пользователь пропустил файл")
                        if self.main_window:
                            self.main_window.after(0,
                                                   self.main_window.update_stats,
                                                   1, 0, 1)

                    show_verification_window(
                        self.main_window,
                        file_path,
                        empty_result,
                        on_save,
                        on_skip
                    )


                show_notification(
                    title="Нужна проверка",
                    message=f"Файл {os.path.basename(file_path)} не похож на соответсвующий.\nОткрыть окно проверки?",
                    on_click=lambda: self.main_window.after(0,
                                                            open_verification) if self.main_window else None,
                    auto_hide_seconds=15
                )
                return

            result = parse_document(text, self.config)
            logging.info(
                f"парсинг: компания={result['company']}, номер={result['number']}, дата={result['date']}, уверенность={result['confidence']}%")

            if not result['company'] and not result['number'] and not result[
                'date']:
                logging.warning(
                    f"Не удалось извлечь данные — показываем окно проверки")

                def open_verification():
                    logging.info("Открываю окно проверки (данные не найдены)")

                    def on_save(user_data):
                        if user_data.get('company') or user_data.get('number') or user_data.get('date'):
                            self._save_with_data(file_path, user_data)
                            if user_data.get('learn'):
                                self._learn_from_user(text, result, user_data)
                            logging.info(f"Пользователь сохранил: {user_data}")

                        if self.main_window:
                            self.main_window.after(0, self.main_window.update_stats, 1, 0, 1)

                    def on_skip():
                        logging.info(f"Пользователь пропустил файл")
                        if self.main_window:
                            self.main_window.after(0, self.main_window.update_stats, 1, 0, 1)

                    show_verification_window(
                        self.main_window,
                        file_path,
                        result,
                        on_save,
                        on_skip
                    )

                show_notification(
                    title="Данные не найдены",
                    message=f"Файл: {os.path.basename(file_path)}\nНе удалось извлечь данные автоматически.",
                    on_click=lambda: self.main_window.after(0, open_verification) if self.main_window else None,
                    auto_hide_seconds=15
                )
                return

            if result['confidence'] >= 80:
                logging.info(f"Высокая уверенность ({result['confidence']}%) — сохраняем")
                self._save_silently(file_path, result)

                if self.main_window:
                    self.main_window.after(0, self.main_window.update_stats, 1, 1, 0)
            else:
                logging.info(f"️ Низкая уверенность ({result['confidence']}%) — показываем уведомление")

                def open_verification():
                    logging.info("Открываем окно проверки (низкая "
                                 "уверенность)")

                    def on_save(user_data):
                        logging.info(f"ользователь сохранил: {user_data}")
                        if user_data.get('learn'):
                            self._learn_from_user(text, result, user_data)
                        self._save_with_data(file_path, user_data)

                        if self.main_window:
                            self.main_window.after(0, self.main_window.update_stats, 1, 0, 1)

                    def on_skip():
                        logging.info(f"Пользователь пропустил файл")
                        if self.main_window:
                            self.main_window.after(0, self.main_window.update_stats, 1, 0, 1)

                    show_verification_window(
                        self.main_window,
                        file_path,
                        result,
                        on_save,
                        on_skip
                    )

                show_notification(
                    title="Нужна проверка",
                    message=f"Файл: {os.path.basename(file_path)}\nУверенность: {result['confidence']}%",
                    on_click=lambda: self.main_window.after(0, open_verification) if self.main_window else None,
                    auto_hide_seconds=15
                )

        except Exception as e:
            logging.error(f"Ошибка обработки {file_path}: {e}")
            import traceback
            traceback.print_exc()

    def _save_silently(self, file_path, result):
        from renamer import move_and_rename

        data = {
            'company': result.get('company'),
            'number': result.get('number'),
            'date': result.get('date')
        }

        output_folder = self.config.get('output_folder')
        new_path = move_and_rename(file_path, data, output_folder)

        if new_path:
            logging.info(f'Файл перемещен: {os.path.basename(new_path)}')
        else:
            logging.error(f'Не удалось сохранить файл: {os.path.basename(new_path)}')

    def _save_with_data(self, file_path, user_data):
        """Сохраняет сданными пользователя"""

        from renamer import move_and_rename

        data = {
            'company': user_data.get('company'),
            'number': user_data.get('number'),
            'date': user_data.get('date')
        }
        output_folder = self.config.get('output_folder')
        new_path = move_and_rename(file_path, data, output_folder)
        if new_path:
            logging.info(f'Файл перемещен: {os.path.basename(new_path)}')
        else:
            logging.error(f'Не удалось сохранить файл: '
                          f'{os.path.basename(file_path)}')

    def _learn_from_user(self, original_text, parsed_data, user_data):
        """Запоминает исправления от пользователя"""
        from memory import add_correction
        if (user_data.get('company') and user_data['company'] !=
                parsed_data.get('company')):
            add_correction(
                wrong_value=parsed_data.get('company') or '',
                correct_value=user_data['company'],
                context=original_text[:200],
                field_type='company'
            )
        if (user_data.get('number') and user_data['number'] !=
                parsed_data.get('number')):
            add_correction(
                wrong_value=parsed_data.get('number') or '',
                correct_value=user_data['number'],
                context=original_text[:200],
                field_type='number'
            )
        if (user_data.get('date') and user_data['date'] !=
                parsed_data.get('date')):
            add_correction(
                wrong_value=parsed_data.get('date') or '',
                correct_value=user_data['date'],
                context=original_text[:200],
                field_type='date'
            )

    def _print_result(self, file_path, result):
        print(f'ФАЙЛ: {os.path.basename(file_path)}')
        print(f'Компания: {result['company']}')
        print(f'Источник: {result['details']['company_source']} {result['details']['company_score']}%')
        print(f'Номер: {result['number']}')
        print(f'Источник: {result['details']['number_source']} {result['details']['number_score']}%')
        print(f'Дата: {result['date']}')
        print(f'Источник: {result['details']['date_source']} {result['details']['date_score']}%')
        print(f'УВЕРЕННОСТЬ: {result['confidence']}%')
        if result['confidence'] >= 80:
            print('Сохраняем по-тихому')
        else:
            print('Нужно уведомление')

def start_watching(scan_folder=None, main_window=None):
    print(f'\n[watcher] запускаем start_watching()')
    print(f'[watcher] scan_folder: {scan_folder}')
    config = load_config()
    if scan_folder is None:
        scan_folder = config.get('scan_folder',
                                 'C:\\Scans')
    print(f'[watcher] scan_folder: {scan_folder}')
    if not os.path.exists(scan_folder):
        print(f'[watcher] Папка сканов не найдена: {scan_folder}')
        print(f'[watcher] Создаю новую папку...')
        os.makedirs(scan_folder, exist_ok=True)

    print(f'[watcher] Слежу за папкой: {scan_folder}')
    print('[watcher] Чтобы остановить - нажми Ctrl+C')

    handler = ScanHandler(config, main_window=main_window)
    observer = Observer()
    observer.schedule(handler, scan_folder, recursive=False)
    print(f'[watcher] Observer создан, запускаем...')
    observer.start()
    print(f'[watcher] Observer запущен')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info(f'Останавливаем слежение...')
        observer.stop()
    observer.join()
    logging.info('Watcher остановлен')
if __name__ == '__main__':
    start_watching()
