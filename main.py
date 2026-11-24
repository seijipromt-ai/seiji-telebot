import os
import json
import logging
import asyncio
import threading
import tempfile
import shutil
import random
import re
import requests
import emoji
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from flask import Flask
from telegram import Update, MessageEntity
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError

# --- DUMMY FLASK WEB SERVER (Para hindi patayin ni Render) ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is alive and running 24/7!", 200

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port, use_reloader=False)

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8829077203:AAGk5Xj_zMwKsxefc4mkttwhcWQa1V0U")
OWNER_ID = int(os.environ.get("OWNER_ID", 6907359862))
DATA_FILE = "bot_data.json"
LOG_FILE = "bot.log"
DAILY_LIKE_TIME = "05:00"
IST = ZoneInfo("Asia/Dhaka")

# --- PREMIUM EMOJI CONFIGURATION ---
CUSTOM_EMOJIS = {
    "welcome": ("⭐", "6336646834139700626"), "success": ("✅", "6336861449360514102"),
    "error": ("❌", "6337033209397649451"), "broadcast": ("📢", "6336698133229082903"),
    "status": ("📊", "6336674562448563935"), "bot_active": ("🚀", "6336674562448563935"),
    "like": ("❤️", "6336861449360514102"), "user": ("👤", "6336674562448563935"),
    "uid": ("🔢", "6336646834139700626"), "region": ("🌍", "6336674562448563935"),
    "level": ("📊", "6336674562448563935"), "time": ("⏰", "6336674562448563935"),
    "days": ("📅", "6336674562448563935"), "pause": ("⏸️", "6336674562448563935"),
    "active": ("✅", "6336861449360514102"), "help": ("🤖", "6336674562448563935"),
    "stats": ("📊", "6336674562448563935"), "admin": ("👑", "6336674562448563935"),
    "group": ("🏢", "6336674562448563935"), "api": ("📈", "6336674562448563935"),
    "info": ("ℹ️", "6336674562448563935"), "warning": ("⚠️", "6336674562448563935"),
    "star": ("🌟", "6336646834139700626"), "fire": ("🔥", "6336674562448563935"),
    "settings": ("⚙️", "6336674562448563935"), "backup": ("📦", "6336674562448563935"),
    "restore": ("♻️", "6336674562448563935"), "test": ("🔍", "6336674562448563935"),
    "run": ("▶️", "6336674562448563935"), "id": ("🆔", "6336674562448563935"),
    "name": ("📋", "6336674562448563935"), "command": ("⚡", "6336674562448563935"),
    "example": ("📝", "6336674562448563935"), "result": ("🎯", "6336674562448563935"),
    "date": ("📆", "6336674562448563935"), "total": ("🔢", "6336674562448563935"),
    "failed": ("❌", "6337033209397649451"), "sent": ("✅", "6336861449360514102"),
    "processing": ("⏳", "6336674562448563935"), "completed": ("✅", "6336861449360514102"),
    "active_groups": ("🏢", "6336674562448563935"), "users_count": ("👥", "6336674562448563935"),
}

PREMIUM_EMOJIS = [
    "6100639476441161711", "6102462664288509137", "6100199534351097095",
    "6102926404792360795", "6100409966273764915", "6100430105375415737",
    "6102470558438400435", "6100451820730064687", "6102638599033858630",
    "6100179369479642954", "6100485115316542792", "6102661242101440205",
    "6102592514034770678", "6102475626499808862", "6102863908723236868",
    "6102510630483271620", "6282589525348720171", "6055377380204092112",
    "6055551219005398825", "6055181976371994390", "6055481009175010794",
    "6055484548228062462", "6055202102588742236", "6055450347403484860",
    "6055228576767155521", "6055183995006623379", "6337009415278828759",
    "6336756235546663929", "6334772471757020134", "6336732269629153634",
    "6336833407519038409", "6337048276142924106", "6337018975876030803",
    "6336608132189395373", "6336797785060286399", "6336685231147326793",
    "6336907611669011898", "6336988189550451848", "6337098578799893838",
    "6336808092981796477", "6337020083977592163", "6337112997005107243",
    "6337051755066433311", "6336835907190004485", "6336618976981818626",
    "6336857218817728795", "6336974471424908889", "6337125748763008448",
    "6337098338281725706", "6336962978092425393", "6336633214798404108",
    "6337019139084786234", "6337035356881296575", "6337026908680625329",
    "6336690569791676356", "6337106906741480828", "6337072645787361389",
    "6336720729052027967", "6336670885956557643", "6337113894653271580",
    "6334488003188105980", "6336721798498884548", "6336799284003873851",
    "6337112129421713282", "6336599202952388231", "6336755629956275338",
    "6334702021408465964", "6337109865973948062", "6336708763273142215",
    "6337083451925078342", "6336930400765484501", "6334788126912815244",
    "6337059606266651217", "6336812005697002754", "6336813629194640485",
    "6337085796977221633", "6336663202260065128", "6334324468013341494",
    "6337047855236129713", "6336782885818742144", "6336664645369076808",
    "6336910583786383660", "6336862179504954500", "6336697226990985005",
    "6336772620846899242", "6337033209397649451", "6336861449360514102",
    "6336573617832206335", "6337055242579876765", "6336789422758960593",
    "6336781331040577785", "6336603218746810844", "6337123072998383823",
    "6336894825551371014", "6334681658968513467", "6336799919659031563",
    "6336707603631972035", "6336874467406389346", "6336756411640323933",
    "6336608037700115865", "6336613247495445753", "6336973539417007164",
    "6336931040715612818", "6336653869296132233", "6336836572909938734",
    "6336798231736885254", "6336813951317187443", "6336866435817545002",
    "6336662845777780692", "6336580455420141312", "6336750437340816001",
    "6336677470141422007", "6337078718871117522", "6336931345658289868",
    "6336935322798005307", "6336646834139700626", "6337010179783007229",
    "6336618208182673162", "6336580975111184057", "6336957184181543528",
    "6336991256157101601", "6336655355354815762", "6336795865209904645",
    "6337054177427988529", "6336855354801921798", "6336878444546105899",
    "6336861037043654967", "6336662472115626382", "6337093386184432717",
    "6336637947852365586", "6336876696494417749", "6334678278829252492",
    "6337087411884923105", "6336989731443711607", "6336882614959349480",
    "6336886055228153516", "6336797591786757523", "6336674519498890396",
    "6336856849450540332", "6337048379222138619", "6336816932024491505",
    "6336672814396874442", "6336835035311644293", "6336668004033504924",
    "6336682357814205676", "6336764563488252026", "6337100812182887680",
    "6336575056646249129"
]

def get_emoji(key: str) -> str:
    char, _ = CUSTOM_EMOJIS.get(key, ("❓", None))
    return char

def get_emoji_entity(key: str, offset: int) -> MessageEntity:
    char, emoji_id = CUSTOM_EMOJIS.get(key, ("❓", None))
    if emoji_id:
        return MessageEntity(type="custom_emoji", offset=offset, length=len(char), custom_emoji_id=emoji_id)
    return None

def get_random_premium_emoji_id() -> str:
    return random.choice(PREMIUM_EMOJIS)

def process_text_with_premium_emojis(text: str, entities: list = None) -> tuple:
    if entities is None: entities = []
    final_text, new_entities = "", []
    offset_map = {}
    current_old_offset, current_new_offset = 0, 0
    i = 0
    while i < len(text):
        char = text[i]
        offset_map[current_old_offset] = current_new_offset
        if emoji.is_emoji(char):
            rand_id = get_random_premium_emoji_id()
            placeholder = "✨"
            new_entities.append(MessageEntity(type="custom_emoji", offset=current_new_offset, length=len(placeholder), custom_emoji_id=rand_id))
            final_text += placeholder
            char_len = len(char.encode('utf-16-le')) // 2
            current_old_offset += char_len
            current_new_offset += len(placeholder)
        else:
            final_text += char
            current_old_offset += 1
            current_new_offset += 1
        i += 1
    offset_map[current_old_offset] = current_new_offset
    for ent in entities:
        if ent.type == "custom_emoji": continue
        new_start = offset_map.get(ent.offset)
        new_end = offset_map.get(ent.offset + ent.length)
        if new_start is not None and new_end is not None:
            new_entities.append(MessageEntity(type=ent.type, offset=new_start, length=new_end - new_start, url=ent.url, user=ent.user, language=ent.language, custom_emoji_id=ent.custom_emoji_id))
    return final_text, new_entities

def create_premium_response(text: str, emoji_key: str = None, bold: bool = True, code_words: list = None, italic: bool = False) -> tuple:
    final_text, entities, offset = text, [], 0
    if emoji_key:
        emoji_char, _ = CUSTOM_EMOJIS.get(emoji_key, ("❓", None))
        if emoji_char:
            final_text = f"{emoji_char} {text}"
            ent = get_emoji_entity(emoji_key, 0)
            if ent: entities.append(ent); offset = len(emoji_char) + 1
    if bold: entities.append(MessageEntity(type="bold", offset=0, length=len(final_text)))
    if italic: entities.append(MessageEntity(type="italic", offset=0, length=len(final_text)))
    if code_words:
        for word in code_words:
            idx = final_text.find(str(word))
            if idx != -1: entities.append(MessageEntity(type="code", offset=idx, length=len(str(word))))
    return process_text_with_premium_emojis(final_text, entities)

# --- LOGGING SETUP ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO, handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()])
logger = logging.getLogger(__name__)

application = None
scheduler = None

# --- DATA STORAGE ---
def is_owner(user_id): return user_id == OWNER_ID
def is_private_chat(update): return update.effective_chat.type == 'private'

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f: return json.load(f)
        except:
            return initialize_data()
    return initialize_data()

def initialize_data():
    return {"users": {}, "total_likes": {}, "custom_message": "", "allowed_groups": [], "auto_like_uids": {}, "paused_uids": [], "settings": {"daily_like_time": DAILY_LIKE_TIME}, "like_limits": {}, "api_stats": {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}, "active_groups": []}

def save_data(data):
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            json.dump(data, tmp, indent=4)
            tmp.flush()
        shutil.move(tmp.name, DATA_FILE)
    except Exception as e:
        logger.error(f"Error saving data: {e}")

def format_uid_key(user_id, uid): return f"{user_id}_{uid}"
def parse_uid_key(key):
    parts = key.split('_', 1)
    return (parts[0], parts[1]) if len(parts) == 2 else (None, None)

def update_user_info(data, user):
    user_id = str(user.id)
    tg_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = user.username or "N/A"
    if user_id not in data["users"]: data["users"][user_id] = {"telegram_name": tg_name, "username": username, "uid": None}
    else: data["users"][user_id]["telegram_name"] = tg_name; data["users"][user_id]["username"] = username
    return data

def update_group_info(data, chat):
    chat_id, chat_title = str(chat.id), chat.title or "Unknown Group"
    if "active_groups" not in data: data["active_groups"] = []
    if not any(g["chat_id"] == chat_id for g in data["active_groups"]):
        data["active_groups"].append({"chat_id": chat_id, "chat_title": chat_title, "added_date": datetime.now(IST).isoformat()})
    return data

def owner_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_owner(update.effective_user.id):
            text, entities = create_premium_response("Access Denied! Owner only.", emoji_key="error")
            await update.message.reply_text(text, entities=entities)
            return
        return await func(update, context)
    return wrapper

# --- API HELPER ---
async def call_like_api(uid, region, retry_count=0):
    max_retries = 3
    # ⚠️ PALITAN ITO NG TOTOONG API URL MO
    api_url = f"https://api.mocky.io/v2/5f5c" 
    
    try:
        # Mock response para hindi mag-crash kung wala pang totoong API
        if "mocky.io" in api_url:
            return {"PlayerNickname": "TestPlayer", "UID": uid, "PlayerLevel": 50, "PlayerRegion": region, "LikesbeforeCommand": 100, "LikesafterCommand": 150, "LikesGivenByAPI": 50, "status": "success"}
            
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        data = load_data()
        data["api_stats"]["total_calls"] += 1
        data["api_stats"]["successful_calls"] += 1
        save_data(data)
        return response.json()
    except Exception as e:
        logger.error(f"API Error for UID {uid}: {str(e)}")
        data = load_data()
        data["api_stats"]["total_calls"] += 1
        data["api_stats"]["failed_calls"] += 1
        save_data(data)
        if retry_count < max_retries:
            await asyncio.sleep((2 ** retry_count) * 5)
            return await call_like_api(uid, region, retry_count + 1)
        raise Exception("API temporarily unavailable")

async def send_like_response(update, context, api_data, uid, region, remaining_days, is_daily=False):
    try:
        prefix = "✨ Daily Auto-Like Results ✨" if is_daily else "✨ Like Results ✨"
        response_text = (f"{prefix}\n\n{get_emoji('user')} Nickname: {api_data.get('PlayerNickname', 'N/A')}\n"
            f"{get_emoji('uid')} UID: {api_data.get('UID', 'N/A')}\n{get_emoji('level')} Level: {api_data.get('PlayerLevel', 'N/A')}\n"
            f"{get_emoji('region')} Region: {api_data.get('PlayerRegion', 'N/A')}\n{get_emoji('like')} Likes Before: {api_data.get('LikesbeforeCommand', 'N/A')}\n"
            f"{get_emoji('like')} Likes After: {api_data.get('LikesafterCommand', 'N/A')}\n{get_emoji('like')} Likes Given: {api_data.get('LikesGivenByAPI', 'N/A')}\n"
            f"{get_emoji('days')} Days Remaining: {remaining_days}\n{get_emoji('success')} Status: {api_data.get('status', 'N/A')}\n"
            f"{get_emoji('time')} Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')}")
        
        data = load_data()
        if data.get("custom_message"): response_text += f"\n\n✨ {data['custom_message']}"
        final_text, entities = process_text_with_premium_emojis(response_text)
        
        if is_daily:
            await application.bot.send_message(chat_id=update, text=final_text, entities=entities)
            await send_to_all_groups(final_text, entities)
        else:
            await update.message.reply_text(final_text, entities=entities)
            if not is_private_chat(update): await send_to_all_groups(final_text, entities)
        return True
    except Exception as e:
        logger.error(f"Error sending like response: {e}")
        return False

async def send_to_all_groups(message, entities=None):
    data = load_data()
    for group in data.get("active_groups", []):
        try:
            await application.bot.send_message(chat_id=group["chat_id"], text=message, entities=entities)
            await asyncio.sleep(0.5)
        except Exception:
            data["active_groups"] = [g for g in data["active_groups"] if g["chat_id"] != group["chat_id"]]
            save_data(data)

# --- SCHEDULER ---
async def reschedule_daily_job():
    if not scheduler: return
    data = load_data()
    time_str = data.get("settings", {}).get("daily_like_time", DAILY_LIKE_TIME)
    hour, minute = map(int, time_str.split(':'))
    try: scheduler.remove_job("daily_like_job")
    except: pass
    scheduler.add_job(daily_like_job, trigger=CronTrigger(hour=hour, minute=minute), id='daily_like_job', replace_existing=True, coalesce=True, max_instances=1, misfire_grace_time=600)

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    data = update_user_info(data, update.effective_user)
    if not is_private_chat(update): data = update_group_info(data, update.effective_chat)
    save_data(data)
    text, entities = create_premium_response("✨ Welcome to the Auto-Like Bot ✨\n\n🤖 This bot helps you automatically send likes to your game UID daily.\n\n📋 Use /help to see all commands.", emoji_key="welcome")
    await update.message.reply_text(text, entities=entities)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = ("✨ Auto-Like Bot Commands ✨\n\n📋 User Commands:\n⭐ /help - Show this message\n⭐ /mylike - Check total likes\n⭐ /myuids - Show registered UIDs\n\n👑 Owner Commands:\n⭐ /autolike {uid} {region} {days}\n⭐ /like {uid} {region}\n⭐ /status\n⭐ /setmessage <text>\n⭐ /setgroup {id}\n⭐ /removeuid {uid}\n⭐ /pauseuid {uid}\n⭐ /resumeuid {uid}\n⭐ /extend {uid} {days}\n⭐ /resetlikes {uid}\n⭐ /ownerbroadcast <msg>\n⭐ /allstats\n⭐ /backup\n⭐ /restore\n⭐ /settime {hour}:{minute}\n⭐ /setlimit {uid} {limit}\n⭐ /checkapi {uid} {region}\n⭐ /runnow\n⭐ /groups")
    text, entities = create_premium_response(help_text, emoji_key="help")
    await update.message.reply_text(text, entities=entities)

@owner_only
async def autolike(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) not in [3, 4]:
        text, entities = create_premium_response("Usage:\n⭐ /autolike {uid} {region} {days}\n⭐ /autolike {uid} {region} {days} {user_id}", emoji_key="warning")
        await update.message.reply_text(text, entities=entities)
        return

    uid, region = context.args[0], context.args[1].upper()
    try: days = int(context.args[2])
    except ValueError:
        text, entities = create_premium_response("Days must be a valid number.", emoji_key="error")
        await update.message.reply_text(text, entities=entities)
        return

    target_user_id = str(context.args[3]) if len(context.args) == 4 else str(update.effective_user.id)
    data = load_data()
    uid_key = format_uid_key(target_user_id, uid)
    expiry_date = (datetime.now(IST) + timedelta(days=days)).isoformat()

    if uid_key in data["auto_like_uids"]:
        existing_expiry = datetime.fromisoformat(data["auto_like_uids"][uid_key]["expiry_date"]).astimezone(IST)
        data["auto_like_uids"][uid_key]["expiry_date"] = (existing_expiry + timedelta(days=days)).isoformat()
        data["auto_like_uids"][uid_key]["region"] = region
        action = "updated"
    else:
        data["auto_like_uids"][uid_key] = {"uid": uid, "region": region, "expiry_date": expiry_date, "chat_id": target_user_id, "paused": False, "last_run": None, "total_likes": 0}
        action = "activated"

    if uid_key in data.get("paused_uids", []): data["paused_uids"].remove(uid_key)
    save_data(data)

    try:
        api_data = await call_like_api(uid, region)
        remaining_days = max(0, (datetime.fromisoformat(expiry_date).astimezone(IST) - datetime.now(IST)).days)
        await send_like_response(update, context, api_data, uid, region, remaining_days, is_daily=False)
        data = load_data()
        if uid_key in data["auto_like_uids"]:
            data["auto_like_uids"][uid_key]["total_likes"] += api_data.get("LikesGivenByAPI", 0)
            data["auto_like_uids"][uid_key]["last_run"] = datetime.now(IST).isoformat()
            save_data(data)
    except Exception as e:
        logger.error(f"Error in autolike: {e}")
        text, entities = create_premium_response("Error calling API.", emoji_key="error")
        await update.message.reply_text(text, entities=entities)
        return

    text, entities = create_premium_response(f"✅ Auto-like {action}!\n🔢 UID: {uid}\n🌍 Region: {region}\n📅 Days: {days}\n\n🔄 Automatic likes daily at {data.get('settings', {}).get('daily_like_time', DAILY_LIKE_TIME)} IST.", emoji_key="success")
    await update.message.reply_text(text, entities=entities)

@owner_only
async def like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        text, entities = create_premium_response("Usage: /like {uid} {region}", emoji_key="warning")
        await update.message.reply_text(text, entities=entities)
        return
    try:
        api_data = await call_like_api(context.args[0], context.args[1].upper())
        await send_like_response(update, context, api_data, context.args[0], context.args[1].upper(), "1")
    except Exception as e:
        text, entities = create_premium_response("Error calling API.", emoji_key="error")
        await update.message.reply_text(text, entities=entities)

@owner_only
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    text, entities = create_premium_response(f"✨ Bot Status ✨\n\n👥 Users: {len(data.get('users', {}))}\n🔄 Auto-Likes: {len(data.get('auto_like_uids', {}))}\n📈 API Calls: {data['api_stats']['total_calls']}\n✅ Success: {data['api_stats']['successful_calls']}\n❌ Failed: {data['api_stats']['failed_calls']}", emoji_key="status")
    await update.message.reply_text(text, entities=entities)

async def mylike(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_likes = data.get("total_likes", {}).get(str(update.effective_user.id))
    if user_likes:
        text, entities = create_premium_response(f"📊 Your Stats:\n\n❤️ Total Likes: {user_likes['count']}\n📅 Days Used: {user_likes['days']}", emoji_key="stats")
    else:
        text, entities = create_premium_response("You have not received any likes yet.", emoji_key="info")
    await update.message.reply_text(text, entities=entities)

async def myuids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = str(update.effective_user.id)
    user_uids = {parse_uid_key(k)[1]: v for k, v in data.get("auto_like_uids", {}).items() if parse_uid_key(k)[0] == user_id}
    if not user_uids:
        text, entities = create_premium_response("No registered UIDs.", emoji_key="info")
        await update.message.reply_text(text, entities=entities)
        return
    
    response_text = "📋 Registered UIDs:\n\n"
    for uid, info in user_uids.items():
        response_text += f"🔢 UID: {uid}\n🌍 Region: {info['region']}\n❤️ Likes: {info.get('total_likes', 0)}\n🔄 Status: {'⏸️ Paused' if format_uid_key(user_id, uid) in data.get('paused_uids', []) else '✅ Active'}\n\n"
    text, entities = create_premium_response(response_text, emoji_key="uid")
    await update.message.reply_text(text, entities=entities)

@owner_only
async def remove_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    data = load_data()
    uid_key = format_uid_key(str(update.effective_user.id), context.args[0])
    if uid_key in data.get("auto_like_uids", {}):
        del data["auto_like_uids"][uid_key]
        if uid_key in data.get("paused_uids", []): data["paused_uids"].remove(uid_key)
        save_data(data)
        text, entities = create_premium_response(f"✅ UID {context.args[0]} removed.", emoji_key="success")
    else:
        text, entities = create_premium_response(f"❌ UID {context.args[0]} not found.", emoji_key="error")
    await update.message.reply_text(text, entities=entities)

@owner_only
async def pause_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    data = load_data()
    uid_key = format_uid_key(str(update.effective_user.id), context.args[0])
    if uid_key in data.get("auto_like_uids", {}):
        if "paused_uids" not in data: data["paused_uids"] = []
        if uid_key not in data["paused_uids"]: data["paused_uids"].append(uid_key); save_data(data)
        text, entities = create_premium_response(f"✅ UID {context.args[0]} paused.", emoji_key="success")
    else:
        text, entities = create_premium_response(f"❌ UID not found.", emoji_key="error")
    await update.message.reply_text(text, entities=entities)

@owner_only
async def resume_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    data = load_data()
    uid_key = format_uid_key(str(update.effective_user.id), context.args[0])
    if uid_key in data.get("auto_like_uids", {}):
        if uid_key in data.get("paused_uids", []): data["paused_uids"].remove(uid_key); save_data(data)
        text, entities = create_premium_response(f"✅ UID {context.args[0]} resumed.", emoji_key="success")
    else:
        text, entities = create_premium_response(f"❌ UID not found.", emoji_key="error")
    await update.message.reply_text(text, entities=entities)

@owner_only
async def extend_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2: return
    data = load_data()
    uid_key = format_uid_key(str(update.effective_user.id), context.args[0])
    if uid_key in data.get("auto_like_uids", {}):
        try:
            days = int(context.args[1])
            current_expiry = datetime.fromisoformat(data["auto_like_uids"][uid_key]["expiry_date"]).astimezone(IST)
            new_expiry = current_expiry + timedelta(days=days)
            data["auto_like_uids"][uid_key]["expiry_date"] = new_expiry.isoformat()
            save_data(data)
            text, entities = create_premium_response(f"✅ UID {context.args[0]} extended by {days} days.", emoji_key="success")
        except:
            text, entities = create_premium_response("Invalid days.", emoji_key="error")
    else:
        text, entities = create_premium_response(f"❌ UID not found.", emoji_key="error")
    await update.message.reply_text(text, entities=entities)

@owner_only
async def reset_likes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    data = load_data()
    uid_key = format_uid_key(str(update.effective_user.id), context.args[0])
    if uid_key in data.get("auto_like_uids", {}):
        data["auto_like_uids"][uid_key]["total_likes"] = 0
        save_data(data)
        text, entities = create_premium_response(f"✅ Likes for UID {context.args[0]} reset to 0.", emoji_key="success")
    else:
        text, entities = create_premium_response(f"❌ UID not found.", emoji_key="error")
    await update.message.reply_text(text, entities=entities)

@owner_only
async def owner_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    message = ' '.join(context.args)
    data = load_data()
    sent, failed = 0, 0
    for user_id in data.get("users", {}).keys():
        try:
            await context.bot.send_message(chat_id=user_id, text=f"📢 Broadcast from Owner:\n\n✨ {message}")
            sent += 1; await asyncio.sleep(0.1)
        except: failed += 1
    text, entities = create_premium_response(f"📢 Broadcast done!\n✅ Sent: {sent}\n❌ Failed: {failed}", emoji_key="broadcast")
    await update.message.reply_text(text, entities=entities)

@owner_only
async def allstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    auto_like_uids = data.get("auto_like_uids", {})
    total_likes = sum(info.get("total_likes", 0) for info in auto_like_uids.values())
    text, entities = create_premium_response(f"📊 Comprehensive Stats:\n\n👥 Users: {len(data.get('users', {}))}\n🔄 Auto-Like UIDs: {len(auto_like_uids)}\n❤️ Total Likes Sent: {total_likes}\n📈 API Calls: {data['api_stats']['total_calls']}\n⭐ Success Rate: {data['api_stats']['successful_calls'] / max(data['api_stats']['total_calls'], 1) * 100:.1f}%", emoji_key="stats")
    await update.message.reply_text(text, entities=entities)

@owner_only
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(DATA_FILE, 'rb') as f:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=f, filename="bot_data_backup.json", caption="📦 Bot Data Backup")
    except Exception as e:
        text, entities = create_premium_response("Backup failed.", emoji_key="error")
        await update.message.reply_text(text, entities=entities)

@owner_only
async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document: return
    try:
        file = await context.bot.get_file(update.message.document.file_id)
        await file.download_to_drive("restore_backup.json")
        with open("restore_backup.json", 'r') as f: backup_data = json.load(f)
        with open(DATA_FILE, 'w') as f: json.dump(backup_data, f, indent=4)
        os.remove("restore_backup.json")
        text, entities = create_premium_response("Backup restored!", emoji_key="success")
    except:
        text, entities = create_premium_response("Restore failed.", emoji_key="error")
    await update.message.reply_text(text, entities=entities)

@owner_only
async def setmessage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    data = load_data()
    data["custom_message"] = ' '.join(context.args)
    save_data(data)
    text, entities = create_premium_response(f"✅ Custom message set.", emoji_key="success")
    await update.message.reply_text(text, entities=entities)

@owner_only
async def setgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    try:
        group_id = int(context.args[0])
        data = load_data()
        if group_id not in data["allowed_groups"]: data["allowed_groups"].append(group_id); save_data(data)
        text, entities = create_premium_response(f"✅ Group {group_id} added.", emoji_key="success")
    except:
        text, entities = create_premium_response("Invalid ID.", emoji_key="error")
    await update.message.reply_text(text, entities=entities)

@owner_only
async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not re.match(r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$', context.args[0]): return
    data = load_data()
    data["settings"]["daily_like_time"] = context.args[0]
    save_data(data)
    await reschedule_daily_job()
    text, entities = create_premium_response(f"✅ Time set to {context.args[0]} IST.", emoji_key="success")
    await update.message.reply_text(text, entities=entities)

@owner_only
async def set_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2: return
    try:
        uid, limit = context.args[0], int(context.args[1])
        data = load_data()
        uid_key = format_uid_key(str(update.effective_user.id), uid)
        if uid_key in data["auto_like_uids"]:
            data["like_limits"][uid_key] = limit; save_data(data)
            text, entities = create_premium_response(f"✅ Limit set to {limit} for {uid}.", emoji_key="success")
        else:
            text, entities = create_premium_response(f"❌ UID not found.", emoji_key="error")
    except:
        text, entities = create_premium_response("Invalid args.", emoji_key="error")
    await update.message.reply_text(text, entities=entities)

@owner_only
async def check_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2: return
    try:
        api_data = await call_like_api(context.args[0], context.args[1].upper())
        text, entities = create_premium_response(f"✅ API Success!\nUID: {api_data.get('UID')}\nPlayer: {api_data.get('PlayerNickname')}", emoji_key="success")
    except:
        text, entities = create_premium_response("API Test Failed.", emoji_key="error")
    await update.message.reply_text(text, entities=entities)

@owner_only
async def runnow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Running job...")
    await daily_like_job()
    await update.message.reply_text("✅ Job completed!")

@owner_only
async def groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    active_groups = data.get("active_groups", [])
    if not active_groups:
        text, entities = create_premium_response("No active groups.", emoji_key="info")
    else:
        resp = "🏢 Active Groups:\n\n" + "\n".join([f"📋 {g['chat_title']} (ID: {g['chat_id']})" for g in active_groups])
        text, entities = create_premium_response(resp, emoji_key="group")
    await update.message.reply_text(text, entities=entities)

async def daily_like_job():
    data = load_data()
    auto_like_uids = data.get("auto_like_uids", {})
    paused_uids = data.get("paused_uids", [])
    expired_keys = []
    
    for uid_key, uid_info in auto_like_uids.items():
        if uid_key in paused_uids: continue
        expiry_date = datetime.fromisoformat(uid_info["expiry_date"]).astimezone(IST)
        if expiry_date <= datetime.now(IST):
            expired_keys.append(uid_key); continue
        try:
            api_data = await call_like_api(uid_info["uid"], uid_info["region"])
            await send_like_response(uid_info["chat_id"], None, api_data, uid_info["uid"], uid_info["region"], max(0, (expiry_date - datetime.now(IST)).days), is_daily=True)
            data = load_data()
            if uid_key in data["auto_like_uids"]:
                data["auto_like_uids"][uid_key]["total_likes"] += api_data.get("LikesGivenByAPI", 0)
                data["auto_like_uids"][uid_key]["last_run"] = datetime.now(IST).isoformat()
                save_data(data)
        except Exception as e:
            logger.error(f"Daily like failed for {uid_info['uid']}: {e}")
        await asyncio.sleep(1)
        
    if expired_keys:
        data = load_data()
        for key in expired_keys:
            if key in data["auto_like_uids"]: del data["auto_like_uids"][key]
            if key in data["paused_uids"]: data["paused_uids"].remove(key)
        save_data(data)

async def on_startup(app: Application):
    global scheduler
    scheduler = AsyncIOScheduler(timezone=IST)
    await reschedule_daily_job()
    scheduler.start()
    logger.info("✅ Scheduler started.")

def main():
    # Start Dummy Web Server for Render
    threading.Thread(target=run_web_server, daemon=True).start()
    
    global application
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("autolike", autolike))
    application.add_handler(CommandHandler("like", like))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("mylike", mylike))
    application.add_handler(CommandHandler("myuids", myuids))
    application.add_handler(CommandHandler("removeuid", remove_uid))
    application.add_handler(CommandHandler("pauseuid", pause_uid))
    application.add_handler(CommandHandler("resumeuid", resume_uid))
    application.add_handler(CommandHandler("extend", extend_uid))
    application.add_handler(CommandHandler("resetlikes", reset_likes))
    application.add_handler(CommandHandler("ownerbroadcast", owner_broadcast))
    application.add_handler(CommandHandler("allstats", allstats))
    application.add_handler(CommandHandler("backup", backup))
    application.add_handler(CommandHandler("restore", restore))
    application.add_handler(CommandHandler("setmessage", setmessage))
    application.add_handler(CommandHandler("setgroup", setgroup))
    application.add_handler(CommandHandler("settime", set_time))
    application.add_handler(CommandHandler("setlimit", set_limit))
    application.add_handler(CommandHandler("checkapi", check_api))
    application.add_handler(CommandHandler("runnow", runnow))
    application.add_handler(CommandHandler("groups", groups))

    application.post_init = on_startup
    logger.info("🤖 Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
