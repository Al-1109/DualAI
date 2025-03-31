// webhook.js - Обработчик Telegram webhook для Vercel API routes
const https = require('https');

// Получаем токен бота из переменных окружения
const TELEGRAM_BOT_TOKEN = process.env.TEST_TELEGRAM_BOT_TOKEN;
const WEBHOOK_SECRET = process.env.TEST_WEBHOOK_SECRET || 'DualAI_Webhook_Secret_2025'; // Добавляем fallback для тестирования

// Базовый URL для Telegram API
const TELEGRAM_API_URL = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}`;

// Логирование с временной меткой
function log(level, message) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] [${level}] ${message}`);
}

// Выполняет HTTP запрос к Telegram API
async function makeRequest(method, params) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(params);
    
    const options = {
      hostname: 'api.telegram.org',
      port: 443,
      path: `/bot${TELEGRAM_BOT_TOKEN}/${method}`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': data.length
      }
    };
    
    const req = https.request(options, (res) => {
      let responseData = '';
      
      res.on('data', (chunk) => {
        responseData += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode === 200) {
          log('INFO', `Успешный запрос ${method}`);
          resolve({ ok: true, response: JSON.parse(responseData) });
        } else {
          log('ERROR', `Ошибка API при запросе ${method}: ${res.statusCode}, ${responseData}`);
          resolve({ ok: false, error: `API error: ${res.statusCode}` });
        }
      });
    });
    
    req.on('error', (error) => {
      log('ERROR', `Исключение при запросе ${method}: ${error.message}`);
      reject({ ok: false, error: error.message });
    });
    
    req.write(data);
    req.end();
  });
}

// Отправляет сообщение пользователю через Telegram API
async function sendTelegramMessage(chat_id, text, reply_markup = null, silent = false) {
  const payload = {
    chat_id: chat_id,
    text: text,
    parse_mode: "Markdown"
  };
  
  if (reply_markup) {
    payload.reply_markup = reply_markup;
  }
  
  // Отключаем уведомление, если флаг silent = true
  if (silent) {
    payload.disable_notification = true;
  }
  
  log('INFO', `Отправка сообщения на ${chat_id}: ${text.substring(0, 50)}...`);
  
  return makeRequest('sendMessage', payload);
}

// Редактирует сообщение
async function editMessage(chat_id, message_id, text, reply_markup = null) {
  const payload = {
    chat_id: chat_id,
    message_id: message_id,
    text: text,
    parse_mode: "Markdown"
  };
  
  if (reply_markup) {
    payload.reply_markup = reply_markup;
  }
  
  log('INFO', `Редактирование сообщения: chat_id=${chat_id}, message_id=${message_id}`);
  
  return makeRequest('editMessageText', payload);
}

// Удаляет сообщение
async function deleteMessage(chat_id, message_id) {
  const payload = {
    chat_id: chat_id,
    message_id: message_id
  };
  
  log('INFO', `Удаление сообщения: chat_id=${chat_id}, message_id=${message_id}`);
  
  return makeRequest('deleteMessage', payload);
}

// Удаляет предыдущие сообщения в чате
async function deleteMessages(chat_id, messages_ids) {
  log('INFO', `Удаление ${messages_ids.length} сообщений в чате ${chat_id}`);
  
  for (const message_id of messages_ids) {
    try {
      await deleteMessage(chat_id, message_id);
      // Небольшая пауза между удалениями
      await new Promise(resolve => setTimeout(resolve, 50)); 
    } catch (error) {
      log('ERROR', `Не удалось удалить сообщение ${message_id}: ${error.message}`);
    }
  }
}

// Объект для хранения ID последних сообщений для каждого чата
const chatLastMessages = {};

// Сохраняет ID последнего сообщения для чата
function saveLastMessageId(chat_id, message_id) {
  if (!chatLastMessages[chat_id]) {
    chatLastMessages[chat_id] = [];
  }
  
  // Добавляем новое ID сообщения
  chatLastMessages[chat_id].push(message_id);
  
  // Ограничиваем размер массива до 10 последних сообщений
  if (chatLastMessages[chat_id].length > 10) {
    chatLastMessages[chat_id].shift();
  }
  
  log('INFO', `Сохранен ID сообщения ${message_id} для чата ${chat_id}. Всего: ${chatLastMessages[chat_id].length}`);
}

// Получает ID последних сообщений для чата
function getLastMessageIds(chat_id) {
  return chatLastMessages[chat_id] || [];
}

// Получает историю чата (последние сообщения)
async function getChat(chat_id) {
  try {
    const payload = {
      chat_id: chat_id
    };
    
    log('INFO', `Получение информации о чате: ${chat_id}`);
    
    return makeRequest('getChat', payload);
  } catch (error) {
    log('ERROR', `Ошибка при получении информации о чате: ${error.message}`);
    return { ok: false };
  }
}

// Отправляет системное служебное сообщение
async function sendServiceMessage(chat_id, text) {
  // Создаем клавиатуру только с одной ключевой кнопкой
  const keyboard = {
    "inline_keyboard": [
      [{"text": "🔑 Открыть главное меню", "callback_data": "show_menu"}]
    ]
  };
  
  return sendTelegramMessage(chat_id, text, keyboard);
}

// Отправляет главное меню
async function sendMainMenu(chat_id, user, cleanup = false) {
  try {
    // Получаем информацию о чате
    const chatInfo = await getChat(chat_id);
    log('INFO', `Информация о чате: ${JSON.stringify(chatInfo)}`);
    
    // Если нужно очистить предыдущие сообщения
    if (cleanup) {
      // Отправляем системное сообщение о сбросе
      await sendServiceMessage(chat_id, "🔄 *Выполняется очистка меню...*\n\nНажмите на кнопку ниже, чтобы продолжить. Ваш чат будет обновлен и готов к работе 👇");
      return { ok: true };
    }
    
    // Создаем клавиатуру с основными разделами
    const keyboard = {
      "inline_keyboard": [
        [{"text": "📋 О проекте", "callback_data": "about"}],
        [{"text": "🛠️ Возможности", "callback_data": "features"}],
        [{"text": "📊 Статистика", "callback_data": "stats"}],
        [{"text": "❓ Помощь", "callback_data": "help"}],
        [{"text": "🧹 Очистить сообщения", "callback_data": "clear_messages"}]
      ]
    };
    
    const menuText = `# Добро пожаловать, ${user}! 👋\n\n` +
      `Это главное меню DualAI бота.\n` +
      `Выберите интересующий вас раздел, нажав на соответствующую кнопку.`;
    
    // Отправляем тихое сообщение (без уведомления)
    const result = await sendTelegramMessage(chat_id, menuText, keyboard, true);
    
    // Если сообщение успешно отправлено, сохраняем его ID
    if (result.ok && result.response.result) {
      saveLastMessageId(chat_id, result.response.result.message_id);
    }
    
    return result;
  } catch (error) {
    log('ERROR', `Ошибка при отправке главного меню: ${error.message}`);
    return { ok: false, error: error.message };
  }
}

// Отправляет новое сообщение и удаляет предыдущее
async function sendNewMessage(chat_id, text, keyboard) {
  // Отправляем новое сообщение (тихое)
  const result = await sendTelegramMessage(chat_id, text, keyboard, true);
  
  // Если сообщение успешно отправлено, сохраняем его ID
  if (result.ok && result.response.result) {
    const newMessageId = result.response.result.message_id;
    saveLastMessageId(chat_id, newMessageId);
  }
  
  return result;
}

// Обработчик запросов в формате Vercel API routes
export default async function handler(req, res) {
  try {
    // Логируем начало обработки запроса
    log('INFO', `Получен ${req.method} запрос на webhook`);
    
    // Обработка GET-запроса для проверки работоспособности
    if (req.method === 'GET') {
      return res.status(200).json({
        status: 'ok',
        message: 'Webhook активен',
        timestamp: new Date().toISOString(),
        version: '1.7.0'
      });
    }
    
    // Обработка POST-запроса от Telegram
    if (req.method === 'POST') {
      // Верификация запроса от Telegram
      const secretHeader = req.headers['x-telegram-bot-api-secret-token'];
      
      log('INFO', `Проверка секрета: полученный=${secretHeader}, ожидаемый=${WEBHOOK_SECRET}`);
      
      // Получаем и парсим данные запроса
      const update = req.body;
      log('INFO', `Получено обновление: ${JSON.stringify(update)}`);
      
      // Обработка текстовых сообщений
      if (update.message && update.message.text) {
        const chat_id = update.message.chat.id;
        const text = update.message.text;
        const user = update.message.from.first_name || 'пользователь';
        
        log('INFO', `Сообщение от ${user} (${chat_id}): ${text}`);
        
        if (text === '/start' || text === '/menu') {
          // Отправляем главное меню с очисткой
          await sendMainMenu(chat_id, user, true);
        } else if (text === '/clean') {
          // Команда для очистки чата
          await sendServiceMessage(chat_id, "🧹 *Выполняется очистка чата...*\n\nНажмите на кнопку ниже, чтобы продолжить работу с ботом 👇");
        } else {
          // Отправляем эхо
          await sendTelegramMessage(chat_id, `Вы сказали: ${text}`);
        }
      }
      
      // Обработка нажатий на кнопки
      else if (update.callback_query) {
        const callback = update.callback_query;
        const chat_id = callback.message.chat.id;
        const message_id = callback.message.message_id;
        const data = callback.data;
        const user = callback.from.first_name || 'пользователь';
        
        log('INFO', `Получен callback с данными: ${data}`);

        // Обрабатываем различные команды
        if (data === 'show_menu') {
          // Удаляем сообщение, на которое нажали
          try {
            await deleteMessage(chat_id, message_id);
          } catch (error) {
            log('WARN', `Не удалось удалить сообщение при переходе в меню: ${error.message}`);
          }
          // Показываем главное меню
          await sendMainMenu(chat_id, user, false);
        }
        else if (data === 'clear_messages') {
          // Удаляем сообщение, на которое нажали
          try {
            await deleteMessage(chat_id, message_id);
          } catch (error) {
            log('WARN', `Не удалось удалить сообщение при очистке: ${error.message}`);
          }
          
          // Очищаем исторические сообщения
          const messageIds = getLastMessageIds(chat_id);
          if (messageIds.length > 0) {
            await deleteMessages(chat_id, messageIds);
            chatLastMessages[chat_id] = [];
          }
          
          // Отправляем системное сообщение
          await sendServiceMessage(chat_id, "🧹 *Чат очищен*\n\nНажмите на кнопку ниже, чтобы вернуться в меню 👇");
        }
        else if (data === 'about') {
          const aboutKeyboard = {
            "inline_keyboard": [
              [{"text": "🔙 Назад в меню", "callback_data": "show_menu"}]
            ]
          };
          
          // Отправляем новое сообщение 
          await sendNewMessage(
            chat_id,
            `# О проекте DualAI 🚀\n\n` +
            `DualAI - это экспериментальный Telegram бот, разработанный для демонстрации возможностей Vercel и webhook API.\n\n` +
            `Версия: 1.7.0\n` +
            `Платформа: Vercel\n` +
            `Технологии: Node.js, JavaScript`,
            aboutKeyboard
          );
          
          // Удаляем сообщение, на которое нажали
          try {
            await deleteMessage(chat_id, message_id);
          } catch (error) {
            log('WARN', `Не удалось удалить сообщение при просмотре раздела: ${error.message}`);
          }
        } 
        else if (data === 'features') {
          const featuresKeyboard = {
            "inline_keyboard": [
              [{"text": "🔙 Назад в меню", "callback_data": "show_menu"}]
            ]
          };
          
          // Отправляем новое сообщение
          await sendNewMessage(
            chat_id,
            `# Возможности бота 🛠️\n\n` +
            `- Статичное меню с навигацией\n` +
            `- Обработка webhook запросов\n` +
            `- Мониторинг состояния\n` +
            `- Интерактивный интерфейс\n` +
            `- Многоуровневое меню\n`,
            featuresKeyboard
          );
          
          // Удаляем сообщение, на которое нажали
          try {
            await deleteMessage(chat_id, message_id);
          } catch (error) {
            log('WARN', `Не удалось удалить сообщение при просмотре раздела: ${error.message}`);
          }
        }
        else if (data === 'stats') {
          const statsKeyboard = {
            "inline_keyboard": [
              [{"text": "🔄 Обновить", "callback_data": "stats"}],
              [{"text": "🔙 Назад в меню", "callback_data": "show_menu"}]
            ]
          };
          
          const now = new Date();
          
          // Отправляем новое сообщение
          await sendNewMessage(
            chat_id,
            `# Статистика 📊\n\n` +
            `🕒 Текущее время: ${now.toISOString()}\n` +
            `👤 Пользователь: ${user}\n` +
            `🆔 ID чата: ${chat_id}\n` +
            `🌐 Webhook: Активен\n`,
            statsKeyboard
          );
          
          // Удаляем сообщение, на которое нажали
          try {
            await deleteMessage(chat_id, message_id);
          } catch (error) {
            log('WARN', `Не удалось удалить сообщение при просмотре раздела: ${error.message}`);
          }
        }
        else if (data === 'help') {
          const helpKeyboard = {
            "inline_keyboard": [
              [{"text": "🔙 Назад в меню", "callback_data": "show_menu"}]
            ]
          };
          
          // Отправляем новое сообщение
          await sendNewMessage(
            chat_id,
            `# Помощь ❓\n\n` +
            `Доступные команды:\n` +
            `/start - Запустить бота\n` +
            `/menu - Показать главное меню\n` +
            `/clean - Очистить чат\n\n` +
            `Для навигации используйте кнопки внизу сообщения.\n` +
            `Для очистки чата нажмите кнопку "Очистить сообщения" в главном меню.`,
            helpKeyboard
          );
          
          // Удаляем сообщение, на которое нажали
          try {
            await deleteMessage(chat_id, message_id);
          } catch (error) {
            log('WARN', `Не удалось удалить сообщение при просмотре раздела: ${error.message}`);
          }
        }
        else if (data === 'menu') {
          // Удаляем сообщение, на которое нажали
          try {
            await deleteMessage(chat_id, message_id);
          } catch (error) {
            log('WARN', `Не удалось удалить сообщение при возврате в меню: ${error.message}`);
          }
          
          // Возврат в главное меню
          await sendMainMenu(chat_id, user, false);
        }
        else {
          // Обработка неизвестной команды
          const backKeyboard = {
            "inline_keyboard": [
              [{"text": "🔙 Назад в меню", "callback_data": "show_menu"}]
            ]
          };
          
          // Отправляем новое сообщение
          await sendNewMessage(
            chat_id,
            `Получена неизвестная команда: ${data}`,
            backKeyboard
          );
          
          // Удаляем сообщение, на которое нажали
          try {
            await deleteMessage(chat_id, message_id);
          } catch (error) {
            log('WARN', `Не удалось удалить сообщение: ${error.message}`);
          }
        }
        
        // Отвечаем на callback, чтобы убрать загрузку с кнопки
        await makeRequest('answerCallbackQuery', {
          callback_query_id: callback.id
        });
      }
      
      // Отвечаем успехом, даже если не обработали конкретный тип сообщения
      return res.status(200).json({ ok: true });
    }
    
    // Обработка других HTTP методов
    return res.status(405).json({
      ok: false,
      error: 'Method not allowed'
    });
    
  } catch (error) {
    log('ERROR', `Общая ошибка обработки webhook: ${error.message}`);
    console.error(error.stack);
    
    return res.status(500).json({
      ok: false,
      error: error.message
    });
  }
} 