import os
import json
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode

TOKEN = '7661540890:AAET00pCElUB4gnbsjwlMWBwr6rBEXgv33o'
ADMIN_ID = 123456789  # <-- Укажи свой Telegram ID

DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

SECTIONS = {
    "helpers": "Хелперы",
    "cheats": "Чит-Скрипты",
    "bots": "Боты"
}

# FSM для добавления скрипта
class AddScript(StatesGroup):
    waiting_for_file = State()
    waiting_for_description = State()

# Инициализация
bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
router = Router()
dp.include_router(router)

def get_scripts(section):
    path = os.path.join(DATA_DIR, f"{section}.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_script(section, script):
    scripts = get_scripts(section)
    scripts.append(script)
    path = os.path.join(DATA_DIR, f"{section}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(scripts, f, ensure_ascii=False, indent=2)

# Главное меню
def main_menu():
    kb = [
        [InlineKeyboardButton(text="1️⃣ Хелперы", callback_data="section_helpers")],
        [InlineKeyboardButton(text="2️⃣ Чит-Скрипты", callback_data="section_cheats")],
        [InlineKeyboardButton(text="3️⃣ Боты", callback_data="section_bots")],
        [InlineKeyboardButton(text="4️⃣ Телеграм чат Arizona Mobile LUA", url="https://t.me/YOUR_CHAT_LINK")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Меню раздела
def section_menu(section, is_admin=False):
    kb = [[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]]
    if is_admin:
        kb.insert(0, [InlineKeyboardButton(text="➕ Добавить скрипт", callback_data=f"add_{section}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Список скриптов
def scripts_keyboard(section):
    scripts = get_scripts(section)
    kb = []
    for idx, script in enumerate(scripts):
        kb.append([InlineKeyboardButton(text=f"{idx+1}. {script['name']}", callback_data=f"show_{section}_{idx}")])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Запуск
@router.message(CommandStart())
async def start_handler(msg: Message):
    text = "<b>Arizona Mobile LUA Bot</b>\n\nВыдача скриптов (.lua) для Аризоны Мобайл.\n\nВыберите раздел:"
    await msg.answer(text, reply_markup=main_menu())

@router.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery):
    await call.message.edit_text(
        "<b>Arizona Mobile LUA Bot</b>\n\nВыдача скриптов (.lua) для Аризоны Мобайл.\n\nВыберите раздел:",
        reply_markup=main_menu()
    )

@router.callback_query(F.data.startswith("section_"))
async def section_handler(call: CallbackQuery):
    section = call.data.split("_")[1]
    is_admin = call.from_user.id == ADMIN_ID
    text = f"<b>{SECTIONS[section]}</b>\n"
    scripts = get_scripts(section)
    if scripts:
        text += "Список доступных скриптов:"
        await call.message.edit_text(
            text,
            reply_markup=scripts_keyboard(section)
        )
    else:
        text += "\nПока скриптов нет."
        await call.message.edit_text(
            text,
            reply_markup=section_menu(section, is_admin)
        )

@router.callback_query(F.data.startswith("show_"))
async def show_script(call: CallbackQuery):
    _, section, idx = call.data.split("_")
    idx = int(idx)
    scripts = get_scripts(section)
    script = scripts[idx]
    file_path = script['file_path']
    description = script['description']
    name = script['name']
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬇️ Скачать", callback_data=f"download_{section}_{idx}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"section_{section}")]
        ]
    )
    text = f"<b>{name}</b>\n\n{description}"
    await call.message.edit_text(text, reply_markup=kb)

@router.callback_query(F.data.startswith("download_"))
async def download_script(call: CallbackQuery):
    _, section, idx = call.data.split("_")
    idx = int(idx)
    scripts = get_scripts(section)
    script = scripts[idx]
    file_path = script['file_path']
    name = script['name']
    file = FSInputFile(file_path, filename=name)
    await call.message.answer_document(file, caption=f"{name}")
    await call.answer("Скрипт отправлен!")

# ===== Админ: Добавление скрипта =====
@router.callback_query(F.data.startswith("add_"))
async def add_script_start(call: CallbackQuery, state: FSMContext):
    section = call.data.split("_")[1]
    if call.from_user.id != ADMIN_ID:
        await call.answer("Нет доступа", show_alert=True)
        return
    await state.update_data(section=section)
    await state.set_state(AddScript.waiting_for_file)
    await call.message.answer("Отправьте .lua файл для добавления:")

@router.message(AddScript.waiting_for_file)
async def add_script_file(msg: Message, state: FSMContext):
    if not msg.document or not msg.document.file_name.endswith('.lua'):
        await msg.answer("Пожалуйста, отправьте .lua файл.")
        return
    data = await state.get_data()
    section = data['section']
    file_id = msg.document.file_id
    file_name = msg.document.file_name
    save_dir = os.path.join(DATA_DIR, section)
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, file_name)
    await msg.document.download(destination=file_path)
    await state.update_data(file_path=file_path, file_name=file_name)
    await state.set_state(AddScript.waiting_for_description)
    await msg.answer("Теперь отправьте описание для этого скрипта:")

@router.message(AddScript.waiting_for_description)
async def add_script_description(msg: Message, state: FSMContext):
    description = msg.text
    data = await state.get_data()
    section = data['section']
    file_path = data['file_path']
    file_name = data['file_name']
    script = {
        "name": file_name,
        "file_path": file_path,
        "description": description
    }
    save_script(section, script)
    await msg.answer(f"Скрипт <b>{file_name}</b> добавлен в раздел <b>{SECTIONS[section]}</b>.")
    await state.clear()

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
