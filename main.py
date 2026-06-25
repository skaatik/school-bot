import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command

# ----------------- НАСТРОЙКИ (ВСТАВЬ СВОИ ДАННЫЕ) -----------------
BOT_TOKEN = "8641012155:AAFNRSYel-4zOvIYXwRJCNyAsmCCysr5qfc"
OWNER_ID = 838524500  
# -----------------------------------------------------------------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect("school_v2.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS grades (id INTEGER PRIMARY KEY AUTOINCREMENT, nickname TEXT UNIQUE, grades_list TEXT DEFAULT '')")
    cursor.execute("CREATE TABLE IF NOT EXISTS teachers (tg_id INTEGER PRIMARY KEY)")
    cursor.execute("CREATE TABLE IF NOT EXISTS parents (parent_id INTEGER PRIMARY KEY, child_nickname TEXT)")
    conn.commit()
    conn.close()

def is_teacher(user_id):
    if user_id == OWNER_ID: return True
    conn = sqlite3.connect("school_v2.db")
    cursor = conn.cursor()
    cursor.execute("SELECT tg_id FROM teachers WHERE tg_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_main_keyboard(user_id):
    buttons = [
        [InlineKeyboardButton(text="📓 Мой дневник", callback_query_data="view_my_grades")],
        [InlineKeyboardButton(text="👨‍👩‍👦 Кабинет Родителя", callback_query_data="parent_menu")]
    ]
    if is_teacher(user_id):
        buttons.append([InlineKeyboardButton(text="👨‍🏫 Панель Учителя", callback_query_data="teacher_menu")])
    if user_id == OWNER_ID:
        buttons.append([InlineKeyboardButton(text="👑 Управление (Админ)", callback_query_data="admin_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = (
        "🏫 **Добро пожаловать в Электронный Дневник Школы!**\n\n"
        "Используй кнопки ниже для управления и просмотра оценок."
    )
    if message.from_user.id == OWNER_ID:
        welcome_text += "\n\n👑 **Вы зашли как Главный Админ бота!**"
        
    await message.answer(welcome_text, reply_markup=get_main_keyboard(message.from_user.id))

@dp.callback_query(F.data == "view_my_grades")
async def process_view_my_grades(callback: CallbackQuery):
    await callback.message.answer("📝 Отправь в чат свой игровой ник, чтобы я нашёл твои оценки.")
    await callback.answer()

@dp.callback_query(F.data == "parent_menu")
async def process_parent_menu(callback: CallbackQuery):
    parent_id = callback.from_user.id
    conn = sqlite3.connect("school_v2.db")
    cursor = conn.cursor()
    cursor.execute("SELECT child_nickname FROM parents WHERE parent_id = ?", (parent_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Проверить оценки ребёнка", callback_query_data="check_child")],
            [InlineKeyboardButton(text="🔄 Изменить ник ребёнка", callback_query_data="link_child")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_query_data="back_main")]
        ])
        await callback.message.edit_text(f"👨‍👩‍👦 **Кабинет родителя**\nПривязанный ученик: `{result}`", reply_markup=kb)
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Привязать ник ребёнка", callback_query_data="link_child")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_query_data="back_main")]
        ])
        await callback.message.edit_text("👨‍👩‍👦 **Кабинет родителя**\nВы ещё не привязали ни одного ученика.", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data == "link_child")
async def process_link_child(callback: CallbackQuery):
    await callback.message.answer("⌨️ Напиши в чат команду: `/parent Ник_Ребёнка` (например: `/parent Ivan_Ivanov`) ")
    await callback.answer()

@dp.callback_query(F.data == "check_child")
async def process_check_child(callback: CallbackQuery):
    parent_id = callback.from_user.id
    conn = sqlite3.connect("school_v2.db")
    cursor = conn.cursor()
    cursor.execute("SELECT child_nickname FROM parents WHERE parent_id = ?", (parent_id,))
    res = cursor.fetchone()
    if res:
        cursor.execute("SELECT grades_list FROM grades WHERE nickname = ?", (res,))
        grades = cursor.fetchone()
        grades_str = grades if (grades and grades) else "Оценок пока нет"
        await callback.message.answer(f"📋 **Дневник ученика {res}:**\n🏅 Оценки: {grades_str}")
    conn.close()
    await callback.answer()

@dp.callback_query(F.data == "teacher_menu")
async def process_teacher_menu(callback: CallbackQuery):
    if not is_teacher(callback.from_user.id):
        await callback.answer("❌ У тебя нет прав учителя!", show_alert=True)
        return
    await callback.message.answer("✍️ Чтобы поставить оценку, напиши в чат команду:\n`/set Ник Оценка` (например: `/set Ivan_Ivanov 5`) ")
    await callback.answer()

@dp.callback_query(F.data == "admin_menu")
async def process_admin_menu(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("❌ Доступно только Админу бота!", show_alert=True)
        return
    await callback.message.answer("👑 **Панель Админа**\nЧтобы выдать права новому учителю, напиши:\n`/add_teacher ID_Телеграма` ")
    await callback.answer()

@dp.callback_query(F.data == "back_main")
async def process_back_main(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏫 **Добро пожаловать в Электронный Дневник Школы!**\n\nИспользуй кнопки ниже для управления и просмотра оценок.",
        reply_markup=get_main_keyboard(callback.from_user.id)
    )
    await callback.answer()

@dp.message(Command("add_teacher"))
async def cmd_add_teacher(message: Message):
    if message.from_user.id != OWNER_ID: return
    args = message.text.split()
    if len(args) < 2 or not args.isdigit():
        await message.answer("⚠️ Ошибка. Пиши: `/add_teacher ID_Учителя`")
        return
    teacher_id = int(args)
    conn = sqlite3.connect("school_v2.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO teachers (tg_id) VALUES (?)", (teacher_id,))
        conn.commit()
        await message.answer(f"✅ ID `{teacher_id}` успешно добавлен в список Учителей!")
    except sqlite3.IntegrityError:
        await message.answer("⚠️ Этот ID уже в списке учителей.")
    finally: conn.close()

@dp.message(Command("set"))
async def set_grade(message: Message):
    if not is_teacher(message.from_user.id): return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("⚠️ Пиши правильно: `/set Ник Оценка`")
        return
    nickname, grade = args, args
    conn = sqlite3.connect("school_v2.db")
    cursor = conn.cursor()
    cursor.execute("SELECT grades_list FROM grades WHERE nickname = ?", (nickname,))
    result = cursor.fetchone()
    if result:
        current_grades = result
        new_grades = f"{current_grades}, {grade}" if current_grades else grade
        cursor.execute("UPDATE grades SET grades_list = ? WHERE nickname = ?", (new_grades, nickname))
    else:
        cursor.execute("INSERT INTO grades (nickname, grades_list) VALUES (?, ?)", (nickname, grade))
    conn.commit()
    conn.close()
    await message.answer(f"✅ Ученику **{nickname}** поставлена оценка **{grade}**!")

@dp.message(Command("parent"))
async def cmd_parent(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Пиши: `/parent Ник`")
        return
    child_nickname = args
    conn = sqlite3.connect("school_v2.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO parents (parent_id, child_nickname) VALUES (?, ?)", (message.from_user.id, child_nickname))
    conn.commit()
    conn.close()
    await message.answer(f"✅ Ученик **{child_nickname}** привязан к родительскому кабинету!")

@dp.message(F.text)
async def view_grades(message: Message):
    nickname = message.text.strip()
    if nickname.startswith("/"): return
    conn = sqlite3.connect("school_v2.db")
    cursor = conn.cursor()
    cursor.execute("SELECT grades_list FROM grades WHERE nickname = ?", (nickname,))
    result = cursor.fetchone()
    conn.close()
    if result and result:
        await message.answer(f"📋 **Оценки ученика {nickname}:**\n🏅 {result}")
    else:
        await message.answer(f"🔍 Ник **{nickname}** не найден или оценок нет.")

async def main():
    init_db()
    print("🚀 Кнопочный бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())