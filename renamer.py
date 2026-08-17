import os
import shutil
import logging
import re
from config import load_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def clean_for_filename(text):
    """Очищает текст, использует правило из config.json"""
    if not text:
        return ''

    config = load_config()
    cleanup = config.get('filename_cleanup', {
        '/': '.',
        ':': '-',
        '*': '',
        '?': '',
        '"': ''
    })

    for old_char, new_char in cleanup.items():
        text = text.replace(old_char, new_char)

    text = re.sub(r'\s+', " ", text).strip()

    text = text.strip('.')
    return text

def build_filename(data):
    company = data.get('company') or ''
    number = data.get('number') or ''
    date = data.get('date') or ''

    company = clean_for_filename(company)
    number = clean_for_filename(number)
    date = clean_for_filename(date)

    filename = f'{company} №{number} {date}.pdf'
    return filename

def get_unique_filename(output_folder, filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(output_folder, new_filename)):
        new_filename = f'{base}_{counter}{ext}'
        counter += 1
    return new_filename

def move_and_rename(source_path, data, output_folder=None):
    """
    :param source_path: путь к исходному ПДФ
    :param data: словарь с компанией, номером и датой
    :param output_folder: куда переместить
    возвращает путь к новому файлу, если ошибка - None
    """
    config = load_config()

    if output_folder is None:
        output_folder = config.get('output_folder', 'C:\\Documents\\Processed')
    try:
        os.makedirs(output_folder, exist_ok=True)
    except Exception as e:
        logging.error(f'Не удалось создать папку {output_folder}: {e}')
        return None
    if not os.path.exists(source_path):
        logging.error(f'Исходный файл не найдн: {source_path}')
        return None

    new_filename = build_filename(data)

    new_filename = get_unique_filename(output_folder, new_filename)

    new_path = os.path.join(output_folder, new_filename)

    try:
        shutil.move(source_path, new_path)
        logging.info(f'Файл сохранен: {new_filename}')
        return new_path
    except Exception as e:
        logging.error(f'Не удалось переместить файл: {e}')
        return None

def delete_file(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f'Файл удален: {os.path.basename(file_path)}')
            return True
    except Exception as e:
        logging.error(f'Не удалось удалить файл: {e}')
    return False
