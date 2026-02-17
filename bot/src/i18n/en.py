"""English localization strings — extracted from n8n workflows."""

SUBSCRIBE_MESSAGE = "To use the bot, please subscribe to the channel: https://t.me/ivanfit_health"

ALREADY_CALCULATED = "Champion, I'm sorry. I cannot calculate your macros a second time."

CALCULATING_MENU = "Got it! Calculating your calories and selecting a menu from the database, please wait a few seconds..."

# --- Funnel Day messages (EN versions) ---
FUNNEL_DAY_0 = (
    'Hey! 🤍\n\n'
    'I want to say a huge thank you for your trust — I truly appreciate that you decided to take care of yourself.\n\n'
    '<b>Nutrition is the first and most important step.</b>\n'
    'But there is one thing almost nobody talks about…\n\n'
    'If your body is <i>"asleep"</i>,\n'
    'food is absorbed poorly,\n'
    'circulation is weak,\n'
    'muscles are turned off.\n\n'
    '<b>And then you get:</b>\n'
    '— swelling\n— lower belly\n— "love handles"\n— flabbiness\n— fatigue\n— heaviness in the body\n\n'
    "It's not laziness or weak willpower. <b>It's just a sleeping body.</b> So it's important to wake it up.\n\n"
    'I recorded a short workout\n'
    '<b>"Wake up your body in 7 minutes"</b> ✨\n\n'
    '<i>No jumping. No strain. No stress.</i>\n\n'
    'This is a gentle activation, after which:\n'
    '→ tension goes away\n→ energy appears\n→ your body starts working properly\n\n'
    '<b>Do it now — and feel the difference.</b>'
)
FUNNEL_DAY_0_BUTTON = "Wake up your body"

FUNNEL_DAY_1 = (
    '<b>Now your body is activated.</b>\n'
    'And in this state, workouts give results 2-3 times faster.\n\n'
    '<b>Nutrition + activation = foundation.</b>\n'
    'Then you can target problem areas:\n\n'
    '• Lower belly\n• Love handles\n• Flabby arms\n• Glute shaping\n• Posture\n\n'
    'I created a workout that targets all these areas in <b>20 minutes a day</b>. No jumping, no exhaustion.\n\n'
    'Girls feel first changes after <b>2-3 sessions</b>.\n\n'
    'While you are in the bot — you can get it at a discount:\n'
    '<s>$25</s> → <b>$15</b>'
)
FUNNEL_DAY_1_BUTTON = "Buy with discount"

FUNNEL_DAY_2 = (
    '<b>Social proof</b>\n\n'
    "You can't imagine how many messages I get after this workout 🙈\n\n"
    'Here are some typical ones:\n'
    '✨ "Swelling gone — legs became drier in three days"\n'
    '✨ "Belly got smaller, even though weight barely changed"\n'
    '✨ "Cellulite became softer and less visible"\n'
    '✨ "Heaviness in the body disappeared"\n\n'
    "This is <b>NOT magic</b> — it's proper work with lymph + muscles that nobody usually talks about.\n\n"
    'Want to try it too?'
)
FUNNEL_DAY_2_BUTTONS = [("Yes, I want results!", "buy_now"), ("Will it suit me?", "check_suitability")]

FUNNEL_DAY_3 = (
    '📅 <b>Pain → Solution</b>\n\n'
    "Let's be honest.\n"
    '90% of girls face the same problems:\n'
    '• puffy face and body\n• love handles\n• tense lower belly\n'
    '• flabby arms\n• poor posture\n• visible cellulite\n\n'
    'The reason is almost always the same:\n'
    '👉 poor lymph function\n👉 inactive deep muscles\n👉 weak posture\n\n'
    'My <b>20-minute workout</b> fixes all of this — gently and effectively.\n\n'
    'Want to start today?'
)
FUNNEL_DAY_3_BUTTONS = [("Yes!", "buy_now"), ("What's in the program?", "show_info")]

FUNNEL_DAY_4 = (
    '📅 <b>Price as a reason to buy</b>\n\n'
    'If I conducted this workout in person, it would cost $30-50.\n'
    'But I want every girl to be able to afford it.\n\n'
    'So in the bot it costs only <b>$15</b>.\n'
    "That's less than:\n• dinner out\n• a new mascara\n• one coffee shop visit\n• food delivery\n\n"
    'The effect is like 2-3 personal training sessions.\n'
    'And the best part — 20 minutes, at home, no equipment.\n\n'
    'Want to grab it at the "friends" price?'
)
FUNNEL_DAY_4_BUTTONS = [("I want a discount", "buy_now"), ("Not for me", "none")]

FUNNEL_DAY_5 = (
    '📅 <b>Day 5 — Soft Deadline</b>\n\n'
    "Today is the last day the workout is available for <b>$15</b>.\n\n"
    'After this, the price goes back.\n'
    'And yes… these small postponements are what most often prevent girls from getting their dream body.\n\n'
    'You can start your journey to:\n'
    '✔️ light legs\n✔️ a flatter belly\n✔️ reduced love handles\n'
    '✔️ better posture\n✔️ firmer glutes\n✔️ less cellulite\n\n'
    'in just 20 minutes a day.\n\n'
    'Ready to grab the workout?'
)
FUNNEL_DAY_5_BUTTONS = [("Yes, I'm in!", "buy_now"), ("Remind me later", "remind_later")]

# --- Callback responses ---
BUY_MESSAGE = (
    "💳 Great! Proceed to payment:\n\n"
    "👇 Press the button below to get the workout\n\n"
    "After payment, access will open automatically! ✅"
)
BUY_BUTTON = " 💳 Pay"

RESULTS_CAPTION = (
    "📌 exercises that hit the target. All problem areas, from love handles to flabby arms.\n\n"
    "📌 the most effective anti-swelling routine\n\n"
    "📌 understanding what cellulite is and how to get rid of it\n\n"
    "📌 your shoulders will finally OPEN UP, and you'll breathe freely\n\n"
    "📌 I'm open to HELP — you can ask me about exercise technique"
)

REMIND_LATER = (
    "You're already on the right path, you have a Nutrition Plan, and I believe you've already integrated it into your LIFE❤️\n"
    'I\'d be happy to see you in my <a href="https://t.me/ivanfit_health">telegram channel</a>, '
    "where you can perfect body beauty and strengthen health🙏"
)

NONE_RESPONSE = (
    "I know well what it's like to save on yourself and doubt whether it's even worth it. "
    "But every time I actually went for it, completed and absorbed the material, "
    "I was proud that I did it because I was able to gain benefit and become better.❤️\n\n"
    "You're already on the right path: you have a nutrition plan, and I believe you've already integrated it into your life.❤️\n\n"
    "And I think you understand that the super-combo is nutrition + workouts (activity). "
    "That's exactly why I created this complex targeting all problem areas.🙏\n\n"
    'I\'d be happy to see you in my <a href="https://t.me/ivanfit_health">telegram channel</a>, '
    "where you can perfect body beauty and strengthen health.🙏"
)

VIDEO_WORKOUT_RESPONSE = (
    "Now your body is activated 🤍\n"
    "And in this state, workouts give results 2-3 times faster.\n\n"
    "Nutrition + activation = foundation.\n"
    "Then you can target problem areas:\n\n"
    "— lower belly\n— love handles\n— flabby arms\n— glute shaping\n— posture\n\n"
    "I created a workout that targets these areas in 20 minutes a day.\n"
    "No jumping, no exhaustion.\n\n"
    "Girls feel first changes after 2-3 sessions 🫶\n\n"
    "While you're in the bot — you can get it at a discount\n"
    "$15 instead of $25."
)
