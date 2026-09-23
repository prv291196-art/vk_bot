import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import random
import datetime
import json
import time
import traceback

class VKBot:
    def __init__(self, token, teacher_id):
        self.token = token
        self.vk = vk_api.VkApi(token=token)
        self.longpoll = VkLongPoll(self.vk)
        self.user_states = {}
        self.pending_requests = {}
        self.teacher_id = teacher_id
        self.request_counter = 0

        self.messages = {
            'start': (
                '👋 Здравствуйте! Вас приветствует Ассистент.\n\n'
                'Вы можете посмотреть актуальное расписание, электронный журнал или записаться на сдачу (пересдачу).'
            ),
            'ask_name': '📝 Напишите свою Фамилию и Имя:',
            'ask_group': '🏫 Напишите свою группу:',
            'confirm': '✅ Отправляем запрос преподавателю. Подтверждаете? (Да/Нет)',
            'teacher_accept_debt': '✅ Вы, {name} ({group}), записались на пересдачу!\n📅 {time}',
            'teacher_accept_lab': '✅ Вы, {name} ({group}), записались на сдачу лабораторной работы!\n📅 {time}',
            'teacher_reject': '❌ Преподаватель отклонил запись. Причина: '
        }

        # Ссылки на электронный журнал
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

    def get_schedule_buttons(self, user_id):
        action_type = self.get_user_data(user_id, 'action_type')
        available_schedule = self.get_available_schedule(action_type)
        today = datetime.datetime.now()
        schedule_items = []
        for display_key, (day_name, time_str, weeks_ahead) in available_schedule.items():
            target_date = self.get_next_weekday_date(day_name, time_str, today, weeks_ahead)
            if target_date < today:
                continue
            date_str = target_date.strftime('%d.%m')
            week_emoji = self.get_week_emoji(target_date)
            week_type = self.get_week_type(target_date)
            auditorium = self.get_auditorium(day_name, time_str, week_type, action_type)
            button_text = f"{week_emoji} {day_name} {time_str} ауд.{auditorium} ({date_str})"
            schedule_items.append((target_date, button_text, day_name, time_str, weeks_ahead, week_type, auditorium))
        schedule_items.sort(key=lambda x: x[0])
        buttons = [item[1] for item in schedule_items]
        buttons.append('Назад')
        if not schedule_items:
            self.send_message(user_id, "❌ В настоящий момент нет доступных слотов для записи.")
        self.set_user_data(user_id, 'schedule_items', schedule_items)
        return buttons

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
            # Если передан кортеж (label, link) — делаем кнопку-ссылку
            if isinstance(button, tuple) and len(button) == 2:
                label, link = button
                keyboard['buttons'].append([{
                    'action': {
                        'type': 'open_link',
                        'label': label,
                        'link': link
                    }
                }])
            else:
                keyboard['buttons'].append([{
                    'action': {'type': 'text', 'label': button},
                    'color': 'primary'
                }])
        return keyboard

    def get_state(self, user_id):
        if user_id not in self.user_states:
            self.user_states[user_id] = 'start'
        return self.user_states[user_id]

    def set_state(self, user_id, state):
        self.user_states[user_id] = state
        print(f'📌 Состояние пользователя {user_id}: {state}')

    def get_user_data(self, user_id, key, default=None):
        data_key = f'{user_id}_{key}'
        return self.user_states.get(data_key, default)

    def set_user_data(self, user_id, key, value):
        data_key = f'{user_id}_{key}'
        self.user_states[data_key] = value
        print(f'💾 Сохранено {key}: {value} для пользователя {user_id}')

    def clear_user_data(self, user_id):
        keys_to_remove = []
        for key in list(self.user_states.keys()):
            if isinstance(key, str) and key.startswith(f'{user_id}_'):
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del self.user_states[key]
        print(f'🧹 Очищены данные пользователя {user_id}')

    def send_to_teacher(self, request_data):
        try:
            task_type = "Пересдача" if request_data['type'] == 'debt' else ("Лабораторная работа" if request_data['type'] == 'lab' else "Контрольная работа")
            message = (
                f"📋 Новая заявка на запись!\n\n"
                f"📝 Тип: {task_type}\n"
                f"👤 Студент: {request_data['student_name']}\n"
                f"🏫 Группа: {request_data['group']}\n"
                f"⏰ Время: {request_data['time']}\n"
                f"🆔 Номер заявки: #{request_data['request_id']}\n"
                f"🆔 VK ID: {request_data['student_id']}\n\n"
                f"Чтобы подтвердить, напишите: Подтвердить #{request_data['request_id']}\n"
                f"Чтобы отклонить, напишите: Отклонить #{request_data['request_id']} [причина]"
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
            text = message.lower()
            if 'подтвердить' in text and '#' in text:
                parts = text.split('#')
                if len(parts) > 1:
                    request_id_str = parts[1].split()[0]
                    if request_id_str.isdigit():
                        request_id = int(request_id_str)
                        if request_id in self.pending_requests:
                            request_data = self.pending_requests[request_id]
                            student_id = request_data['student_id']
                            time_str = request_data['time']
                            name = request_data['student_name']
                            group = request_data['group']
                            if request_data['type'] == 'debt':
                                msg = f"✅ Вы, {name} ({group}), записались на пересдачу!\n📅 {time_str}"
                            elif request_data['type'] == 'lab':
                                msg = f"✅ Вы, {name} ({group}), записались на сдачу лабораторной работы!\n📅 {time_str}"
                            else:
                                msg = f"✅ Вы, {name} ({group}), записались на контрольную работу!\n📅 {time_str}"
                            self.send_message(student_id, msg)
                            del self.pending_requests[request_id]
                            self.send_message(self.teacher_id, f"✅ Заявка #{request_id} подтверждена. Студент уведомлен.")
                            return True
            elif 'отклонить' in text and '#' in text:
                parts = text.split('#')
                if len(parts) > 1:
                    request_part = parts[1].split()
                    if request_part:
                        request_id_str = request_part[0]
                        if request_id_str.isdigit():
                            request_id = int(request_id_str)
                            reason = ' '.join(request_part[1:]) if len(request_part) > 1 else 'Не указана'
                            if request_id in self.pending_requests:
                                request_data = self.pending_requests[request_id]
                                student_id = request_data['student_id']
                                self.send_message(
                                    student_id,
                                    f"❌ Преподаватель отклонил запись.\nПричина: {reason}\nСвяжитесь с преподавателем для уточнения."
                                )
                                del self.pending_requests[request_id]
                                self.send_message(self.teacher_id, f"✅ Заявка #{request_id} отклонена. Студент уведомлен.")
                                return True
            return False
        except Exception as e:
            print(f'❌ Ошибка обработки ответа преподавателя: {e}')
            return False

    def handle_start(self, user_id):
        keyboard = self.create_keyboard(['Расписание', 'Сдача(Пересдача)', 'Электронный журнал'])
        self.send_message(user_id, self.messages['start'], keyboard)
        self.set_state(user_id, 'main_menu')

    def handle_schedule_menu(self, user_id):
        today = datetime.datetime.now()
        week_type = "БЕЛАЯ" if self.get_week_type(today) == 'white' else "ЗЕЛЕНАЯ"
        week_emoji = self.get_week_emoji(today)
        date_str = today.strftime('%d.%m.%Y')
        message = (
            f"📅 Сегодня {date_str}\n"
            f"Текущая неделя: {week_emoji} {week_type}\n\n"
            f"Выберите неделю для просмотра расписания:"
        )
        keyboard = self.create_keyboard(['⬜ Белая неделя', '🟩 Зеленая неделя', 'Назад'])
        self.send_message(user_id, message, keyboard)
        self.set_state(user_id, 'schedule_menu')

    def get_week_schedule_text(self, week_type):
        white_schedule = {
            'Вторник': [
                '08:00-09:30 ауд. 9-412 лек.',
                '09:40-11:10 ауд. 9-410 лаб.',
                '11:20-12:50 ауд. 9-424 лаб.'
            ],
            'Среда': [
                '11:20-12:50 ауд. 357 лаб.',
                '13:20-14:50 ауд. 9-412 пр.'
            ],
            'Четверг': [
                '13:20-14:50 ауд. 9-201 пр.',
                '15:00-16:30 ауд. 9-426 лаб.'
            ],
            'Пятница': [
                '09:40-11:10 ауд. 9-327 пр.',
                '11:20-12:50 ауд. 9-327 пр.',
                '13:20-14:50 ауд. 334 пр.'
            ],
            'Суббота': [
                '08:00-09:30 ауд. 9-405 пр.',
                '09:40-11:10 ауд. 9-405 лек.',
                '11:20-12:50 ауд. 9-405 пр.'
            ]
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
        if week_type == 'white':
            title = "⬜ Белая неделя"
        else:
            title = "🟩 Зеленая неделя"
        schedule_text = self.get_week_schedule_text(week_type)
        message = f"{title}\n\n{schedule_text}\n\nДля возврата нажмите 'Назад'."
        keyboard = self.create_keyboard(['Назад'])
        self.send_message(user_id, message, keyboard)
        self.set_state(user_id, 'week_schedule')

    def handle_action_menu(self, user_id):
        keyboard = self.create_keyboard(['Пересдача', 'Лабораторная работа', 'Контрольная работа', 'Назад'])
        self.send_message(user_id, "📚 Выберите тип работы:", keyboard)
        self.set_state(user_id, 'action_menu')

    # --- Электронный журнал ---
    def handle_journal_menu(self, user_id):
        keyboard = self.create_keyboard(['1 курс', '3 курс', '4 курс', 'Назад'])
        self.send_message(user_id, "📖 Выберите курс:", keyboard)
        self.set_state(user_id, 'journal_menu')

    def handle_journal_course(self, user_id, course):
        groups = self.journal_links.get(course, {})
        if not groups:
            self.send_message(user_id, "❌ Для этого курса пока нет групп.")
            self.handle_journal_menu(user_id)
            return
        # Формируем кнопки-ссылки: (label, link)
        buttons = [(group, link) for group, link in groups.items()]
        buttons.append('Назад')
        keyboard = self.create_keyboard(buttons)
        self.send_message(user_id, f"📚 {course}\nВыберите группу:", keyboard)
        self.set_state(user_id, f'journal_course_{course}')

    def handle_time(self, user_id, extra_warning=None):
        schedule_buttons = self.get_schedule_buttons(user_id)
        keyboard = self.create_keyboard(schedule_buttons)
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
            schedule_items.append((target_date, day_name, time_str, weeks_ahead, week_type, auditorium))
        schedule_items.sort(key=lambda x: x[0])

        message = ""
        if extra_warning:
            message += extra_warning + "\n\n"
        message += "⏰ Выберите день и время сдачи:\n\n"
        for target_date, day_name, time_str, weeks_ahead, week_type, auditorium in schedule_items:
            date_str = target_date.strftime('%d.%m.%Y')
            week_emoji = self.get_week_emoji(target_date)
            message += f"{week_emoji} {day_name} {time_str} - ауд. {auditorium} ({date_str})\n"
        week_emoji = self.get_week_emoji(today)
        week_type = "БЕЛАЯ" if self.get_week_type(today) == 'white' else "ЗЕЛЕНАЯ"
        message += f"\n📅 Текущая неделя: {week_emoji} {week_type}"
        self.send_message(user_id, message, keyboard)
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
        if action_type == 'debt':
            task_type = "пересдачу"
        elif action_type == 'lab':
            task_type = "лабораторную работу"
        else:
            task_type = "контрольную работу"
        keyboard = self.create_keyboard(['Да', 'Нет'])
        self.send_message(
            user_id,
            f"📋 Проверьте данные:\n"
            f"👤 ФИО: {name}\n"
            f"🏫 Группа: {group}\n"
            f"📝 Тип: {task_type}\n"
            f"⏰ Время: {time_info}\n\n"
            f"Отправить запрос преподавателю?",
            keyboard
        )
        self.set_state(user_id, 'confirm')

    def process_message(self, event):
        try:
            user_id = event.user_id
            message = event.text.strip()
            message_lower = message.lower()
            print(f'📨 Получено: "{message}" от {user_id}')
            if user_id == self.teacher_id:
                if self.process_teacher_response(message, user_id):
                    return
            state = self.get_state(user_id)
            print(f'📊 Текущее состояние: {state}')

            if message_lower in ['начать', 'start', 'привет', 'здравствуй']:
                self.clear_user_data(user_id)
                self.handle_start(user_id)
                return

            if state == 'start' or state == 'main_menu':
                if 'расписание' in message_lower:
                    self.handle_schedule_menu(user_id)
                elif 'сдача' in message_lower:
                    self.handle_action_menu(user_id)
                elif 'электронный журнал' in message_lower:
                    self.handle_journal_menu(user_id)
                else:
                    # В главном меню при неверном вводе — просто в начало
                    self.handle_start(user_id)

            elif state == 'schedule_menu':
                if 'белая неделя' in message_lower:
                    self.handle_week_schedule(user_id, 'white')
                elif 'зеленая неделя' in message_lower:
                    self.handle_week_schedule(user_id, 'green')
                elif message_lower == 'назад':
                    self.handle_start(user_id)
                else:
                    # Неверный ввод — в начало
                    self.handle_start(user_id)

            elif state == 'week_schedule':
                if message_lower == 'назад':
                    self.handle_schedule_menu(user_id)
                else:
                    # Неверный ввод — в начало
                    self.handle_start(user_id)

            # --- Электронный журнал ---
            elif state == 'journal_menu':
                if message_lower == 'назад':
                    self.handle_start(user_id)
                elif message in ['1 курс', '3 курс', '4 курс']:
                    self.handle_journal_course(user_id, message)
                else:
                    # Неверный ввод — в начало
                    self.handle_start(user_id)

            elif state.startswith('journal_course_'):
                course = state.replace('journal_course_', '')
                if message_lower == 'назад':
                    self.handle_journal_menu(user_id)
                else:
                    # Неверный ввод — в начало
                    self.handle_start(user_id)

            elif state == 'action_menu':
                if 'пересдача' in message_lower:
                    self.set_user_data(user_id, 'action_type', 'debt')
                    self.handle_time(user_id)
                elif 'лабораторная' in message_lower:
                    self.set_user_data(user_id, 'action_type', 'lab')
                    self.handle_time(
                        user_id,
                        extra_warning=(
                            "⚠️ При записи на лабораторную работу на другую пару помните: "
                            "сначала сдают те, у кого по расписанию стоит пара."
                        )
                    )
                elif 'контрольная' in message_lower:
                    self.set_user_data(user_id, 'action_type', 'test')
                    self.handle_time(
                        user_id,
                        extra_warning=(
                            "⚠️ Контрольную работу нельзя писать на своей паре!"
                        )
                    )
                elif message_lower == 'назад':
                    self.handle_start(user_id)
                else:
                    # Неверный ввод — в начало
                    self.handle_start(user_id)

            elif state == 'time_choose':
                if message_lower == 'назад':
                    self.handle_action_menu(user_id)
                else:
                    schedule_items = self.get_user_data(user_id, 'schedule_items', [])
                    selected_item = None
                    for item in schedule_items:
                        if item[1] == message:
                            selected_item = item
                            break
                    if selected_item:
                        target_date, button_text, day_name, time_str, weeks_ahead, week_type, auditorium = selected_item
                        date_str = target_date.strftime('%d.%m.%Y')
                        time_str_full = f"{day_name} {time_str} - ауд. {auditorium} ({date_str})"
                        self.set_user_data(user_id, 'time', time_str_full)
                        self.send_message(user_id, self.messages['ask_name'])
                        self.set_state(user_id, 'ask_name')
                    else:
                        # Неверный ввод — в начало
                        self.handle_start(user_id)

            elif state == 'ask_name':
                # Здесь НЕ отправляем в начало при неверном вводе — просим ввести снова
                name_parts = message.strip().split()
                if len(name_parts) >= 2:
                    self.set_user_data(user_id, 'name', message.strip())
                    self.send_message(user_id, self.messages['ask_group'])
                    self.set_state(user_id, 'ask_group')
                else:
                    self.send_message(user_id, '❌ Пожалуйста, напишите Фамилию и Имя через пробел.')

            elif state == 'ask_group':
                # Здесь НЕ отправляем в начало при неверном вводе — просим ввести снова
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
                    if not all([name, group, time_str, action_type]):
                        self.send_message(user_id, '❌ Ошибка: не все данные заполнены. Начните заново.')
                        self.clear_user_data(user_id)
                        self.handle_start(user_id)
                        return
                    self.request_counter += 1
                    request_id = self.request_counter
                    request_data = {
                        'request_id': request_id,
                        'student_id': user_id,
                        'student_name': name,
                        'group': group,
                        'task': 'Пересдача' if action_type == 'debt' else ('Лабораторная работа' if action_type == 'lab' else 'Контрольная работа'),
                        'time': time_str,
                        'type': action_type
                    }
                    self.pending_requests[request_id] = request_data
                    if self.send_to_teacher(request_data):
                        self.send_message(user_id, f"✅ Заявка #{request_id} отправлена!\nОжидайте ответа преподавателя.")
                    else:
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
                    # Неверный ввод — в начало
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
        try:
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    print('=' * 50)
                    self.process_message(event)
        except Exception as e:
            print(f'❌ Ошибка в основном цикле: {e}')
            traceback.print_exc()

# Настройки
TOKEN = 'vk1.a.mkFpmi9u2ANOL-wVB9uINJebLwKAL6yZ_CKMrze8hCOrIfhEziM_ztMvg9EYPjDLiPZ8yvw6QV4hYOD32s_1NqkEFFXJgGNKBzDTm_HIVT7C5tnE8pb6UhvRPzPex1SFdCcy73p34rrW61rNjhSv_P0crezSbtEciiJP2ewka6NGBLA9An2qoU21Gr_BjkDb4ec-gptezz5m4vLk41P3Rw'
TEACHER_ID = 144399762

if __name__ == '__main__':
    try:
        bot = VKBot(TOKEN, TEACHER_ID)
        bot.run()
    except Exception as e:
        print(f'❌ Ошибка при запуске: {e}')
        traceback.print_exc()
        input('Нажмите Enter для выхода...')