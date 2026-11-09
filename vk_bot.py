import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import random
import datetime
import json
import time
import traceback
import threading


class VKBot:
    def __init__(self, token, teacher_id):
        self.token = token
        self.vk = vk_api.VkApi(token=token)
        self.longpoll = VkLongPoll(self.vk)
        self.user_states = {}
        self.pending_requests = {}
        self.confirmed_requests = {}
        self.rejected_requests = {}
        self.daily_counters = {}
        self.teacher_id = teacher_id
        self.sent_reminders = set()
        self.sent_daily_reports = set()

        # --- Задачи: у каждого пользователя свои ---
        self.tasks = {}
        self.task_counters = {}
        self.task_reminders = {}
        self.task_reminder_counter = {}
        self.sent_task_reminders = set()

        self.messages = {
            'start': (
                '👋 Здравствуйте! Вас приветствует Ассистент.\n\n'
                'Вы можете посмотреть актуальное расписание, электронный журнал, '
                'записаться на сдачу (пересдачу), вести свои задачи, '
                'узнать про ML-кружок или найти материалы.'
            ),
            'ask_name': '📝 Напишите свою Фамилию и Имя:',
            'ask_group': '🏫 Напишите свою группу:',
            'confirm': '✅ Отправляем запрос преподавателю. Подтверждаете? (Да/Нет)',
        }

        self.journal_links = {
            '1 курс': {
                '🔥#МЛ_26_1': 'https://docs.google.com/spreadsheets/d/1ZdKh9NQ0MUMCUf_IYR_5DHjmIf69TZ6_6SBLSL781is/edit?usp=drive_link',
                '⚙#СДН_26_1': 'https://docs.google.com/spreadsheets/d/1MkMJkWAb1anfP9Ipx4mzUSSJkDT3QxuLHceKB2ot5SA/edit?usp=drive_link',
                '🎨#ТХ_26_1': 'https://docs.google.com/spreadsheets/d/12r-35sBfRTwkJU3e0bCIjy8E1tJicyfc9n21ezKFxnA/edit?usp=drive_link',
                '🚛 #ЭМТ_26_1': 'https://docs.google.com/spreadsheets/d/1Ji_1dD00SX7zNLpG85B4aFhit8UTjfw7vwIKkOfyBl0/edit?usp=drive_link',
                '💡#ЭО_26_1': 'https://docs.google.com/spreadsheets/d/19R8cJiLTUWTTKvTjPx14ylJEICrrlWpmG1thhCEyoQY/edit?usp=drive_link',
                '🔋#ЭО_26_2': 'https://docs.google.com/spreadsheets/d/1Dp3QrYpT3TiSimW1odReelhtFF0lz72jvf0E3ILVkfM/edit?usp=drive_link',
            },
            '3 курс': {
                '💿#АИ_24_1': 'https://docs.google.com/spreadsheets/d/1D7OkwMXWxKE415L_-PcwEljZN8wAS6-9YZJ9kEWmyyU/edit?usp=drive_link',
                '💻#АС_24_1': 'https://docs.google.com/spreadsheets/d/1boVnRx3TmLTrquGYvF1ue7QM4KTAUzKAlM_006SIJqs/edit?usp=drive_link',
                '🖥#АС_24_2': 'https://docs.google.com/spreadsheets/d/1ehyNSWEcWmiRRyjQTt5AmYveFLttF0CMS6y6K8FMzpE/edit?usp=drive_link',
                '📈#САУ_24_1': 'https://docs.google.com/spreadsheets/d/1QTQK7uMg17Xbpgab1UrvCCeusjFxAIDiTQzfkWQxuak/edit?usp=drive_link',
                '➗#ПМ_24_1': 'https://docs.google.com/spreadsheets/d/177LvC5GragRxmGAtZ-ua63LM--7G0AgforMky1dGq5k/edit?usp=drive_link',
                '♾#ПМ_24_2': 'https://docs.google.com/spreadsheets/d/1-LrT8T9kE3Q0YmNw7BEnL8MFzoXeT84kGmcBqYzVG1g/edit?usp=drive_link',
            },
            '4 курс': {
                '🧮#ПМ_23_1': 'https://docs.google.com/spreadsheets/d/1_el3r1YGp6ME2aJ3vkH89ElEIwEyBD8Fm11CLp7LMLE/edit?usp=drive_link',
            }
        }

        self.materials = {
            'Нейросетевые методы ИИ (3 курс, 5 сем.)': {
                'Лекции': [
                    ('Лекция 1. Введение в нейронные сети', 'https://disk.yandex.ru/i/6pq32-XWgnsaMw'),
                    ('Лекция 2. Обучение нейронных сетей: прямое и обратное распространение ошибки', 'https://disk.yandex.ru/i/fCwzlvdHbUr2Pw'),
                    ('Лекция 3. Функции потерь', 'https://disk.yandex.ru/i/gKaZEWtqjZBFWA'),
                    ('Лекция 4. Оптимизация', 'https://disk.yandex.ru/i/kcf4PtoG7jkAjg'),
                    ('Лекция 5. Свёртки в нейронных сетях', 'https://disk.yandex.ru/i/nNRAcYovufarpA'),
                ],
                'Лабораторные работы': [
                    ('Лабораторная 1', 'https://disk.yandex.ru/i/6CWXHGJA5qAcgg'),
                    ('Лабораторная 2', 'https://disk.yandex.ru/i/q6eK0CQx98M4Aw'),
                    ('Лабораторная 3', 'https://disk.yandex.ru/i/tId6qe8eSH6LjQ'),
                    ('Лабораторная 4', 'https://disk.yandex.ru/i/gvn6yHfiEAb_qA'),
                ],
            }
        }

        self.material_titles = {
            'Нейросетевые методы ИИ (3 курс, 5 сем.)':
                'Нейросетевые методы искусственного интеллекта (3 курс, 5 семестр)',
        }

        self.section_titles = {
            'Лекции': 'Лекционные материалы',
            'Лабораторные работы': 'Лабораторные работы',
        }

    # ---------- Инициализация структур для пользователя ----------
    def _ensure_user_tasks(self, user_id):
        if user_id not in self.tasks:
            self.tasks[user_id] = {'urgent': [], 'non_urgent': []}
        if user_id not in self.task_counters:
            self.task_counters[user_id] = {'urgent': 0, 'non_urgent': 0}
        if user_id not in self.task_reminders:
            self.task_reminders[user_id] = []
        if user_id not in self.task_reminder_counter:
            self.task_reminder_counter[user_id] = 0

    # ---------- Утилиты ----------
    def get_week_type(self, date=None):
        if date is None:
            date = datetime.datetime.now().date()
        elif isinstance(date, datetime.datetime):
            date = date.date()
        start_date = datetime.date(2026, 9, 1)
        if date < start_date:
            year = date.year
            if date.month < 9:
                year -= 1
            start_date = datetime.date(year, 9, 1)
        delta = (date - start_date).days
        week_number = delta // 7
        return 'white' if week_number % 2 == 0 else 'green'

    def get_week_emoji(self, date=None):
        week_type = self.get_week_type(date)
        return '⬜' if week_type == 'white' else '🟩'

    def get_next_weekday_date(self, weekday_name, time_str, date=None, weeks_ahead=0):
        weekdays = {
            'Понедельник': 0, 'Вторник': 1, 'Среда': 2, 'Четверг': 3,
            'Пятница': 4, 'Суббота': 5, 'Воскресенье': 6
        }
        if date is None:
            today = datetime.datetime.now()
        else:
            if isinstance(date, datetime.datetime):
                today = date
            else:
                today = datetime.datetime.combine(date, datetime.datetime.min.time())
        current_weekday = today.weekday()
        target_weekday = weekdays[weekday_name]
        days_ahead = target_weekday - current_weekday
        if days_ahead <= 0:
            days_ahead += 7
        days_ahead += weeks_ahead * 7
        target_date = today + datetime.timedelta(days=days_ahead)
        hour, minute = map(int, time_str.split(':'))
        return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

    def get_auditorium(self, day_name, time_str, week_type, action_type):
        if action_type in ('debt', 'lab'):
            if day_name == 'Вторник' and time_str == '12:50':
                return '9-424'
            elif day_name == 'Четверг' and time_str == '15:00':
                return '9-426'
            elif day_name == 'Пятница' and time_str == '13:20':
                return '334'
        elif action_type == 'test':
            if day_name == 'Вторник' and time_str == '9:40':
                return '9-410'
            elif day_name == 'Пятница' and time_str == '13:20':
                return '334'
            elif day_name == 'Суббота' and week_type == 'white':
                if time_str == '8:00':
                    return '9-405'
                elif time_str == '9:40':
                    return '9-405'
        return ''

    def get_available_schedule(self, action_type=None):
        today = datetime.datetime.now()
        schedule = {}
        if action_type in ('debt', 'lab'):
            for day, time_str in [('Вторник', '12:50'), ('Четверг', '15:00'), ('Пятница', '13:20')]:
                target_time = self.get_next_weekday_date(day, time_str, today)
                if target_time > today:
                    schedule[f'{day} {time_str}'] = (day, time_str, 0)
        elif action_type == 'test':
            for day, time_str in [('Вторник', '9:40'), ('Пятница', '13:20')]:
                target_time = self.get_next_weekday_date(day, time_str, today)
                if target_time > today:
                    schedule[f'{day} {time_str}'] = (day, time_str, 0)
            for weeks_offset in range(0, 5):
                saturday_time = self.get_next_weekday_date('Суббота', '8:00', today, weeks_offset)
                saturday_date = saturday_time.date()
                if self.get_week_type(saturday_date) == 'white' and saturday_time > today:
                    schedule['Суббота 8:00'] = ('Суббота', '8:00', weeks_offset)
                    saturday_time2 = self.get_next_weekday_date('Суббота', '9:40', today, weeks_offset)
                    if saturday_time2 > today:
                        schedule['Суббота 9:40'] = ('Суббота', '9:40', weeks_offset)
                    break
        return schedule

    # ---------- Отправка/клавиатуры ----------
    def send_message(self, user_id, message, keyboard=None):
        try:
            params = {
                'user_id': user_id,
                'message': message,
                'random_id': random.randint(1, 1000000)
            }
            if keyboard:
                params['keyboard'] = json.dumps(keyboard, ensure_ascii=False)
            self.vk.method('messages.send', params)
            print(f'✅ Отправлено сообщение пользователю {user_id}')
            return True
        except Exception as e:
            print(f'❌ Ошибка отправки: {e}')
            return False

    def create_keyboard(self, buttons, one_time=True):
        keyboard = {'one_time': one_time, 'buttons': []}
        for button in buttons:
            if isinstance(button, tuple) and len(button) == 2:
                label, link = button
                keyboard['buttons'].append([{
                    'action': {'type': 'open_link', 'label': label, 'link': link}
                }])
            else:
                keyboard['buttons'].append([{
                    'action': {'type': 'text', 'label': button},
                    'color': 'primary'
                }])
        return keyboard

    def create_grid_keyboard(self, rows, one_time=True):
        keyboard = {'one_time': one_time, 'buttons': []}
        for row in rows:
            if isinstance(row, str):
                row = (row,)
            button_row = []
            for button in row:
                if isinstance(button, tuple) and len(button) == 2:
                    label, link = button
                    button_row.append({
                        'action': {'type': 'open_link', 'label': label, 'link': link}
                    })
                else:
                    button_row.append({
                        'action': {'type': 'text', 'label': button},
                        'color': 'primary'
                    })
            keyboard['buttons'].append(button_row)
        return keyboard

    # ---------- State helpers ----------
    def get_state(self, user_id):
        if user_id not in self.user_states:
            self.user_states[user_id] = 'start'
        return self.user_states[user_id]

    def set_state(self, user_id, state):
        self.user_states[user_id] = state

    def get_user_data(self, user_id, key, default=None):
        return self.user_states.get(f'{user_id}_{key}', default)

    def set_user_data(self, user_id, key, value):
        self.user_states[f'{user_id}_{key}'] = value

    def clear_user_data(self, user_id):
        keys_to_remove = [k for k in list(self.user_states.keys())
                          if isinstance(k, str) and k.startswith(f'{user_id}_')]
        for key in keys_to_remove:
            del self.user_states[key]

    # ---------- Нумерация заявок ----------
    def make_request_id(self, target_date):
        date_key = target_date.strftime('%d.%m')
        n = self.daily_counters.get(date_key, 0) + 1
        self.daily_counters[date_key] = n
        return f'{n}-{date_key}'

    # ---------- Заявки ----------
    def send_to_teacher(self, request_data):
        try:
            task_type = {
                'debt': 'Пересдача',
                'lab': 'Лабораторная работа',
                'test': 'Контрольная работа'
            }[request_data['type']]
            message = (
                f"📋 Новая заявка на запись!\n\n"
                f"📝 Тип: {task_type}\n"
                f"👤 Студент: {request_data['student_name']}\n"
                f"🏫 Группа: {request_data['group']}\n"
                f"⏰ Время: {request_data['time']}\n"
                f"🆔 Номер заявки: #{request_data['request_id']}\n\n"
                f"Чтобы подтвердить, напишите: да#{request_data['request_id']}\n"
                f"Чтобы отклонить, напишите: нет#{request_data['request_id']} [причина]"
            )
            self.send_message(self.teacher_id, message)
            self.send_message(
                request_data['student_id'],
                f"⏳ Заявка #{request_data['request_id']} отправлена преподавателю.\nОжидайте ответа..."
            )
            return True
        except Exception as e:
            print(f'❌ Ошибка отправки преподавателю: {e}')
            return False

    def process_teacher_response(self, message, user_id):
        try:
            if user_id != self.teacher_id:
                return False
            text = message.strip().lower()

            if text.startswith('отменить#'):
                rest = text[len('отменить#'):].strip()
                parts = rest.split(maxsplit=1)
                request_id = parts[0] if parts else ''
                reason = parts[1] if len(parts) > 1 else 'Не указана'
                if not request_id:
                    self.send_message(self.teacher_id, "❌ Укажите номер: отменить#номер [причина]")
                    return True
                rd = None
                if request_id in self.pending_requests:
                    rd = self.pending_requests.pop(request_id)
                elif request_id in self.confirmed_requests:
                    rd = self.confirmed_requests.pop(request_id)
                else:
                    self.send_message(self.teacher_id, f"❌ Запись #{request_id} не найдена.")
                    return True
                rd['reject_reason'] = reason
                rd['cancelled_by_teacher'] = True
                self.rejected_requests[request_id] = rd
                self.send_message(
                    rd['student_id'],
                    f"🚫 Преподаватель отменил вашу запись #{request_id}.\nПричина: {reason}\n"
                    f"Свяжитесь с преподавателем для уточнения."
                )
                self.send_message(self.teacher_id, f"✅ Запись #{request_id} отменена. Студент уведомлён.")
                return True

            if '#' not in text:
                return False
            head, tail = text.split('#', 1)
            head = head.strip()
            request_id = tail.split()[0] if tail else ''
            if not request_id:
                return False

            if head == 'да':
                if request_id in self.pending_requests:
                    rd = self.pending_requests.pop(request_id)
                    rid = rd['request_id']
                    name, group = rd['student_name'], rd['group']
                    if rd['type'] == 'debt':
                        msg = f"✅ Вы, {name} ({group}), записались на пересдачу!\n📅 {rd['time']}"
                    elif rd['type'] == 'lab':
                        msg = f"✅ Вы, {name} ({group}), записались на сдачу лабораторной работы!\n📅 {rd['time']}"
                    else:
                        msg = f"✅ Вы, {name} ({group}), записались на контрольную работу!\n📅 {rd['time']}"
                    self.send_message(rd['student_id'], msg)
                    self.confirmed_requests[rid] = rd
                    self.send_message(self.teacher_id, f"✅ Заявка #{rid} подтверждена. Студент уведомлён.")
                    return True

            elif head == 'нет':
                reason = ' '.join(tail.split()[1:]) if len(tail.split()) > 1 else 'Не указана'
                if request_id in self.pending_requests:
                    rd = self.pending_requests.pop(request_id)
                    rid = rd['request_id']
                    rd['reject_reason'] = reason
                    self.rejected_requests[rid] = rd
                    self.send_message(
                        rd['student_id'],
                        f"❌ Преподаватель отклонил запись #{rid}.\nПричина: {reason}\n"
                        f"Свяжитесь с преподавателем для уточнения."
                    )
                    self.send_message(self.teacher_id, f"✅ Заявка #{rid} отклонена. Студент уведомлён.")
                    return True
            return False
        except Exception as e:
            print(f'❌ Ошибка обработки ответа преподавателя: {e}')
            return False

    # ---------- Меню ----------
    def handle_start(self, user_id):
        if user_id == self.teacher_id:
            rows = [
                ('Расписание', 'Сдача(Пересдача)'),
                ('Электронный журнал', 'Записи'),
                ('ML-кружок', 'Материалы'),
                ('Задачи', 'О ассистенте'),
            ]
        else:
            rows = [
                ('Расписание', 'Сдача(Пересдача)'),
                ('Электронный журнал', 'Мои записи'),
                ('ML-кружок', 'Материалы'),
                ('Задачи', 'О ассистенте'),
            ]
        self.send_message(user_id, self.messages['start'], self.create_grid_keyboard(rows))
        self.set_state(user_id, 'main_menu')

    def handle_schedule_menu(self, user_id):
        today = datetime.datetime.now()
        week_type = "БЕЛАЯ" if self.get_week_type(today) == 'white' else "ЗЕЛЕНАЯ"
        message = (
            f"📅 Сегодня {today.strftime('%d.%m.%Y')}\n"
            f"Текущая неделя: {self.get_week_emoji(today)} {week_type}\n\n"
            f"Выберите неделю для просмотра расписания:"
        )
        self.send_message(user_id, message, self.create_keyboard(['⬜ Белая неделя', '🟩 Зеленая неделя', 'Назад']))
        self.set_state(user_id, 'schedule_menu')

    def get_week_schedule_text(self, week_type):
        white_schedule = {
            'Вторник': ['08:00-09:30 ауд. 9-412 лек.', '09:40-11:10 ауд. 9-410 лаб.', '11:20-12:50 ауд. 9-424 лаб.'],
            'Среда': ['11:20-12:50 ауд. 357 лаб.', '13:20-14:50 ауд. 9-412 пр.'],
            'Четверг': ['13:20-14:50 ауд. 9-201 пр.', '15:00-16:30 ауд. 9-426 лаб.'],
            'Пятница': ['09:40-11:10 ауд. 9-327 пр.', '11:20-12:50 ауд. 9-327 пр.', '13:20-14:50 ауд. 334 пр.'],
            'Суббота': ['08:00-09:30 ауд. 9-405 пр.', '09:40-11:10 ауд. 9-405 лек.', '11:20-12:50 ауд. 9-405 пр.']
        }
        green_schedule = {
            'Вторник': white_schedule['Вторник'],
            'Среда': white_schedule['Среда'],
            'Четверг': white_schedule['Четверг'],
            'Пятница': white_schedule['Пятница'],
            'Суббота': []
        }
        schedule = white_schedule if week_type == 'white' else green_schedule
        lines = []
        for day, pairs in schedule.items():
            if pairs:
                lines.append(f"📅 {day}:")
                for pair in pairs:
                    lines.append(f"  • {pair}")
                lines.append("")
        return "\n".join(lines).strip()

    def handle_week_schedule(self, user_id, week_type):
        title = "⬜ Белая неделя" if week_type == 'white' else "🟩 Зеленая неделя"
        schedule_text = self.get_week_schedule_text(week_type)
        self.send_message(user_id, f"{title}\n\n{schedule_text}\n\nДля возврата нажмите 'Назад'.",
                          self.create_keyboard(['Назад']))
        self.set_state(user_id, 'week_schedule')

    def handle_action_menu(self, user_id):
        self.send_message(user_id, "📚 Выберите тип работы:",
                          self.create_keyboard(['Пересдача', 'Лабораторная работа', 'Контрольная работа', 'Назад']))
        self.set_state(user_id, 'action_menu')

    def handle_journal_menu(self, user_id):
        self.send_message(user_id, "📖 Выберите курс:", self.create_keyboard(['1 курс', '3 курс', '4 курс', 'Назад']))
        self.set_state(user_id, 'journal_menu')

    def handle_journal_course(self, user_id, course):
        groups = self.journal_links.get(course, {})
        if not groups:
            self.send_message(user_id, "❌ Для этого курса пока нет групп.")
            self.handle_journal_menu(user_id)
            return
        buttons = [(g, l) for g, l in groups.items()] + ['Назад']
        self.send_message(user_id, f"📚 {course}\nВыберите группу:", self.create_keyboard(buttons))
        self.set_state(user_id, f'journal_course_{course}')

    # ---------- Запись на сдачу ----------
    def get_schedule_buttons(self, user_id):
        action_type = self.get_user_data(user_id, 'action_type')
        available_schedule = self.get_available_schedule(action_type)
        today = datetime.datetime.now()
        schedule_items = []
        for display_key, (day_name, time_str, weeks_ahead) in available_schedule.items():
            target_date = self.get_next_weekday_date(day_name, time_str, today, weeks_ahead)
            if target_date < today:
                continue
            week_type = self.get_week_type(target_date)
            auditorium = self.get_auditorium(day_name, time_str, week_type, action_type)
            date_str = target_date.strftime('%d.%m')
            button_text = f"{self.get_week_emoji(target_date)} {day_name} {time_str} ауд.{auditorium} ({date_str})"
            schedule_items.append((target_date, button_text, day_name, time_str, weeks_ahead, week_type, auditorium))
        schedule_items.sort(key=lambda x: x[0])
        buttons = [i[1] for i in schedule_items] + ['Назад']
        if not schedule_items:
            self.send_message(user_id, "❌ В настоящий момент нет доступных слотов для записи.")
        self.set_user_data(user_id, 'schedule_items', schedule_items)
        return buttons

    def handle_time(self, user_id, extra_warning=None):
        buttons = self.get_schedule_buttons(user_id)
        action_type = self.get_user_data(user_id, 'action_type')
        available_schedule = self.get_available_schedule(action_type)
        today = datetime.datetime.now()
        items = []
        for _, (day_name, time_str, weeks_ahead) in available_schedule.items():
            target_date = self.get_next_weekday_date(day_name, time_str, today, weeks_ahead)
            if target_date < today:
                continue
            week_type = self.get_week_type(target_date)
            auditorium = self.get_auditorium(day_name, time_str, week_type, action_type)
            items.append((target_date, day_name, time_str, weeks_ahead, week_type, auditorium))
        items.sort(key=lambda x: x[0])

        message = (extra_warning + "\n\n") if extra_warning else ""
        message += "⏰ Выберите день и время сдачи:\n\n"
        for target_date, day_name, time_str, _, _, auditorium in items:
            message += (f"{self.get_week_emoji(target_date)} {day_name} {time_str} - "
                        f"ауд. {auditorium} ({target_date.strftime('%d.%m.%Y')})\n")
        week_emoji = self.get_week_emoji(today)
        wt = "БЕЛАЯ" if self.get_week_type(today) == 'white' else "ЗЕЛЕНАЯ"
        message += f"\n📅 Текущая неделя: {week_emoji} {wt}"
        self.send_message(user_id, message, self.create_keyboard(buttons))
        self.set_state(user_id, 'time_choose')

    def handle_confirm(self, user_id):
        time_info = self.get_user_data(user_id, 'time')
        name = self.get_user_data(user_id, 'name')
        group = self.get_user_data(user_id, 'group')
        action_type = self.get_user_data(user_id, 'action_type')
        if not all([time_info, name, group, action_type]):
            self.send_message(user_id, '❌ Ошибка: не все данные заполнены. Начните заново.')
            self.clear_user_data(user_id)
            self.handle_start(user_id)
            return
        task_type = {'debt': 'пересдачу', 'lab': 'лабораторную работу', 'test': 'контрольную работу'}[action_type]
        self.send_message(
            user_id,
            f"📋 Проверьте данные:\n👤 ФИО: {name}\n🏫 Группа: {group}\n"
            f"📝 Тип: {task_type}\n⏰ Время: {time_info}\n\nОтправить запрос преподавателю?",
            self.create_keyboard(['Да', 'Нет'])
        )
        self.set_state(user_id, 'confirm')

    # ---------- Материалы ----------
    def handle_materials_menu(self, user_id):
        subjects = list(self.materials.keys())
        if not subjects:
            self.send_message(user_id, "📭 Материалов пока нет.", self.create_keyboard(['Назад']))
            self.set_state(user_id, 'materials_menu')
            return
        buttons = subjects + ['Назад']
        self.send_message(user_id, "📚 Материалы\nВыберите дисциплину:", self.create_keyboard(buttons))
        self.set_state(user_id, 'materials_menu')

    def handle_material_subject(self, user_id, subject):
        sections = self.materials.get(subject, {})
        if not sections:
            self.send_message(user_id, "❌ Для этой дисциплины пока нет разделов.")
            self.handle_materials_menu(user_id)
            return
        self.set_user_data(user_id, 'material_subject', subject)
        buttons = list(sections.keys()) + ['Назад']
        full_title = self.material_titles.get(subject, subject)
        self.send_message(user_id, f"📚 {full_title}\nВыберите раздел:", self.create_keyboard(buttons))
        self.set_state(user_id, 'material_subject')

    def handle_material_section(self, user_id, section):
        subject = self.get_user_data(user_id, 'material_subject')
        if not subject or subject not in self.materials:
            self.send_message(user_id, "❌ Ошибка: дисциплина не выбрана. Начните заново.")
            self.handle_materials_menu(user_id)
            return
        materials = self.materials[subject].get(section, [])
        if not materials:
            self.send_message(user_id, "📭 В этом разделе пока нет материалов.",
                              self.create_keyboard(['Назад']))
            self.set_state(user_id, 'material_section')
            return

        full_section = self.section_titles.get(section, section)
        if section == 'Лекции':
            icon = '📚'
        elif section == 'Лабораторные работы':
            icon = '🧪'
        else:
            icon = '📂'

        lines = [f"{icon} {full_section}\n"]
        for label, link in materials:
            lines.append(f"{label}\n{link}\n")
        message = "\n".join(lines).strip()

        self.send_message(user_id, message, self.create_keyboard(['Назад']))
        self.set_state(user_id, 'material_section')

    # ---------- ЗАДАЧИ ----------
    def handle_tasks_menu(self, user_id):
        self._ensure_user_tasks(user_id)
        user_tasks = self.tasks[user_id]
        lines = ["📝 Задачи", ""]

        lines.append(f"🔴 Срочные ({len(user_tasks['urgent'])}):")
        if user_tasks['urgent']:
            for t in user_tasks['urgent']:
                lines.append(f"  {t['id']}. {t['text']}")
        else:
            lines.append("  📭 Задач нет.")
        lines.append("")

        lines.append(f"🟢 Не срочные ({len(user_tasks['non_urgent'])}):")
        if user_tasks['non_urgent']:
            for t in user_tasks['non_urgent']:
                lines.append(f"  {t['id']}. {t['text']}")
        else:
            lines.append("  📭 Задач нет.")

        self.send_message(user_id, "\n".join(lines),
                          self.create_keyboard(['Срочные', 'Не срочные', 'Назад']))
        self.set_state(user_id, 'tasks_menu')

    def _format_task_list(self, user_id, category):
        self._ensure_user_tasks(user_id)
        tasks = self.tasks[user_id][category]
        if not tasks:
            return "📭 Задач нет."
        return "\n".join(f"{t['id']}. {t['text']}" for t in tasks)

    def handle_task_category(self, user_id, category):
        self._ensure_user_tasks(user_id)
        self.set_user_data(user_id, 'task_category', category)
        title = "🔴 Срочные задачи" if category == 'urgent' else "🟢 Не срочные задачи"
        body = self._format_task_list(user_id, category)
        lines = [title, "", body]
        self.send_message(user_id, "\n".join(lines),
                          self.create_keyboard(['Добавить задачу', 'Удалить задачу',
                                                'Настроить оповещение', 'Назад']))
        self.set_state(user_id, 'task_category')

    def handle_task_add(self, user_id):
        self._ensure_user_tasks(user_id)
        self.send_message(user_id, "✏️ Напишите текст задачи:", self.create_keyboard(['Назад']))
        self.set_state(user_id, 'task_add')

    def handle_task_delete(self, user_id):
        self._ensure_user_tasks(user_id)
        self.send_message(user_id, "🗑 Напишите номер задачи, которую нужно удалить:",
                          self.create_keyboard(['Назад']))
        self.set_state(user_id, 'task_delete')

    def _get_category_reminders(self, user_id, category):
        self._ensure_user_tasks(user_id)
        return [r for r in self.task_reminders[user_id] if r['category'] == category]

    def _format_reminder(self, r, idx):
        if r['mode'] == 'daily':
            return f"{idx}. Раз в день в {r['time']}"
        else:
            end = r.get('end') or 'без окончания'
            return f"{idx}. Каждые {r['interval']} мин с {r['start']} до {end}"

    def handle_task_reminder_menu(self, user_id):
        self._ensure_user_tasks(user_id)
        cat = self.get_user_data(user_id, 'task_category', 'urgent')
        cat_title = "🔴 Срочные" if cat == 'urgent' else "🟢 Не срочные"
        reminders = self._get_category_reminders(user_id, cat)

        lines = [f"🔔 Напоминания о задачах ({cat_title}):", ""]
        if reminders:
            for i, r in enumerate(reminders, 1):
                lines.append(self._format_reminder(r, i))
        else:
            lines.append("📭 По умолчанию напоминаний нет.")
            lines.append("💡 Вы можете настроить их как вам удобно.")
        lines.append("")
        lines.append("Выберите действие:")

        buttons = ['Раз в день', 'С периодичностью']
        if reminders:
            buttons.append('Удалить напоминание')
        buttons.append('Назад')

        self.send_message(user_id, "\n".join(lines), self.create_keyboard(buttons))
        self.set_state(user_id, 'task_reminder_menu')

    def handle_task_reminder_delete(self, user_id):
        self._ensure_user_tasks(user_id)
        cat = self.get_user_data(user_id, 'task_category', 'urgent')
        cat_title = "🔴 Срочные" if cat == 'urgent' else "🟢 Не срочные"
        reminders = self._get_category_reminders(user_id, cat)

        if not reminders:
            self.send_message(user_id, "📭 Нет напоминаний для удаления.",
                              self.create_keyboard(['Назад']))
            self.set_state(user_id, 'task_reminder_delete')
            return

        lines = [f"🗑 Удаление напоминаний ({cat_title}):", ""]
        for i, r in enumerate(reminders, 1):
            lines.append(self._format_reminder(r, i))
        lines.append("")
        lines.append("Напишите номер напоминания, которое нужно удалить.")
        self.send_message(user_id, "\n".join(lines), self.create_keyboard(['Назад']))
        self.set_state(user_id, 'task_reminder_delete')

    # ---------- ЗАДАЧИ: фоновые проверки ----------
    def check_task_reminders(self, now):
        for uid, reminders in list(self.task_reminders.items()):
            for rem in reminders:
                try:
                    cur_min = now.hour * 60 + now.minute
                    if rem['mode'] == 'daily':
                        hh, mm = map(int, rem['time'].split(':'))
                        target_min = hh * 60 + mm
                        key = f"daily_{uid}_{rem['id']}_{now.strftime('%Y-%m-%d')}_{rem['time']}"
                        if cur_min == target_min and key not in self.sent_task_reminders:
                            self.sent_task_reminders.add(key)
                            self._send_task_reminder(uid, rem)
                    elif rem['mode'] == 'interval':
                        sh, sm = map(int, rem['start'].split(':'))
                        start_min = sh * 60 + sm
                        end_min = None
                        if rem.get('end'):
                            eh, em = map(int, rem['end'].split(':'))
                            end_min = eh * 60 + em
                        if cur_min < start_min:
                            continue
                        if end_min is not None and cur_min > end_min:
                            continue
                        interval = rem['interval']
                        if (cur_min - start_min) % interval == 0:
                            key = f"interval_{uid}_{rem['id']}_{now.strftime('%Y-%m-%d')}_{cur_min}"
                            if key in self.sent_task_reminders:
                                continue
                            self.sent_task_reminders.add(key)
                            self._send_task_reminder(uid, rem)
                except Exception as e:
                    print(f'❌ Ошибка в check_task_reminders: {e}')

    def _send_task_reminder(self, user_id, rem):
        category = rem['category']
        title = "🔴 Срочные" if category == 'urgent' else "🟢 Не срочные"
        body = self._format_task_list(user_id, category)
        lines = [f"🔔 Напоминание о задачах ({title}):\n", body]
        self.send_message(user_id, "\n".join(lines))

    # ---------- О ассистенте ----------
    def handle_about(self, user_id):
        message = (
            "ℹ️ О ассистенте\n\n"
            "Этот бот — ваш цифровой помощник в учебном процессе. "
            "Он создан, чтобы упростить взаимодействие студентов и преподавателя.\n\n"
            "🎓 Для студентов:\n"
            "📅 актуальное расписание занятий (белая / зелёная неделя);\n"
            "📖 электронный журнал по группам и курсам;\n"
            "📝 запись на пересдачу, лабораторные и контрольные работы;\n"
            "🗂 просмотр своих записей и их статусов;\n"
            "⏰ напоминание за 2 часа до записи;\n"
            "📚 доступ к лекционным материалам и лабораторным работам;\n"
            "✅ личный список задач (срочные / не срочные) — "
            "записывайте контрольные, типовые расчёты, курсовые и другие дела, "
            "чтобы ничего не забыть;\n"
            "🔔 по умолчанию напоминаний нет — вы можете настроить их как вам удобно: "
            "раз в день в заданное время или с периодичностью в заданном интервале;\n"
            "🤖 информация о ML-кружке «Липовый интеллект».\n\n"
            "👨‍🏫 Для преподавателя:\n"
            "✅ подтверждение / отклонение / отмена заявок студентов;\n"
            "📒 просмотр всех записей (прошедших за неделю и предстоящих);\n"
            "📅 ежедневный отчёт о записях в 7:00;\n"
            "📝 список задач (срочные и не срочные) с возможностью добавления, "
            "удаления и настройки напоминаний;\n"
            "🔔 по умолчанию напоминаний нет — настраиваются как удобно: "
            "раз в день в заданное время или с периодичностью в заданном интервале.\n\n"
            "💡 Ассистент экономит ваше время и помогает не забыть важное.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👨‍💻 Автор ассистента:\n"
            "Попов Роман Валерьевич\n"
            "кандидат технических наук,\n"
            "старший преподаватель кафедры\n"
            "прикладной математики и системного анализа"
        )
        self.send_message(user_id, message, self.create_keyboard(['Назад']))
        self.set_state(user_id, 'about')

    # ---------- ML-кружок ----------
    def handle_ml_club(self, user_id):
        message = (
            "🤖 ML-кружок \"Липовый интеллект\"\n\n"
            "Приглашаю студентов 2–4 курсов и магистрантов на практикум, "
            "где мы изучаем практическое применение машинного обучения — "
            "от идеи до реальных задач.\n\n"
            "📅 Расписание:\n"
            "⚪ Суббота (белая неделя) — 13:00–14:30, ауд. 9-423\n"
            "🟢 Суббота (зелёная неделя) — 13:00–14:30, ауд. 9-423\n"
            "🟢 Суббота (зелёная неделя) — 14:30–16:00, ауд. 9-423\n\n"
            "🎯 Что будем делать:\n"
            "🔹 решать практические задания по ML;\n"
            "🔹 участвовать в хакатонах;\n"
            "🔹 обсуждать новости машинного обучения;\n"
            "🔹 разбирать теорию и применять её на практике;\n"
            "🔹 помогать друг другу и расти вместе.\n\n"
            "Присоединяйтесь! 🚀"
        )
        self.send_message(user_id, message, self.create_keyboard(['Назад']))
        self.set_state(user_id, 'ml_club')

    # ---------- «Мои записи» (студент) ----------
    def handle_my_requests(self, user_id):
        items = []
        for rid, rd in (list(self.pending_requests.items())
                        + list(self.confirmed_requests.items())
                        + list(self.rejected_requests.items())):
            if rd['student_id'] == user_id:
                if rid in self.pending_requests:
                    status = '⏳ На рассмотрении'
                elif rid in self.confirmed_requests:
                    status = '✅ Подтверждена'
                else:
                    if rd.get('cancelled_by_teacher'):
                        status = '🚫 Отменена преподавателем'
                    else:
                        status = '❌ Отклонена'
                items.append((rd.get('target_date'), rid, rd, status))
        items.sort(key=lambda x: x[0] or datetime.datetime.min)

        if not items:
            self.send_message(user_id, "📭 У вас нет записей.", self.create_keyboard(['Назад']))
            self.set_state(user_id, 'my_requests')
            return

        lines = [
            "📒 Ваши записи:",
            "✅ — подтверждена",
            "⏳ — на рассмотрении",
            "❌ — отклонена",
            "🚫 — отменена преподавателем",
            ""
        ]
        for target_date, rid, rd, status in items:
            task = {'debt': 'Пересдача', 'lab': 'Лабораторная', 'test': 'Контрольная'}[rd['type']]
            time_part = rd['time'].split(' - ')[0] if ' - ' in rd['time'] else rd['time']
            date_str = target_date.strftime('%d.%m.%Y') if target_date else '—'
            lines.append(
                f"#{rid} — {date_str} {time_part}\n"
                f"   📝 {task} | {status}"
            )
            if status in ('❌ Отклонена', '🚫 Отменена преподавателем') and rd.get('reject_reason'):
                lines.append(f"   💬 Причина: {rd['reject_reason']}")
        self.send_message(user_id, "\n".join(lines), self.create_keyboard(['Назад']))
        self.set_state(user_id, 'my_requests')

    # ---------- «Записи» (преподаватель) ----------
    def handle_teacher_requests(self, user_id):
        now = datetime.datetime.now()
        week_ago = now - datetime.timedelta(days=7)
        items = []

        for rid, rd in list(self.pending_requests.items()) + list(self.confirmed_requests.items()):
            td = rd.get('target_date')
            if not td:
                continue
            if td < week_ago:
                continue
            status = '⏳' if rid in self.pending_requests else '✅'
            items.append((td, rid, rd, status))

        items.sort(key=lambda x: x[0])

        header = [
            "📒 Записи:",
            "✅ — подтверждена",
            "⏳ — на рассмотрении",
        ]
        footer = [
            "",
            "Чтобы отменить запись: отменить#номер [причина]"
        ]

        if not items:
            lines = header + ["", "📭 Записей нет."] + footer
            self.send_message(user_id, "\n".join(lines),
                              self.create_keyboard(['Назад']))
            self.set_state(user_id, 'teacher_requests')
            return

        by_day = {}
        for td, rid, rd, status in items:
            key = td.strftime('%d.%m.%Y')
            by_day.setdefault(key, []).append((rid, rd, status))

        lines = header[:]
        for day in sorted(by_day.keys(), key=lambda d: datetime.datetime.strptime(d, '%d.%m.%Y')):
            lines.append(f"\n📅 {day}")
            for rid, rd, status in by_day[day]:
                task = {'debt': 'Пересдача', 'lab': 'Лабораторная', 'test': 'Контрольная'}[rd['type']]
                time_part = rd['time'].split(' - ')[0] if ' - ' in rd['time'] else rd['time']
                lines.append(
                    f"{status} #{rid} | {rd['student_name']} ({rd['group']}) | "
                    f"{task} | {time_part}"
                )
        lines.extend(footer)
        self.send_message(user_id, "\n".join(lines), self.create_keyboard(['Назад']))
        self.set_state(user_id, 'teacher_requests')

    # ---------- Фоновые задачи ----------
    def background_worker(self):
        while True:
            try:
                now = datetime.datetime.now()
                today_key = now.strftime('%Y-%m-%d')

                if now.hour >= 7 and today_key not in self.sent_daily_reports:
                    self.send_daily_report(today_key)

                self.check_reminders(now)
                self.check_task_reminders(now)
                self.cleanup_rejected(now)
                self._cleanup_sent_task_reminders(now)

                time.sleep(30)
            except Exception as e:
                print(f'❌ Ошибка фонового потока: {e}')
                traceback.print_exc()
                time.sleep(30)

    def _cleanup_sent_task_reminders(self, now):
        today = now.strftime('%Y-%m-%d')
        to_del = [k for k in self.sent_task_reminders if today not in k]
        for k in to_del:
            self.sent_task_reminders.discard(k)

    def cleanup_rejected(self, now):
        week_ago = now - datetime.timedelta(days=7)
        to_delete = [rid for rid, rd in self.rejected_requests.items()
                     if rd.get('target_date') and rd['target_date'] < week_ago]
        for rid in to_delete:
            del self.rejected_requests[rid]

    def send_daily_report(self, today_key):
        today = datetime.datetime.now().date()
        items = []
        for rid, rd in self.confirmed_requests.items():
            td = rd.get('target_date')
            if td and td.date() == today:
                items.append((td, rid, rd))
        items.sort(key=lambda x: x[0])

        if not items:
            self.send_message(
                self.teacher_id,
                f"📅 Записи на сегодня ({today.strftime('%d.%m.%Y')}):\n"
                f"❌ Записей нет."
            )
        else:
            lines = [f"📅 Записи на сегодня ({today.strftime('%d.%m.%Y')}):\n"]
            for td, rid, rd in items:
                task = {'debt': 'Пересдача', 'lab': 'Лабораторная', 'test': 'Контрольная'}[rd['type']]
                time_part = rd['time'].split(' - ')[0] if ' - ' in rd['time'] else rd['time']
                lines.append(f"• #{rid} | {rd['student_name']} ({rd['group']}) | {task} | {time_part}")
            self.send_message(self.teacher_id, "\n".join(lines))
        self.sent_daily_reports.add(today_key)

    def check_reminders(self, now):
        for rid, rd in list(self.confirmed_requests.items()):
            td = rd.get('target_date')
            if not td:
                continue
            delta = td - now
            if datetime.timedelta(hours=1, minutes=50) <= delta <= datetime.timedelta(hours=2, minutes=10):
                reminder_key = f'{rid}_{td.strftime("%Y%m%d%H%M")}'
                if reminder_key in self.sent_reminders:
                    continue
                task = {'debt': 'Пересдача', 'lab': 'Лабораторная', 'test': 'Контрольная'}[rd['type']]
                time_part = rd['time'].split(' - ')[0] if ' - ' in rd['time'] else rd['time']
                self.send_message(
                    rd['student_id'],
                    f"⏰ Напоминание!\nЧерез 2 часа у вас запись #{rid}:\n"
                    f"📝 {task}\n📅 {time_part}\n🏫 {rd['time']}"
                )
                self.sent_reminders.add(reminder_key)

    # ---------- Основной обработчик ----------
    def process_message(self, event):
        try:
            user_id = event.user_id
            message = event.text.strip()
            message_lower = message.lower()

            if user_id == self.teacher_id:
                if self.process_teacher_response(message, user_id):
                    return

            state = self.get_state(user_id)

            if message_lower in ['начать', 'start', 'привет', 'здравствуй']:
                self.clear_user_data(user_id)
                self.handle_start(user_id)
                return

            if state in ('start', 'main_menu'):
                if 'расписание' in message_lower:
                    self.handle_schedule_menu(user_id)
                elif 'сдача' in message_lower:
                    self.handle_action_menu(user_id)
                elif 'электронный журнал' in message_lower:
                    self.handle_journal_menu(user_id)
                elif 'ml-кружок' in message_lower or 'ml кружок' in message_lower:
                    self.handle_ml_club(user_id)
                elif 'материалы' in message_lower:
                    self.handle_materials_menu(user_id)
                elif message_lower == 'задачи':
                    self.handle_tasks_menu(user_id)
                elif 'о ассистенте' in message_lower:
                    self.handle_about(user_id)
                elif message_lower == 'записи' and user_id == self.teacher_id:
                    self.handle_teacher_requests(user_id)
                elif message_lower == 'мои записи' and user_id != self.teacher_id:
                    self.handle_my_requests(user_id)
                else:
                    self.handle_start(user_id)

            elif state == 'schedule_menu':
                if 'белая неделя' in message_lower:
                    self.handle_week_schedule(user_id, 'white')
                elif 'зеленая неделя' in message_lower:
                    self.handle_week_schedule(user_id, 'green')
                elif message_lower == 'назад':
                    self.handle_start(user_id)
                else:
                    self.handle_start(user_id)

            elif state == 'week_schedule':
                if message_lower == 'назад':
                    self.handle_schedule_menu(user_id)
                else:
                    self.handle_start(user_id)

            elif state == 'journal_menu':
                if message_lower == 'назад':
                    self.handle_start(user_id)
                elif message in ['1 курс', '3 курс', '4 курс']:
                    self.handle_journal_course(user_id, message)
                else:
                    self.handle_start(user_id)

            elif state.startswith('journal_course_'):
                if message_lower == 'назад':
                    self.handle_journal_menu(user_id)
                else:
                    self.handle_start(user_id)

            elif state == 'materials_menu':
                if message_lower == 'назад':
                    self.handle_start(user_id)
                elif message in self.materials:
                    self.handle_material_subject(user_id, message)
                else:
                    self.handle_materials_menu(user_id)

            elif state == 'material_subject':
                subject = self.get_user_data(user_id, 'material_subject')
                if message_lower == 'назад':
                    self.handle_materials_menu(user_id)
                elif subject and message in self.materials.get(subject, {}):
                    self.handle_material_section(user_id, message)
                else:
                    self.handle_materials_menu(user_id)

            elif state == 'material_section':
                if message_lower == 'назад':
                    subject = self.get_user_data(user_id, 'material_subject')
                    if subject:
                        self.handle_material_subject(user_id, subject)
                    else:
                        self.handle_materials_menu(user_id)
                else:
                    self.handle_materials_menu(user_id)

            elif state == 'tasks_menu':
                if message_lower == 'назад':
                    self.handle_start(user_id)
                elif message_lower == 'срочные':
                    self.handle_task_category(user_id, 'urgent')
                elif message_lower in ('не срочные', 'несрочные'):
                    self.handle_task_category(user_id, 'non_urgent')
                else:
                    self.handle_tasks_menu(user_id)

            elif state == 'task_category':
                if message_lower == 'назад':
                    self.handle_tasks_menu(user_id)
                elif message_lower == 'добавить задачу':
                    self.handle_task_add(user_id)
                elif message_lower == 'удалить задачу':
                    self.handle_task_delete(user_id)
                elif message_lower == 'настроить оповещение':
                    self.handle_task_reminder_menu(user_id)
                else:
                    self.handle_task_category(user_id, self.get_user_data(user_id, 'task_category', 'urgent'))

            elif state == 'task_add':
                if message_lower == 'назад':
                    cat = self.get_user_data(user_id, 'task_category', 'urgent')
                    self.handle_task_category(user_id, cat)
                else:
                    self._ensure_user_tasks(user_id)
                    cat = self.get_user_data(user_id, 'task_category', 'urgent')
                    self.task_counters[user_id][cat] += 1
                    new_id = self.task_counters[user_id][cat]
                    self.tasks[user_id][cat].append({'id': new_id, 'text': message})
                    self.send_message(user_id, f"✅ Задача #{new_id} добавлена.")
                    self.handle_task_category(user_id, cat)

            elif state == 'task_delete':
                if message_lower == 'назад':
                    cat = self.get_user_data(user_id, 'task_category', 'urgent')
                    self.handle_task_category(user_id, cat)
                else:
                    self._ensure_user_tasks(user_id)
                    cat = self.get_user_data(user_id, 'task_category', 'urgent')
                    num_str = message.strip().lstrip('#')
                    if not num_str.isdigit():
                        self.send_message(user_id, "❌ Введите номер задачи (число) или 'Назад'.")
                    else:
                        nid = int(num_str)
                        before = len(self.tasks[user_id][cat])
                        self.tasks[user_id][cat] = [t for t in self.tasks[user_id][cat] if t['id'] != nid]
                        if len(self.tasks[user_id][cat]) < before:
                            for i, t in enumerate(self.tasks[user_id][cat], 1):
                                t['id'] = i
                            self.task_counters[user_id][cat] = len(self.tasks[user_id][cat])
                            self.send_message(user_id, f"🗑 Задача #{nid} удалена.")
                        else:
                            self.send_message(user_id, f"❌ Задача #{nid} не найдена.")
                        self.handle_task_category(user_id, cat)

            elif state == 'task_reminder_menu':
                if message_lower == 'назад':
                    cat = self.get_user_data(user_id, 'task_category', 'urgent')
                    self.handle_task_category(user_id, cat)
                elif message_lower == 'удалить напоминание':
                    self.handle_task_reminder_delete(user_id)
                elif 'раз в день' in message_lower:
                    self.send_message(user_id,
                                      "⏰ Напишите время в формате ЧЧ:ММ (например 09:30), когда напоминать:",
                                      self.create_keyboard(['Назад']))
                    self.set_state(user_id, 'task_reminder_daily_time')
                elif 'с периодичностью' in message_lower:
                    self.send_message(user_id,
                                      "🔁 Напишите интервал в минутах (например 60):",
                                      self.create_keyboard(['Назад']))
                    self.set_state(user_id, 'task_reminder_interval_value')
                else:
                    self.handle_task_reminder_menu(user_id)

            elif state == 'task_reminder_delete':
                if message_lower == 'назад':
                    self.handle_task_reminder_menu(user_id)
                else:
                    self._ensure_user_tasks(user_id)
                    cat = self.get_user_data(user_id, 'task_category', 'urgent')
                    num_str = message.strip().lstrip('#')
                    if not num_str.isdigit():
                        self.send_message(user_id, "❌ Введите номер напоминания (число) или 'Назад'.")
                    else:
                        nid = int(num_str)
                        cat_reminders = self._get_category_reminders(user_id, cat)
                        if 1 <= nid <= len(cat_reminders):
                            target = cat_reminders[nid - 1]
                            self.task_reminders[user_id] = [
                                r for r in self.task_reminders[user_id] if r['id'] != target['id']
                            ]
                            self.send_message(user_id, f"🗑 Напоминание #{nid} удалено (задачи сохранены).")
                        else:
                            self.send_message(user_id, f"❌ Напоминание #{nid} не найдено.")
                        self.handle_task_reminder_menu(user_id)

            elif state == 'task_reminder_daily_time':
                if message_lower == 'назад':
                    self.handle_task_reminder_menu(user_id)
                else:
                    try:
                        hh, mm = map(int, message.strip().split(':'))
                        if not (0 <= hh < 24 and 0 <= mm < 60):
                            raise ValueError
                        self._ensure_user_tasks(user_id)
                        cat = self.get_user_data(user_id, 'task_category', 'urgent')
                        self.task_reminder_counter[user_id] += 1
                        self.task_reminders[user_id].append({
                            'id': self.task_reminder_counter[user_id],
                            'category': cat,
                            'mode': 'daily',
                            'time': f"{hh:02d}:{mm:02d}",
                        })
                        self.send_message(user_id, f"✅ Напоминание раз в день в {hh:02d}:{mm:02d} сохранено.")
                        self.handle_task_reminder_menu(user_id)
                    except Exception:
                        self.send_message(user_id, "❌ Неверный формат. Напишите ЧЧ:ММ, например 09:30.")

            elif state == 'task_reminder_interval_value':
                if message_lower == 'назад':
                    self.handle_task_reminder_menu(user_id)
                else:
                    if not message.strip().isdigit() or int(message.strip()) <= 0:
                        self.send_message(user_id, "❌ Введите целое число минут > 0.")
                    else:
                        self.set_user_data(user_id, 'interval_value', int(message.strip()))
                        self.send_message(user_id,
                                          "⏰ Напишите время начала в формате ЧЧ:ММ:",
                                          self.create_keyboard(['Назад']))
                        self.set_state(user_id, 'task_reminder_interval_start')

            elif state == 'task_reminder_interval_start':
                if message_lower == 'назад':
                    self.handle_task_reminder_menu(user_id)
                else:
                    try:
                        hh, mm = map(int, message.strip().split(':'))
                        if not (0 <= hh < 24 and 0 <= mm < 60):
                            raise ValueError
                        self.set_user_data(user_id, 'interval_start', f"{hh:02d}:{mm:02d}")
                        self.send_message(user_id,
                                          "⏰ Напишите время окончания в формате ЧЧ:ММ "
                                          "(или '-', чтобы без окончания):",
                                          self.create_keyboard(['-', 'Назад']))
                        self.set_state(user_id, 'task_reminder_interval_end')
                    except Exception:
                        self.send_message(user_id, "❌ Неверный формат. Напишите ЧЧ:ММ, например 09:30.")

            elif state == 'task_reminder_interval_end':
                if message_lower == 'назад':
                    self.handle_task_reminder_menu(user_id)
                else:
                    end_time = None
                    if message.strip() != '-':
                        try:
                            hh, mm = map(int, message.strip().split(':'))
                            if not (0 <= hh < 24 and 0 <= mm < 60):
                                raise ValueError
                            end_time = f"{hh:02d}:{mm:02d}"
                        except Exception:
                            self.send_message(user_id, "❌ Неверный формат. Напишите ЧЧ:ММ или '-'.")
                            return
                    self._ensure_user_tasks(user_id)
                    cat = self.get_user_data(user_id, 'task_category', 'urgent')
                    interval = self.get_user_data(user_id, 'interval_value', 60)
                    start = self.get_user_data(user_id, 'interval_start', '09:00')
                    self.task_reminder_counter[user_id] += 1
                    self.task_reminders[user_id].append({
                        'id': self.task_reminder_counter[user_id],
                        'category': cat,
                        'mode': 'interval',
                        'interval': interval,
                        'start': start,
                        'end': end_time,
                    })
                    end_str = end_time if end_time else "без окончания"
                    self.send_message(user_id,
                                      f"✅ Напоминание каждые {interval} мин с {start} до {end_str} сохранено.")
                    self.handle_task_reminder_menu(user_id)

            elif state in ('my_requests', 'teacher_requests', 'ml_club', 'about'):
                if message_lower == 'назад':
                    self.handle_start(user_id)
                else:
                    self.handle_start(user_id)

            elif state == 'action_menu':
                if 'пересдача' in message_lower:
                    self.set_user_data(user_id, 'action_type', 'debt')
                    self.handle_time(user_id)
                elif 'лабораторная' in message_lower:
                    self.set_user_data(user_id, 'action_type', 'lab')
                    self.handle_time(
                        user_id,
                        extra_warning=("⚠️ При записи на лабораторную работу на другую пару помните: "
                                       "сначала сдают те, у кого по расписанию стоит пара.")
                    )
                elif 'контрольная' in message_lower:
                    self.set_user_data(user_id, 'action_type', 'test')
                    self.handle_time(user_id, extra_warning="⚠️ Контрольную работу нельзя писать на своей паре!")
                elif message_lower == 'назад':
                    self.handle_start(user_id)
                else:
                    self.handle_start(user_id)

            elif state == 'time_choose':
                if message_lower == 'назад':
                    self.handle_action_menu(user_id)
                else:
                    schedule_items = self.get_user_data(user_id, 'schedule_items', [])
                    selected = next((it for it in schedule_items if it[1] == message), None)
                    if selected:
                        target_date, _, day_name, time_str, _, _, auditorium = selected
                        time_str_full = f"{day_name} {time_str} - ауд. {auditorium} ({target_date.strftime('%d.%m.%Y')})"
                        self.set_user_data(user_id, 'time', time_str_full)
                        self.set_user_data(user_id, 'target_date', target_date)
                        self.send_message(user_id, self.messages['ask_name'])
                        self.set_state(user_id, 'ask_name')
                    else:
                        self.handle_start(user_id)

            elif state == 'ask_name':
                if len(message.strip().split()) >= 2:
                    self.set_user_data(user_id, 'name', message.strip())
                    self.send_message(user_id, self.messages['ask_group'])
                    self.set_state(user_id, 'ask_group')
                else:
                    self.send_message(user_id, '❌ Пожалуйста, напишите Фамилию и Имя через пробел.')

            elif state == 'ask_group':
                if len(message.strip()) >= 2:
                    self.set_user_data(user_id, 'group', message.strip())
                    self.handle_confirm(user_id)
                else:
                    self.send_message(user_id, '❌ Пожалуйста, укажите группу.')

            elif state == 'confirm':
                if message_lower == 'да':
                    name = self.get_user_data(user_id, 'name')
                    group = self.get_user_data(user_id, 'group')
                    time_str = self.get_user_data(user_id, 'time')
                    action_type = self.get_user_data(user_id, 'action_type')
                    target_date = self.get_user_data(user_id, 'target_date')
                    if not all([name, group, time_str, action_type, target_date]):
                        self.send_message(user_id, '❌ Ошибка: не все данные заполнены. Начните заново.')
                        self.clear_user_data(user_id)
                        self.handle_start(user_id)
                        return

                    request_id = self.make_request_id(target_date)
                    request_data = {
                        'request_id': request_id,
                        'student_id': user_id,
                        'student_name': name,
                        'group': group,
                        'task': {'debt': 'Пересдача', 'lab': 'Лабораторная работа',
                                 'test': 'Контрольная работа'}[action_type],
                        'time': time_str,
                        'type': action_type,
                        'target_date': target_date,
                    }
                    self.pending_requests[request_id] = request_data
                    if self.send_to_teacher(request_data):
                        self.send_message(user_id, f"✅ Заявка #{request_id} отправлена!\nОжидайте ответа преподавателя.")
                    else:
                        date_key = target_date.strftime('%d.%m')
                        self.daily_counters[date_key] = max(0, self.daily_counters.get(date_key, 1) - 1)
                        self.pending_requests.pop(request_id, None)
                        self.send_message(user_id, "❌ Не удалось отправить заявку. Попробуйте позже.")
                    self.clear_user_data(user_id)
                    self.set_state(user_id, 'start')
                    self.handle_start(user_id)
                elif message_lower == 'нет':
                    self.send_message(user_id, '❌ Отмена отправки заявки.')
                    self.clear_user_data(user_id)
                    self.set_state(user_id, 'start')
                    self.handle_start(user_id)
                else:
                    self.handle_start(user_id)

            else:
                self.clear_user_data(user_id)
                self.handle_start(user_id)

        except Exception as e:
            print(f'❌ Критическая ошибка: {e}')
            traceback.print_exc()
            try:
                self.send_message(event.user_id, '❌ Произошла ошибка. Напишите "Начать", чтобы начать заново.')
            except:
                pass
            self.clear_user_data(event.user_id)
            self.set_state(event.user_id, 'start')

    def run(self):
        print('🤖 Бот запущен!')
        print(f'👨‍🏫 ID преподавателя: {self.teacher_id}')
        print('📱 Готов к работе с сообществом')
        print('=' * 50)

        threading.Thread(target=self.background_worker, daemon=True).start()

        try:
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    print('=' * 50)
                    self.process_message(event)
        except Exception as e:
            print(f'❌ Ошибка в основном цикле: {e}')
            traceback.print_exc()


# Настройки
TOKEN = 'vk1.a.6Om-_r3kzMpKtjtJAldQl8YkSc0oLCfTpPZ4KrvEg4O-pYm-VQTGGSxJ6g5Sih1-ezZOHqMWN6bJOZtay3wd2jR6ehVfnKGFnyTShgJ25TF_ZLtWCzrW4OwR3WRW1Gq54bZlhXxbNqYFz9zLwdvowSNcRqOcr0l3Uq9A4-PLRZPvit9HLS3CNgoFwWOkBWoRXoSMu0BR3n0Jd1D7k8s46A'
TEACHER_ID = 144399762

if __name__ == '__main__':
    try:
        bot = VKBot(TOKEN, TEACHER_ID)
        bot.run()
    except Exception as e:
        print(f'❌ Ошибка при запуске: {e}')
        traceback.print_exc()
        input('Нажмите Enter для выхода...')