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
  // Zone selection (RU)
  zone_belly: { label: 'Выбрал зону: Низ живота', botResponse: 'Запущена воронка для зоны «Низ живота»' },
  zone_thighs: { label: 'Выбрал зону: Ушки на бёдрах', botResponse: 'Запущена воронка для зоны «Ушки на бёдрах»' },
  zone_arms: { label: 'Выбрал зону: Дряблость рук', botResponse: 'Запущена воронка для зоны «Дряблость рук»' },
  zone_glutes: { label: 'Выбрал зону: Форма ягодиц', botResponse: 'Запущена воронка для зоны «Форма ягодиц»' },
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

// Labels for funnel_message events (event_data = "stage_N" or special keys)
export const funnelStageLabels: Record<string, string> = {
  wakeup_sent: 'Разбуди тело (утренняя зарядка)',
  stage_0_zone_ask: 'Выбор проблемной зоны',
  stage_0: 'Этап 0 — Знакомство',
  stage_1: 'Этап 1 — Мотивация',
  stage_2: 'Этап 2 — Фото результатов',
  stage_3: 'Этап 3 — Видео-кружок',
  stage_4: 'Этап 4 — Социальное доказательство',
  stage_5: 'Этап 5 — Видео / Hard sell',
  stage_6: 'Этап 6 — Повторное предложение',
  stage_7: 'Этап 7 — Мягкое напоминание',
  stage_8: 'Этап 8 — Финальный призыв',
  stage_9: 'Этап 9 — Upsell',
  stage_10: 'Этап 10 — Upsell повторный',
  stage_11: 'Этап 11 — Дожим',
  stage_12: 'Этап 12 — Финал',
};

// Human-readable labels for funnel_variant (zone)
export const funnelVariantLabels: Record<string, string> = {
  belly: 'Низ живота',
  thighs: 'Ушки на бёдрах',
  arms: 'Дряблость рук',
  glutes: 'Форма ягодиц',
};

// Max funnel stage by language
// RU: 12 stages (belly), 11 stages (thighs/arms/glutes)
// EN/AR: 10 stages
export function getMaxFunnelStage(language?: string | null, variant?: string | null): number {
  if (!language || language === 'ru') {
    if (variant === 'belly') return 12;
    if (variant === 'thighs' || variant === 'arms' || variant === 'glutes') return 11;
    return 12; // default for RU without variant
  }
  return 10; // EN, AR
}
