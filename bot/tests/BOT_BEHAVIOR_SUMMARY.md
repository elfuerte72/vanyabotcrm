# Bot Behavior Summary (RU / EN / AR)

Summary of how the bot responds, what text it sends, and how Telegram buttons work across all 3 languages.

---

## 1. Core Messages

| Message | RU | EN | AR |
|---------|----|----|-----|
| **ALREADY_CALCULATED** | "Чемпион, извини. Я не могу второй раз тебе рассчитать КБЖУ." | "Champion, I'm sorry. I cannot calculate your macros a second time." | "بطل، اعتذر منك. لا يمكنني حساب السعرات والماكروز لك مرة ثانية." |
| **CALCULATING_MENU** | "Принял! Считаю твои калории и подбираю меню..." | "Got it! Calculating your calories and selecting a menu..." | "تم الاستلام! جاري حساب سعراتك الحرارية..." |
| **SUBSCRIBE_MESSAGE** | "Чтобы использовать бота, подпишись на канал..." | "To use the bot, please subscribe to the channel..." | "لاستخدام البوت، يرجى الاشتراك في القناة..." |

### /start
Sends a trilingual greeting (RU + EN + AR combined in a single message). Not language-aware — same message for all users.

### Meal Plan (format_meal_plan_html)
**Localization gap**: Headers are hardcoded in Russian regardless of user language:
- "ПЛАН ПИТАНИЯ ГОТОВ!" (always Russian)
- "ИТОГО ЗА ДЕНЬ:" (always Russian)
- Meal icons: detected by keyword (RU/EN/AR meal names supported)

---

## 2. Sales Funnel (Days 0-5)

### Day 0 — "Wake up your body"
| | RU | EN | AR |
|--|----|----|-----|
| **Theme** | Разбуди тело — зарядка 7 минут | Wake up your body in 7 min | أيقظ جسمك في 7 دقائق |
| **Tone** | Feminine ("ты решила") | Gender-neutral | Feminine ("قررت") |
| **Button** | `[Разбуди тело]` → `video_workout` | `[Wake up your body]` → `video_workout` | `[أيقظ جسمك]` → `video_workout` |

### Day 1 — "Buy with discount"
| | RU | EN | AR |
|--|----|----|-----|
| **Theme** | Тело включилось, скидка на тренировку | Body activated, workout discount | الجسم تنشط، خصم على التمرين |
| **Price** | ~~1900₽~~ → **990₽** | ~~$25~~ → **$15** | ~~$25~~ → **$15** |
| **Button** | `[Купить со скидкой]` → `buy_now` | `[Buy with discount]` → `buy_now` | `[اشتري بخصم]` → `buy_now` |

### Day 2 — "Social proof"
| | RU | EN | AR |
|--|----|----|-----|
| **Theme** | Отзывы: отёки, живот, целлюлит | Testimonials: swelling, belly, cellulite | شهادات: تورم، بطن، سيلوليت |
| **Buttons** | `[Да, хочу результат!]` → `buy_now` | `[Yes, I want results!]` → `buy_now` | `[نعم، أريد نتائج!]` → `buy_now` |
| | `[Тренировка подойдёт мне?]` → `check_suitability` | `[Will it suit me?]` → `check_suitability` | `[هل يناسبني؟]` → `check_suitability` |

### Day 3 — "Pain → Solution"
| | RU | EN | AR |
|--|----|----|-----|
| **Theme** | Проблемные зоны + решение за 20 мин | Problem areas + 20-min fix | مناطق مشكلة + حل في 20 دقيقة |
| **Buttons** | `[Да!]` → `buy_now` | `[Yes!]` → `buy_now` | `[نعم!]` → `buy_now` |
| | `[Что в программе?]` → `show_info` | `[What's in the program?]` → `show_info` | `[ماذا في البرنامج؟]` → `show_info` |

### Day 4 — "Price as reason to buy"
| | RU | EN | AR |
|--|----|----|-----|
| **Theme** | Цена 990₽ < ужин/тушь/кофейня | Price $15 < dinner/mascara/coffee | السعر $15 < عشاء/ماسكارا/مقهى |
| **Price** | **990₽** | **$15** | **$15** |
| **Buttons** | `[Хочу скидку]` → `buy_now` | `[I want a discount]` → `buy_now` | `[أريد خصماً]` → `buy_now` |
| | `[Мне не подходит]` → `none` | `[Not for me]` → `none` | `[لا يناسبني]` → `none` |

### Day 5 — "Soft deadline"
| | RU | EN | AR |
|--|----|----|-----|
| **Theme** | Последний день скидки 990₽ | Last day at $15 | آخر يوم بسعر $15 |
| **Buttons** | `[Да, беру!]` → `buy_now` | `[Yes, I'm in!]` → `buy_now` | `[نعم، آخذه!]` → `buy_now` |
| | `[Напомни позже]` → `remind_later` | `[Remind me later]` → `remind_later` | `[ذكرني لاحقاً]` → `remind_later` |

### Funnel Stage Lifecycle
```
User gets meal plan → set_food_received() → funnel_stage=0
                                              ↓
Daily 23:00 UTC cron → get_funnel_targets (stage 0-4, non-buyers)
                                              ↓
Send message → update_funnel_stage (stage+1)
                                              ↓
Day 0 (stage 0) → Day 1 (stage 1) → ... → Day 5 (stage 5) → EXIT
                                              ↓
If buy_now clicked at ANY stage → is_buyer=TRUE → excluded from funnel
```

---

## 3. Callback Responses

### buy_now
| | RU | EN | AR |
|--|----|----|-----|
| **Text** | "💳 Отлично! Переходи к оплате..." | "💳 Great! Proceed to payment..." | "💳 ممتاز! انتقلي للدفع..." |
| **Button** | `[💳 Оплатить]` → URL (Tribute) | `[💳 Pay]` → URL (Tribute) | `[💳 ادفع]` → URL (Tribute) |
| **CRM** | `mark_as_buyer(user_id)` → `is_buyer=TRUE` | Same | Same |

### show_info
| | All languages |
|--|---------------|
| **Action** | Downloads and sends info video from Google Drive |
| **CRM** | No data changes |
| **Error** | "Sorry, video is temporarily unavailable." |

### show_results
| | RU | EN | AR |
|--|----|----|-----|
| **Action** | Sends random results photo with caption | Same | Same |
| **Caption** | "📌 упражнения которые бьют в «цель»..." | "📌 exercises that hit the target..." | "📌 تمارين تصيب الهدف..." |
| **CRM** | No data changes | Same | Same |

### check_suitability
| | All languages |
|--|---------------|
| **Action** | Downloads and sends suitability video from Google Drive |
| **CRM** | No data changes |

### remind_later
| | RU | EN | AR |
|--|----|----|-----|
| **Text** | "Ты уже на верном пути... буду рад видеть в канале" | "You're already on the right path..." | "أنت بالفعل على الطريق الصحيح..." |
| **CRM** | No data changes | Same | Same |

### none
| | RU | EN | AR |
|--|----|----|-----|
| **Text** | "Я хорошо знаю, что такое экономить на себе..." | "I know well what it's like to save on yourself..." | "أعرف جيداً ما يعنيه التوفير على نفسك..." |
| **CRM** | No data changes | Same | Same |

### video_workout
| | RU | EN | AR |
|--|----|----|-----|
| **Text** | "Вот теперь тело включилось..." | "Now your body is activated..." | "الآن جسمك تنشط..." |
| **Price** | 990₽ вместо 1900 | $15 instead of $25 | $15 بدلاً من $25 |
| **Buttons** | `[▶️ Смотреть видео]` → URL | `[▶️ Watch video]` → URL | `[▶️ شاهد الفيديو]` → URL |
| | `[💳 Оплатить]` → `buy_now` | `[💳 Pay]` → `buy_now` | `[💳 ادفع]` → `buy_now` |
| **CRM** | `advance_funnel_if_at_stage(user_id, 1)` — conditional stage 1→2 | Same | Same |

---

## 4. Language Differences

### Currency & Pricing
| | RU | EN | AR |
|--|----|----|-----|
| Regular price | 1900₽ | $25 | $25 |
| Discount price | 990₽ | $15 | $15 |
| In-person comparison | 1500-3000₽ | $30-50 | $30-50 |

### Tone & Address
| | RU | EN | AR |
|--|----|----|-----|
| Gender | Feminine (ты решила, ты внедрила) | Neutral/feminine (you decided) | Feminine (قررت, أنت) |
| Formality | Informal (ты) | Informal (you) | Semi-formal |

### Payment URLs
Currently all 3 languages use the same `settings.tribute_link`. EN/AR Ziina support is a TODO.

### Localization Gaps
1. **Meal plan headers** — `format_meal_plan_html()` uses hardcoded Russian text: "ПЛАН ПИТАНИЯ ГОТОВ!", "ИТОГО ЗА ДЕНЬ:", etc.
2. **Voice transcription error** — Fallback is English-only: "Sorry, I couldn't process your voice message"
3. **show_info error** — Fallback is English-only: "Sorry, video is temporarily unavailable"
4. **Calculating message** — `_process_text_message` sends ALL 3 languages concatenated instead of just the detected language
5. **AI agent food prompt** — System prompt is in Russian, so meal names tend to be Russian regardless of user language

---

## 5. Test Coverage Summary

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_kbju_pipeline.py` | 15 | Full KBJU pipeline × 3 languages, guards, conversation route |
| `test_funnel_simulation.py` | 71 | 6-day cycle × 3 languages, buttons, text, error resilience |
| `test_callbacks_multilang.py` | 40 | 7 callbacks × 3 languages, CRM updates, keyboard config |
| `test_db_integration.py` | 19 | Real DB: upsert, funnel, buyer, advance, chat history |
| `test_callbacks.py` | 13 | Original callback tests (covered by multilang) |
| `test_funnel.py` | 7 | Original funnel message tests (covered by simulation) |
| `test_funnel_integration.py` | ~25 | Original funnel integration (covered by simulation) |
| `test_calculator.py` | 9 | Calculator pure function tests |
| `test_calculator_extended.py` | ~25 | Extended calculator edge cases |
| `test_formatter.py` | ~20 | Formatter, meal plan HTML, validation |
| `test_language.py` | 10 | Language detection |
| `test_i18n.py` | 3 | i18n module completeness |
| `test_message_handler.py` | ~12 | Message handler (covered by pipeline) |
| **Total** | **~269** | |
