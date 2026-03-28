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
  // Onboarding
  lang_ru: { label: 'Выбрал язык: Русский', botResponse: 'Начат диалог на русском' },
  lang_en: { label: 'Выбрал язык: English', botResponse: 'Начат диалог на английском' },
  lang_ar: { label: 'Выбрал язык: العربية', botResponse: 'Начат диалог на арабском' },
  // Conversation
  confirm_data: { label: 'Подтвердил данные', botResponse: 'Запущен расчёт КБЖУ и генерация рациона' },
  fix_data: { label: 'Хочет исправить данные', botResponse: 'Предложено указать что исправить' },
  // RU-only callbacks
  confirm_paid_ru: { label: 'Подтвердил оплату (RU)', botResponse: 'Пользователь отмечен как покупатель' },
  video_workout: { label: 'Бесплатная тренировка', botResponse: 'Отправлена ссылка на видео тренировки' },
  learn_workout: { label: 'Узнать о тренировке', botResponse: 'Отправлена информация о тренировке + ссылка' },
  video_circle: { label: 'Видео-кружок «как это работает»', botResponse: 'Отправлен видео-кружок' },
  upsell_decline: { label: 'Отказ от допродажи', botResponse: 'Пользователь отклонил upsell' },
  // EN funnel question buttons (en_funnel_q_0 .. en_funnel_q_10)
  en_funnel_q_0: { label: 'EN Question (stage 0)', botResponse: 'Отправлено следующее сообщение воронки' },
  en_funnel_q_1: { label: 'EN Question (stage 1)', botResponse: 'Отправлено следующее сообщение воронки' },
  en_funnel_q_2: { label: 'EN Question (stage 2)', botResponse: 'Отправлено следующее сообщение воронки' },
  en_funnel_q_3: { label: 'EN Question (stage 3)', botResponse: 'Отправлено следующее сообщение воронки' },
  en_funnel_q_4: { label: 'EN Question (stage 4)', botResponse: 'Отправлено следующее сообщение воронки' },
  en_funnel_q_5: { label: 'EN Question (stage 5)', botResponse: 'Отправлено следующее сообщение воронки' },
  en_funnel_q_6: { label: 'EN Question (stage 6)', botResponse: 'Отправлено следующее сообщение воронки' },
  en_funnel_q_7: { label: 'EN Question (stage 7)', botResponse: 'Отправлено следующее сообщение воронки' },
  en_funnel_q_8: { label: 'EN Question (stage 8)', botResponse: 'Отправлено следующее сообщение воронки' },
  en_funnel_q_9: { label: 'EN Question (upsell 9)', botResponse: 'Отправлено upsell сообщение воронки' },
  en_funnel_q_10: { label: 'EN Question (upsell 10)', botResponse: 'Отправлено upsell сообщение воронки' },
  // AR funnel question buttons (ar_funnel_q_0 .. ar_funnel_q_8)
  ar_funnel_q_0: { label: 'AR Question (stage 0)', botResponse: 'Отправлено следующее сообщение воронки' },
  ar_funnel_q_1: { label: 'AR Question (stage 1)', botResponse: 'Отправлено следующее сообщение воронки' },
  ar_funnel_q_2: { label: 'AR Question (stage 2)', botResponse: 'Отправлено следующее сообщение воронки' },
  ar_funnel_q_3: { label: 'AR Question (stage 3)', botResponse: 'Отправлено следующее сообщение воронки' },
  ar_funnel_q_4: { label: 'AR Question (stage 4)', botResponse: 'Отправлено следующее сообщение воронки' },
  ar_funnel_q_5: { label: 'AR Question (stage 5)', botResponse: 'Отправлено следующее сообщение воронки' },
  ar_funnel_q_6: { label: 'AR Question (stage 6)', botResponse: 'Отправлено следующее сообщение воронки' },
  ar_funnel_q_7: { label: 'AR Question (stage 7)', botResponse: 'Отправлено следующее сообщение воронки' },
  ar_funnel_q_8: { label: 'AR Question (stage 8)', botResponse: 'Отправлено следующее сообщение воронки' },
  ar_funnel_q_9: { label: 'AR Question (upsell 9)', botResponse: 'Отправлено upsell сообщение воронки' },
  ar_funnel_q_10: { label: 'AR Question (upsell 10)', botResponse: 'Отправлено upsell сообщение воронки' },
};

// Labels for funnel_message events (event_data = "stage_N")
export const funnelStageLabels: Record<string, string> = {
  stage_0: 'Воронка: этап 0',
  stage_1: 'Воронка: этап 1',
  stage_2: 'Воронка: этап 2',
  stage_3: 'Воронка: этап 3',
  stage_4: 'Воронка: этап 4',
  stage_5: 'Воронка: этап 5',
  stage_6: 'Воронка: этап 6',
  stage_7: 'Воронка: этап 7',
  stage_8: 'Воронка: этап 8',
  stage_9: 'Воронка: этап 9 (upsell)',
  stage_10: 'Воронка: этап 10 (upsell)',
};
