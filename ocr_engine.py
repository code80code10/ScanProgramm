import fitz
import pytesseract
from PIL import Image
import io
import re
import logging
import os
from paths import BASE_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def find_tesseract():
    script_dir = BASE_DIR
    portable_path = os.path.join(script_dir, "tesseract", "tesseract.exe")
    if os.path.exists(portable_path):
        logging.info(f'Тессеракт нашёль в папочке: {portable_path}')
        return portable_path

    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Tesseract\tesseract.exe',
        r'D:\Tesseract-OCR\tesseract.exe',
    ]
    for path in possible_paths:
        if os.path.exists(path):
            logging.info(f'Tesseract нашёль: {path}')
            return path
    logging.error('Tesseract неть')
    return None

tesseract_path = find_tesseract()
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    logging.warning('TESSERACT не настроен. OCR не будет робить')

def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            logging.warning(f'PDF пустой: {pdf_path}')
            return ''
        page = doc[0]
        text = page.get_text()

        if text and len(text.strip()) > 20:
            logging.info('Текст извлечен через get_text()')
            doc.close()
            return text.strip()
        logging.info('Текстовый слой пуст, используем Tesseract...')
        pix = page.get_pixmap(dpi=300)
        img_data = pix.tobytes('png')
        image = Image.open(io.BytesIO(img_data))

        script_dir = BASE_DIR
        tessdata_dir = os.path.join(script_dir, 'tesseract', 'tessdata')
        custom_config = f'--psm 6 --tessdata-dir "{tessdata_dir}"'

        text = pytesseract.image_to_string(
            image,
            lang='rus+eng',
            config=custom_config
        )
        doc.close()
        if not text or len(text.strip()) < 10:
            logging.warning(f'Tesseract не смог прочитать {pdf_path}')
            return ''
        logging.info(f'Tesseract прочитал {len(text)} символов')
        return text.strip()
    except Exception as e:
        logging.error(f'Ошибка при чтении {pdf_path}: {e}')
        return ''
def extract_text_from_page(pdf_path, page_num=0):
    try:
        doc = fitz.open(pdf_path)
        if page_num >= len(doc):
            doc.close()
            return ''
        page = doc[page_num]
        text = page.get_text()
        if text and len(text.strip()) > 20:
            doc.close()
            return text.strip()
        pix = page.get_pixmap(dpi=300)
        img_data = pix.tobytes('png')
        image = Image.open(io.BytesIO(img_data))

        script_dir = BASE_DIR
        tessdata_dir = os.path.join(script_dir, 'tesseract', 'tessdata')
        custom_config = f'--psm 6 --tessdata-dir "{tessdata_dir}"'

        text = pytesseract.image_to_string(
            image,
            lang='rus+eng',
            config=custom_config
        )
        doc.close()
        return text.strip() if text else ''
    except Exception as e:
        logging.error(f'Ошибка чтении страницы {page_num}: {e}')
        return ''

