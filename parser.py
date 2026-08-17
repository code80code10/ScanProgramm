import re
import logging
from datetime import datetime
from fuzzywuzzy import fuzz, process
from config import load_config

def normalize_ocr_text(text):
    replacements = [
        (r'\bО00\b', 'ООО'),
        (r'\bО\b(?=\s+[А-Я])', 'ООО'),
        (r'\bА0\b', 'АО'),
        (r'\bAО\b', 'АО'),
        (r'\bAO\b', 'АО'),
        (r'\bИП\b', 'ИП'),
        (r'\bИГ\b', 'ИП'),
        (r'\bЗAО\b', 'ЗАО'),
        (r'\bЗАO\b', 'ЗАО'),
        (r'\bЗAO\b', 'ЗАО'),
        (r'\bПAO\b', 'ПАО'),
        (r'""', '"'),
        (r"''", "'"),
        (r'—', '-'),
        (r'0(?=[А-Яа-я])', 'О'),
        (r'(?<=[А-Яа-я])0', 'О'),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    return text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
def extract_date(text, last_date=None):
    from memory import check_correction
    corrected_date = check_correction(text, 'date')
    if corrected_date:
        return corrected_date, 100, 'memory'
    patterns = [
        r'(\d{2})[./\-](\d{2})[./\-](\d{4})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            day, month, year = match.groups()
            date_str = f'{day}.{month}.{year}'
            try:
                date_obj = datetime.strptime(date_str, '%d.%m.%Y')
                current_year = date_obj.year
                if date_obj.year < current_year - 5 or date_obj.year > current_year:
                    continue
                return date_str, 100 , 'first_page'
            except ValueError:
                continue
    if last_date:
        return last_date, 50, 'last_file'
    return None, 0, 'not_found'
def extract_number(text):
    from memory import check_correction
    corrected_number = check_correction(text, 'number')
    if corrected_number:
        return corrected_number, 100, 'memory'
    match = re.search(r'№\s*([\d]+[-/]?[\d]*[-/]?[А-ЯA-Z]?)', text)
    if match:
        number =match.group(1)
        number = number.replace('/', '.')
        return number, 100, 'with_symbol'
    match = re.search(r'номер\s+(?документа)?[:\s]*\n?\s*(\d+)', text, re.IGNORECASE)
    if match:
        return match.group(1), 80, 'by_label'
    numbers = re.findall(r'\b(\d{4,10})\b', text)
    if numbers:
        return numbers[0], 50, 'just_number'
    return None, 0, 'not_found'
def extract_company(text, config):
    from memory import check_correction
    corrected_company = check_correction(text, 'company')
    if corrected_company:
        return corrected_company, 100, 'memory'
    known_companies = config.get('known_companies', [])
    exclude_codes = {
        # классификаторы
        'ОКУД', 'ОКПО', 'ОКВЭД', 'ОКОП', 'ОКДП', 'ОКП', 'ОКЕИ', 'ОКН',
        'ОКАТО', 'ОКФС', 'ОКФ', 'ОКОГУ', 'ОКСТ', 'ОКСТП', 'ОКПД', 'ОКПД2',
        # служебные
        'ИНН', 'КПП', 'ОГРН', 'ОГРНИП', 'СНИЛС', 'РН', 'ФС', 'РФ', 'НДС',
        'GPS', 'ФСС', 'ПФР', 'ФНС', 'РОССТАТ', 'ЕГРЮЛ', 'ЕГРИП',
        # коды форм
        'КО', 'ТОРГ', 'М', 'Т', 'РП', 'АКТ', 'СЧ', 'Н', 'АК', 'ДОГ', 'НАКЛ',
        'СПР', 'ВКЛ', 'ИЗМ', 'ПРИЛ', 'УПД', 'КС', 'КО-2',
        # и тд
        'СССР', 'СНГ', 'ЕС', 'ООН',
    }
    exclude_words = {
        'КВИТАНЦИЯ', 'АКТ', 'НАКЛАДНАЯ', 'ДОГОВОР', 'СЧЕТ', 'ФАКТУРА',
        'ВЕДОМОСТЬ', 'ОТЧЕТ', 'СПРАВКА', 'ЗАЯВЛЕНИЕ', 'ПРИКАЗ', 'РАСПОРЯЖЕНИЕ',
        'УСТАВ', 'ПРОТОКОЛ', 'РЕШЕНИЕ', 'ПИСЬМО', 'СЧЁТ', 'СЧЕТА', 'СЧЕТУ',
        'АКТУ', 'АКТА', 'ДОГОВОРА', 'НАКЛАДНОЙ', 'КВИТАНЦИИ',
        'ПРИЛОЖЕНИЕ', 'СПЕЦИФИКАЦИЯ', 'СПИСОК', 'ПЕРЕЧЕНЬ', 'РЕЕСТР',
        'ВЫПИСКА', 'КОПИЯ', 'ДУБЛИКАТ', 'ОРИГИНАЛ',
        'ДИРЕКТОР', 'БУХГАЛТЕР', 'КАССИР', 'МЕНЕДЖЕР', 'РУКОВОДИТЕЛЬ',
        'ГЕНЕРАЛЬНЫЙ', 'ИСПОЛНИТЕЛЬ', 'ЗАКАЗЧИК', 'ПОКУПАТЕЛЬ', 'ПРОДАВЕЦ',
        'ПОСТАВЩИК', 'ПЕРЕВОЗЧИК', 'ЭКСПЕДИТОР',
        'РОССИЯ', 'МОСКВА', 'САНКТ', 'ПЕТЕРБУРГ', 'Г', 'Г.', 'ГОРОД',
        'УЛ', 'УЛИЦА', 'ПР', 'ПРОСПЕКТ', 'Д', 'ДОМ', 'ОФИС', 'СКЛАД',
        'ТЕЛ', 'ФАКС', 'EMAIL', 'ПОЧТА', 'САЙТ', 'WWW', 'HTTP',
        'ДАТА', 'НОМЕР', 'КОД', 'ФОРМА', 'ВИД', 'ТИП', 'СТРАНА',
        'СУММА', 'ИТОГО', 'ВСЕГО', 'РУБ', 'КОП', 'ТЫС', 'МЛН',
    }
    #ПРИОРИТЕТ ПО СПИСКУ
    if known_companies:
        potential_companies:re.findall(
            r'(?:ООО|АО|ЗАО|ОАО|ПАО)\s[А-Яа-яA-Za-z"«»\s\-]+',
            text)
        best_match = None
        best_score = 0

        for potential in potential_companies:
            potential = potential.strip()
            potential_clean = potential_replace('"', '').replace("«",
                                                                 '').replace('»','')
            potential_clean = re.sub(r'\s+', ' ', potential_clean).strip()
            potential_clean = re.sub(r'\s+\d+$', '', potential_clean)
            if len(potential_clean) < 5:
                continue
            match = process.extractOne(
                potential_clean,
                known_companies,
                scorer=fuzz.partial_ratio
            )
            if match and match[1] > best_score and match[1] > 75:
                best_match = match
                best_score = match[1]
        if best_match:
            score = best_match[1]
            confidence = 60 + int((score - 75) * 1.4)
            confidence = min(95, confidence)
            return best_match[0], confidence, 'known_list'
    #ПРИОРИТЕТ ОБЩИМ ПОИСКОМ
    company_matches = re.finditer(r'(?:ООО|АО|ЗАО|ОАО|ПАО)\s+(['
                                  r'А-Яа-яA-Za-z"«»\s\-\.]+)', text)
    for match in company_matches:
        full_match = match.group(0).strip()
        name_part = match.group(1).strip()
        name_clean = name_part.replace('"', '').replace("«",'').replace('»','')
        name_clean = re.sub(r'\s+', ' ', name_clean).strip()
        if len(name_clean) < 3:
            continue
        words = name_clean.split()
        if len(words) > 4:
            name_clean = ' '.join(words[:4])
        prefix = full_match.split()[0]
        valid_prefixes = {'ООО','АО','ИП','ЗАО','ОАО','ПАО','НАО'}
        if prefix not in valid_prefixes:
            continue
        company_result = f'{prefix} {name_clean}'
        name_upper = name_clean.upper()
        if any(word in name_upper for word in exclude_words):
            continue
        if any(code in name_upper for code in exclude_words):
            continue
        logging.info(f'Компания найдена общим списком: {company_result}')
        return company_result, 60, 'general_search'
    #ПРИОРИТЕТ АББРЕВИАТУР(ТОЛЬКО ЕСЛИ ВКЛЮЧЕНО)
    use_abbr = config.get('use_abbreviation_search', False)
    if use_abbr:
        abbr = extract_abbrevation(text, exclude_words, exclude_codes)
        if abbr:
            logging.info(f'Компания найдена как аббревиатура: {abbr}')
            return abbr, 70, 'abbreviation'
    return None, 0, 'not_found'

def extract_abbrevation(text):
    company_patterns = re.finditer(r'(?:ООО|АО|ИП|ЗАО|ОАО|ПАО|НАО)\s+['
                                  r'А-Яа-яA-Za-z"«»\s\-\.]', text)
    for match in company_patterns:
        end_pos = match.end()
        after_company = text[end_pos:end_pos + 80]
        abbr_match = re.search(
            r'\s*[\((]([А-ЯA-ZЁ]{3,20}(?:\s+[А-ЯA-ZЁ]{2,20})*)[\))]',
            after_company)
        if abbr_match:
            abbr = abbr_match.group(1).strip()
            if abbr not in exclude_codes and not re.search(r'\d', abbr):
                return abbr
        comma_match = re.search(r'\s*([А-ЯA-ZЁ]{3,20}(?:\s+[А-ЯA-ZЁ]{2,'
                                r'20})*)', after_company)
        if comma_match:
            abbr = comma_match.group(1).strip()
            if abbr not in exclude_codes and not re.search(r'\d', abbr):
                return abbr
    return None
def shorten_company_name(name, max_len=30):
    if len(name) <= max_len:
        return name
    quote_match = re.search(r'[«"]([^»"]+)[»"]', name)
    if quote_match:
        short_name = quote_match.group(1)
        before_quote = name[:quote_match.start()].strip()
        words = before_quote.split()
        initials = ''.join([w[0].upper() for w in words if w])
        return f'{initials} {short_name}'
    words = name.split()[:3]
    return ''.join(words)
def clean_company_name(company, config):
    if not company:
        return None
    my_company = config.get('my_company', '')
    exclude_directors = config.get('exclude_directors', [])
    if my_company and company.lower() == my_company.lower():
        return None
    for director in exclude_directors:
        if director.lower() in company.lower():
            return None
    max_lenght =config.get('extraction', {}).get('company', {}).get(
                                                          'shorten_if_longer_than',30)
    company = shorten_company_name(company, max_lenght)
    return company
def parse_document(text, config, last_date=None):
    from memory import get_last_date, update_last_processed
    logging.info('Начинаем парсинг документа...')
    if not last_date:
        last_date = get_last_date()
    text = normalize_ocr_text(text)
    date, date_score, date_source = extract_date(text, last_date)
    number, number_score, number_source = extract_number(text)
    company, company_score, company_source = extract_company(text, config)
    company = clean_company_name(company, config)
    if company is None:
        company_score = 0
        company_source = 'excluded'
    details = {
        'date_score': date_score,
        'date_source': date_source,
        'company_score': company_score,
        'company_source': company_source,
        'number_score': number_score,
        'number_source': number_source,
    }
    confidence = calculate_confidence(details)
    result = {
        'date': date,
        'number': number,
        'company': company,
        'confidence': confidence,
        'details': details
    }
    if date or company or number:
        update_last_processed(date, company, number)
    logging.info(f'Результат парсинга: компания={company} ({company_source}, {company_score}%),'
                 f'номер={number} ({number_source}, {number_score}%),'
                 f'дата={date} ({date_source}, {date_score}%),'
                 f'общая уверенность={confidence}%')
    return result
def calculate_confidence(details):
    scores = []

    if details.get('company_score') is not None and details['company_score']> 0:
        scores.append(details['company_score'])
    if details.get('date_score') is not None and details['date_score'] > 0:
        scores.append(details['date_score'])
    if details.get('number_score') is not None and details['number_score'] > 0:
        scores.append(details['number_score'])
    if not scores:
        return 0
    return sum(scores) // len(scores)


def is_valid_document(text):
    document_keywords = [
        'приходный ордер', 'накладная', 'счет', 'акт', 'договор',
        'счет-фактура', 'товарная накладная',
        'универсальный передаточный документ',
        'квитанция', 'платежное поручение', 'платежка',
        'расписка', 'заявление', 'справка',
        'поставщик', 'покупатель', 'продавец', 'плательщик',
        'грузополучатель', 'отправитель', 'получатель',
        'товар', 'услуга', 'продукция',
        'цена', 'стоимость', 'сумма', 'количество',
        'номер', 'дата', 'подпись', 'печать',
        'инн', 'кпп', 'огрн', 'окпо', 'счет', 'банк',
    ]
    exclude_keywords = [
        'учебник', 'учебное пособие','глава', 'параграф', 'раздел','страница', 'стр.', 'издание', 'издательство',
        'автор','оглавление', 'содержание', 'введение', 'заключение',
        'список литературы', 'библиография', 'приложение',
    ]
    text_lower = text.lower()
    doc_matches = sum(1 for keyword in document_keywords if keyword in text_lower)
    exclude_matches = sum(1 for keyword in exclude_keywords if keyword in text_lower)

    if exclude_matches > doc_matches:
        logging.info(
            f"не документ: {exclude_matches} признаков")
        return False
    if doc_matches >= 3:
        logging.info(f"документ: {doc_matches} признаков")
        return True

    logging.info(f"всего {doc_matches} признаков")
    return False

