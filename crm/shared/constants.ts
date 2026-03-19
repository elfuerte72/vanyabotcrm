export const goalLabels: Record<string, string> = {
  weight_loss: 'Похудение',
  weight_gain: 'Набор массы',
  maintenance: 'Поддержание',
  muscle_gain: 'Набор мышц',
};

export const activityLabels: Record<string, string> = {
  sedentary: 'Сидячий образ жизни',
  light: 'Лёгкая активность',
  moderate: 'Умеренная активность',
  active: 'Высокая активность',
  very_active: 'Очень высокая активность',
};

// Human-readable labels for callback button names
// Based on actual Telegram bot inline keyboard button texts
export const eventButtonLabels: Record<string, { label: string; botResponse: string }> = {
  // callback_ru
  buy_now: { label: 'Купить сейчас', botResponse: 'Отправлена ссылка на оплату' },
  show_info: { label: 'Подробнее о программе', botResponse: 'Отправлено видео с информацией' },
  show_results: { label: 'Результаты клиентов', botResponse: 'Отправлено фото результатов' },
  remind_later: { label: 'Напомнить позже', botResponse: 'Отправлено мотивационное сообщение' },
  check_suitability: { label: 'Подходит ли мне?', botResponse: 'Отправлено видео о подходимости' },
  none: { label: 'Отказ от покупки', botResponse: 'Отправлено прощальное сообщение' },
  // callback_en
  nutrition_en: { label: 'Nutrition info', botResponse: 'Sent nutrition + training explanation' },
  cardio_en: { label: 'Cardio vs Muscle', botResponse: 'Sent cardio vs strength training info' },
  different: { label: 'What makes it different?', botResponse: 'Sent unique program explanation' },
  beginner: { label: "I'm a beginner", botResponse: 'Sent beginner-friendly explanation' },
  price: { label: 'Why this price?', botResponse: 'Sent pricing explanation (49 AED)' },
  help: { label: 'Help', botResponse: 'Sent program summary + access info' },
  coaching: { label: 'Coaching options', botResponse: 'Sent coaching packages (79/99 AED)' },
  gym: { label: 'What gym do I need?', botResponse: 'Sent gym requirements (barbell + dumbbells)' },
  access: { label: 'Get access', botResponse: 'Sent access details + payment info' },
  upgrade_79: { label: 'Technique Check (79 AED)', botResponse: 'Создан заказ Ziina, отправлена ссылка' },
  upgrade_99: { label: '7-Day Coaching (99 AED)', botResponse: 'Создан заказ Ziina, отправлена ссылка' },
  // funnel day events
  day_1: { label: 'День 1 воронки', botResponse: 'Отправлено сообщение дня 1' },
  day_2: { label: 'День 2 воронки', botResponse: 'Отправлено сообщение дня 2' },
  day_3: { label: 'День 3 воронки', botResponse: 'Отправлено сообщение дня 3' },
  day_4: { label: 'День 4 воронки', botResponse: 'Отправлено сообщение дня 4' },
  day_5: { label: 'День 5 воронки', botResponse: 'Отправлено сообщение дня 5' },
};
