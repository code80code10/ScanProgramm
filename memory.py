import json
import os
import logging
from datetime import datetime
from paths import BASE_DIR

MEMORY_FILE = os.path.join(BASE_DIR, 'memory.json')
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

def load_memory():
    try:
        if not os.path.exists(MEMORY_FILE):
            logging.info("Файл памяти не найден, создаю новый...")
            return create_default_memory()
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            memory = json.load(f)
        return memory
    except Exception as e:
        logging.error(f'Ошибка загрузки памяти: {e}')
        return create_default_memory()
def save_memory(memory):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
        logging.info(f'Память сохранена в {MEMORY_FILE}')
        return True
    except Exception as e:
        logging.error(f'Ошибка сохранения памяти: {e}')
        return False
def create_default_memory():
    default_memory = {
        'corrections': [],
        'positions': {},
        'last_processed': {
            'date': None,
            'company': None,
            'number': None
        }
    }
    save_memory(default_memory)
    return default_memory
def add_correction(wrong_value, correct_value, context, field_type):
    """wrong value: что программа нашла неправильно, correct_value:что
    пользователь исправил, context: текст вокруг найденного значения(50
    символов до и после), field_type: тип поля(date/number/company)"""
    memory = load_memory()
    correction = {
        'wrong': wrong_value,
        'correct': correct_value,
        'context': context,
        'field_type': field_type,
        'timestamp': datetime.now().isoformat()
    }
    memory['corrections'].append(correction)
    if len(memory['corrections']) > 1000:
        memory['corrections'] = memory['corrections'][-1000:]
    save_memory(memory)
    logging.info(f'Добавлено исправление: {wrong_value} -> {correct_value}')
def check_correction(text, field_type):
    memory = load_memory()
    for correction in memory['corrections']:
        if correction['field_type'] != field_type:
            continue
        if correction['context'] in text:
            logging.info(f'Найдено исправление в памяти: '
                         f'{correction['wrong']} -> {correction["correct"]}')
            return correction['correct']
    return None
def update_last_processed(date, company, number):
    memory = load_memory()
    memory['last_processed'] = {
        'date': date,
        'company': company,
        'number': number
    }
    save_memory(memory)
    logging.info(f'Обновляем данные последнего файла: дата={date}'
                 f' компания={company} номер={number}')
def get_last_date():
    memory = load_memory()
    return memory.get('last_processed', {}).get('date')
def save_position(field_type, doc_type, position_info):
    """
    :param field_type: date, number, company
    :param doc_type: накладная, акт, счет-фактура и тд
    :param position_info: {'after': 'поставщик:', 'zone': 'first_10_lines'}
    """
    memory = load_memory()
    if doc_type not in memory:
        memory['positions'][doc_type] = {}
    memory['positions'][doc_type][field_type] = position_info
    save_memory(memory)
    logging.info(f'Сохранена позиция для {field_type} в {doc_type}')
def get_position(field_type, doc_type):
    memory = load_memory()
    return memory.get('positions', {}).get(doc_type, {}).get(field_type)