```python
import json
import os
import random
import threading
import time
from datetime import datetime

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, SlideTransition

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogButtonContainer,
    MDDialogHeadlineText,
    MDDialogSupportingText,
)
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except Exception:
    PLYER_AVAILABLE = False


# ============================================================
# ANDROID: папка данных приложения
# ============================================================

APP_DIR = MDApp.get_running_app().user_data_dir if MDApp.get_running_app() else None

if APP_DIR is None:
    # Во время запуска до создания MDApp используем папку рядом с main.py.
    APP_DIR = os.path.dirname(os.path.abspath(__file__))


SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")
DATA_FILE = os.path.join(APP_DIR, "app_data.json")

SHORT_DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб"]

COLOR_MAP = {
    "Зеленый": "Green",
    "Белый": "Gray",
    "Красный": "Red",
    "Синий": "Blue",
    "Оранжевый": "Orange",
    "Фиолетовый": "Purple",
    "Голубой": "Cyan",
    "Розовый": "Pink",
}


# ============================================================
# РАБОТА С НАСТРОЙКАМИ
# ============================================================

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")

    return {
        "notify_time": "17:00",
        "enabled": True,
        "repeat_interval": 15,
        "theme_color": "Фиолетовый",
    }


def save_settings(data):
    try:
        os.makedirs(APP_DIR, exist_ok=True)

        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=4
            )

    except Exception as e:
        print(f"Ошибка сохранения настроек: {e}")


# ============================================================
# РАБОТА С ДАННЫМИ
# ============================================================

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")

    default_days = {}

    for day in SHORT_DAYS:
        default_days[day] = [
            {
                "num": i,
                "name": "",
                "hw": "",
                "done": False
            }
            for i in range(1, 8)
        ]

    return {
        "has_saturday": True,
        "schedule": default_days
    }


def save_data(data):
    try:
        os.makedirs(APP_DIR, exist_ok=True)

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=4
            )

    except Exception as e:
        print(f"Ошибка сохранения данных: {e}")


SETTINGS = load_settings()
APP_DATA = load_data()

today_weekday = datetime.now().weekday()

CURRENT_SELECTED_DAY = (
    SHORT_DAYS[today_weekday]
    if today_weekday < 6
    else "Пн"
)


# ============================================================
# УВЕДОМЛЕНИЯ
# ============================================================

def send_notification():
    if not PLYER_AVAILABLE:
        return

    try:
        notification.notify(
            title="Школьный помощник",
            message="У тебя еще остались невыполненные уроки!",
            app_name="School Helper",
            timeout=10
        )
    except Exception as e:
        print(f"Ошибка уведомления: {e}")


def notification_checker():
    last_notified_time = 0

    while True:
        try:
            now = datetime.now()

            current_time_str = now.strftime("%H:%M")

            interval_sec = (
                SETTINGS.get("repeat_interval", 15) * 60
            )

            current_day_name = (
                SHORT_DAYS[now.weekday()]
                if now.weekday() < 6
                else "Пн"
            )

            schedule = APP_DATA.get(
                "schedule",
                {}
            )

            today_lessons = schedule.get(
                current_day_name,
                []
            )

            has_undone_hw = any(
                item.get("hw", "").strip() != ""
                and not item.get("done", False)
                for item in today_lessons
            )

            if (
                SETTINGS.get("enabled", True)
                and has_undone_hw
            ):
                notify_time = SETTINGS.get(
                    "notify_time",
                    "17:00"
                )

                if current_time_str >= notify_time:

                    if (
                        time.time() - last_notified_time
                        >= interval_sec
                    ):
                        send_notification()
                        last_notified_time = time.time()

        except Exception as e:
            print(
                f"Ошибка в потоке уведомлений: {e}"
            )

        time.sleep(15)


# ============================================================
# ГЛАВНЫЙ ЭКРАН
# ============================================================

class MainMenuScreen(MDScreen):

    dialog = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = MDBoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(10)
        )

        # Верхняя панель
        self.top_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(52),
            spacing=dp(5)
        )

        self.day_label = MDLabel(
            text="",
            font_style="Title",
            role="medium"
        )

        self.time_clock_label = MDLabel(
            text="",
            halign="right",
            font_style="Title",
            role="medium"
        )

        edit_btn = MDIconButton(
            icon="square-edit-outline",
            on_release=self.open_editor
        )

        settings_btn = MDIconButton(
            icon="cog",
            on_release=self.open_settings
        )

        self.top_bar.add_widget(self.day_label)
        self.top_bar.add_widget(self.time_clock_label)
        self.top_bar.add_widget(edit_btn)
        self.top_bar.add_widget(settings_btn)

        # Список уроков
        self.scroll = MDScrollView()

        self.lessons_layout = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None
        )

        self.lessons_layout.bind(
            minimum_height=self.lessons_layout.setter("height")
        )

        self.scroll.add_widget(
            self.lessons_layout
        )

        # Дни недели
        self.days_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(52),
            spacing=dp(6)
        )

        self.layout.add_widget(self.top_bar)
        self.layout.add_widget(self.scroll)
        self.layout.add_widget(self.days_bar)

        self.add_widget(self.layout)

        Clock.schedule_interval(
            self.update_live_clock,
            1
        )

    def update_live_clock(self, dt):
        self.time_clock_label.text = (
            datetime.now().strftime("%H:%M:%S")
        )

    def on_enter(self):
        self.refresh_ui()

    def refresh_ui(self):

        global CURRENT_SELECTED_DAY

        day_full_names = {
            "Пн": "Понедельник",
            "Вт": "Вторник",
            "Ср": "Среда",
            "Чт": "Четверг",
            "Пт": "Пятница",
            "Сб": "Суббота"
        }

        self.day_label.text = (
            f"Сегодня: "
            f"{day_full_names.get(CURRENT_SELECTED_DAY, CURRENT_SELECTED_DAY)}"
        )

        self.lessons_layout.clear_widgets()

        day_lessons = APP_DATA[
            "schedule"
        ].get(
            CURRENT_SELECTED_DAY,
            []
        )

        for lesson in day_lessons:

            card = MDBoxLayout(
                padding=dp(10),
                size_hint_y=None,
                height=dp(90),
                orientation="horizontal",
                spacing=dp(10)
            )

            text_box = MDBoxLayout(
                orientation="vertical"
            )

            lesson_name = (
                lesson.get("name", "").strip()
                or "—"
            )

            hw_text = (
                lesson.get("hw", "").strip()
                or "Нет задания"
            )

            is_done = lesson.get(
                "done",
                False
            )

            lbl_num = MDLabel(
                text=(
                    f"Урок {lesson['num']}: "
                    f"{lesson_name}"
                ),
                font_style="Title",
                role="small"
            )

            lbl_hw = MDLabel(
                text=f"ДЗ: {hw_text}",
                font_style="Body",
                role="medium"
            )

            text_box.add_widget(lbl_num)
            text_box.add_widget(lbl_hw)

            card.add_widget(text_box)

            if lesson.get("hw", "").strip():

                check_btn = MDIconButton(
                    icon=(
                        "checkbox-marked-circle"
                        if is_done
                        else "checkbox-blank-circle-outline"
                    ),
                    theme_icon_color="Custom",
                    icon_color=(
                        (0.2, 0.8, 0.2, 1)
                        if is_done
                        else (0.6, 0.6, 0.6, 1)
                    ),
                    size_hint=(None, None),
                    size=(dp(48), dp(48)),
                    pos_hint={"center_y": 0.5},
                    on_release=lambda x, l=lesson:
                        self.handle_click_done(l)
                )

                card.add_widget(check_btn)

            self.lessons_layout.add_widget(card)

        # Дни
        self.days_bar.clear_widgets()

        days = [
            "Пн",
            "Вт",
            "Ср",
            "Чт",
            "Пт"
        ]

        if APP_DATA.get(
            "has_saturday",
            True
        ):
            days.append("Сб")

        for d in days:

            style_type = (
                "filled"
                if d == CURRENT_SELECTED_DAY
                else "tonal"
            )

            btn = MDButton(
                style=style_type,
                size_hint_x=1,
                height=dp(44),
                on_release=lambda x, day=d:
                    self.change_day(day)
            )

            btn.add_widget(
                MDButtonText(
                    text=d
                )
            )

            self.days_bar.add_widget(btn)

    def change_day(self, day_name):

        global CURRENT_SELECTED_DAY

        CURRENT_SELECTED_DAY = day_name

        self.refresh_ui()

    def handle_click_done(self, lesson):

        if lesson.get("done", False):
            self.show_already_done_dialog()
        else:
            self.confirm_done(lesson)

    def show_already_done_dialog(self):

        btn_ok = MDButton(
            style="text",
            on_release=lambda x:
                self.dialog.dismiss()
                if self.dialog
                else None
        )

        btn_ok.add_widget(
            MDButtonText(text="ОК")
        )

        btn_container = MDDialogButtonContainer()

        btn_container.add_widget(btn_ok)

        self.dialog = MDDialog(
            MDDialogHeadlineText(
                text="Уже сделано!"
            ),
            MDDialogSupportingText(
                text=(
                    "Задание по этому уроку "
                    "уже отмечено выполненным."
                )
            ),
            btn_container
        )

        self.dialog.open()

        Clock.schedule_once(
            lambda dt:
                self.dialog.dismiss()
                if self.dialog
                else None,
            4
        )

    def confirm_done(self, lesson):

        chance_bad_grade = (
            random.randint(1, 10) == 1
        )

        warning_text = (
            "Вы точно всё сделали?\n\n"
            "(Внимание: если вы схитрили, "
            "есть 10% шанс получить отрицательную оценку!)"
        )

        if chance_bad_grade:

            warning_text += (
                "\n\n⚠️ ОЙ! Похоже, учитель заметил "
                "неладное и поставил вам 2-ку!"
            )

        btn_cancel = MDButton(
            style="text",
            on_release=lambda x:
                self.dialog.dismiss()
                if self.dialog
                else None
        )

        btn_cancel.add_widget(
            MDButtonText(text="Отмена")
        )

        btn_confirm = MDButton(
            style="filled",
            on_release=lambda x, l=lesson:
                self.toggle_lesson_done(l)
        )

        btn_confirm.add_widget(
            MDButtonText(
                text="Точно всё сделал!"
            )
        )

        btn_container = MDDialogButtonContainer()

        btn_container.add_widget(
            btn_cancel
        )

        btn_container.add_widget(
            btn_confirm
        )

        self.dialog = MDDialog(
            MDDialogHeadlineText(
                text="Проверка выполнения ДЗ"
            ),
            MDDialogSupportingText(
                text=warning_text
            ),
            btn_container
        )

        self.dialog.open()

    def toggle_lesson_done(self, lesson):

        lesson["done"] = True

        save_data(APP_DATA)

        if self.dialog:
            self.dialog.dismiss()

        self.refresh_ui()

    def open_editor(self, instance):

        self.manager.transition = SlideTransition(
            direction="left"
        )

        self.manager.current = "hw_editor"

    def open_settings(self, instance):

        self.manager.transition = SlideTransition(
            direction="left"
        )

        self.manager.current = "settings_screen"


# ============================================================
# НАСТРОЙКИ
# ============================================================

class SettingsScreen(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = MDBoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(15)
        )

        top_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(52),
            spacing=dp(10)
        )

        back_btn = MDIconButton(
            icon="arrow-left",
            on_release=self.go_back
        )

        title = MDLabel(
            text="Настройки",
            font_style="Title",
            role="large"
        )

        top_bar.add_widget(back_btn)
        top_bar.add_widget(title)

        scroll = MDScrollView()

        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(20),
            size_hint_y=None,
            padding=[
                0,
                dp(5),
                0,
                dp(15)
            ]
        )

        content.bind(
            minimum_height=content.setter("height")
        )

        ver_label = MDLabel(
            text="Версия: Android beta 1.01.4",
            font_style="Body",
            role="medium",
            size_hint_y=None,
            height=dp(24)
        )

        # Время
        time_card = MDBoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(8),
            size_hint_y=None
        )

        time_card.bind(
            minimum_height=time_card.setter("height")
        )

        time_title = MDLabel(
            text="Первое напоминание (ЧЧ:ММ)",
            font_style="Title",
            role="small",
            size_hint_y=None,
            height=dp(24)
        )

        self.time_input = MDTextField(
            mode="outlined",
            size_hint_y=None,
            height=dp(52)
        )

        self.time_input.add_widget(
            MDTextFieldHintText(
                text="например 17:00"
            )
        )

        self.time_input.text = SETTINGS.get(
            "notify_time",
            "17:00"
        )

        time_card.add_widget(time_title)
        time_card.add_widget(self.time_input)

        # Интервал
        self.repeat_interval = SETTINGS.get(
            "repeat_interval",
            15
        )

        interval_card = MDBoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(10),
            size_hint_y=None
        )

        interval_card.bind(
            minimum_height=interval_card.setter("height")
        )

        interval_title = MDLabel(
            text=(
                "Повторять напоминание "
                "если не сделано:"
            ),
            font_style="Title",
            role="small",
            size_hint_y=None,
            height=dp(30)
        )

        self.interval_box = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(48)
        )

        self.build_interval_buttons()

        interval_card.add_widget(interval_title)
        interval_card.add_widget(self.interval_box)

        # Цвет
        color_card = MDBoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(12),
            size_hint_y=None
        )

        color_card.bind(
            minimum_height=color_card.setter("height")
        )

        color_title = MDLabel(
            text="Цвет интерфейса приложения:",
            font_style="Title",
            role="small",
            size_hint_y=None,
            height=dp(30)
        )

        self.selected_color = SETTINGS.get(
            "theme_color",
            "Фиолетовый"
        )

        self.colors_grid = GridLayout(
            cols=2,
            spacing=[
                dp(10),
                dp(10)
            ],
            size_hint_y=None
        )

        self.colors_grid.bind(
            minimum_height=self.colors_grid.setter(
                "height"
            )
        )

        self.build_color_buttons()

        color_card.add_widget(color_title)
        color_card.add_widget(
            self.colors_grid
        )

        # Уведомления
        self.is_enabled = SETTINGS.get(
            "enabled",
            True
        )

        self.toggle_container = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(48)
        )

        self.build_toggle_button()

        # Сохранение
        save_btn = MDButton(
            style="filled",
            pos_hint={"center_x": 0.5},
            size_hint_x=None,
            width=dp(240),
            height=dp(48),
            on_release=self.save
        )

        save_btn.add_widget(
            MDButtonText(
                text="Сохранить настройки"
            )
        )

        content.add_widget(ver_label)
        content.add_widget(time_card)
        content.add_widget(interval_card)
        content.add_widget(color_card)
        content.add_widget(self.toggle_container)
        content.add_widget(save_btn)

        scroll.add_widget(content)

        layout.add_widget(top_bar)
        layout.add_widget(scroll)

        self.add_widget(layout)

    def build_interval_buttons(self):

        self.interval_box.clear_widgets()

        for mins in [5, 15, 30]:

            is_sel = (
                self.repeat_interval == mins
            )

            btn = MDButton(
                style=(
                    "filled"
                    if is_sel
                    else "tonal"
                ),
                size_hint_x=1,
                height=dp(48),
                on_release=lambda x, m=mins:
                    self.set_interval(m)
            )

            btn.add_widget(
                MDButtonText(
                    text=f"{mins} мин"
                )
            )

            self.interval_box.add_widget(btn)

    def set_interval(self, mins):

        self.repeat_interval = mins

        self.build_interval_buttons()

    def build_color_buttons(self):

        self.colors_grid.clear_widgets()

        all_colors = [
            "Зеленый",
            "Белый",
            "Красный",
            "Синий",
            "Оранжевый",
            "Фиолетовый",
            "Голубой",
            "Розовый"
        ]

        for c in all_colors:

            is_sel = (
                c == self.selected_color
            )

            btn = MDButton(
                style=(
                    "filled"
                    if is_sel
                    else "tonal"
                ),
                size_hint_x=1,
                height=dp(48),
                on_release=lambda x, col=c:
                    self.set_color(col)
            )

            btn.add_widget(
                MDButtonText(
                    text=c
                )
            )

            self.colors_grid.add_widget(btn)

    def set_color(self, color_name):

        self.selected_color = color_name

        self.build_color_buttons()

    def build_toggle_button(self):

        self.toggle_container.clear_widgets()

        btn = MDButton(
            style=(
                "filled"
                if self.is_enabled
                else "tonal"
            ),
            pos_hint={"center_x": 0.5},
            size_hint_x=None,
            width=dp(220),
            height=dp(48),
            on_release=self.toggle_notifications
        )

        btn.add_widget(
            MDButtonText(
                text=(
                    f"Уведомления: "
                    f"{'ВКЛ' if self.is_enabled else 'ВЫКЛ'}"
                )
            )
        )

        self.toggle_container.add_widget(btn)

    def toggle_notifications(self, instance):

        self.is_enabled = not self.is_enabled

        self.build_toggle_button()

    def go_back(self, instance):

        self.manager.transition = SlideTransition(
            direction="right"
        )

        self.manager.current = "main_menu"

    def save(self, instance):

        SETTINGS["notify_time"] = (
            self.time_input.text.strip()
        )

        SETTINGS["enabled"] = (
            self.is_enabled
        )

        SETTINGS["repeat_interval"] = (
            self.repeat_interval
        )

        SETTINGS["theme_color"] = (
            self.selected_color
        )

        save_settings(SETTINGS)

        app = MDApp.get_running_app()

        app.theme_cls.primary_palette = (
            COLOR_MAP.get(
                self.selected_color,
                "Purple"
            )
        )

        self.go_back(instance)


# ============================================================
# РЕДАКТИРОВАНИЕ РАСПИСАНИЯ
# ============================================================

class HWEditorScreen(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = MDBoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(10)
        )

        top_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(52),
            spacing=dp(10)
        )

        back_btn = MDIconButton(
            icon="arrow-left",
            on_release=self.go_back
        )

        self.title_lbl = MDLabel(
            text="Редактирование урока и ДЗ",
            font_style="Title",
            role="large"
        )

        top_bar.add_widget(back_btn)
        top_bar.add_widget(self.title_lbl)

        scroll = MDScrollView()

        self.inputs_layout = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            size_hint_y=None,
            padding=[
                0,
                dp(10),
                0,
                dp(10)
            ]
        )

        self.inputs_layout.bind(
            minimum_height=self.inputs_layout.setter(
                "height"
            )
        )

        self.name_inputs = []
        self.hw_inputs = []

        for i in range(1, 8):

            card = MDBoxLayout(
                orientation="vertical",
                padding=dp(10),
                spacing=dp(10),
                size_hint_y=None,
                height=dp(190)
            )

            lbl = MDLabel(
                text=f"Урок {i}",
                font_style="Title",
                role="small",
                size_hint_y=None,
                height=dp(24)
            )

            inp_name = MDTextField(
                mode="outlined",
                size_hint_y=None,
                height=dp(56)
            )

            inp_name.add_widget(
                MDTextFieldHintText(
                    text="Название предмета"
                )
            )

            inp_hw = MDTextField(
                mode="outlined",
                size_hint_y=None,
                height=dp(56)
            )

            inp_hw.add_widget(
                MDTextFieldHintText(
                    text="Задание (ДЗ)"
                )
            )

            self.name_inputs.append(
                inp_name
            )

            self.hw_inputs.append(
                inp_hw
            )

            card.add_widget(lbl)
            card.add_widget(inp_name)
            card.add_widget(inp_hw)

            self.inputs_layout.add_widget(card)

        scroll.add_widget(
            self.inputs_layout
        )

        save_btn = MDButton(
            style="filled",
            pos_hint={"center_x": 0.5},
            size_hint_x=None,
            width=dp(240),
            height=dp(48),
            on_release=self.save_data_editor
        )

        save_btn.add_widget(
            MDButtonText(
                text="Сохранить измененное"
            )
        )

        layout.add_widget(top_bar)
        layout.add_widget(scroll)
        layout.add_widget(save_btn)

        self.add_widget(layout)

    def on_enter(self):

        self.title_lbl.text = (
            f"Редактирование "
            f"({CURRENT_SELECTED_DAY})"
        )

        day_lessons = APP_DATA[
            "schedule"
        ].get(
            CURRENT_SELECTED_DAY,
            []
        )

        for i in range(7):

            if i < len(day_lessons):

                self.name_inputs[i].text = (
                    day_lessons[i].get(
                        "name",
                        ""
                    )
                )

                self.hw_inputs[i].text = (
                    day_lessons[i].get(
                        "hw",
                        ""
                    )
                )

    def go_back(self, instance):

        self.manager.transition = SlideTransition(
            direction="right"
        )

        self.manager.current = "main_menu"

    def save_data_editor(self, instance):

        day_lessons = APP_DATA[
            "schedule"
        ].get(
            CURRENT_SELECTED_DAY,
            []
        )

        for i in range(7):

            day_lessons[i]["name"] = (
                self.name_inputs[i].text.strip()
            )

            day_lessons[i]["hw"] = (
                self.hw_inputs[i].text.strip()
            )

            day_lessons[i]["done"] = False

        APP_DATA[
            "schedule"
        ][CURRENT_SELECTED_DAY] = day_lessons

        save_data(APP_DATA)

        self.go_back(instance)


# ============================================================
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ============================================================

class SchoolApp(MDApp):

    def build(self):

        self.theme_cls.theme_style = "Dark"

        current_color_name = SETTINGS.get(
            "theme_color",
            "Фиолетовый"
        )

        self.theme_cls.primary_palette = (
            COLOR_MAP.get(
                current_color_name,
                "Purple"
            )
        )

        sm = ScreenManager()

        sm.add_widget(
            MainMenuScreen(
                name="main_menu"
            )
        )

        sm.add_widget(
            HWEditorScreen(
                name="hw_editor"
            )
        )

        sm.add_widget(
            SettingsScreen(
                name="settings_screen"
            )
        )

        return sm

    def on_start(self):
        """
        Запускаем проверку уведомлений
        после полного запуска приложения.
        """

        threading.Thread(
            target=notification_checker,
            daemon=True
        ).start()


if __name__ == "__main__":
    SchoolApp().run()
```
