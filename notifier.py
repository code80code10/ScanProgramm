import tkinter as tk
import logging
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class PopupNotification:
    """
    Всплывающее сообщение справа снизу
    Не блокирует работу
    """
    def __init__(self, title, message, on_click=None, auto_hide_seconds=15):
        """
        :param title: Заголовок уведомления
        :param message: текст уведомления
        :param on_click: функция вызывается при клике на "Проверить"
        :param auto_hide_seconds: через сколько сек скрыть
        """
        self.on_click = on_click
        self.auto_hide_seconds = auto_hide_seconds
        self.hidden = False

        self.thread = threading.Thread(target=self._create_window,
                                       args=(title, message), daemon=True)
        self.thread.start()

    def _create_window(self, title, message):
        """Окно уведомлений"""
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        width = 400
        height = 200
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - width - 20
        y_start = screen_height
        y_end = screen_height - height - 60

        self.root.geometry(f'{width}x{height}+{x}+{y_start}')

        bg_color = '#E5E4E2'
        text_color = '#000000'
        accent_color = '#6c5874'

        main_frame = tk.Frame(self.root, bg=bg_color, relief='solid', bd=2)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = tk.Label(
            main_frame,
            text=f'{title}',
            bg=bg_color,
            fg=accent_color,
            font=('Arial', 20, 'bold'),
            anchor=tk.CENTER,
            justify="center"
        )
        title_label.pack(fill=tk.X, padx=10, pady=(10, 5))

        msg_label = tk.Label(
            main_frame,
            text=message,
            bg=bg_color,
            fg=text_color,
            font=('Arial', 11),
            anchor=tk.CENTER,
            wraplength=320,
            justify="center"
        )
        msg_label.pack(fill=tk.X, padx=10, pady=(0, 10))

        buttons_frame = tk.Frame(main_frame, bg=bg_color)
        buttons_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        check_btn = tk.Button(
            buttons_frame,
            text='Проверить',
            bg=accent_color,
            fg='white',
            font=('Arial', 11, 'bold'),
            relief='flat',
            cursor='hand2',
            command=self._on_check_click,
            width=20
        )
        check_btn.pack(side=tk.LEFT, padx=(0, 5))
        ignore_btn = tk.Button(
            buttons_frame,
            text='Игнорировать',
            bg='#9C9C9C',
            fg='white',
            font=('Arial', 11, 'bold'),
            relief='flat',
            cursor='hand2',
            command=self._on_ignore_click,
            width=20
        )
        ignore_btn.pack(side=tk.LEFT)

        self._animate_show(x, y_start, y_end)
        if self.auto_hide_seconds > 0:
            self.root.after(self.auto_hide_seconds * 1000, self._auto_hide)
        self.root.mainloop()
    def _animate_show(self, x, y_start, y_end):
        """Анимация появления снизу вверх"""
        current_y = y_start
        step = 10
        delay = 10
        def animate():
            nonlocal current_y
            if current_y > y_end:
                current_y -= step
                self.root.geometry(f'+{x}+{current_y}')
                self.root.after(delay, animate)
        animate()

    def _animate_hide(self, callback=None):
        """Анимация скрытия уезжает вниз"""
        screen_height = self.root.winfo_screenheight()
        current_y = self.root.winfo_y()
        step = 10
        delay = 10

        def animate():
            nonlocal current_y
            if current_y < screen_height:
                current_y += step
                self.root.geometry(f'+{self.root.winfo_x()}+{current_y}')
                self.root.after(delay, animate)
            else:
                self.root.destroy()
                if callback:
                    callback()
        animate()

    def _on_check_click(self):
        """Клик на "Проверить" """
        if not self.hidden:
            self.hidden = True
            self._animate_hide()
            if self.on_click:
                self.on_click()

    def _on_ignore_click(self):
        """Клик на "Игнорировать" """
        if not self.hidden:
            self.hidden = True
            self._animate_hide()

    def _auto_hide(self):
        """Автоматическое скрытие"""
        if not self.hidden:
            self.hidden = True
            logging.info("Уведомление автоматически скрыто")
            self._animate_hide()

def show_notification(title, message, on_click=None, auto_hide_seconds=15):
    """
    Функция для показа уведомления
    Создает поп-ап в отдельном потоке
    """
    PopupNotification(title, message, on_click, auto_hide_seconds)