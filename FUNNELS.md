# Документация по воронкам сообщений

Воронка запускается после того, как пользователь получает расчёт КБЖУ и план питания (`get_food = TRUE`). Планировщик проверяет `next_funnel_msg_at` каждые 15 минут и отправляет сообщения, когда время пришло.

---

## Общая схема

| | RU | EN | AR |
|---|---|---|---|
| Аудитория | Женщины | Мужчины (ОАЭ) | Мужчины (ОАЭ) |
| Продукт | Тренировка 40 мин, дома | Тренировка в зале, сушка + мышцы | Тренировка в зале, сушка + мышцы |
| Цена | 690 руб. | 49 AED | 49 درهم |
| Стадий | 8 (0-7) | 11 (0-10) | 11 (0-10) |
| Upsell | Нет | 2 (стадии 9-10) | 2 (стадии 9-10) |
| Фото | Стадии 1, 2 | Стадии 0, 6 | Стадии 0, 6 |
| Видео-кружочки | Стадии 3, 5 | Нет | Нет |
| Кнопки-вопросы | Нет | Стадии 0-8 | Стадии 0-8 |
| Callback prefix | — | `en_funnel_q_` | `ar_funnel_q_` |
| Оплата | Tribute | Ziina | Ziina |

---

## RU — Русская воронка (8 стадий)

**Аудитория:** женщины, домашние тренировки, проблемные зоны.
**Цена:** 690 руб. (вместо 1390 руб.)
**Тайминг:** привязан к московскому времени (MSK).

### Расписание

| Стадия | Когда отправляется | Интервал |
|--------|-------------------|----------|
| 0 | +30 мин после КБЖУ | — |
| 1 | +2.5ч после stage 0 | +2.5ч |
| 2 | Следующий день, 10:00 MSK | ~следующее утро |
| 3 | Следующий день, 10:00 MSK | ~следующее утро |
| 4 | Тот же день, 19:00 MSK | ~вечер |
| 5 | Следующий день, 19:00 MSK | ~следующий вечер |
| 6 | Следующий день, 11:00 MSK | ~следующее утро |
| 7 | Следующий день, 10:00 MSK | ~следующее утро |

### Стадии

#### Stage 0 — Подарок: утренняя активация
- **Медиа:** нет
- **Кнопка:** `[Разбудить тело]` → `video_workout` (ссылка на видео)

**Текст:**
> Привет!
>
> Меня зовут Иван, и я рад что ты здесь — значит, ты уже сделала первый шаг к себе.
>
> Твой план питания уже у тебя. Это основа. Но скажу честно:
>
> Даже самое правильное питание работает в два раза медленнее, если тело совсем не двигается. Не потому что «надо потеть» — а потому что движение запускает обмен, убирает отёки, делает кожу упругой изнутри.
>
> Я сделал тебе подарок — короткую утреннюю активацию на 7 минут. Не тренировка. Просто — как проснуться и почувствовать себя человеком с самого утра.

---

#### Stage 1 — Фото до/после + тизер тренировки
- **Медиа:** фото (stage_1)
- **Кнопка:** `[Узнать про тренировку]` → `learn_workout`

**Текст:**
> Надеюсь, активация зашла
>
> Посмотри на эти два фото. Это реальная девушка. Без хирургии. Без изнуряющих диет.
>
> Ушки на бёдрах стали меньше. Руки подтянулись. Живот ниже пупка — плоский. Осанка изменилась — она буквально стала выше.
>
> Это произошло потому, что она начала делать одну конкретную тренировку — направленно на те самые зоны, которые нас беспокоят.
>
> Я собрал такую тренировку. Без оборудования. Дома. 40 минут — и работают именно те места, от которых хочется избавиться.
>
> Расскажу подробнее завтра. Если уже хочешь знать:

---

#### Stage 2 — История Маши + фото до/после
- **Медиа:** фото (stage_2)
- **Кнопки:** нет

**Текст:**
> Хочу рассказать тебе про одну девушку.
>
> Маша написала мне в феврале. Она не ходила в зал — «нет времени, дорого, стыдно». Её беспокоило: ушки на бёдрах, дряблость рук и низ живота. Она говорила: «Я не хочу худеть, я хочу быть подтянутой».
>
> Через 3 недели после тренировки она написала мне:
>
> «Я не верила, что это поможет. Но бёдра реально изменились. И руки. И я стала стоять прямее».
>
> Маша занималась дома. Просто следовала тренировке — шаг за шагом, как я показал.
>
> Завтра покажу изнутри — как устроена тренировка и почему она работает именно на эти зоны.

---

#### Stage 3 — Кружочек «как это работает»
- **Медиа:** видео-кружочек (how_it_works)
- **Кнопка:** `[Посмотреть]` → `video_circle`

**Текст:**
> Часто спрашивают: «А как это вообще работает?»
>
> Объясняю голосом — коротко и без сложных слов. Почему обычные приседания не убирают ушки, что нужно делать по-другому и как понять что ты делаешь правильно.

---

#### Stage 4 — Подробное описание тренировки (текст)
- **Медиа:** нет
- **Кнопки:** нет

**Текст:**
> Показываю тебе, что внутри тренировки.
>
> Зоны, с которыми мы работаем:
> → Ушки на бёдрах — изолированная работа на галифе-зону
> → Дряблость рук и трицепс — результат виден через 2–3 недели
> → Низ живота — без перегрузки шеи и поясницы
> → Ягодицы: 2 упражнения — одно формирует нижнюю часть, второе создаёт округлый верх
> → Осанка: 2 упражнения на грудной отдел — открытые плечи и красивая спина
>
> Бонус: дыхательная техника против отёков
>
> Формат:
> → Без зала и оборудования — только ты и 40 минут
> → Бутылка воды вместо гантели — этого достаточно
> → Варианты каждого упражнения по сложности
>
> Завтра — честный разговор про цену. Оставайся на связи

---

#### Stage 5 — Sales pitch: 690 руб. + кружочек
- **Медиа:** видео-кружочек (will_it_suit)
- **Кнопка:** `[Забрать тренировку]` → `buy_now`

**Текст:**
> Хочу сказать тебе кое-что важное.
>
> Я вложил в эту тренировку всё, что знаю о женском теле...
>
> Что ты получишь:
> → Полноценную 40-минутную видео-тренировку на все проблемные зоны
> → Бёдра (ушки), руки, низ живота, ягодицы, осанка — всё в одном
> → Дыхательная техника против отёков
> → Детальный разбор техники каждого упражнения
> → Личная поддержка — вопросы пишешь мне напрямую в Telegram
>
> **690 руб.** — только здесь, только сейчас.
> Стандартная цена — 1390 руб. Экономия — 700 руб.

---

#### Stage 6 — Мягкое напоминание
- **Медиа:** нет
- **Кнопка:** `[Забрать тренировку]` → `buy_now`

**Текст:**
> Напоминаю — не чтобы давить, а чтобы ты не пожалела
>
> Часто бывает: видишь, думаешь «куплю потом» — и потом уже другая цена.
>
> Цена 690 руб. только для подписчиц бота
>
> Если есть вопросы — просто напиши мне. Отвечу честно.

---

#### Stage 7 — Благодарность + канал (без продажи)
- **Медиа:** нет
- **Кнопка:** `[Подписаться на канал]` → URL: https://t.me/ivanfit_health

**Текст:**
> Спасибо, что была со мной эти дни
>
> Вне зависимости от того, взяла ли ты тренировку или нет — я рад что ты здесь.
> В моём Telegram-канале — каждый день бесплатно:
> → упражнения и лайфхаки для тела
> → питание без голодания и срывов
> → честные советы от практикующего тренера
> → мотивация, которая не раздражает

---

## EN — Английская воронка (11 стадий)

**Аудитория:** мужчины, тренировки в зале, сушка с сохранением мышц.
**Цена:** 49 AED (вместо 99 AED).
**Тайминг:** интервальный (не привязан к часовому поясу).

### Расписание

| Стадия | Интервал после предыдущей | Тип |
|--------|--------------------------|-----|
| 0 | +30 мин после КБЖУ | Основная |
| 1 | +5 мин после stage 0 | Основная |
| 2 | +1 час | Основная |
| 3 | +1 час | Основная |
| 4 | +1 час | Основная |
| 5 | +1 час | Основная |
| 6 | +1 час | Основная |
| 7 | +1 час | Основная |
| 8 | +1 час | Основная |
| 9 | +1 час | Upsell |
| 10 | +24 часа | Upsell |

> Кнопка-вопрос (❓) мгновенно отправляет следующую стадию, не дожидаясь таймера.

### Стадии 0-8 — Основная воронка

Каждая стадия имеет 2 кнопки:
- `[✅ Get Access — 49 AED]` → `buy_now`
- `[❓ Вопрос]` → `en_funnel_q_{stage}` (мгновенный переход к следующей стадии)

---

#### Stage 0 — Intro + фото
- **Медиа:** фото (en_stage_0)

**Текст:**
> bro 👊 This is what happens when nutrition meets the right training.
>
> Most men cut calories, lose weight — and end up looking smaller and flat. Not lean. Not muscular. Just… smaller.
>
> I see this every day. Men who train hard, eat right — but lose muscle because their training method is wrong.
>
> That's exactly what this workout is built to fix.
>
> One method. Protects your muscle while you lose the fat. Used by men in Abu Dhabi, London, New York, Mumbai — same result.
>
> 🔒 Special price for you: 49 AED — only inside this chat. Outside it costs 99 AED. This offer won't stay here long.

**Кнопка-вопрос:** `❓ Does training really matter?`

---

#### Stage 1 — Training matters
**Текст:**
> Great question — and you're right to ask.
>
> Here's the truth most coaches won't tell you:
>
> When you're in a calorie deficit, your body looks for energy everywhere. Without the right training signal — it burns muscle alongside fat.
>
> Perfect nutrition + wrong training = lose fat AND muscle.
> Perfect nutrition + right training = lose fat, KEEP muscle.
>
> The difference isn't how hard you work. It's whether your training tells your body to protect the muscle.
>
> This workout does exactly that.

**Кнопка-вопрос:** `❓ Can I just do cardio?`

---

#### Stage 2 — Cardio alone costs you muscle
**Текст:**
> Cardio burns calories. That part is true.
>
> But cardio alone during a cut will cost you:
> ❌ Your muscle — body breaks it down for energy
> ❌ Your shape — you lose size, not just fat
> ❌ Your strength — you get smaller, not leaner
>
> Men who only do cardio during a cut end up looking softer — not harder.
>
> To keep your muscle, your body needs a specific strength signal. Not more cardio. The right training method.
>
> That's what this workout gives you.

**Кнопка-вопрос:** `❓ What makes it different?`

---

#### Stage 3 — Built for cutting
**Текст:**
> Most programs are built for bulking or general fitness.
>
> This one is built for one specific situation:
> → You're cutting calories
> → You want to keep your muscle
> → You train in a normal gym
>
> Equipment you need: ✅ Barbell ✅ Dumbbells ✅ Bodyweight
>
> That's it. No machines. No special setup. Any gym in Abu Dhabi, London, Mumbai, New York — you're ready.
>
> The difference isn't the exercises. It's the training logic built specifically for fat loss + muscle retention.

**Кнопка-вопрос:** `❓ Need a special gym?`

---

#### Stage 4 — No special gym needed
**Текст:**
> No special gym needed. ✅
>
> Any standard gym works. Anywhere in the world.
>
> You need: → Barbell + plates → Dumbbells → Space for bodyweight work
>
> The method works because of HOW you train — not what equipment you have.
>
> Smart programming > expensive equipment.

**Кнопка-вопрос:** `❓ I'm a beginner — will it work?`

---

#### Stage 5 — Beginners get fastest results
**Текст:**
> Perfect — beginners get results the fastest. ✅
>
> Your body responds quickly when you start training correctly from day one.
>
> Everything is explained clearly: → What to do → How to do it → Why it works for fat loss + muscle retention
>
> No guessing. No confusion. No wasted sessions.
>
> Most men waste months doing the wrong thing. You won't.

**Кнопка-вопрос:** `❓ What do I get after paying?`

---

#### Stage 6 — What you get + фото
- **Медиа:** фото (en_stage_6)

**Текст:**
> After payment — instant access. ✅
>
> You get:
> ✅ Full workout structure — session by session
> ✅ Exercises: barbell + dumbbells + bodyweight
> ✅ The training logic for fat loss + muscle retention explained clearly
> ✅ No machines needed
> ✅ Works in any gym — Abu Dhabi, London, Mumbai, anywhere
> ✅ PDF guide — how to progressively overload
>
> This is not a random exercise list. It's a proven method.
>
> If you have any questions — message me directly on Telegram. 💬
> 👉 @Ivan_Razmazin

**Кнопка-вопрос:** `❓ Why only 49 AED?`

---

#### Stage 7 — Price justification
**Текст:**
> Because I want every serious man to have access to this. ✅
>
> 49 AED is less than one dinner out. But the wrong training method can cost you months of lost progress — and muscle you won't get back easily.
>
> You're not paying for a workout. You're paying for the method that makes your cut actually work.
>
> One time. No subscription. Instant access.
>
> 🔒 This price exists only inside this chat. Come back later — it's 99 AED.

**Кнопка-вопрос:** `❓ I want personal help`

---

#### Stage 8 — Final push
**Текст:**
> You eat right. You show up to the gym. You want to look lean and muscular — not just lighter.
>
> But every week without the right training method — you're losing muscle that won't come back easily.
>
> Men from Abu Dhabi to London to Mumbai have fixed this with one workout. One clear method.
>
> 🔒 49 AED — only here, only now. After this chat — 99 AED.
>
> Don't leave without it.

**Кнопка-вопрос:** `❓ I want coaching`

---

### Стадии 9-10 — Upsell (после покупки)

#### Stage 9 — Upsell 1: Technique Check (79 AED)
- **Кнопки:** `[✅ Technique Check — 79 AED]` → `buy_now` | `[⬅️ No thanks, just workout]` → `upsell_decline`

**Текст:**
> One more thing before you start. 👊
>
> Most men lose 20–30% of their results because of form mistakes they don't even know they're making.
>
> → Send me 3–5 videos of your key exercises
> → I review each one personally
> → You get exact corrections — what to fix, how to fix it
>
> One session of correct form builds more muscle than weeks of sloppy reps.

---

#### Stage 10 — Upsell 2: 7-Day Coaching (129 AED)
- **Кнопки:** `[✅ 7-Day Coaching — 129 AED]` → `buy_now` | `[⬅️ No thanks, I'm good]` → `upsell_decline`

**Текст:**
> How was your first session? 👊
>
> If you want to move faster — and not figure everything out alone:
>
> **7-Day Personal Coaching — 129 AED** ✅
>
> → Daily check-ins with me personally
> → Workout adjusted to your body and schedule
> → Nutrition tweaks based on your real progress
> → Direct answers to every question
>
> 7 days with the right guidance gets you further than most men go training alone in a month.

---

## AR — Арабская воронка (11 стадий)

**Аудитория:** мужчины ОАЭ, тренировки в зале, сушка с сохранением мышц.
**Диалект:** Gulf Arabic (خليجي) — разговорный стиль ОАЭ, мужские формы обращения.
**Цена:** 49 درهم (вместо 99 درهم).
**Тайминг:** идентичен EN (интервальный).

### Расписание

| Стадия | Интервал после предыдущей | Тип |
|--------|--------------------------|-----|
| 0 | +30 мин после КБЖУ | Основная |
| 1 | +5 мин после stage 0 | Основная |
| 2 | +1 час | Основная |
| 3 | +1 час | Основная |
| 4 | +1 час | Основная |
| 5 | +1 час | Основная |
| 6 | +1 час | Основная |
| 7 | +1 час | Основная |
| 8 | +1 час | Основная |
| 9 | +1 час | Upsell |
| 10 | +24 часа | Upsell |

> Кнопка-вопрос (❓) мгновенно отправляет следующую стадию, не дожидаясь таймера.

### Стадии 0-8 — Основная воронка

Каждая стадия имеет 2 кнопки:
- `[✅ احصل على التمرين — 49 درهم]` → `buy_now`
- `[❓ Вопрос]` → `ar_funnel_q_{stage}` (мгновенный переход к следующей стадии)

---

#### Stage 0 — Intro + фото
- **Медиа:** фото (en_stage_0 — общее с EN)

**Текст:**
> يا بطل 👊 هذا اللي يصير لما التغذية تلتقي بالتمرين الصح.
>
> أغلب الشباب ينزلون سعراتهم، ينزل وزنهم — بس يطلعون أصغر وممسوحين. مو ناشفين. مو عضليين. بس… أصغر.
>
> أشوف هالشي كل يوم. شباب يتمرنون بجد، ياكلون صح — بس يخسرون عضل لأن طريقة تمرينهم غلط.
>
> هذا التمرين مصمم بالضبط يحل هالمشكلة.
>
> طريقة وحدة. تحمي عضلك وانت تنزل الدهون. شباب من أبوظبي، لندن، نيويورك، مومباي — نفس النتيجة.
>
> 🔒 سعر خاص لك: 49 درهم — بس داخل هالشات. برا يكلف 99 درهم. هالعرض ما بيدوم.

**Кнопка-вопрос:** `❓ التمرين فعلاً يفرق؟`

---

#### Stage 1 — التمرين يفرق
**Текст:**
> سؤال ممتاز — وحق عليك تسأل.
>
> هذي الحقيقة اللي أغلب المدربين ما يقولونها:
>
> لما تكون في عجز سعرات، جسمك يدور على طاقة من كل مكان. بدون إشارة التمرين الصح — يحرق عضل مع الدهون.
>
> تغذية مثالية + تمرين غلط = تخسر دهون وعضل.
> تغذية مثالية + تمرين صح = تخسر دهون وتحافظ على العضل.
>
> الفرق مو بقوة التمرين. الفرق إن تمرينك يقول لجسمك يحمي العضل.
>
> هذا التمرين يسوي بالضبط كذا.

**Кнопка-вопрос:** `❓ ما اسوي كارديو بس؟`

---

#### Stage 2 — الكارديو لحاله ما يكفي
**Текст:**
> الكارديو يحرق سعرات. هالشي صح.
>
> بس الكارديو لحاله وقت الكت بيكلفك:
> ❌ عضلك — جسمك يكسره عشان طاقة
> ❌ شكلك — تنزل حجم، مو بس دهون
> ❌ قوتك — تصغر، مو تنشف
>
> الشباب اللي يسوون كارديو بس وقت الكت يطلعون أنعم — مو أقوى.
>
> عشان تحافظ على عضلك، جسمك يحتاج إشارة قوة محددة. مو كارديو زيادة. طريقة التمرين الصح.
>
> هذا اللي يعطيك إياه هالتمرين.

**Кнопка-вопрос:** `❓ شو الفرق عن غيره؟`

---

#### Stage 3 — مصمم للكت
**Текст:**
> أغلب البرامج مصممة للبلك أو اللياقة العامة.
>
> هذا مصمم لحالة وحدة بالضبط:
> → انت في عجز سعرات
> → تبي تحافظ على عضلك
> → تتمرن في جيم عادي
>
> المعدات اللي تحتاجها: ✅ بار ✅ دمبلز ✅ وزن الجسم
>
> بس كذا. لا أجهزة. لا سيت أب خاص. أي جيم في أبوظبي، لندن، مومباي، نيويورك — جاهز.
>
> الفرق مو التمارين. الفرق منطق التمرين المصمم خصيصاً لحرق الدهون + حماية العضل.

**Кнопка-вопрос:** `❓ أحتاج جيم خاص؟`

---

#### Stage 4 — لا تحتاج جيم خاص
**Текст:**
> لا تحتاج جيم خاص. ✅
>
> أي جيم عادي يمشي. في أي مكان بالعالم.
>
> تحتاج: → بار + أوزان → دمبلز → مكان لتمارين وزن الجسم
>
> الطريقة تشتغل بسبب كيف تتمرن — مو شو المعدات عندك.
>
> برمجة ذكية > معدات غالية.

**Кнопка-вопрос:** `❓ أنا مبتدئ — بينفع؟`

---

#### Stage 5 — المبتدئين يحصلون على أسرع نتائج
**Текст:**
> ممتاز — المبتدئين يحصلون على أسرع نتائج. ✅
>
> جسمك يستجيب بسرعة لما تبدأ تتمرن صح من أول يوم.
>
> كل شي موضح بوضوح: → شو تسوي → كيف تسويه → ليش يشتغل لحرق الدهون + حماية العضل
>
> لا تخمين. لا لخبطة. لا جلسات ضايعة.
>
> أغلب الشباب يضيعون شهور يسوون الشي الغلط. انت ما بتسوي كذا.

**Кнопка-вопрос:** `❓ شو أحصل بعد الدفع؟`

---

#### Stage 6 — شو تحصل بعد الدفع + фото
- **Медиа:** фото (en_stage_6 — общее с EN)

**Текст:**
> بعد الدفع — وصول فوري. ✅
>
> تحصل على:
> ✅ هيكل التمرين الكامل — جلسة بجلسة
> ✅ التمارين: بار + دمبلز + وزن الجسم
> ✅ منطق التمرين لحرق الدهون + حماية العضل موضح بوضوح
> ✅ لا تحتاج أجهزة
> ✅ يشتغل في أي جيم — أبوظبي، لندن، مومباي، أي مكان
> ✅ دليل PDF — كيف تزيد الحمل تدريجياً
>
> هذي مو قائمة تمارين عشوائية. هذي طريقة مثبتة.
>
> لو عندك أي سؤال — كلمني مباشرة على تيليجرام. 💬
> 👉 @Ivan_Razmazin

**Кнопка-вопрос:** `❓ ليش بس 49 درهم؟`

---

#### Stage 7 — ليش السعر رخيص
**Текст:**
> لأني أبي كل شخص جاد يوصل لهالشي. ✅
>
> 49 درهم أقل من عشا برا. بس طريقة التمرين الغلط ممكن تكلفك شهور من التقدم الضايع — وعضل ما بيرجع بسهولة.
>
> انت مو تدفع على تمرين. انت تدفع على الطريقة اللي تخلي الكت فعلاً يشتغل.
>
> مرة وحدة. لا اشتراك. وصول فوري.
>
> 🔒 هالسعر موجود بس داخل هالشات. ترجع بعدين — يصير 99 درهم. هالعرض لك الحين.

**Кнопка-вопрос:** `❓ أبي مساعدة شخصية`

---

#### Stage 8 — الفرصة الأخيرة
**Текст:**
> انت تاكل صح. تروح الجيم. تبي تطلع ناشف وعضلي — مو بس أخف.
>
> بس كل أسبوع بدون طريقة التمرين الصح — تخسر عضل ما بيرجع بسهولة.
>
> شباب من أبوظبي لـ لندن لـ مومباي حلوا هالمشكلة بتمرين واحد. طريقة واحدة واضحة.
>
> 🔒 49 درهم — بس هنا، بس الحين. بعد هالشات — 99 درهم.
>
> لا تطلع بدونه.

**Кнопка-вопрос:** `❓ أبي تدريب شخصي`

---

### Стадии 9-10 — Upsell (после покупки)

#### Stage 9 — Upsell 1: فحص التكنيك (79 درهم)
- **Кнопки:** `[✅ فحص التكنيك — 79 درهم]` → `buy_now` | `[⬅️ لا شكراً، التمرين بس]` → `upsell_decline`

**Текст:**
> شي ثاني قبل ما تبدأ. 👊
>
> أغلب الشباب يخسرون 20-30% من نتائجهم بسبب أخطاء في الفورم ما يدرون عنها أصلاً.
>
> → أرسل لي 3-5 فيديوهات من تمارينك الأساسية
> → أراجع كل واحد شخصياً
> → تحصل على تصحيحات دقيقة — شو تعدل، كيف تعدله
>
> جلسة وحدة بفورم صح تبني عضل أكثر من أسابيع بتكرارات غلط.

---

#### Stage 10 — Upsell 2: تدريب شخصي 7 أيام (129 درهم)
- **Кнопки:** `[✅ تدريب 7 أيام — 129 درهم]` → `buy_now` | `[⬅️ لا شكراً، كذا تمام]` → `upsell_decline`

**Текст:**
> كيف كانت أول جلسة؟ 👊
>
> لو تبي تتقدم أسرع — وما تحل كل شي لحالك:
>
> **تدريب شخصي 7 أيام — 129 درهم** ✅
>
> → متابعة يومية معي شخصياً
> → التمرين معدل على جسمك وجدولك
> → تعديلات التغذية بناءً على تقدمك الفعلي
> → إجابات مباشرة على كل سؤال
>
> 7 أيام مع التوجيه الصح توصلك أبعد من أغلب الشباب اللي يتمرنون لحالهم بشهر.

---

## Техническая информация

### Файлы

| Файл | Описание |
|------|----------|
| `bot/src/i18n/ru.py` | Русские тексты |
| `bot/src/i18n/en.py` | Английские тексты |
| `bot/src/i18n/ar.py` | Арабские тексты |
| `bot/src/funnel/messages.py` | Маппинг стадий → сообщений |
| `bot/src/funnel/sender.py` | Batch-отправка (25 msg/batch, 1s delay) |
| `bot/src/db/queries.py` | Тайминги (`calculate_next_send_time()`) |
| `bot/src/handlers/callbacks.py` | Обработка кнопок |

### Callback data

| Callback | Действие |
|----------|---------|
| `buy_now` | Показать кнопку оплаты (Tribute/Ziina) |
| `video_workout` | Отправить ссылку на видео (RU stage 0) |
| `learn_workout` | Показать описание тренировки (RU stage 1) |
| `video_circle` | Отправить видео-кружочек (RU stage 3) |
| `en_funnel_q_{0-8}` | EN: мгновенный переход к следующей стадии |
| `ar_funnel_q_{0-8}` | AR: мгновенный переход к следующей стадии |
| `upsell_decline` | Отклонение upsell |

### Тестовые скрипты

```bash
# RU
./scripts/run.sh stage_0.py        # Отправить стадию 0
./scripts/run.sh reset.py          # Сброс на stage 0

# EN
./scripts_en/run.sh stage_0.py     # Отправить стадию 0
./scripts_en/run.sh reset.py       # Сброс на stage 0

# AR
./scripts_ar/run.sh stage_0.py     # Отправить стадию 0
./scripts_ar/run.sh reset.py       # Сброс на stage 0
```
