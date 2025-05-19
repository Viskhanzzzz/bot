import json
import os
import random
import time
import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# === Настройки ===
TOKEN = "7610376495:AAFud9TUXvyQZxZ6KgSMM5fEFEidjKQHwYg"
CREATOR_ID = 7667043683  # Замени на свой Telegram ID
DATA_FILE = "users.json"
PROMO_FILE = "promocodes.json"
CARDS_FILE = "cards.json"
DAILY_CODE_FILE = "dailycode.json"

# === Глобальные переменные ===
users = {}
cards = {}
daily_code = {}

# === Шансы выпадения карт ===
RARITY_CHANCES = [
    ("Limited", 0.02),
    ("Мифическая", 0.1),
    ("Легендарная", 1),
    ("Эпическая", 2),
    ("Редкая", 10),
    ("Обычная", 86.88),
]

# === Шансы победы по редкости ===
RARITY_WIN_CHANCE = {
    "Limited": 99,
    "Мифическая": 85,
    "Легендарная": 70,
    "Эпическая": 40,
    "Редкая": 20,
    "Обычная": 10,
}

# === Загрузка / сохранение данных ===
def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_all():
    global users, cards, daily_code
    users = load_json(DATA_FILE)
    cards = load_json(CARDS_FILE)
    daily_code = load_json(DAILY_CODE_FILE)

def save_all():
    save_json(DATA_FILE, users)
    save_json(CARDS_FILE, cards)
    save_json(DAILY_CODE_FILE, daily_code)

# === Генерация уникального ID ===
def generate_unique_id():
    while True:
        code = str(random.randint(100000, 999999))
        if code not in [u.get("unique_id") for u in users.values()]:
            return code

# === Инициализация пользователя ===
def ensure_user(uid):
    uid = str(uid)
    if uid not in users:
        users[uid] = {
            "unique_id": generate_unique_id(),
            "balance": 0,
            "spins": [],
            "inventory": [],
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "pvp_selected": None,
            "pvp_opponent": None,
            "used_today": {},  # id карты: количество
            "username": "",
        }

# === Команда /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)

    if users[uid].get("registered"):
        await update.message.reply_text(
            "Вы уже зарегистрированы.\n"
            "Напишите /myid, чтобы узнать свой уникальный PvP-код."
        )
        return

    users[uid]["registered"] = True
    users[uid]["username"] = update.effective_user.username or update.effective_user.full_name
    save_all()

    await update.message.reply_text(
        f"Добро пожаловать в карточного PvP-бота!\n"
        f"Твой уникальный ID: {users[uid]['unique_id']}\n"
        f"Передай его друзьям, чтобы они могли вызвать тебя на дуэль.\n"
        f"Напиши /profile чтобы посмотреть свой профиль."
    )

# === Команда /myid ===
async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)
    await update.message.reply_text(f"Твой уникальный ID: {users[uid]['unique_id']}")

# === Команда /profile ===
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)
    user = users[uid]

    total_value = sum([cards.get(c['id'], {}).get("price", 0) for c in user["inventory"]])
    rarity_count = {}

    for c in user["inventory"]:
        r = cards.get(c["id"], {}).get("rarity", "Обычная")
        rarity_count[r] = rarity_count.get(r, 0) + 1

    text = (
        f"👤 Профиль игрока\n"
        f"Уникальный ID: {user['unique_id']}\n"
        f"Баланс Рё: {user['balance']}\n"
        f"Побед: {user['wins']}\n"
        f"Поражений: {user['losses']}\n"
        f"Ничьи: {user['draws']}\n"
        f"Стоимость коллекции: {total_value} Рё\n"
        f"Всего карт: {len(user['inventory'])}\n\n"
    )
    text += "Карты по редкости:\n"
    for r, count in rarity_count.items():
        text += f" - {r}: {count}\n"

    buttons = [[InlineKeyboardButton("📖 Просмотреть все карты", callback_data="view_all_cards")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# === Карточки по шаблону (4 примера) ===
def init_card_templates():
    global cards
    if cards:
        return
    cards = {
        "c1": {
            "name": "Греф",
            "rarity": "Мифическая",
            "price": 100,
            "image": "gref.jpeg"
        },
        "c5": {
            "name": "Cselx",
            "rarity": "Легендарная",
            "price": 75,
            "image": "cselx.jpeg"
        },
        "c6": {
            "name": "Висхан",
            "rarity": "Мифическая",
            "price": 150,
            "image": "vvvv.jpeg"
        },
        "c7": {
            "name": "Boob",
            "rarity": "Легендарная",
            "price": 75,
            "image": "boob.jpeg"
        },
        "c8": {
            "name": "Акфлуп",
            "rarity": "Легендарная",
            "price": 75,
            "image": "akflyp.jpeg"
        },
        "c9": {
            "name": "Фейси",
            "rarity": "Легендарная",
            "price": 75,
            "image": "imran.jpeg"
        },
        "c10": {
            "name": "Ильдар",
            "rarity": "Легендарная",
            "price": 75,
            "image": "ildar.jpeg"
        },
        "c11": {
            "name": "Клекс",
            "rarity": "Обычная",
            "price": 2,
            "image": "cselx2.png"
        },
        "c12": {
            "name": "Катана",
            "rarity": "Обычная",
            "price": 2,
            "image": "serafim2.jpeg"
        },
        "c13": {
            "name": "Масрур",
            "rarity": "Легендарная",
            "price": 75,
            "image": "masrur.jpeg"
        },
        "c14": {
            "name": "Акфлуп2",
            "rarity": "Обычная",
            "price": 1,
            "image": "akfyp2.jpeg"
        },
        "c2": {
            "name": "Лилит",
            "rarity": "Limited",
            "price": 500,
            "image": "lilith.jpeg"
        },
        "c3": {
            "name": "Серафим",
            "rarity": "Мифическая",
            "price": 100,
            "image": "serafim.jpeg"
        },
        "c4": {
            "name": "Админ Прошмандовок",
            "rarity": "Limited",
            "price": 1000,
            "image": "adminp.jpeg"
        },
        
    }
    save_json(CARDS_FILE, cards)

# === Команда /spin ===
async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)
    user = users[uid]
    now = time.time()

    # Проверка задержки 5 часов
    recent_spins = [s for s in user["spins"] if now - s < 5 * 3600]
    if recent_spins:
        remain = int(5 * 3600 - (now - recent_spins[-1])) // 60
        await update.message.reply_text(f"Следующий спин доступен через {remain} минут.")
        return

    # Выбор случайной карты по шансам
    roll = random.uniform(0, 100)
    acc = 0
    chosen_card_id = "c4"  # По умолчанию
    for cid, card in cards.items():
        rarity = card["rarity"]
        for r, chance in RARITY_CHANCES:
            if rarity == r:
                acc += chance
                if roll <= acc:
                    chosen_card_id = cid
                break

    card = cards[chosen_card_id]
    user["inventory"].append({"id": chosen_card_id})
    user["spins"].append(now)
    save_all()

    await update.message.reply_photo(
        photo=open(card["image"], "rb") if os.path.exists(card["image"]) else None,
        caption=(
            f"Ты получил карту!\n\n"
            f"Имя: {card['name']}\n"
            f"Редкость: {card['rarity']}\n"
            f"Стоимость: {card['price']} Рё"
        )
    )

async def spingive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != CREATOR_ID:
        await update.message.reply_text("У тебя нет прав на эту команду.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Используй: /spingive <кол-во> <uid>")
        return

    try:
        amount = int(context.args[0])
        target_uid = context.args[1]

        if target_uid in user_data:
            user_data[target_uid]['spins'] += amount
            save_data()
            await update.message.reply_text(f"Выдано {amount} спинов игроку с ID {target_uid}.")
        else:
            await update.message.reply_text("Игрок с таким ID не найден.")
    except:
        await update.message.reply_text("Ошибка. Проверь ввод.")

# === /dublicate — продажа дубликатов за Рё ===
async def dublicate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)
    user = users[uid]

    rarity_list = ["Limited", "Мифическая", "Легендарная", "Эпическая", "Редкая", "Обычная"]
    buttons = [[InlineKeyboardButton(r, callback_data=f"dup_{r}")] for r in rarity_list]
    await update.message.reply_text("Выбери редкость для обмена дубликатов:", reply_markup=InlineKeyboardMarkup(buttons))

async def handle_duplicate_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    rarity = query.data.split("_")[1]
    ensure_user(uid)

    cards_of_rarity = [c for c in users[uid]["inventory"] if cards.get(c["id"], {}).get("rarity") == rarity]
    counted = {}
    for c in cards_of_rarity:
        counted[c["id"]] = counted.get(c["id"], 0) + 1

    options = []
    for cid, count in counted.items():
        if count > 1:
            card = cards[cid]
            options.append([
                InlineKeyboardButton(f"{card['name']} ({count})", callback_data=f"sell_{cid}"),
                InlineKeyboardButton("💰 Все", callback_data=f"sellall_{cid}")
            ])
    if not options:
        await query.edit_message_text("Нет дубликатов выбранной редкости.")
    else:
        await query.edit_message_text("Выбери карту для продажи:", reply_markup=InlineKeyboardMarkup(options))

async def handle_sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    ensure_user(uid)

    data = query.data
    cid = data.split("_")[1]
    user = users[uid]
    card_price = cards[cid]["price"]

    if data.startswith("sellall_"):
        count = sum(1 for c in user["inventory"] if c["id"] == cid)
        sold = count - 1
        user["inventory"] = [c for c in user["inventory"] if c["id"] != cid] + [{"id": cid}]
        user["balance"] += sold * card_price
        await query.edit_message_text(f"Продано {sold} дубликатов по {card_price} Рё = {sold * card_price}")
    elif data.startswith("sell_"):
        inv = [i for i, c in enumerate(user["inventory"]) if c["id"] == cid]
        if len(inv) < 2:
            await query.edit_message_text("У тебя только 1 такая карта.")
            return
        user["inventory"].pop(inv[0])
        user["balance"] += card_price
        await query.edit_message_text(f"Продано 1 дубликат за {card_price} Рё")

    save_all()

# === /inventory — листание карт ===
async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)

    inv = users[uid]["inventory"]
    if not inv:
        await update.message.reply_text("Инвентарь пуст.")
        return
    context.user_data["inv_index"] = 0
    await show_card(update, context, uid, 0)

async def show_card(update, context, uid, index):
    inv = users[uid]["inventory"]
    card_id = inv[index]["id"]
    card = cards[card_id]
    text = (
        f"Имя: {card['name']}\n"
        f"Редкость: {card['rarity']}\n"
        f"Стоимость: {card['price']} Рё"
    )
    buttons = []
    if index > 0:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"card_{index - 1}"))
    if index < len(inv) - 1:
        buttons.append(InlineKeyboardButton("➡️ Далее", callback_data=f"card_{index + 1}"))

    media = InputMediaPhoto(open(card["image"], "rb")) if os.path.exists(card["image"]) else None

    if update.callback_query:
        await update.callback_query.edit_message_media(media, reply_markup=InlineKeyboardMarkup([buttons]) if buttons else None)
        await update.callback_query.edit_message_caption(caption=text)
    else:
        await update.message.reply_photo(photo=open(card["image"], "rb") if os.path.exists(card["image"]) else None,
                                         caption=text,
                                         reply_markup=InlineKeyboardMarkup([buttons]) if buttons else None)

async def handle_card_scroll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    index = int(query.data.split("_")[1])
    await show_card(update, context, uid, index)

# === /promocode — ввод пользователем ===
async def promocode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)
    await update.message.reply_text("Введите промокод:")
    context.user_data["awaiting_promo"] = True

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)

    if context.user_data.get("awaiting_promo"):
        code = update.message.text.strip()
        promos = load_json(PROMO_FILE)

        if code in promos:
            amount = promos[code]["amount"]
            users[uid]["balance"] += amount
            del promos[code]
            save_json(PROMO_FILE, promos)
            save_all()
            await update.message.reply_text(f"Промокод применён! +{amount} Рё")
        elif code == daily_code.get("code"):
            if uid in daily_code.get("used", []):
                await update.message.reply_text("Ты уже использовал суточный промокод.")
            else:
                users[uid]["balance"] += daily_code["amount"]
                daily_code.setdefault("used", []).append(uid)
                save_all()
                await update.message.reply_text(f"Суточный промокод активирован! +{daily_code['amount']} Рё")
        else:
            await update.message.reply_text("Неверный промокод.")
        context.user_data["awaiting_promo"] = False

# === /code — только для админа ===
async def admin_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if uid != str(ADMIN_ID):
        return await update.message.reply_text("Недостаточно прав.")
    args = context.args
    if len(args) == 0:
        promos = load_json(PROMO_FILE)
        text = "📜 Активные промокоды:\n"
        for code, data in promos.items():
            text += f"{code} — {data['amount']} Рё\n"
        await update.message.reply_text(text or "Нет активных промокодов.")
    elif len(args) == 2:
        code = args[0]
        target_uid = args[1]
        promos = load_json(PROMO_FILE)
        promos[code] = {"amount": random.choice([10, 30, 50])}
        save_json(PROMO_FILE, promos)
        await update.message.reply_text(f"Промокод {code} создан для {target_uid}.")
    else:
        await update.message.reply_text("Формат: /code <код> <уникальный ID игрока>")

# === Обновление ежедневного кода ===
def update_daily_code():
    global daily_code
    now = datetime.datetime.now()
    if "expires" not in daily_code or datetime.datetime.fromisoformat(daily_code["expires"]) < now:
        daily_code = {
            "code": f"DAY{random.randint(100, 999)}",
            "amount": 50,
            "used": [],
            "expires": (now + datetime.timedelta(days=1)).isoformat()
        }
        save_json(DAILY_CODE_FILE, daily_code)

# === /shop — покупка Рё или спинов ===
async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("Купить спин (10 Рё)", callback_data="buy_spin")],
        [InlineKeyboardButton("Купить Рё (через DonationAlerts)", url="https://www.donationalerts.com/r/viskhanzzzz")]
    ]
    await update.message.reply_text("Магазин", reply_markup=InlineKeyboardMarkup(buttons))

async def handle_shop_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    ensure_user(uid)

    if query.data == "buy_spin":
        if users[uid]["balance"] < 10:
            await query.edit_message_text("Недостаточно Рё.")
        else:
            users[uid]["balance"] -= 10
            users[uid]["spins"].append(0)  # Позволяет сразу крутить
            save_all()
            await query.edit_message_text("Ты купил дополнительный спин. Используй /spin.")

# === /pvp — отправка вызова ===
async def pvp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)

    if update.message.reply_to_message:
        target_id = str(update.message.reply_to_message.from_user.id)
    elif context.args:
        target_code = context.args[0]
        target_id = next((k for k, v in users.items() if v["unique_id"] == target_code), None)
    else:
        return await update.message.reply_text("Используй /pvp <код игрока> или ответом на его сообщение.")

    if not target_id or target_id == uid or target_id not in users:
        return await update.message.reply_text("Игрок не найден.")

    users[uid]["pvp_opponent"] = target_id
    users[target_id]["pvp_opponent"] = uid
    save_all()
    await update.message.reply_text("Вызов отправлен. Ждём, пока соперник примет сражение.")
    await context.bot.send_message(chat_id=target_id, text="Тебе кинули вызов! Напиши /accept, чтобы принять.")

# === /accept — принятие вызова ===
async def accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(uid)
    opponent = users[uid].get("pvp_opponent")

    if not opponent:
        return await update.message.reply_text("Нет активных вызовов.")
    
    await update.message.reply_text("Выберите карту для битвы:")
    await show_card_choice(update, context, uid)

async def show_card_choice(update, context, uid):
    buttons = []
    inv = users[uid]["inventory"]
    for i, c in enumerate(inv):
        cid = c["id"]
        name = cards[cid]["name"]
        rarity = cards[cid]["rarity"]
        use_count = users[uid]["used_today"].get(cid, 0)
        if use_count >= 5:
            continue
        buttons.append([InlineKeyboardButton(f"{name} ({rarity})", callback_data=f"choose_{i}")])
    if not buttons:
        return await update.message.reply_text("Нет доступных карт. Все использованы сегодня.")
    await update.message.reply_text("Выберите карту:", reply_markup=InlineKeyboardMarkup(buttons))

async def choose_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    index = int(query.data.split("_")[1])
    card = users[uid]["inventory"][index]
    cid = card["id"]

    if users[uid]["used_today"].get(cid, 0) >= 5:
        await query.answer("Эта карта уже использовалась 5 раз сегодня.", show_alert=True)
        return

    users[uid]["pvp_selected"] = card
    users[uid]["used_today"][cid] = users[uid]["used_today"].get(cid, 0) + 1
    await query.edit_message_text(f"Вы выбрали карту: {cards[cid]['name']}")

    opp = users[uid]["pvp_opponent"]
    if users.get(opp, {}).get("pvp_selected"):
        await resolve_battle(uid, opp, context, update.effective_chat.id)

async def resolve_battle(uid1, uid2, context, chat_id):
    u1 = users[uid1]
    u2 = users[uid2]
    c1 = cards[u1["pvp_selected"]["id"]]
    c2 = cards[u2["pvp_selected"]["id"]]

    r1, r2 = RARITY_WIN_CHANCE[c1["rarity"]], RARITY_WIN_CHANCE[c2["rarity"]]
    chance = 50 + (r1 - r2) // 2
    draw_chance = 5

    roll = random.randint(1, 100)
    if roll <= draw_chance:
        result = "⚔️ Бой завершился ничьей!"
        u1["draws"] += 1
        u2["draws"] += 1
    elif roll <= chance:
        winner, loser = uid1, uid2
    else:
        winner, loser = uid2, uid1

    if roll > draw_chance:
        users[winner]["wins"] += 1
        users[loser]["losses"] += 1
        # Победитель получает карту соперника
        users[winner]["inventory"].append(users[loser]["pvp_selected"])
        users[loser]["inventory"].remove(users[loser]["pvp_selected"])
        result = f"🏆 Победил: @{users[winner]['username']} и забрал карту!"

    u1["pvp_selected"] = None
    u2["pvp_selected"] = None
    u1["pvp_opponent"] = None
    u2["pvp_opponent"] = None
    save_all()

    await context.bot.send_message(chat_id=chat_id, text=f"Победил: {winner}\nПроиграл: {loser}")
    await resolve_pvp(user_id, opp_id, context, update.effective_chat.id)

# === Топ по победам /topf и стоимости /topc ===
async def topf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = sorted(users.items(), key=lambda x: x[1]["wins"], reverse=True)[:10]
    text = "🏆 Топ игроков по победам:\n"
    for i, (uid, u) in enumerate(top, 1):
        text += f"{i}. @{u['username']} — {u['wins']} побед\n"
    await update.message.reply_text(text)

async def topc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    def calc_value(u): return sum(cards.get(c["id"], {}).get("price", 0) for c in u["inventory"])
    top = sorted(users.items(), key=lambda x: calc_value(x[1]), reverse=True)[:10]
    text = "💰 Топ по стоимости коллекции:\n"
    for i, (uid, u) in enumerate(top, 1):
        text += f"{i}. @{u['username']} — {calc_value(u)} Рё\n"
    await update.message.reply_text(text)

# === Ежедневный сброс ===
def reset_daily_usage():
    for u in users.values():
        u["used_today"] = {}
        u["daily_claimed"] = False
    save_all()

# === Запуск бота ===
def main():
    load_all()
    update_daily_code()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("spin", spin))
    app.add_handler(CommandHandler("inventory", inventory))
    app.add_handler(CommandHandler("dublicate", dublicate))
    app.add_handler(CommandHandler("promocode", promocode))
    app.add_handler(CommandHandler("code", admin_code))
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("topf", topf))
    app.add_handler(CommandHandler("topc", topc))
    app.add_handler(CommandHandler("pvp", pvp))
    app.add_handler(CommandHandler("accept", accept))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_duplicate_menu, pattern="^dup_"))
    app.add_handler(CallbackQueryHandler(handle_sell, pattern="^sell"))
    app.add_handler(CallbackQueryHandler(handle_card_scroll, pattern="^card_"))
    app.add_handler(CallbackQueryHandler(choose_card, pattern="^choose_"))
    app.add_handler(CallbackQueryHandler(handle_shop_buttons, pattern="^buy_"))
    app.add_handler(CommandHandler("spingive", spingive))

    app.run_polling()

if __name__ == "__main__":
    main()            
