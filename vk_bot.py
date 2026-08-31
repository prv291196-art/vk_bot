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
        self.pending_requests = {}  # Ожидающие заявки {request_id: data}
        self.teacher_id = teacher_id  # ID преподавателя
        self.request_counter = 0
        
        self.messages = {
            'start': (
                '👋 Здравствуйте! Это бот по записи для сдачи долгов и лабораторных работ.\n\n'
                '📌 Для пересдачи всегда нужно записываться.\n'
                '📌 Если вы хотите сдать лабораторную работу с другой группой или в день консультации — '
                'нужно записаться.\n'
                '📌 Если вы хотите сдать лабораторную на своей паре — записываться не нужно.\n\n'
                'Выберите действие:'
            ),
            'ask_name': '📝 Напишите свою Фамилию и Имя:',
            'ask_group': '🏫 Напишите свою группу:',
            'time': '⏰ Выберите день и время сдачи:',
            'confirm': '✅ Отправляем запрос преподавателю. Подтверждаете? (Да/Нет)',
            'teacher_accept_debt': '✅ Вы, {name} ({group}), записались на пересдачу!\n📅 {time}',
            'teacher_accept_lab': '✅ Вы, {name} ({group}), записались на сдачу лабораторной работы!\n📅 {time}',
            'teacher_reject': '❌ Преподаватель отклонил запись. Причина: '
        }

    def get_week_type(self, date=None):
        """
        Определяет тип недели: 'white' или 'green'
        Белая неделя - четная неделя от 1 сентября 2026 года
        """
        if date is None:
            date = datetime.datetime.now().date()
        elif isinstance(date, datetime.datetime):
            date = date.date()
        
        # Начальная точка: 1 сентября 2026 года - белая неделя
        start_date = datetime.date(2026, 9, 1)
        
        # Если дата раньше 1 сентября 2026
        if date < start_date:
            # Ищем ближайшее 1 сентября в прошлом
            year = date.year
            if date.month < 9:
                year -= 1
            start_date = datetime.date(year, 9, 1)
        
        # Разница в днях от начальной даты
        delta = (date - start_date).days
        
        # Номер недели от начальной даты (0 - первая неделя)
        week_number = delta // 7
        
        # Если неделя четная - белая, нечетная - зеленая
        if week_number % 2 == 0:
            return 'white'
        else:
            return 'green'

    def get_week_emoji(self, date=None):
        """Возвращает эмодзи для обозначения типа недели"""
        week_type = self.get_week_type(date)
        if week_type == 'white':
            return '⬜'
        else:
            return '🟩'

    def get_next_weekday_date(self, weekday_name, time_str, date=None, weeks_ahead=0):
        """Получает дату указанного дня недели с учетом смещения по неделям"""
        weekdays = {
            'Понедельник': 0,
            'Вторник': 1,
            'Среда': 2,
            'Четверг': 3,
            'Пятница': 4,
            'Суббота': 5,
            'Воскресенье': 6
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
        
        # Рассчитываем разницу дней до целевого дня
        days_ahead = target_weekday - current_weekday
        
        # Если целевой день уже прошел на этой неделе, берем следующую неделю
        if days_ahead <= 0:
            days_ahead += 7
        
        # Добавляем смещение по неделям
        days_ahead += weeks_ahead * 7
        
        target_date = today + datetime.timedelta(days=days_ahead)
        
        # Устанавливаем время
        hour, minute = map(int, time_str.split(':'))
        target_datetime = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return target_datetime

    def get_auditorium(self, day_name, time_str, week_type):
        """Возвращает аудиторию для указанного дня, времени и типа недели"""
        if day_name == 'Вторник':
            return '9-424'
        elif day_name == 'Четверг':
            return '9-424'
        elif day_name == 'Суббота':
            if week_type == 'white':
                return '9-405'
            else:  # green
                return '334'
        return ''

    def get_available_schedule(self, action_type=None):
        """Возвращает доступные дни для записи с учетом типа недели и типа действия"""
        today = datetime.datetime.now()
        today_date = today.date()
        
        schedule = {}
        
        # Для пересдачи - всегда доступны
        if action_type == 'debt':
            # Проверяем, что время не прошло
            tuesday_time = self.get_next_weekday_date('Вторник', '12:50', today)
            if tuesday_time > today:
                schedule['Вторник 12:50'] = ('Вторник', '12:50', 0)
            
            saturday_time = self.get_next_weekday_date('Суббота', '11:20', today)
            if saturday_time > today:
                schedule['Суббота 11:20'] = ('Суббота', '11:20', 0)
        
        # Для лабораторной работы
        elif action_type == 'lab':
            # Всегда доступны, если время не прошло
            tuesday_time = self.get_next_weekday_date('Вторник', '12:50', today)
            if tuesday_time > today:
                schedule['Вторник 12:50'] = ('Вторник', '12:50', 0)
            
            thursday_time = self.get_next_weekday_date('Четверг', '15:00', today)
            if thursday_time > today:
                schedule['Четверг 15:00'] = ('Четверг', '15:00', 0)
            
            # Субботы доступны только на ЗЕЛЕНОЙ неделе
            # Ищем ближайшую зеленую неделю
            for weeks_offset in range(0, 5):
                # Получаем дату субботы с учетом смещения
                saturday_time = self.get_next_weekday_date('Суббота', '9:40', today, weeks_offset)
                saturday_date = saturday_time.date()
                
                # Проверяем тип недели для этой субботы
                test_week_type = self.get_week_type(saturday_date)
                
                if test_week_type == 'green':
                    # Проверяем, что это не прошлая дата
                    if saturday_time > today:
                        schedule['Суббота 9:40'] = ('Суббота', '9:40', weeks_offset)
                        schedule['Суббота 11:20'] = ('Суббота', '11:20', weeks_offset)
                        break
        
        return schedule

    def get_schedule_buttons(self, user_id):
        """Создает кнопки с днями недели и актуальными датами, отсортированные по дате"""
        action_type = self.get_user_data(user_id, 'action_type')
        available_schedule = self.get_available_schedule(action_type)
        today = datetime.datetime.now()
        
        schedule_items = []
        for display_key, (day_name, time_str, weeks_ahead) in available_schedule.items():
            # Получаем дату с учетом смещения
            target_date = self.get_next_weekday_date(day_name, time_str, today, weeks_ahead)
            
            # Проверяем, что дата не в прошлом
            if target_date < today:
                continue
                
            date_str = target_date.strftime('%d.%m')
            
            # Определяем эмодзи для этой конкретной даты
            week_emoji = self.get_week_emoji(target_date)
            week_type = self.get_week_type(target_date)
            
            auditorium = self.get_auditorium(day_name, time_str, week_type)
            
            # Формируем текст кнопки
            button_text = f"{week_emoji} {day_name} {time_str} - ауд. {auditorium} ({date_str})"
            schedule_items.append((target_date, button_text, day_name, time_str, weeks_ahead, week_type, auditorium))
        
        # Сортируем по дате
        schedule_items.sort(key=lambda x: x[0])
        buttons = [item[1] for item in schedule_items]
        
        # Добавляем кнопку "Назад", если есть элементы
        if buttons:
            buttons.append('Назад')
        else:
            buttons.append('Назад')
            # Если нет доступных слотов, сообщаем об этом
            self.send_message(user_id, "❌ В настоящий момент нет доступных слотов для записи.")
        
        # Сохраняем данные для обработки выбора
        self.set_user_data(user_id, 'schedule_items', schedule_items)
        
        return buttons

    def send_message(self, user_id, message, keyboard=None):
        """Отправка сообщения пользователю"""
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
        """Создание клавиатуры"""
        keyboard = {
            'one_time': one_time,
            'buttons': []
        }
        for button in buttons:
            keyboard['buttons'].append([{
                'action': {
                    'type': 'text',
                    'label': button
                },
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
        """Очищает временные данные пользователя"""
        keys_to_remove = []
        for key in list(self.user_states.keys()):
            if isinstance(key, str) and key.startswith(f'{user_id}_'):
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del self.user_states[key]
        print(f'🧹 Очищены данные пользователя {user_id}')

    def send_to_teacher(self, request_data):
        """Отправка заявки преподавателю"""
        try:
            task_type = "Пересдача" if request_data['type'] == 'debt' else "Сдача лабораторной"
            
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
                f"⏳ Заявка #{request_data['request_id']} отправлена преподавателю.\n"
                f"Ожидайте ответа..."
            )
            
            return True
        except Exception as e:
            print(f'❌ Ошибка отправки преподавателю: {e}')
            return False

    def process_teacher_response(self, message, user_id):
        """Обработка ответа от преподавателя"""
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
                            else:
                                msg = f"✅ Вы, {name} ({group}), записались на сдачу лабораторной работы!\n📅 {time_str}"
                            
                            self.send_message(student_id, msg)
                            del self.pending_requests[request_id]
                            
                            self.send_message(
                                self.teacher_id,
                                f"✅ Заявка #{request_id} подтверждена. Студент уведомлен."
                            )
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
                                    f"❌ Преподаватель отклонил запись.\n"
                                    f"Причина: {reason}\n"
                                    f"Свяжитесь с преподавателем для уточнения."
                                )
                                
                                del self.pending_requests[request_id]
                                
                                self.send_message(
                                    self.teacher_id,
                                    f"✅ Заявка #{request_id} отклонена. Студент уведомлен."
                                )
                                return True
            
            return False
            
        except Exception as e:
            print(f'❌ Ошибка обработки ответа преподавателя: {e}')
            return False

    def handle_start(self, user_id):
        keyboard = self.create_keyboard(['Пересдача', 'Сдать лабораторную'])
        self.send_message(user_id, self.messages['start'], keyboard)
        self.set_state(user_id, 'main_menu')

    def handle_ask_name(self, user_id, action_type):
        """Запрос ФИО"""
        self.set_user_data(user_id, 'action_type', action_type)
        self.send_message(user_id, self.messages['ask_name'])
        self.set_state(user_id, 'ask_name')

    def handle_ask_group(self, user_id):
        """Запрос группы"""
        self.send_message(user_id, self.messages['ask_group'])
        self.set_state(user_id, 'ask_group')

    def handle_time(self, user_id):
        """Отображение расписания с актуальными датами"""
        schedule_buttons = self.get_schedule_buttons(user_id)
        keyboard = self.create_keyboard(schedule_buttons)
        
        action_type = self.get_user_data(user_id, 'action_type')
        available_schedule = self.get_available_schedule(action_type)
        today = datetime.datetime.now()
        
        schedule_items = []
        for display_key, (day_name, time_str, weeks_ahead) in available_schedule.items():
            target_date = self.get_next_weekday_date(day_name, time_str, today, weeks_ahead)
            
            # Проверяем, что дата не в прошлом
            if target_date < today:
                continue
                
            week_type = self.get_week_type(target_date)
            auditorium = self.get_auditorium(day_name, time_str, week_type)
            schedule_items.append((target_date, day_name, time_str, weeks_ahead, week_type, auditorium))
        
        schedule_items.sort(key=lambda x: x[0])
        
        message = "⏰ Выберите день и время сдачи:\n\n"
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
        """Подтверждение перед отправкой преподавателю"""
        time_info = self.get_user_data(user_id, 'time')
        name = self.get_user_data(user_id, 'name')
        group = self.get_user_data(user_id, 'group')
        action_type = self.get_user_data(user_id, 'action_type')
        
        if not all([time_info, name, group, action_type]):
            self.send_message(user_id, '❌ Ошибка: не все данные заполнены. Начните заново.')
            self.clear_user_data(user_id)
            self.handle_start(user_id)
            return
        
        task_type = "пересдачу" if action_type == 'debt' else "лабораторную работу"
        
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
            
            # Проверяем, не ответ ли это от преподавателя
            if user_id == self.teacher_id:
                if self.process_teacher_response(message, user_id):
                    return
            
            state = self.get_state(user_id)
            print(f'📊 Текущее состояние: {state}')
            
            # Обработка команды "начать"
            if message_lower in ['начать', 'start', 'привет', 'здравствуй']:
                self.clear_user_data(user_id)
                self.handle_start(user_id)
                return

            # Обработка состояний
            if state == 'start' or state == 'main_menu':
                if 'пересдача' in message_lower:
                    self.handle_ask_name(user_id, 'debt')
                elif 'лабораторную' in message_lower or 'лаба' in message_lower:
                    self.handle_ask_name(user_id, 'lab')
                else:
                    keyboard = self.create_keyboard(['Пересдача', 'Сдать лабораторную'])
                    self.send_message(user_id, 'Пожалуйста, выберите действие из меню! 👇', keyboard)

            elif state == 'ask_name':
                name_parts = message.strip().split()
                if len(name_parts) >= 2:
                    self.set_user_data(user_id, 'name', message.strip())
                    self.handle_ask_group(user_id)
                else:
                    self.send_message(user_id, '❌ Пожалуйста, напишите Фамилию и Имя через пробел.')

            elif state == 'ask_group':
                if len(message.strip()) >= 2:
                    self.set_user_data(user_id, 'group', message.strip())
                    self.handle_time(user_id)
                else:
                    self.send_message(user_id, '❌ Пожалуйста, укажите группу.')

            elif state == 'time_choose':
                if message_lower == 'назад':
                    self.clear_user_data(user_id)
                    self.handle_start(user_id)
                else:
                    # Проверяем по сохраненным данным
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
                        self.handle_confirm(user_id)
                    else:
                        self.send_message(user_id, '❌ Выберите день из списка!')

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
                        'task': 'Пересдача' if action_type == 'debt' else 'Лабораторная работа',
                        'time': time_str,
                        'type': action_type
                    }
                    
                    self.pending_requests[request_id] = request_data
                    
                    if self.send_to_teacher(request_data):
                        self.send_message(
                            user_id,
                            f"✅ Заявка #{request_id} отправлена!\n"
                            f"Ожидайте ответа преподавателя."
                        )
                    else:
                        self.send_message(
                            user_id,
                            "❌ Не удалось отправить заявку. Попробуйте позже."
                        )
                    
                    self.clear_user_data(user_id)
                    self.set_state(user_id, 'start')
                    self.handle_start(user_id)
                    
                elif message_lower == 'нет':
                    self.send_message(user_id, '❌ Отмена отправки заявки.')
                    self.clear_user_data(user_id)
                    self.set_state(user_id, 'start')
                    self.handle_start(user_id)
                else:
                    self.send_message(user_id, '❌ Ответьте "Да" или "Нет"!')

            else:
                self.clear_user_data(user_id)
                self.handle_start(user_id)

        except Exception as e:
            print(f'❌ Критическая ошибка: {e}')
            traceback.print_exc()
            try:
                self.send_message(
                    event.user_id, 
                    '❌ Произошла ошибка. Напишите "Начать", чтобы начать заново.'
                )
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