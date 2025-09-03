# app/telegram_notifier.py
import asyncio
from telegram import Bot
import io
import os
from typing import Dict, Optional, Any
import threading
import logging
from contextlib import asynccontextmanager

# Используем относительные импорты для модулей внутри пакета `app`
from .core.config import TELEGRAM_BOT_TOKEN
from .database import get_user_by_name

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Глобальные переменные для бота
bot_instance: Optional[Bot] = None

# --- ФУНКЦИЯ ОТПРАВКИ УВЕДОМЛЕНИЙ ---

async def send_photo_with_caption(bot, chat_id, photo_url_internal, caption):
    """
    Отправляет фото с подписью указанному пользователю.
    """
    if not photo_url_internal:
        logger.error(f"[Telegram Bot ERROR] photo_url_internal is None or empty for chat_id {chat_id}")
        return
    photo_path = None
    try:
        photo_filename = photo_url_internal.lstrip('/')
        photo_path = os.path.abspath(photo_filename)
        logger.debug(f"[Telegram Bot DEBUG] Полный путь к фото: {photo_path}")
        if not os.path.exists(photo_path):
            logger.error(f"[Telegram Bot ERROR] Файл изображения не найден: {photo_path}")
            return
        with open(photo_path, 'rb') as photo_file:
            photo_bytes = photo_file.read()
            input_file = io.BytesIO(photo_bytes)
            input_file.name = os.path.basename(photo_path)
            await bot.send_photo(chat_id=chat_id, photo=input_file, caption=caption, parse_mode='HTML')
        logger.debug(f"[Telegram Bot DEBUG] Фото успешно отправлено пользователю {chat_id}")
    except FileNotFoundError:
        error_path = photo_path if photo_path is not None else "unknown"
        logger.error(f"[Telegram Bot ERROR] Файл изображения не найден при попытке открытия: {error_path}")
    except Exception as e:
        error_path = photo_path if photo_path is not None else "unknown"
        logger.error(f"[Telegram Bot ERROR] Ошибка при отправке фото пользователю {chat_id} (path: {error_path}): {e}")

def send_telegram_notification_async(defect_data: Dict[Any, Any], responsible_person: Optional[str], executor_person: Optional[str]):
    """
    Асинхронно отправляет уведомления в Telegram.
    """
    logger.debug(f"[Telegram Notifier] send_telegram_notification_async вызвана с: defect_data={defect_data}, "
          f"responsible_person={responsible_person}, executor_person={executor_person}")

    if not TELEGRAM_BOT_TOKEN:
        logger.info("[Telegram Notifier] Уведомления отключены: не указан токен.")
        return

    # Создаем асинхронную задачу для отправки
    async def _send_notification():
        """Внутренняя асинхронная функция для выполнения отправки."""
        global bot_instance
        if not bot_instance:
             logger.error("[Telegram Notifier] Бот не инициализирован. Невозможно отправить уведомление.")
             return

        try:
            defect_id = defect_data.get('id', 'N/A')
            equipment = defect_data.get('equipment', 'N/A')
            section = defect_data.get('section', 'N/A')
            description = defect_data.get('description', 'N/A')
            danger_level = defect_data.get('danger_level', 'N/A')
            photo_url_internal = defect_data.get('photo_url', None)

            # Формируем текст сообщения
            message_text = (
                f"🔔 <b>Уведомление о дефекте</b>\n"
                f"<b>ID:</b> {defect_id}\n"
                f"<b>Оборудование:</b> {equipment}\n"
                f"<b>Участок:</b> {section}\n"
                f"<b>Описание:</b> {description}\n"
                f"<b>Уровень опасности:</b> {danger_level}\n"
            )

            tasks = []
            notified_users = []

            # Уведомление ответственного
            if responsible_person:
                user = get_user_by_name(responsible_person)
                if user:
                    user_id = user['telegram_id']
                    msg_text_resp = f"{message_text}<i>Вы назначены ответственным.</i>"
                    logger.debug(f"[Telegram Notifier] Добавляем задачу уведомления для ответственного: {responsible_person} (ID: {user_id})")
                    if photo_url_internal:
                        task = send_photo_with_caption(bot_instance, user_id, photo_url_internal, msg_text_resp)
                        tasks.append(task)
                    else:
                        task = bot_instance.send_message(chat_id=user_id, text=msg_text_resp, parse_mode='HTML')
                        tasks.append(task)
                    notified_users.append(responsible_person)

            # Уведомление исполнителя
            if executor_person and executor_person != responsible_person:
                user = get_user_by_name(executor_person)
                if user:
                    user_id = user['telegram_id']
                    msg_text_exec = f"{message_text}<i>Вы назначены исполнителем.</i>"
                    logger.debug(f"[Telegram Notifier] Добавляем задачу уведомления для исполнителя: {executor_person} (ID: {user_id})")
                    if photo_url_internal:
                        task = send_photo_with_caption(bot_instance, user_id, photo_url_internal, msg_text_exec)
                        tasks.append(task)
                    else:
                        task = bot_instance.send_message(chat_id=user_id, text=msg_text_exec, parse_mode='HTML')
                        tasks.append(task)
                    notified_users.append(executor_person)

            # Отправляем все сообщения параллельно
            if tasks:
                logger.debug(f"[Telegram Notifier] Отправка {len(tasks)} уведомлений...")
                # Создаем задачи для каждой корутины
                task_objects = [asyncio.create_task(t) for t in tasks]
                results = await asyncio.gather(*task_objects, return_exceptions=True)
                logger.info(f"[Telegram Notifier] Уведомления отправлены для дефекта ID {defect_id} пользователям: {notified_users}")
                # Проверка результатов на ошибки
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"[Telegram Notifier ERROR] Ошибка при отправке уведомления пользователю {notified_users[i]}: {result}")
            else:
                logger.debug("[Telegram Notifier] Нет задач для отправки уведомлений.")

        except Exception as e:
            logger.error(f"[Telegram Notifier] Критическая ошибка в _send_notification для дефекта ID {defect_data.get('id', 'N/A')}: {e}")

    # Планируем выполнение задачи в активном event loop
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_send_notification())
        logger.debug("[Telegram Notifier] Асинхронная задача уведомления создана и запланирована.")
    except RuntimeError:
        # Если event loop не запущен, запускаем в новом loop
        logger.warning("[Telegram Notifier] RuntimeError: no running event loop. Попытка запуска в новом loop...")
        try:
            new_loop = asyncio.new_event_loop()
            def run_loop():
                asyncio.set_event_loop(new_loop)
                new_loop.run_until_complete(_send_notification())
                new_loop.close()
            thread = threading.Thread(target=run_loop, daemon=True)
            thread.start()
            logger.debug("[Telegram Notifier] Асинхронная задача уведомления запущена в новом потоке.")
        except Exception as e2:
            logger.error(f"[Telegram Notifier] Не удалось запустить задачу уведомления даже в новом loop/thread: {e2}")

# --- ЖИЗНЕННЫЙ ЦИКЛ ПРИЛОЖЕНИЯ ---

@asynccontextmanager
async def lifespan(app):
    """Lifespan handler для инициализации бота."""
    logger.info("[App Lifespan] Запуск приложения...")
    global bot_instance
    if TELEGRAM_BOT_TOKEN:
        bot_instance = Bot(token=TELEGRAM_BOT_TOKEN)
        logger.info("[App Lifespan] Telegram бот инициализирован.")
    else:
        logger.info("[App Lifespan] Токен Telegram бота не указан.")
    yield
    logger.info("[App Lifespan] Остановка приложения...")
    # Очистка ресурсов, если необходимо