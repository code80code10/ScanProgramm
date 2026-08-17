import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')

class SetupWindow:
    """Окно настройки программы, открывается при первом запуске"""
    def __init__(self, parent=None):

        self.parent = parent
        self.saved = False

        self.config = self._load_existing_config()

        if self.parent is None:
            raise RuntimeError(
                "SetupWindow должен создаваться с parent (главное окно)")



        self.root = tk.Toplevel(self.parent)
        self.root.transient(self.parent)

        self.root.title('Настройка ScanProgramm')
        self.root.geometry('700x600')
        self.root.resizable(False, False)

        self.root.update_idletasks()
        width = 700
        height = 600
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f'{width}x{height}+{x}+{y}')

        self.root.protocol('WM_DELETE_WINDOW', self._on_cancel)

        self._build_ui()

    def _load_existing_config(self):
        try:
            from paths import BASE_DIR
            config_path = os.path.join(BASE_DIR, 'config.json')
        except:
            config_path = 'config.json'

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f'Ошибка загрузки конфига: {e}')

        return {
            'scan_folder': '',
            'output_folder': '',
            'my_company': '',
            'exclude_directors': [],
            'known_companies': [],
            'use_abbreviation_search': False,
            'extraction': {
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
            'filename_cleanup': {
                '/': '.',
                '?': '',
                '"': ''
            },
            'priority_rules': [],
            'confidence_threshold': 0
        }

    def _build_ui(self):
        '''Строит интерфейс'''

        title_label = tk.Label(
            self.root,
            text='Добро пожаловать в ScanProgramm',
            font=('Arial', 24, 'bold'),
            fg='black',

        )
        title_label.pack(pady=(20,10))

        subtitle_label = tk.Label(
            self.root,
            text='Измененные настройки отображаются на главном экране\n '
                 'только после презапуска программы',
            font=('Arial', 13),
            fg='gray'
        )
        subtitle_label.pack(pady=(0,10))

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, padx=20, pady=10)

        folders_tab = ttk.Frame(notebook, padding='20')
        notebook.add(folders_tab, text='Папки'),
        self._build_folders_tab(folders_tab)

        companies_tab = ttk.Frame(notebook, padding='20')
        notebook.add(companies_tab, text='Компании')
        self._build_companies_tab(companies_tab)

        rules_tab = ttk.Frame(notebook, padding='20')
        notebook.add(rules_tab, text='Правила')
        self._build_rules_tab(rules_tab)

        buttons_frame = ttk.Frame(self.root)
        buttons_frame.pack(fill=tk.X, padx=20, pady=(0,15), anchor=tk.N)

        save_btn = ttk.Button(
            buttons_frame,
            text='Сохранить и начать работу',
            command=self._on_save,
            width=30
        )
        save_btn.pack(side=tk.RIGHT)

        cancel_btn = ttk.Button(
            buttons_frame,
            text='Отменить',
            command=self._on_cancel,
            width=15
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(0, 10))
        logging.info("[SETUP] _build_ui завершён без ошибок")
        self.root.after(5000, lambda: logging.info(
            "[SETUP] Прошло 5 секунд — окно всё ещё должно быть видно"))
    def _build_folders_tab(self, parent):
        """Вкладка "Папки" """
        row1 = tk.Frame(parent)
        row1.pack(fill=tk.X, pady=(10, 3))

        tk.Label(row1, text='Папка сканов', font=('Arial', 12,
                                                  'bold')).pack(side=tk.LEFT)
        self.scan_status = tk.Label(row1, text='не выбрана', fg='red',
                                    font=('Arial', 10))
        self.scan_status.pack(side=tk.RIGHT)

        row2 = tk.Frame(parent)
        row2.pack(fill=tk.X, pady=(0, 25))
        self.scan_folder_var = tk.StringVar()

        self.scan_entry = tk.Entry(row2, textvariable=self.scan_folder_var,
                                    font=('Arial', 12), bd=2,
                                   relief='solid', bg='white')
        self.scan_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,8))

        scan_btn = ttk.Button(row2, text='Обзор...',
                              command=self._choose_scan_folder, width=12)
        scan_btn.pack(side=tk.RIGHT)

        self.scan_folder_var.trace_add('write', self._on_scan_folder_changed)

        row3 = tk.Frame(parent)
        row3.pack(fill=tk.X, pady=(10, 3))

        tk.Label(row3, text='Папка готовых документов', font=('Arial', 12,
                                                              'bold')).pack(side=tk.LEFT)
        self.output_status = tk.Label(row3, text='не выбрана', fg='red',
                                      font=('Arial', 10))
        self.output_status.pack(side=tk.RIGHT)

        row4 = tk.Frame(parent)
        row4.pack(fill=tk.X, pady=(0, 15))

        self.output_folder_var = tk.StringVar()

        self.output_entry = tk.Entry(row4,
                                     textvariable=self.output_folder_var,
                                     font=('Arial', 12), bd=2,
                                     relief='solid', bg='white')
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True,
                               padx=(0,8))

        output_btn = ttk.Button(row4, text='Обзор...', command=self._choose_output_folder, width=12)
        output_btn.pack(side=tk.RIGHT)

        self.output_folder_var.trace_add('write', self._on_output_folder_changed)


    def _build_companies_tab(self, parent):
        """Вкладка "Компании" """

        ttk.Label(parent, text='Название твоей компании(исключает из имен '
                               'файлов, \nтак программа не будет брать '
                               'твою компанию за продавца):', font=('Arial',
                                                                    12,
                                                                    'bold')).pack(anchor=tk.W, pady=(0,5))
        self.my_company_var = tk.StringVar()
        my_company_entry = ttk.Entry(parent,
                                     textvariable=self.my_company_var, width=60)
        my_company_entry.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(parent, text='Список известных компаний(если есть):',
                  font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0,5))

        companies_frame = ttk.Frame(parent)
        companies_frame.pack(fill=tk.X, expand=True, pady=(0, 10))

        self.companies_text = tk.Text(companies_frame, height=10, width=70,
                                      font=('Arial', 9), wrap=tk.WORD)
        self.companies_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(companies_frame, orient=tk.VERTICAL,
                                  command=self.companies_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.companies_text.config(yscrollcommand=scrollbar.set)

        import_btn = ttk.Button(parent, text='Импортировать из блокнота',
                                command=self._import_companies, width=30 )
        import_btn.pack(anchor=tk.W)

        self.companies_count = ttk.Label(parent, text='Компаний в списке: 0',
                                        foreground='gray', font=('Arial', 11))
        self.companies_count.pack(anchor=tk.W, pady=(5, 0))

        self.companies_text.bind('<KeyRelease>', self._update_companies_count)

    def _build_rules_tab(self, parent):
        """Вкладка "Правила" """

        ttk.Label(parent, text='Порог уверенности (%):', font=('Arial', 12,
                                                               'bold')).pack(anchor=tk.W, pady=(0,5))

        self.confidence_var = tk.IntVar(value=80)
        confidence_spin = ttk.Spinbox(parent, from_=50, to=100,
                                      textvariable=self.confidence_var,
                                      width=10, style='Big.TSpinbox', font=('Arial', 12))
        confidence_spin.pack(anchor=tk.W, pady=(10,20))

        ttk.Label(parent, text='Если уверенность ниже порога - программа '
                               'выведет уведомление для проверки',
                  foreground='gray', font=('Arial', 11),
                  wraplength=600).pack(anchor=tk.W, padx=(0,20))

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        ttk.Label(parent, text='Дополнительные настройки:', font=('Arial',
                                                                  12,
                                                                  'bold')).pack(anchor=tk.W, pady=(0,10))

        self.use_abbr_var = tk.BooleanVar(value=False)
        abbr_check = ttk.Checkbutton(
            parent,
            text='Искать аббревиатуры компаний(экспериментальная функция)',
            variable=self.use_abbr_var
        )
        abbr_check.pack(anchor=tk.W, padx=(0,10))

        ttk.Label(parent,
                  text='Не рекмендуется включать, часто дает ошибки',
                  foreground='red', font=('Arial', 12), wraplength=600).pack(
            anchor=tk.W)

    def _on_scan_folder_changed(self, *args):
        value = self.scan_folder_var.get().strip()
        if value:
            self.scan_status.config(text='выбрана', fg='green')
            self.scan_entry.config(bg='#cadaba')
        else:
            self.scan_status.config(text='не выбрана', fg='red')
            self.scan_entry.config(bg='#f5f5f5')

    def _on_output_folder_changed(self, *args):
        value = self.output_folder_var.get().strip()
        if value:
            self.output_status.config(text='выбрана', fg='green')
            self.output_entry.config(bg='#cadaba')
        else:
            self.output_status.config(text='не выбрана', fg='red')
            self.output_entry.config(background='#f5f5f5')

    def _update_companies_count(self, event=None):
        text = self.companies_text.get('1.0', tk.END).strip()
        if text:
            count = len([line for line in text.split('\n') if line.strip()])
        else:
            count = 0
        self.companies_count.config(text=f'Компаний в списке: {count}')

    def _choose_scan_folder(self):
        """Выбор папки сканов"""
        folder = filedialog.askdirectory(title='Выбери папку куда сканер '
                                               'сохраняет файлы')
        if folder:
            self.scan_folder_var.set(folder)

    def _choose_output_folder(self):
        """Выбор папки для готовых документов"""
        folder = filedialog.askdirectory(title='Выбери папку куда сохранять '
                                               'готовые документы')
        if folder:
            self.output_folder_var.set(folder)

    def _import_companies(self):
        """Импорт компаний из текстового файла"""
        file_path = filedialog.askopenfilename(
            title='Выбери файл со списком компаний', filetypes=[('Text '
                                                                 'Files',
                                                                 '*.txt'), ('All files', '*.*')]
        )
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            companies = [line.strip() for line in lines if line.strip()]

            if not companies:
                messagebox.showwarning('Пустой файл', 'Файл не содержит '
                                                      'компаний')
                return
            current_text = self.companies_text.get(1.0, tk.END).strip()
            if current_text:
                new_text = current_text + '\n' + '\n'.join(companies)
            else:
                new_text = '\n'.join(companies)

            self.companies_text.delete(1.0, tk.END)
            self.companies_text.insert(1.0, new_text)

            messagebox.showinfo('Импортировано успешно', f'Импортировано '
                                                         f'{len(companies)} '
                                                         f'компаний')
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось импортировать: {e}')

    def _on_save(self):
        """сохранение настроек"""

        if not self.scan_folder_var.get().strip():
            messagebox.showerror('Ошибка', 'Укажи папку куда сканер '
                                           'сохраняет файлы')
            return

        if not self.output_folder_var.get().strip():
            messagebox.showerror('Ошибка', "Укажи папку куда сохранять "
                                           "готовые документы")
            return

        self.config['scan_folder'] = self.scan_folder_var.get().strip()
        self.config['output_folder'] = self.output_folder_var.get().strip()
        self.config['my_company'] = self.my_company_var.get().strip()
        self.config['use_abbreviation_search'] = self.use_abbr_var.get()
        self.config['confidence_threshold'] = self.confidence_var.get()

        companies_text = self.companies_text.get(1.0, tk.END).strip()
        if companies_text:
            self.config['known_companies'] = [line.strip() for line in
                                              companies_text.split('\n') if
                                              line.strip()]
        else:
            self.config['known_companies'] = []

        try:
            from paths import BASE_DIR
            config_path = os.path.join(BASE_DIR, 'config.json')
        except:
            config_path = 'config.json'
        try:

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            self.saved = True

            self.root.grab_release()
            self.root.destroy()
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось сохранить: {e}')


    def _on_cancel(self):
        if messagebox.askyesno('Отмена', "Точно? Без настроек программа не "
                                         "сможет "
                                         "работать"):
            self.root.grab_release()
            self.root.destroy()
    def show(self):
        self.root.wait_window()
        return self.saved

def show_setup_window(parent=None):
    try:
        window = SetupWindow(parent=parent)
        result = window.show()
        return result
    except Exception as e:
        logging.error(e)
        raise

