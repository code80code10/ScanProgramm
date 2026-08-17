import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import fitz
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
def get_first_page_image(pdf_path, max_size=(500,700)):
    import tempfile
    try:
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            logging.error('pdf пустой')
            return None
        page = doc[0]

        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_path = temp_file.name
        temp_file.close()

        try:
            page.get_pixmap(matrix=fitz.Matrix(150/72, 150/72)).save(temp_path)

            logging.info([f'GUI Страница сохранена в: {temp_path}'])

            img = Image.open(temp_path)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(img)
            return photo
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            doc.close()
    except Exception as e:
        logging.error(f'Ошибка загрузки картинки: {e}')
        import traceback
        traceback.print_exc()
        return None
class VerificationWindow:
    def __init__(self, parent, pdf_path, parsed_data, on_save, on_skip):
        """
        :param pdf_path: путь к PDF
        :param parsed_data: результат парсинга(словарь с date, number, company)
        :param on_save: функция которая вызывается при сохранении(с
        исправленными данными)
        :param on_skip: функция которая вызывается при пропуске
        """
        self.pdf_path = pdf_path
        self.parsed_data = parsed_data
        self.on_save = on_save
        self.on_skip = on_skip
        self.result = None

        self.root = tk.Toplevel(parent)
        self.root.title(f'Проверка: {os.path.basename(pdf_path)}')
        self.root.geometry('1000x700')
        self.root.resizable(True, True)

        self.root.attributes('-topmost', True)

        self.root.transient(parent)
        self.root.grab_set()

        self.root.update_idletasks()
        width = 1000
        height = 700
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        self._build_ui()

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding='10')
        main_frame.pack(fill=tk.BOTH, expand=True)
        left_frame = ttk.LabelFrame(main_frame, text="Скан документа",
                                    padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        photo = get_first_page_image(self.pdf_path)
        if photo:
            image_label = ttk.Label(left_frame, image=photo)
            image_label.image = photo
            image_label.pack()
        else:
            ttk.Label(left_frame, text='Не удалось загрузить скан', foreground='red').pack()
        right_frame = ttk.LabelFrame(main_frame, text='Данные документа', padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(5,
                                                                          0))
        right_frame.config(width=300)
        ttk.Label(right_frame, text=f'Файл:', font=('Arial', 9,
                                                    'bold')).pack(anchor=tk.W)
        ttk.Label(right_frame, text=os.path.basename(self.pdf_path),
                  foreground='gray').pack(anchor=tk.W, pady=(0, 10))
        confidence = self.parsed_data.get('confidence', 0)
        color = 'green' if confidence > 80 else 'orange' if confidence >= 50 else 'red'

        conf_frame = ttk.Frame(right_frame)
        conf_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(conf_frame, text='Уверенность:', font=('Arial', 9,
                                                         'bold')).pack(
            side=tk.LEFT)
        ttk.Label(conf_frame, text=f' {confidence}%', foreground=color,
                  font=('Arial', 11, 'bold')
                  ).pack(side=tk.LEFT)

        ttk.Label(right_frame, text='Компания:', font=('Arial', 10,
                                                       'bold')).pack(anchor=tk.W)
        self.company_var = tk.StringVar(value=self.parsed_data.get(
            'company') or '')
        self.company_entry = ttk.Entry(right_frame,
                                       textvariable=self.company_var,
                                       font=('Arial', 10), width=40)
        self.company_entry.pack(fill=tk.X, pady=(2, 10))

        details = self.parsed_data.get('details', {})
        company_source = details.get('company_source', 'not_found')
        company_score = details.get('company_score', 0)
        ttk.Label(right_frame, text=f'Источник: {company_source} ('
                                    f'{company_score}%)',
                  foreground='gray', font=('Arial', 8)).pack(anchor=tk.W, pady=(0, 10))

        ttk.Label(right_frame, text='Номер документа:', font=('Arial', 10,
                                                              'bold')).pack(anchor=tk.W)
        self.number_var = tk.StringVar(value=self.parsed_data.get(
            'number') or '')
        self.number_entry = ttk.Entry(right_frame,
                                      textvariable=self.number_var, font=('Arial', 10), width=40)
        self.number_entry.pack(fill=tk.X, pady=(2, 10))
        number_source = details.get('number_source', 'not_found')
        number_score = details.get('number_score', 0)
        ttk.Label(right_frame, text=f'Источник: {number_source} ('
                                    f'{number_score}%)', foreground='gray',
                  font=('Arial', 8)).pack(anchor=tk.W, pady=(0, 10))

        ttk.Label(right_frame, text='Дата:', font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        self.date_var = tk.StringVar(value=self.parsed_data.get('date') or '')
        self.date_entry = ttk.Entry(right_frame, textvariable=self.date_var,
                                    font=('Arial', 10), width=40)
        self.date_entry.pack(fill=tk.X, pady=(2, 10))
        date_source = details.get('date_source', 'not_found')
        date_score = details.get('date_score', 0)
        ttk.Label(right_frame, text=f'Источник: {date_source} ('
                                    f'{date_score}%)', foreground='gray',
                  font=('Arial', 8)).pack(anchor=tk.W, pady=(0, 10))

        self.learn_var = tk.BooleanVar(value=True)
        learn_check = ttk.Checkbutton(right_frame, text='Запомнить мои '
                                                        'исправления', variable=self.learn_var)
        learn_check.pack(anchor=tk.W, pady=(10, 15))

        buttons_frame = tk.Frame(right_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        save_btn = ttk.Button(buttons_frame, text='Сохранить и научить',
                              command=self._on_save, width=25)
        save_btn.pack(side=tk.LEFT, padx=(0, 5))
        skip_btn = ttk.Button(buttons_frame, text='Пропустить',
                              command=self._on_skip, width=15)
        skip_btn.pack(side=tk.LEFT)

        ttk.Label(
            right_frame, text='Если данные не верные - исправь\n и нажми '
                              '"Сохранить"', foreground='#a0add6',
            font=('Arial', 10), wraplength=330).pack(
            anchor=tk.W, pady=(15, 0))
    def _on_save(self):
        self.result = {
            'company': self.company_var.get().strip() or None,
            'number': self.number_var.get().strip() or None,
            'date': self.date_var.get().strip() or None,
            'learn': self.learn_var.get(),
            'action': 'save'
        }
        self.root.destroy()
        if self.on_save:
            self.on_save(self.result)
    def _on_skip(self):
        self.result = {
            'action': 'skip'
        }
        self.root.destroy()
        if self.on_skip:
            self.on_skip()
    def show(self):
        self.root.mainloop()
        return self.result

def show_verification_window(parent, pdf_path, parsed_data, on_save=None,
                             on_skip=None):
    window = VerificationWindow(parent, pdf_path, parsed_data, on_save,
                                on_skip)
    return window.show()