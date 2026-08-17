import json
import os
import logging
from paths import BASE_DIR


CONDIG_FILE = os.path.join(BASE_DIR, 'config.json')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def load_config():
    try:
        if not os.path.exists(CONDIG_FILE):
            logging.warning(f'Файл {CONDIG_FILE} не найден, создаю новый...')
            return create_default_config()

        with open(CONDIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)

        return config

    except Exception as e:
        logging.error(f'Ошибка загрузки конфига: {e}')
        return create_default_config()

def save_config(config):
    try:
        with open(CONDIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logging.info(f'Конфиг сохранен в {CONDIG_FILE}')
        return True
    except Exception as e:
        logging.error(f'Ошибка сохранения конфига: {e}')
        return False
def create_default_config():
    default_config = {
        'scan_folder': 'C:\\Scans',
        'output_folder': 'C:\\Documents\\Processed',

        'extractions': {
            'date': {
                'max_pages_to_check': 3,
                'fallback_to_last_file': True
            },
            'company': {
                'use_context': True,
                'shorten_if_longer_than': 30
            },
            'number': {
                'take_first': True
            }
        },
        'my_company': 'ООО МояФирма',
        'exclude_directors': ['Иванов И.И.', "Петр П.П."],
        'known_companies': [],
        'use_abbreviation_search': False,
        'abbreviations': {
            'акционерное общество': "АО",
            "общество с ограниченной ответсвенностью": "ООО",
            "индивидуальный предприниматель": "ИП"
        },
        'filename_cleanup': {
            '/': '.',
            '\\': '.',
            ':': '-',
            '*': '',
            '?': ''
        },
        'priority_rules': [
            {
                'condition': 'счет-фактура',
                'template': 'Счет-фактура_{date}'
            },
        ],
        'confidence_threshold': 80
    }
    save_config(default_config)
    return default_config
def import_companies_from_file(file_path):
    try:
        if not os.path.exists(file_path):
            logging.error(f'Файл не найден: {file_path}')
            return False
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        companies = []
        for line in lines:
            company = line.strip()
            if company:
                companies.append(company)
        if not companies:
            logging.warning(f'Файл пустой или не содержит компаний')
            return False
        config = load_config()
        existing = set(config.get('known_companies', []))
        new_companies = [c for c in companies if c not in existing]
        if not new_companies:
            logging.info('Все компании уже есть в списке')
            return True
        config['known_companies'] = list(existing) + new_companies
        save_config(config)
        logging.info(f'Добавлено {len(new_companies)} новых компаний')
        logging.info(f'Всего компаний в списке: {len(config['known_companies'])}')
        return True
    except Exception as e:
        logging.error(f'Ошибка импорта компаний: {e}')
        return False
