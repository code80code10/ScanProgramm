import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
import os
from config import load_config, save_config
from paths import BASE_DIR
from setup_window import show_setup_window

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('ScanProgramm')
        self.root.geometry('700x600')
        self.root.resizable(False, False)

        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 700) // 2
        y = (screen_height - 600) // 2
        self.root.geometry(f'700x600+{x}+{y}')

        self.is_running = False
        self.stopped_by_button = False
        self.watcher_thread = None
        self.observer = None

        self.stats = {
            'processed': 0,
            'auto_saved': 0,
            'need_check': 0

        }
        self._build_ui()

        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

        self.root.after(500, self._auto_start)

    def _build_ui(self):

        title_frame = tk.Frame(self.root, bg='#a0add6', height=90)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text='ScanProgramm',
            bg='#a0add6',
            fg='white',
            font=('Arial', 22, 'bold')
        ).pack(pady=(15,0))

        tk.Label(
            title_frame,
            text='Автоматическая обработка сканов',
            bg='#a0add6',
            fg='black',
            font=('Arial', 14)
        ).pack()

        status_frame = tk.LabelFrame(self.root, text='Статус', padx=15,
                                     pady=15, font=('Arial', 11))
        status_frame.pack(fill=tk.X, padx=20, pady=(15,10))

        state_frame = tk.Frame(status_frame)
        state_frame.pack(fill=tk.X)

        self.status_indicator = tk.Label(
            state_frame,
            text='***',
            fg='red',
            font=('Arial', 26)
        )
        self.status_indicator.pack(side=tk.LEFT, padx=(0,10))

        self.status_label = tk.Label(
            state_frame,
            text='Остановлена',
            font=('Arial', 16, 'bold'),
            fg='gray'
        )
        self.status_label.pack(side=tk.LEFT)

        config = load_config()
        scan_folder = config.get('scan_folder', 'Не указана')
        output_folder = config.get('output_folder', 'Не указана')

        info_frame = tk.Frame(status_frame)
        info_frame.pack(fill=tk.X, pady=(10,0))

        self.scan_folder_label = tk.Label(
            info_frame,
            text=f'Сканы: {scan_folder}',
            font=('Arial', 13),
            fg='gray',
            anchor='w'
        ).pack(fill=tk.X)

        self.output_folder_label = tk.Label(
            info_frame,
            text=f'Готовые: {output_folder}',
            font=('Arial', 13),
            fg='gray',
            anchor='w'
        ).pack(fill=tk.X)

        stats_frame = tk.LabelFrame(self.root, text='Статистика', padx=15, pady=15, font=('Arial', 11))
        stats_frame.pack(fill=tk.X, padx=20, pady=10)

        self.stats_label = tk.Label(
            stats_frame,
            text='Обработано: 0 | Сохранено: 0 | Нужна проверка: 0',
            font=('Arial', 13),
            fg='#7f7679'
        )
        self.stats_label.pack()

        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(fill=tk.X, padx=20, pady=15)

        self.start_stop_btn = tk.Button(
            buttons_frame,
            text='ЗАПУСТИТЬ',
            bg='#92cf94',
            fg='white',
            font=('Arial', 14, 'bold'),
            relief='flat',
            cursor='hand2',
            command=self._toggle_running,
            height=2
        )
        self.start_stop_btn.pack(fill=tk.X, pady=(0, 10))

        setting_btn = tk.Button(
            buttons_frame,
            text='Настройки',
            bg='#a0add6',
            fg='white',
            font=('Arial', 14),
            relief='flat',
            cursor='hand2',
            command=self._open_settings

        )
        setting_btn.pack(fill=tk.X)

        tk.Label(
            self.root,
            text='ScanProgramm | all data is processed locally',
            font=('Arial', 9),
            fg='gray'
        ).pack(side=tk.BOTTOM, pady=(0,10))

    def _auto_start(self):
        self._toggle_running()
    def _toggle_running(self):
        if self.is_running:
            self._stop()
        else:
            self._start()

    def _start(self):
        try:
            config = load_config()
            scan_folder = config.get('scan_folder', 'C:\\Scans')

            if not os.path.exists(scan_folder):
                os.makedirs(scan_folder, exist_ok=True)

            from watcher import ScanHandler
            from watchdog.observers import Observer

            handler = ScanHandler(config, main_window=self.root)
            self.observer = Observer()
            self.observer.schedule(handler, scan_folder, recursive=False)
            self.observer.start()

            self.is_running = True
            self.stopped_by_button = False

            self.status_indicator.config(fg='#92cf94')
            self.status_label.config(text='Работает', fg='gray')
            self.start_stop_btn.config(text='ОСТАНОВИТЬ', bg='#ffbabc')

            logging.info('программа запущена')
        except Exception as e:
            logging.error(f'Ошибка запуска: {e}')
            messagebox.showerror('ERROR', f'не удалось запустить: \n{e}')

    def _stop(self):
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=2)
                self.observer = None

            self.is_running = False
            self.stopped_by_button = True

            self.status_indicator.config(fg='red')
            self.status_label.config(text='Остановлена', fg='gray')
            self.start_stop_btn.config(
                text='ЗАПУСТИТЬ',
                bg='#92cf94',
            )

            logging.info('Программа остановлена')

        except Exception as e:
            logging.error(f'Ошибка остановки: {e}')

    def _open_settings(self):
        was_running = self.is_running
        if was_running:
            self._stop()

        #self.root.withdraw()

        if self.root is None:
            #self.root.deiconify()
            messagebox.showerror("Ошибка",
                                 "Главное окно уничтожено — невозможно открыть настройки")
            return

        try:
            from setup_window import show_setup_window
            saved = show_setup_window(parent=self.root)
            self._refresh_ui()

        except Exception as e:
            self._restore_main_window(was_running)
            return
        if was_running:
            self.root.after(300, self._start)

    def _refresh_ui(self):
        try:
            from config import load_config
            config = load_config()

            scan_folder = config.get('scan_folder', 'Не указана')
            output_folder = config.get('output_folder', 'Не указана')

            if hasattr(self, 'scan_folder_label'):
                self.scan_folder_label.config(text=f'Сканы: {scan_folder}')
            if hasattr(self, 'output_folder_label'):
                self.output_folder_label.config(text=f'Готовые: {output_folder}')

            print(f'[MAIN] UI обновлен, сканы={scan_folder}, готовые={output_folder}')
        except Exception as e:
            print(f'Не удалось обновить UI: {e}')


    def _restore_main_window(self, was_running):
        try:
            if self.root.winfo_exists():

                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
                self.root.attributes('-topmost', True)
                self.root.after(200, lambda: self.root.attributes(
                    '-topmost', False))

                print("[MAIN] Главное окно восстановлено")

                if was_running:
                    self.root.after(500, self._start)

        except Exception as e:
            print(f"Ошибка восстановления окна: {e}")

    def _on_close(self):
        if self.is_running and not self.stopped_by_button:
            result = messagebox.askyesnocancel(
                'Программа работает',
                'Остановить и закрыть?'
            )
            if result is True:
                self._stop()
                self.root.destroy()
            elif result is False:
                pass
            else:
                pass
        else:
            self.root.destroy()

    def update_status(self, processed=0, auto_saved=0, need_check=0):
        self.stats['processed'] += processed
        self.stats['auto_saved'] += auto_saved
        self.stats['need_check'] += need_check

        self.stats_label.config(
            text=f'Обработано: {self.stats["processed"]} |'
                 f'Сохранено: {self.stats["auto_saved"]} |'
                 f'Нужна проверка: {self.stats["need_check"]} '

        )

    def run(self):
        self.root.mainloop()

def run_main_window():
    window = MainWindow()
    window.run()

if __name__ == '__main__':
    run_main_window()