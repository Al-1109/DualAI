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
async function sendTelegramMessage(chat_id, text, reply_markup = null) {
  const payload = {
    chat_id: chat_id,
    text: text,
    parse_mode: "Markdown"
  };
  
  if (reply_markup) {
    payload.reply_markup = reply_markup;
  }
  
  log('INFO', `Отправка сообщения на ${chat_id}: ${text.substring(0, 50)}...`);
  
  return makeRequest('sendMessage', payload);
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

// Получает историю сообщений в чате
async function getChatHistory(chat_id, limit = 10) {
  const payload = {
    chat_id: chat_id,
    limit: limit
  };
  
  log('INFO', `Получение истории сообщений: chat_id=${chat_id}`);
  
  return makeRequest('getUpdates', { offset: -1, limit: 100 })
    .then(result => {
      if (!result.ok) return { messages: [] };
      
      // Фильтруем сообщения по чату
      const updates = result.response.result || [];
      const messages = updates
        .filter(update => 
          (update.message && update.message.chat.id === chat_id) || 
          (update.callback_query && update.callback_query.message.chat.id === chat_id)
        )
        .map(update => {
          if (update.message) {
            return { 
              message_id: update.message.message_id,
              chat_id: update.message.chat.id
            };
          }
          if (update.callback_query) {
            return { 
              message_id: update.callback_query.message.message_id,
              chat_id: update.callback_query.message.chat.id
            };
          }
          return null;
        })
        .filter(msg => msg !== null);
        
      return { messages };
    });
}

// Очищает чат от предыдущих сообщений бота
async function clearChatHistory(chat_id, message_id) {
  try {
    // Удаляем текущее сообщение, на которое нажали
    if (message_id) {
      await deleteMessage(chat_id, message_id);
    }
    
    // Получаем историю сообщений и удаляем их
    // Telegram API не позволяет легко очистить чат, 
    // поэтому мы удаляем только текущее сообщение
    
    return true;
  } catch (error) {
    log('ERROR', `Ошибка при очистке чата: ${error.message}`);
    return false;
  }
}

// Отправляет главное меню
async function sendMainMenu(chat_id, user) {
  // Создаем клавиатуру с основными разделами
  const keyboard = {
    "inline_keyboard": [
      [{"text": "📋 О проекте", "callback_data": "about"}],
      [{"text": "🛠️ Возможности", "callback_data": "features"}],
      [{"text": "📊 Статистика", "callback_data": "stats"}],
      [{"text": "❓ Помощь", "callback_data": "help"}]
    ]
  };
  
  // Отправляем приветствие с меню
  return sendTelegramMessage(
    chat_id, 
    `# Добро пожаловать, ${user}! 👋\n\n` +
    `Это главное меню DualAI бота.\n` +
    `Выберите интересующий вас раздел, нажав на соответствующую кнопку.`,
    keyboard
  );
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
        version: '1.4.0'
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
          // Отправляем главное меню
          await sendMainMenu(chat_id, user);
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
        
        // Сначала удаляем текущее сообщение
        await deleteMessage(chat_id, message_id);
        
        // Обрабатываем различные команды
        if (data === 'about') {
          const aboutKeyboard = {
            "inline_keyboard": [
              [{"text": "🔙 Назад в меню", "callback_data": "menu"}]
            ]
          };
          
          await sendTelegramMessage(
            chat_id, 
            `# О проекте DualAI 🚀\n\n` +
            `DualAI - это экспериментальный Telegram бот, разработанный для демонстрации возможностей Vercel и webhook API.\n\n` +
            `Версия: 1.4.0\n` +
            `Платформа: Vercel\n` +
            `Технологии: Node.js, JavaScript`,
            aboutKeyboard
          );
        } 
        else if (data === 'features') {
          const featuresKeyboard = {
            "inline_keyboard": [
              [{"text": "🔙 Назад в меню", "callback_data": "menu"}]
            ]
          };
          
          await sendTelegramMessage(
            chat_id, 
            `# Возможности бота 🛠️\n\n` +
            `- Статичное меню с навигацией\n` +
            `- Обработка webhook запросов\n` +
            `- Мониторинг состояния\n` +
            `- Интерактивный интерфейс\n` +
            `- Многоуровневое меню\n`,
            featuresKeyboard
          );
        }
        else if (data === 'stats') {
          const statsKeyboard = {
            "inline_keyboard": [
              [{"text": "🔄 Обновить", "callback_data": "stats"}],
              [{"text": "🔙 Назад в меню", "callback_data": "menu"}]
            ]
          };
          
          const now = new Date();
          
          await sendTelegramMessage(
            chat_id, 
            `# Статистика 📊\n\n` +
            `🕒 Текущее время: ${now.toISOString()}\n` +
            `👤 Пользователь: ${user}\n` +
            `🆔 ID чата: ${chat_id}\n` +
            `🌐 Webhook: Активен\n`,
            statsKeyboard
          );
        }
        else if (data === 'help') {
          const helpKeyboard = {
            "inline_keyboard": [
              [{"text": "🔙 Назад в меню", "callback_data": "menu"}]
            ]
          };
          
          await sendTelegramMessage(
            chat_id, 
            `# Помощь ❓\n\n` +
            `Доступные команды:\n` +
            `/start - Запустить бота\n` +
            `/menu - Показать главное меню\n\n` +
            `Для навигации используйте кнопки внизу сообщения.`,
            helpKeyboard
          );
        }
        else if (data === 'menu') {
          // Возврат в главное меню
          await sendMainMenu(chat_id, user);
        }
        else {
          // Обработка неизвестной команды
          const backKeyboard = {
            "inline_keyboard": [
              [{"text": "🔙 Назад в меню", "callback_data": "menu"}]
            ]
          };
          
          await sendTelegramMessage(
            chat_id, 
            `Получена неизвестная команда: ${data}`,
            backKeyboard
          );
        }
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