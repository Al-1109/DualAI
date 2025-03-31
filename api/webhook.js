// webhook.js - Обработчик Telegram webhook для Vercel API routes
const https = require('https');

// Получаем токен бота из переменных окружения
const TELEGRAM_BOT_TOKEN = process.env.TEST_TELEGRAM_BOT_TOKEN;
const WEBHOOK_SECRET = process.env.TEST_WEBHOOK_SECRET;

// Базовый URL для Telegram API
const TELEGRAM_API_URL = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}`;

// Логирование с временной меткой
function log(level, message) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] [${level}] ${message}`);
}

// Отправляет сообщение пользователю через Telegram API
async function sendTelegramMessage(chat_id, text, reply_markup = null) {
  return new Promise((resolve, reject) => {
    const payload = {
      chat_id: chat_id,
      text: text,
      parse_mode: "Markdown"
    };
    
    if (reply_markup) {
      payload.reply_markup = reply_markup;
    }
    
    const data = JSON.stringify(payload);
    
    log('INFO', `Отправка сообщения на ${chat_id}: ${text.substring(0, 50)}...`);
    
    const options = {
      hostname: 'api.telegram.org',
      port: 443,
      path: `/bot${TELEGRAM_BOT_TOKEN}/sendMessage`,
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
          log('INFO', `Сообщение успешно отправлено, chat_id: ${chat_id}`);
          resolve({ ok: true, response: JSON.parse(responseData) });
        } else {
          log('ERROR', `Ошибка API при отправке: ${res.statusCode}, ${responseData}`);
          resolve({ ok: false, error: `API error: ${res.statusCode}` });
        }
      });
    });
    
    req.on('error', (error) => {
      log('ERROR', `Исключение при отправке сообщения: ${error.message}`);
      reject({ ok: false, error: error.message });
    });
    
    req.write(data);
    req.end();
  });
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
        version: '1.3.0'
      });
    }
    
    // Обработка POST-запроса от Telegram
    if (req.method === 'POST') {
      // Верификация запроса от Telegram
      const secretHeader = req.headers['x-telegram-bot-api-secret-token'];
      
      if (WEBHOOK_SECRET && secretHeader !== WEBHOOK_SECRET) {
        log('WARNING', "Получен неверифицированный запрос");
        return res.status(403).json({
          ok: false,
          error: 'Forbidden'
        });
      }
      
      // Получаем и парсим данные запроса
      const update = req.body;
      log('INFO', `Получено обновление ID: ${update.update_id}`);
      
      // Обработка текстовых сообщений
      if (update.message && update.message.text) {
        const chat_id = update.message.chat.id;
        const text = update.message.text;
        const user = update.message.from.first_name || 'пользователь';
        
        log('INFO', `Сообщение от ${user} (${chat_id}): ${text}`);
        
        if (text === '/start') {
          // Создаем клавиатуру с кнопками
          const keyboard = {
            "inline_keyboard": [
              [{"text": "О боте", "callback_data": "info"}],
              [{"text": "Тест", "callback_data": "test"}]
            ]
          };
          
          // Отправляем приветствие
          await sendTelegramMessage(
            chat_id, 
            `👋 Привет, ${user}!\n\nЯ тестовый бот для проекта DualAI на Vercel.\nЯ использую webhook-подход.`,
            keyboard
          );
        } else {
          // Отправляем эхо
          await sendTelegramMessage(chat_id, `Вы сказали: ${text}`);
        }
      }
      
      // Обработка нажатий на кнопки
      else if (update.callback_query) {
        const callback = update.callback_query;
        const chat_id = callback.message.chat.id;
        const data = callback.data;
        
        log('INFO', `Получен callback с данными: ${data}`);
        
        if (data === 'info') {
          await sendTelegramMessage(chat_id, "Это тестовый бот для проекта DualAI на Vercel через webhook.");
        } else if (data === 'test') {
          await sendTelegramMessage(chat_id, "Тестовое сообщение. Webhook работает!");
        } else {
          await sendTelegramMessage(chat_id, `Получена команда: ${data}`);
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