import requests
import re
import time
import random
import string
import threading
import json
import os
import asyncio
from telegram import Bot
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse, parse_qs
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.ext import MessageHandler, filters
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# Thêm vào sau các import, trước hàm login_and_get_cookies()
import pickle
# Thêm sau các import
import logging
from datetime import datetime, timedelta, timezone

# Múi giờ Việt Nam (UTC+7)
VIETNAM_TZ = timezone(timedelta(hours=7))
# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Thay thế các print bằng logging

def save_session():
    """Lưu session hiện tại vào file"""
    global session
    try:
        with open('session.pkl', 'wb') as f:
            pickle.dump(session, f)
        print("💾 Đã lưu session vào file")
    except Exception as e:
        print(f"⚠️ Lỗi lưu session: {e}")

def load_session():
    """Đọc session từ file"""
    global session
    try:
        with open('session.pkl', 'rb') as f:
            session = pickle.load(f)
        print("📂 Đã load session từ file")
        return True
    except:
        return False
# ========== CẤU HÌNH ==========CÓ
BOT_TOKEN = "8930029347:AAHnNFIRybvlZkWf5MnTic-xXuhQdBkhy4I"
EMAIL = "779@gmail.com"
PASSWORD = "abc12345"
BASE_URL = "https://veloragame.com"
CHECK_INTERVAL = 25
ADMIN_IDS = [5180190297, 8076250181]  # Danh sách admin user ID
WITHDRAW_FEE_PERCENT = 15
WITHDRAW_FIXED_FEE = 5000

# ========== FILE LƯU DỮ LIỆU ==========
TRACKING_FILE = "tracking_orders.json"
BALANCE_FILE = "user_balance.json"
BANNED_USERS_FILE = "banned_users.json"
WITHDRAW_REQUESTS_FILE = "withdraw_requests.json"
PENDING_USERS_FILE = "pending_users.json"
pending_users = []  # Lưu user đang chờ duyệt
WITHDRAW_BANK_FILE = "withdraw_bank.json"
user_withdraw_banks = {}  # {user_id: [{'bank': 'MSB', 'stk': '123', 'name': 'TRAN VAN A'}]}

# ========== BIẾN TOÀN CỤC ==========
session = requests.Session()
csrf_token = None
is_logged_in = False
tracking_orders = {}
user_balance = {}
banned_users = []
withdraw_requests = {}
checking_thread = None
checking_active = True

# ========== HÀM LƯU/LOAD DỮ LIỆU ==========
APPROVED_USERS_FILE = "approved_users.json"
approved_users = []

def save_approved_users():
    with open(APPROVED_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(approved_users, f, ensure_ascii=False, indent=2)

def load_approved_users():
    global approved_users
    if os.path.exists(APPROVED_USERS_FILE):
        try:
            with open(APPROVED_USERS_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    approved_users = json.loads(content)
                else:
                    approved_users = []
        except:
            approved_users = []
    else:
        approved_users = []
    print(f"✅ Đã load {len(approved_users)} user đã duyệt")
def save_tracking():
    with open(TRACKING_FILE, 'w', encoding='utf-8') as f:
        json.dump(tracking_orders, f, ensure_ascii=False, indent=2)

def load_tracking():
    global tracking_orders
    if os.path.exists(TRACKING_FILE):
        try:
            with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    tracking_orders = json.loads(content)
                else:
                    tracking_orders = {}
                    print("⚠️ File tracking_orders.json rỗng, khởi tạo mới")
        except json.JSONDecodeError:
            tracking_orders = {}
            print("⚠️ File tracking_orders.json bị lỗi, khởi tạo mới")
        except Exception as e:
            tracking_orders = {}
            print(f"⚠️ Lỗi đọc file tracking_orders.json: {e}")
    else:
        tracking_orders = {}
        print("📂 Không tìm thấy file tracking_orders.json, khởi tạo mới")
    
    print(f"📂 Đã load {len(tracking_orders)} đơn hàng")

def save_balance():
    with open(BALANCE_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_balance, f, ensure_ascii=False, indent=2)
def save_pending_users():
    with open(PENDING_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(pending_users, f, ensure_ascii=False, indent=2)
def save_withdraw_banks():
    with open(WITHDRAW_BANK_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_withdraw_banks, f, ensure_ascii=False, indent=2)

def load_withdraw_banks():
    global user_withdraw_banks
    if os.path.exists(WITHDRAW_BANK_FILE):
        with open(WITHDRAW_BANK_FILE, 'r', encoding='utf-8') as f:
            user_withdraw_banks = json.load(f)
def load_pending_users():
    global pending_users
    if os.path.exists(PENDING_USERS_FILE):
        try:
            with open(PENDING_USERS_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    pending_users = json.loads(content)
                else:
                    pending_users = []
        except:
            pending_users = []
    else:
        pending_users = []
    print(f"⏳ Đã load {len(pending_users)} user chờ duyệt")
def load_balance():
    global user_balance
    if os.path.exists(BALANCE_FILE):
        try:
            with open(BALANCE_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    user_balance = json.loads(content)
                else:
                    user_balance = {}
                    print("⚠️ File user_balance.json rỗng, khởi tạo mới")
        except json.JSONDecodeError:
            user_balance = {}
            print("⚠️ File user_balance.json bị lỗi, khởi tạo mới")
        except Exception as e:
            user_balance = {}
            print(f"⚠️ Lỗi đọc file user_balance.json: {e}")
    else:
        user_balance = {}
        print("💰 Không tìm thấy file user_balance.json, khởi tạo mới")
    
    print(f"💰 Đã load số dư cho {len(user_balance)} user")

def save_banned():
    with open(BANNED_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(banned_users, f, ensure_ascii=False, indent=2)

def load_banned():
    global banned_users
    if os.path.exists(BANNED_USERS_FILE):
        try:
            with open(BANNED_USERS_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    banned_users = json.loads(content)
                else:
                    banned_users = []
                    print("⚠️ File banned_users.json rỗng, khởi tạo mới")
        except json.JSONDecodeError:
            banned_users = []
            print("⚠️ File banned_users.json bị lỗi, khởi tạo mới")
        except Exception as e:
            banned_users = []
            print(f"⚠️ Lỗi đọc file banned_users.json: {e}")
    else:
        banned_users = []
        print("🚫 Không tìm thấy file banned_users.json, khởi tạo mới")
    
    print(f"🚫 Đã load {len(banned_users)} user bị ban")

def save_withdraw_requests():
    with open(WITHDRAW_REQUESTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(withdraw_requests, f, ensure_ascii=False, indent=2)

def load_withdraw_requests():
    global withdraw_requests
    if os.path.exists(WITHDRAW_REQUESTS_FILE):
        try:
            with open(WITHDRAW_REQUESTS_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    withdraw_requests = json.loads(content)
                else:
                    withdraw_requests = {}
                    print("⚠️ File withdraw_requests.json rỗng, khởi tạo mới")
        except json.JSONDecodeError:
            withdraw_requests = {}
            print("⚠️ File withdraw_requests.json bị lỗi, khởi tạo mới")
        except Exception as e:
            withdraw_requests = {}
            print(f"⚠️ Lỗi đọc file withdraw_requests.json: {e}")
    else:
        withdraw_requests = {}
        print("💸 Không tìm thấy file withdraw_requests.json, khởi tạo mới")
    
    print(f"💸 Đã load {len(withdraw_requests)} yêu cầu rút tiền")

def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_banned(user_id):
    return str(user_id) in banned_users

# ========== TÍNH TOÁN PHÍ RÚT ==========
def calculate_withdraw_amount(amount):
    """Tính số tiền sau khi trừ phí 15% + 5k"""
    fee = amount * WITHDRAW_FEE_PERCENT / 100 + WITHDRAW_FIXED_FEE
    after_fee = amount - fee
    return {
        'original': amount,
        'fee': fee,
        'after_fee': after_fee,
        'fee_percent': WITHDRAW_FEE_PERCENT,
        'fixed_fee': WITHDRAW_FIXED_FEE
    }

# ========== MENU NGANG ==========
def get_main_menu(user_id):
    is_admin_user = is_admin(user_id)
    
    if is_admin_user:
        keyboard = [
            [
                InlineKeyboardButton(
                    text="Tạo đơn", 
                    icon_custom_emoji_id="5213394688735717942",
                    callback_data="menu_new"
                ),
                InlineKeyboardButton(
                    text="Số dư", 
                    icon_custom_emoji_id="5375312095346704820",
                    callback_data="menu_balance"
                ),
                InlineKeyboardButton(
                    text="Theo dõi", 
                    icon_custom_emoji_id="5197269100878907942",
                    callback_data="menu_tracking"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Rút tiền", 
                    icon_custom_emoji_id="5373174941095050893",
                    callback_data="menu_withdraw"
                ),
                InlineKeyboardButton(
                    text="DS User", 
                    icon_custom_emoji_id="5453957997418004470",
                    callback_data="admin_users"
                ),
                InlineKeyboardButton(
                    text="Doanh thu", 
                    icon_custom_emoji_id="5028746137645876535",
                    callback_data="admin_revenue"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Ban User", 
                    icon_custom_emoji_id="5240241223632954241",
                    callback_data="admin_ban"
                ),
                InlineKeyboardButton(
                    text="Mở ban", 
                    icon_custom_emoji_id="5465443379917629504",
                    callback_data="admin_unban"
                ),
                InlineKeyboardButton(
                    text="Duyệt rút", 
                    icon_custom_emoji_id="5440547189669516347",
                    callback_data="admin_approve_withdraw"
                )
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    text="Tạo đơn", 
                    icon_custom_emoji_id="5213394688735717942",
                    callback_data="menu_new"
                ),
                InlineKeyboardButton(
                    text="Số dư", 
                    icon_custom_emoji_id="5375312095346704820",
                    callback_data="menu_balance"
                ),
                InlineKeyboardButton(
                    text="Theo dõi", 
                    icon_custom_emoji_id="5197269100878907942",
                    callback_data="menu_tracking"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Rút tiền", 
                    icon_custom_emoji_id="5373174941095050893",
                    callback_data="menu_withdraw"
                )
            ]
        ]
    
    return InlineKeyboardMarkup(keyboard)

def get_bank_menu():
    keyboard = [
        [
            InlineKeyboardButton(
                text="MSB", 
                icon_custom_emoji_id="5264895611517300926",  # ID emoji 🏦 của bạn
                callback_data="create_MSB"
            )
        ],
        [
            InlineKeyboardButton(
                text="BIDV", 
                icon_custom_emoji_id="5264895611517300926",  # ID emoji 🏦 của bạn
                callback_data="create_BIDV"
            )
        ],
        [
            InlineKeyboardButton(
                text="Quay lại", 
                icon_custom_emoji_id="5253997076169115797",  # ID emoji 🔙 của bạn
                callback_data="menu_main"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_withdraw_amount_menu(user_id, bank_index=None):
    """Menu nhập số tiền rút"""
    balance = user_balance.get(str(user_id), {}).get('balance', 0)
    bank_suffix = f"_{bank_index}" if bank_index is not None else ""
    
    keyboard = [
        [InlineKeyboardButton(f"💰 Số dư: {balance:,.0f} VND", callback_data="noop")],
        [InlineKeyboardButton("💵 200,000 VND", callback_data=f"withdraw_200000{bank_suffix}"),
        InlineKeyboardButton("💵 500,000 VND", callback_data=f"withdraw_500000{bank_suffix}")],
        [InlineKeyboardButton("💵 1,000,000 VND", callback_data=f"withdraw_1000000{bank_suffix}"),
        InlineKeyboardButton("💵 2,000,000 VND", callback_data=f"withdraw_2000000{bank_suffix}")],
        [InlineKeyboardButton("✏️ Nhập số tiền", callback_data=f"withdraw_custom{bank_suffix}")],
        [InlineKeyboardButton("🔙 Quay lại", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_withdraw_confirm_menu(request_id, amount, after_fee):
    """Menu xác nhận rút tiền cho admin"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Xác nhận", callback_data=f"approve_withdraw_{request_id}"),
            InlineKeyboardButton("❌ Từ chối", callback_data=f"reject_withdraw_{request_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_menu():
    keyboard = [[InlineKeyboardButton("🔙 Quay lại menu", callback_data="menu_main")]]
    return InlineKeyboardMarkup(keyboard)
def get_withdraw_bank_menu(user_id):
    """Menu quản lý tài khoản rút tiền"""
    banks = user_withdraw_banks.get(str(user_id), [])
    
    keyboard = []
    
    if banks:
        keyboard.append([InlineKeyboardButton("📋 DANH SÁCH TÀI KHOẢN", callback_data="noop")])
        for i, bank in enumerate(banks):
            keyboard.append([
                InlineKeyboardButton(
                    f"🏦 {bank['bank']} - {bank['stk'][-6:]} - {bank['name'][:15]}", 
                    callback_data=f"select_withdraw_bank_{i}"
                )
            ])
        keyboard.append([InlineKeyboardButton("➕ THÊM TÀI KHOẢN", callback_data="add_withdraw_bank")])
        keyboard.append([InlineKeyboardButton("❌ XÓA TÀI KHOẢN", callback_data="delete_withdraw_bank")])
    else:
        keyboard.append([InlineKeyboardButton("➕ THÊM TÀI KHOẢN RÚT TIỀN", callback_data="add_withdraw_bank")])
    
    keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data="menu_withdraw")])
    
    return InlineKeyboardMarkup(keyboard)
# ========== HÀM ĐĂNG NHẬP ==========
def login_and_get_cookies():
    global session, csrf_token, is_logged_in
    print("🔐 Đang đăng nhập bằng Selenium headless...")
    
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # ========== THÊM: USER-AGENT CHO CHROME ==========
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 Chrome/148.0.0.0 Mobile Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(f"{BASE_URL}/login")
        
        # Chờ trang tải xong
        wait = WebDriverWait(driver, 10)
        
        # Nhập email
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_input.clear()
        email_input.send_keys(EMAIL)
        
        # Nhập password
        password_input = driver.find_element(By.NAME, "password")
        password_input.clear()
        password_input.send_keys(PASSWORD)
        
        # Tìm nút đăng nhập
        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
        login_btn.click()
        
        # Chờ chuyển hướng
        wait.until(EC.url_contains("/dashboard"))
        time.sleep(2)
        
        # ========== SỬA: LƯU COOKIES ĐẦY ĐỦ (CẢ DOMAIN VÀ PATH) ==========
        for cookie in driver.get_cookies():
            session.cookies.set(
                cookie['name'],
                cookie['value'],
                domain=cookie.get('domain', 'veloragame.com'),
                path=cookie.get('path', '/')
            )
            print(f"🍪 Cookie: {cookie['name']} = {cookie['value'][:30]}...")
        
        # ========== SỬA: THÊM HEADERS KHI LẤY CSRF TOKEN ==========
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'vi-VN,vi;q=0.9'
        }
        
        resp = session.get(f"{BASE_URL}/virtual-accounts/create", headers=headers, timeout=30)
        match = re.search(r'name="_token"\s+value="([^"]+)"', resp.text)
        if match:
            csrf_token = match.group(1)
            print(f"✅ Lấy CSRF token: {csrf_token[:50]}...")
        else:
            # ========== THÊM: THỬ TÌM TOKEN Ở DẠNG KHÁC ==========
            match2 = re.search(r'csrf-token" content="([^"]+)"', resp.text)
            if match2:
                csrf_token = match2.group(1)
                print(f"✅ Lấy CSRF token (meta tag): {csrf_token[:50]}...")
        
        # ========== THÊM: LƯU SESSION VÀO FILE ==========
        save_session()
        
        is_logged_in = True
        print("✅ Đăng nhập thành công!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi đăng nhập: {e}")
        if driver:
            driver.save_screenshot("login_error.png")
            print("📸 Đã lưu screenshot: login_error.png")
        return False
    finally:
        if driver:
            driver.quit()
def refresh_session_with_remember_cookie():
    """Tự động đăng nhập lại bằng remember_web cookie (không cần Selenium)"""
    global session, is_logged_in, csrf_token
    
    # ========== THÊM: HEADERS CHO REQUEST ==========
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U) AppleWebKit/537.36 Chrome/148.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        'Accept-Language': 'vi-VN,vi;q=0.9',
        'Cache-Control': 'max-age=0',
        'Referer': f"{BASE_URL}/dashboard"
    }
    
    try:
        # Tìm remember cookie trong session
        remember_cookie = None
        remember_cookie_name = None
        
        for cookie in session.cookies:
            if cookie.name.startswith('remember_web'):
                remember_cookie = cookie.value
                remember_cookie_name = cookie.name
                break
        
        if not remember_cookie:
            print("⚠️ Không tìm thấy remember cookie, cần đăng nhập lại bằng Selenium")
            return False
        
        print(f"🍪 Tìm thấy remember cookie: {remember_cookie_name[:30]}...")
        
        # ========== SỬA: TẠO SESSION MỚI VỚI ĐẦY ĐỦ COOKIE ==========
        new_session = requests.Session()
        
        # Set remember cookie
        new_session.cookies.set(
            remember_cookie_name,
            remember_cookie,
            domain='veloragame.com',
            path='/'
        )
        
        # ========== THÊM: COPY CÁC COOKIE KHÁC ==========
        for cookie in session.cookies:
            if not cookie.name.startswith('remember_web'):
                new_session.cookies.set(
                    cookie.name,
                    cookie.value,
                    domain=cookie.domain or 'veloragame.com',
                    path=cookie.path or '/'
                )
        
        # Thử truy cập dashboard với headers đầy đủ
        resp = new_session.get(
            f"{BASE_URL}/dashboard", 
            headers=headers,
            timeout=30, 
            allow_redirects=False
        )
        
        # ========== SỬA: KIỂM TRA KỸ HƠN ==========
        if resp.status_code == 200:
            # Kiểm tra nội dung không phải trang login
            if 'Đăng nhập' not in resp.text and 'login' not in resp.text.lower():
                # Thành công, cập nhật session mới
                session = new_session
                
                # Lấy CSRF token mới với headers đầy đủ
                resp2 = session.get(
                    f"{BASE_URL}/virtual-accounts/create", 
                    headers=headers,
                    timeout=30
                )
                
                # Thử nhiều cách tìm token
                match = re.search(r'name="_token"\s+value="([^"]+)"', resp2.text)
                if not match:
                    match = re.search(r'csrf-token" content="([^"]+)"', resp2.text)
                if not match:
                    match = re.search(r'<input[^>]*name="_token"[^>]*value="([^"]+)"', resp2.text)
                
                if match:
                    csrf_token = match.group(1)
                    print(f"✅ Lấy CSRF token mới: {csrf_token[:30]}...")
                else:
                    print("⚠️ Không lấy được CSRF token mới")
                
                # ========== THÊM: LƯU SESSION VÀO FILE ==========
                save_session()
                
                is_logged_in = True
                print("✅ Đã refresh session thành công bằng remember cookie (không cần Selenium)")
                return True
        
        # Xử lý redirect
        if resp.status_code == 302:
            location = resp.headers.get('Location', '')
            if 'login' in location:
                print("⚠️ Remember cookie đã hết hạn, cần đăng nhập lại bằng Selenium")
                return False
        
        print("⚠️ Refresh bằng remember cookie thất bại, cần đăng nhập lại bằng Selenium")
        return False
        
    except Exception as e:
        print(f"❌ Lỗi refresh session: {e}")
        return False
    
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retry():
    """
    Tạo session với cơ chế retry tự động
    Giúp tăng độ ổn định khi network không ổn định
    """
    session = requests.Session()
    
    # Cấu hình retry
    retry_strategy = Retry(
        total=3,                      # Tổng số lần retry
        backoff_factor=1,             # Thời gian chờ giữa các lần retry: 1s, 2s, 4s
        status_forcelist=[429, 500, 502, 503, 504],  # Retry khi gặp các status code này
        allowed_methods=["HEAD", "GET", "OPTIONS"]    # Chỉ retry với các method này
    )
    
    # Tạo adapter và mount vào session
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    # Set default headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U) AppleWebKit/537.36 Chrome/148.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        'Accept-Language': 'vi-VN,vi;q=0.9'
    })
    
    return session
async def chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Kiểm tra admin
    if not is_admin(user_id):
        await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này!")
        return
    
    # Lấy nội dung tin nhắn
    if not context.args and not update.message.photo:
        await update.message.reply_text(
            "📌 CÁCH DÙNG:\n"
            "/chat <nội dung> - Gửi tin nhắn text đến tất cả user\n"
            "/chat (kèm ảnh) - Gửi ảnh + caption đến tất cả user\n\n"
            "✨ Ví dụ:\n"
            "/chat Thông báo: Bảo trì hệ thống lúc 22h\n"
            "(gửi ảnh kèm caption)"
        )
        return
    
    # Lấy caption (nội dung text)
    caption = ' '.join(context.args) if context.args else None
    if update.message.caption:
        caption = update.message.caption
    
    # Lấy ảnh (nếu có)
    photo = update.message.photo[-1] if update.message.photo else None
    
    # Lấy tất cả user đã duyệt
    target_users = approved_users.copy() if approved_users else list(user_balance.keys())
    
    if not target_users:
        await update.message.reply_text("📭 Không có user nào để gửi tin nhắn!")
        return
    
    # Gửi tin nhắn
    success_count = 0
    fail_count = 0
    
    status_msg = await update.message.reply_text(f"⏳ Đang gửi tin nhắn đến {len(target_users)} user...")
    
    for uid in target_users:
        try:
            if photo:
                # Gửi ảnh kèm caption
                await context.bot.send_photo(
                    chat_id=int(uid),
                    photo=photo.file_id,
                    caption=caption
                )
            else:
                # Gửi text
                await context.bot.send_message(
                    chat_id=int(uid),
                    text=caption
                )
            success_count += 1
        except Exception as e:
            fail_count += 1
            print(f"❌ Lỗi gửi cho user {uid}: {e}")
        
        # Delay nhẹ để tránh spam
        await asyncio.sleep(0.1)
    
    # Thông báo kết quả
    await status_msg.edit_text(
        f"✅ ĐÃ GỬI XONG!\n\n"
        f"📨 Thành công: {success_count} user\n"
        f"❌ Thất bại: {fail_count} user\n"
        f"📝 Nội dung: {caption if caption else '(không có caption)'}"
    )
async def check_orders_loop():
    global tracking_orders, user_balance, is_logged_in
    
    # ========== THÊM: HEADERS CHUẨN NHƯ CURL ==========
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,en-US;q=0.6',
        'cache-control': 'max-age=0',
        'referer': 'https://veloragame.com/orders',
        'sec-ch-ua': '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 Chrome/148.0.0.0 Mobile Safari/537.36'
    }
    
    while True:
        try:
            if not is_logged_in:
                print("⚠️ Chưa đăng nhập, đang đăng nhập lại...")
                # Thử dùng remember cookie trước (nhanh)
                if not refresh_session_with_remember_cookie():
                    # Nếu thất bại, mới dùng Selenium
                    await asyncio.to_thread(login_and_get_cookies)
                await asyncio.sleep(5)
                continue
            
            # ========== SỬA: THÊM HEADERS VÀ allow_redirects=False ==========
            response = await asyncio.to_thread(
                session.get, 
                f"{BASE_URL}/orders", 
                headers=headers,                    # ✅ THÊM HEADERS
                timeout=60,
                allow_redirects=False               # ✅ KHÔNG tự động redirect
            )
            
            # ========== SỬA: XỬ LÝ 302 ĐÚNG CÁCH ==========
            if response.status_code == 302:
                print("⚠️ Session hết hạn (302), đăng nhập lại...")
                
                # ✅ LƯU COOKIE TỪ RESPONSE TRƯỚC KHI ĐĂNG NHẬP LẠI
                if response.cookies:
                    session.cookies.update(response.cookies)
                    print(f"🍪 Đã lưu {len(response.cookies)} cookie từ response 302")
                
                is_logged_in = False
                
                # ✅ THỬ DÙNG REMEMBER COOKIE
                if not refresh_session_with_remember_cookie():
                    await asyncio.to_thread(login_and_get_cookies)
                continue
            
            # ========== SỬA: CẬP NHẬT COOKIE KHI THÀNH CÔNG ==========
            if response.status_code == 200:
                html = response.text
                
                # Cập nhật cookie mới từ response
                if response.cookies:
                    session.cookies.update(response.cookies)
                    print(f"🍪 Đã cập nhật {len(response.cookies)} cookie")
                
                # Kiểm tra nếu bị redirect về login (phát hiện session chết)
                if 'Đăng nhập' in html or 'Khu vực quản trị' in html or 'login' in html.lower():
                    print("⚠️ Phát hiện trang login, session đã hết hạn!")
                    is_logged_in = False
                    
                    # ✅ THỬ DÙNG REMEMBER COOKIE TRƯỚC
                    if not refresh_session_with_remember_cookie():
                        await asyncio.to_thread(login_and_get_cookies)
                    continue
                
                print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Đã lấy dữ liệu orders (length: {len(html)} chars)")
                await check_for_new_payments_async(html)
                
            else:
                print(f"⚠️ Lỗi {response.status_code} - {response.reason}")
                
        except asyncio.TimeoutError:
            print(f"⚠️ [{datetime.now().strftime('%H:%M:%S')}] Timeout, thử lại sau 15 giây...")
            await asyncio.sleep(15)
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            import traceback
            traceback.print_exc()                     # ✅ THÊM: IN CHI TIẾT LỖI
            await asyncio.sleep(15)
        
        await asyncio.sleep(30)                       # ✅ GIỮ NGUYÊN 10s
def is_session_valid():
    """Kiểm tra session có còn hiệu lực không"""
    try:
        resp = session.get(f"{BASE_URL}/dashboard", timeout=10, allow_redirects=False)
        return resp.status_code == 200
    except:
        return False
def is_order_expired(created_at_str):
    """Kiểm tra đơn có quá 24 giờ hay không"""
    from datetime import datetime
    try:
        created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
        hours_ago = (datetime.now() - created_at).total_seconds() / 3600
        return hours_ago >= 24  # True nếu quá 24 giờ
    except:
        return False
async def refresh_session_periodically():
    """Định kỳ refresh session để tránh hết hạn"""
    while True:
        await asyncio.sleep(1800)  # 30 phút
        print("🔄 Đang refresh session định kỳ...")
        await asyncio.to_thread(login_and_get_cookies)
        print("✅ Refresh session thành công")
async def check_for_new_payments_async(html):
    global tracking_orders, user_balance
    
    from datetime import datetime
    
    print("🔍 Đang kiểm tra đơn hàng có tiền về...")
    
    # Lấy danh sách order_code từ HTML
    order_codes_in_html = set(re.findall(r'ORD-[A-Z0-9]{25}', html))
    
    # ========== 1. KIỂM TRA TRONG DANH SÁCH ORDERS (TUẦN TỰ - NHANH) ==========
    for order_code, order_info in tracking_orders.items():
        # Bỏ qua đơn quá 24 giờ
        created_at = order_info.get('created_at')
        if created_at:
            try:
                created_time = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                hours_ago = (datetime.now() - created_time).total_seconds() / 3600
                if hours_ago >= 24:
                    print(f"⏰ Đơn {order_code} đã quá 24 giờ ({hours_ago:.1f}h), bỏ qua kiểm tra")
                    tracking_orders[order_code]['status'] = 'expired'
                    save_tracking()
                    continue
            except:
                pass
        
        # Kiểm tra nếu đã gửi thông báo trong 30 giây gần đây (tránh spam)
        last_notify = order_info.get('last_notify_time')
        if last_notify:
            try:
                last_time = datetime.strptime(last_notify, '%Y-%m-%d %H:%M:%S')
                if (datetime.now() - last_time).seconds < 30:
                    print(f"⏰ Bỏ qua {order_code} - đã gửi thông báo trong 30 giây")
                    continue
            except:
                pass
        
        actual_amount = None
        
        if order_code in html:
            patterns = [
                r'<td data-label="Số tiền">([\d.]+)</td>',
                r'<td data-label="Số tiền">([\d,]+)</td>',
                r'<td data-label="Số tiền">(\d+)</td>',
                r'Số tiền["\']?>([\d.,]+)',
                r'(\d{1,3}(?:[.,]\d{3})*)\s*(?:VND|đ|vnd)',
            ]
            
            idx = html.find(order_code)
            if idx != -1:
                surrounding = html[max(0, idx-500):min(len(html), idx+500)]
                
                for pattern in patterns:
                    match = re.search(pattern, surrounding, re.IGNORECASE | re.DOTALL)
                    if match:
                        amount_str = match.group(1).replace('.', '').replace(',', '')
                        try:
                            actual_amount = int(amount_str)
                            if actual_amount > 0:
                                print(f"💰 Tìm thấy {order_code}: {actual_amount:,} VND")
                                break
                        except:
                            continue
        
        if actual_amount is not None and actual_amount > 0:
            if actual_amount <= 1000:
                print(f"⚠️ Bỏ qua đơn {order_code} với số tiền {actual_amount:,} VND (tiền mặc định)")
                continue
            
            await process_payment(order_code, order_info, actual_amount)
    
    # ========== 2. KIỂM TRA TRANG CHI TIẾT (SONG SONG) ==========
    # Tạo danh sách các đơn cần check chi tiết
    pending_orders = [
        (code, info) for code, info in tracking_orders.items()
        if info.get('status') != 'paid'
    ]
    
    if pending_orders:
        print(f"🚀 Đang kiểm tra song song {len(pending_orders)} đơn qua trang chi tiết...")
        
        # Tạo task cho từng đơn
        tasks = [check_order_detail_parallel(code, info) for code, info in pending_orders]
        
        # Chạy TẤT CẢ cùng lúc
        await asyncio.gather(*tasks)
        
        print(f"✅ Đã kiểm tra xong {len(pending_orders)} đơn")
    
    save_tracking()
    save_balance()


async def check_order_detail_parallel(order_code, order_info):
    """Kiểm tra chi tiết 1 đơn (dùng cho song song)"""
    from datetime import datetime
    
    if order_info.get('status') == 'paid':
        return None
    
    # Bỏ qua đơn quá 24 giờ
    created_at = order_info.get('created_at')
    if created_at:
        try:
            created_time = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            hours_ago = (datetime.now() - created_time).total_seconds() / 3600
            if hours_ago >= 24:
                print(f"⏰ Đơn {order_code} đã quá 24 giờ, bỏ qua")
                tracking_orders[order_code]['status'] = 'expired'
                save_tracking()
                return None
        except:
            pass
    
    detail_url = f"{BASE_URL}/virtual-accounts/views/{order_code}"
    try:
        detail_response = await asyncio.to_thread(session.get, detail_url, timeout=30)
        if detail_response.status_code == 200:
            detail_html = detail_response.text
            
            patterns_detail = [
                r'Số tiền.*?(\d{1,3}(?:[.,]\d{3})*)\s*(?:VND|đ|vnd)',
                r'<td[^>]*class="[^"]*amount[^"]*"[^>]*>([\d.,]+)<',
                r'class="[^"]*price[^"]*"[^>]*>([\d.,]+)<',
                r'(\d{1,3}(?:[.,]\d{3})*)\s*(?:VND|đ)',
                r'([\d.,]+)\s*(?:VND|đ)',
            ]
            
            for pattern in patterns_detail:
                amount_match = re.search(pattern, detail_html, re.DOTALL | re.IGNORECASE)
                if amount_match:
                    amount_str = amount_match.group(1).replace('.', '').replace(',', '')
                    try:
                        actual_amount = int(amount_str)
                        if actual_amount > 0:
                            if actual_amount <= 1000:
                                print(f"⚠️ Bỏ qua đơn {order_code} với số tiền {actual_amount:,} VND (tiền mặc định)")
                                return None
                            
                            print(f"🔍 Phát hiện đơn {order_code} qua trang chi tiết: {actual_amount:,} VND")
                            await process_payment(order_code, order_info, actual_amount)
                            return True
                    except:
                        continue
            
            # Nếu có trạng thái xác nhận nhưng không tìm thấy số tiền
            if 'Xác nhận' in detail_html or 'is-success' in detail_html:
                print(f"⚠️ Đơn {order_code} có trạng thái xác nhận, lấy số tiền mặc định: {order_info.get('amount', 0)} VND")
                default_amount = order_info.get('amount', 0)
                if default_amount > 0 and default_amount > 1000:
                    await process_payment(order_code, order_info, default_amount)
                    return True
                    
    except Exception as e:
        print(f"⚠️ Lỗi check chi tiết {order_code}: {e}")
    
    return False
async def check_orders_parallel(html):
    """Kiểm tra tất cả đơn song song"""
    global tracking_orders
    
    # Lấy danh sách đơn cần kiểm tra (chưa paid)
    pending_orders = [
        (code, info) for code, info in tracking_orders.items() 
        if info.get('status') != 'paid'
    ]
    
    if not pending_orders:
        return
    
    print(f"🚀 Đang kiểm tra song song {len(pending_orders)} đơn...")
    
    # Tạo task cho từng đơn (dùng chính hàm check_single_order của bạn)
    tasks = [check_single_order(code, info) for code, info in pending_orders]
    
    # Chạy TẤT CẢ cùng lúc
    await asyncio.gather(*tasks)
    
    print(f"✅ Đã kiểm tra xong {len(pending_orders)} đơn")
async def check_single_order(order_code, order_info):
    """Kiểm tra trạng thái đơn hàng qua trang chi tiết"""
    detail_url = f"{BASE_URL}/virtual-accounts/views/{order_code}"
    try:
        detail_response = await asyncio.to_thread(session.get, detail_url, timeout=30)
        if detail_response.status_code == 200:
            detail_html = detail_response.text
            
            # Kiểm tra nếu có trạng thái ACTIVE và số tiền
            if 'ACTIVE' in detail_html or 'Xác nhận' in detail_html:
                # Tìm số tiền
                amount_match = re.search(r'Số tiền.*?(\d{1,3}(?:,\d{3})*)\s*đ', detail_html, re.DOTALL)
                if not amount_match:
                    amount_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*đ', detail_html)
                
                if amount_match:
                    amount_str = amount_match.group(1).replace(',', '')
                    actual_amount = int(amount_str)
                    if actual_amount > 0:
                        print(f"💰 Phát hiện đơn {order_code} qua trang chi tiết: {actual_amount:,} VND")
                        await process_payment(order_code, order_info, actual_amount)
                        return True
    except Exception as e:
        print(f"⚠️ Lỗi check đơn {order_code}: {e}")
    return False
async def process_payment(order_code, order_info, actual_amount):
    global tracking_orders, user_balance
    
    user_id = str(order_info['user_id'])
    
    # Khởi tạo nếu chưa có
    if user_id not in user_balance:
        user_balance[user_id] = {
            'balance': 0,
            'total_orders': 0,
            'last_update': '',
            'history': [],
            'withdraw_history': []
        }
    
    old_balance = user_balance[user_id]['balance']
    new_balance = old_balance + actual_amount
    
    # Cập nhật số dư
    user_balance[user_id]['balance'] = new_balance
    user_balance[user_id]['total_orders'] += 1
    user_balance[user_id]['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Lưu lịch sử
    user_balance[user_id]['history'].append({
        'order_code': order_code,
        'amount': actual_amount,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'customer_name': order_info.get('customer_name', 'N/A')
    })
    
    # Đếm số lần nhận tiền
    if 'paid_count' not in tracking_orders[order_code]:
        tracking_orders[order_code]['paid_count'] = 0
    tracking_orders[order_code]['paid_count'] += 1
    
    # Cập nhật trạng thái đơn hàng
    tracking_orders[order_code]['status'] = 'paid'
    tracking_orders[order_code]['paid_amount'] = actual_amount
    tracking_orders[order_code]['paid_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"💰 {order_code} - {actual_amount:,} VND (lần thứ {tracking_orders[order_code]['paid_count']})")
    print(f"   User {user_id}: {old_balance:,} → {new_balance:,} VND")
    
    # Gửi thông báo bất đồng bộ
    await send_telegram_notification_async(user_id, order_code, actual_amount, order_info, new_balance)
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Tạo session với retry
def create_session_with_retry():
    session = requests.Session()
    retry = Retry(
        total=3,
        read=3,
        connect=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
async def addmoney_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Bạn không có quyền!")
        return
    
    if len(context.args) != 2:
        await update.message.reply_text("📌 CÁCH DÙNG:\n/addmoney <user_id> <số_tiền>")
        return
    
    target_id = str(context.args[0])
    amount = int(context.args[1])
    
    if target_id not in user_balance:
        user_balance[target_id] = {
            'balance': 0,
            'total_orders': 0,
            'last_update': '',
            'history': [],
            'withdraw_history': []
        }
    
    old_balance = user_balance[target_id]['balance']
    user_balance[target_id]['balance'] += amount
    user_balance[target_id]['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    save_balance()  # Lưu vào file
    
    await update.message.reply_text(
        f"<tg-emoji emoji-id='5440547189669516347'>✅</tg-emoji> Đã cộng {amount:,.0f} VND cho user {target_id}\n\n"
        f"💰 Số dư cũ: {old_balance:,.0f} VND\n"
        f"💵 Số dư mới: {user_balance[target_id]['balance']:,.0f} VND",
        parse_mode='HTML'
    )
# Trong login_and_get_cookies, thay session = create_session_with_retry()
async def check_for_new_payments(html):
    global tracking_orders, user_balance
    
    # Lấy danh sách order_code từ HTML
    order_codes_in_html = set(re.findall(r'ORD-[A-Z0-9]{25}', html))
    
    for order_code, order_info in tracking_orders.items():
        if order_info.get('status') == 'paid':
            continue
        
        actual_amount = None
        
        # CHỈ TÌM TRONG DANH SÁCH ORDERS (BỎ CÁCH 2)
        if order_code in html:
            pattern = rf'href="[^"]*{re.escape(order_code)}[^"]*".*?'
            pattern += r'<td data-label="Số tiền">([\d.]+)</table>'
            match = re.search(pattern, html, re.DOTALL)
            if match:
                amount_str = match.group(1).replace('.', '')
                actual_amount = int(amount_str)
        
        if actual_amount is not None and actual_amount > 0:
            user_id = str(order_info['user_id'])
            
            # Khởi tạo nếu chưa có
            if user_id not in user_balance:
                user_balance[user_id] = {
                    'balance': 0,
                    'total_orders': 0,
                    'last_update': '',
                    'history': [],
                    'withdraw_history': []
                }
            
            # CỘNG TIỀN VÀO BALANCE
            old_balance = user_balance[user_id]['balance']
            new_balance = old_balance + actual_amount
            
            user_balance[user_id]['balance'] = new_balance
            user_balance[user_id]['total_orders'] += 1
            user_balance[user_id]['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Lưu lịch sử
            user_balance[user_id]['history'].append({
                'order_code': order_code,
                'amount': actual_amount,
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'customer_name': order_info.get('customer_name', 'N/A')
            })
            
            # Cập nhật trạng thái đơn hàng
            tracking_orders[order_code]['status'] = 'paid'
            tracking_orders[order_code]['paid_amount'] = actual_amount
            tracking_orders[order_code]['paid_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"💰 {order_code} - {actual_amount:,} VND")
            print(f"   User {user_id}: {old_balance:,} → {new_balance:,} VND")
            
            # Gửi thông báo
            asyncio.create_task(send_telegram_notification_async(user_id, order_code, actual_amount, order_info, new_balance))
    
    save_tracking()
    save_balance()
async def send_telegram_notification_async(user_id, order_code, amount, order_info, new_balance):
    """Gửi thông báo khi có tiền về - bất đồng bộ, gửi song song"""
    try:
        # Cập nhật thời gian gửi thông báo cuối cùng
        tracking_orders[order_code]['last_notify_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_tracking()
        
        # 1. TIN NHẮN CHO USER
        user_message = (
            f"<tg-emoji emoji-id='5224257782013769471'>💰</tg-emoji> CÓ TIỀN VỀ! <tg-emoji emoji-id='5224257782013769471'>💰</tg-emoji>\n\n"
            f"<tg-emoji emoji-id='5285265460286217966'>✅</tg-emoji> Đơn hàng: {order_code}\n"
            f"<tg-emoji emoji-id='5364109867156001787'>👤</tg-emoji> Khách hàng: {order_info.get('customer_name', 'N/A')}\n"
            f"<tg-emoji emoji-id='5264895611517300926'>🏦</tg-emoji> Ngân hàng: {order_info.get('bank', 'MSB')}\n"
            f"<tg-emoji emoji-id='5267300544094948794'>💳</tg-emoji> STK: {order_info.get('stk', 'N/A')}\n"
            f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> Số tiền: {amount:,.0f} VND\n"
            f"<tg-emoji emoji-id='5440621591387980068'>🕐</tg-emoji> Thời gian: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}\n\n"
            f"<tg-emoji emoji-id='5028746137645876535'>📊</tg-emoji> Số dư hiện tại: {new_balance:,.0f} VND"
        )
        
        # 2. TIN NHẮN CHO ADMIN
        admin_message = (
            f"<tg-emoji emoji-id='5224257782013769471'>💰</tg-emoji> CÓ TIỀN VỀ! <tg-emoji emoji-id='5224257782013769471'>💰</tg-emoji>\n\n"
            f"<tg-emoji emoji-id='5285265460286217966'>✅</tg-emoji> Đơn hàng: {order_code}\n"
            f"<tg-emoji emoji-id='5364109867156001787'>👤</tg-emoji> User ID: {user_id}\n"
            f"<tg-emoji emoji-id='5364109867156001787'>👤</tg-emoji> Khách hàng: {order_info.get('customer_name', 'N/A')}\n"
            f"<tg-emoji emoji-id='5264895611517300926'>🏦</tg-emoji> Ngân hàng: {order_info.get('bank', 'MSB')}\n"
            f"<tg-emoji emoji-id='5267300544094948794'>💳</tg-emoji> STK: {order_info.get('stk', 'N/A')}\n"
            f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> Số tiền: {amount:,.0f} VND\n"
            f"<tg-emoji emoji-id='5028746137645876535'>📊</tg-emoji> Số dư user: {new_balance:,.0f} VND\n"
            f"<tg-emoji emoji-id='5440621591387980068'>🕐</tg-emoji> Thời gian: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}"
        )
        
        # 3. TẠO BOT VÀ GỬI ĐỒNG THỜI
        bot = Bot(token=BOT_TOKEN)
        tasks = []
        
        # Gửi cho user
        tasks.append(bot.send_message(
            chat_id=int(user_id), 
            text=user_message,
            parse_mode='HTML'
        ))
        
        # Gửi cho tất cả admin
        for admin_id in ADMIN_IDS:
            tasks.append(bot.send_message(
                chat_id=admin_id, 
                text=admin_message,
                parse_mode='HTML'
            ))
        
        # GỬI TẤT CẢ CÙNG LÚC
        await asyncio.gather(*tasks)
        
        paid_count = tracking_orders[order_code].get('paid_count', 1)
        print(f"📨 Đã gửi thông báo lần thứ {paid_count} đến user {user_id} và {len(ADMIN_IDS)} admin")
            
    except Exception as e:
        print(f"❌ Lỗi gửi: {e}")

async def send_payment_notification(user_id, order_code, amount, order_info, new_balance):
    try:
        bot = Bot(token=BOT_TOKEN)
        message = (
            f"<tg-emoji emoji-id='5224257782013769471'>💰</tg-emoji> CÓ TIỀN VỀ! <tg-emoji emoji-id=''>💰</tg-emoji>\n\n"
            f"<tg-emoji emoji-id='5440547189669516347'>✅</tg-emoji> Đơn hàng: {order_code}\n"
            f"<tg-emoji emoji-id='5364109867156001787'>👤</tg-emoji> Khách hàng: {order_info.get('customer_name', 'N/A')}\n"
            f"<tg-emoji emoji-id='5264895611517300926'>🏦</tg-emoji> Ngân hàng: {order_info.get('bank', 'MSB')}\n"
            f"<tg-emoji emoji-id='5267300544094948794'>💳</tg-emoji> STK: {order_info.get('stk', 'N/A')}\n"
            f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> Số tiền: {amount:,.0f} VND\n"
            f"<tg-emoji emoji-id='5440621591387980068'>🕐</tg-emoji> Thời gian: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}\n\n"
            f"<tg-emoji emoji-id='5028746137645876535'>📊</tg-emoji> Số dư hiện tại: {new_balance:,.0f} VND"
        )
        await bot.send_message(
            chat_id=int(user_id), 
            text=message,
            parse_mode='HTML'  # ✅ THÊM DÒNG NÀY
        )
        print(f"📨 Đã gửi thông báo đến user {user_id} - {amount:,} VND")
    except Exception as e:
        print(f"❌ Lỗi gửi: {e}")
# ========== HÀM TẠO TÀI KHOẢN ẢO ==========
async def create_virtual_account(customer_name, bank_name="MSB", user_id=None):
    global session, csrf_token, is_logged_in
    
    print("="*60)
    print(f"🔍 [DEBUG] BẮT ĐẦU TẠO TÀI KHOẢN")
    print(f"   👤 Tên KH: {customer_name}")
    print(f"   🏦 Ngân hàng: {bank_name}")
    print(f"   🆔 User ID: {user_id}")
    print(f"   🔐 is_logged_in: {is_logged_in}")
    print("="*60)
    
    if not is_logged_in or not csrf_token:
        print("⚠️ Chưa đăng nhập, đang đăng nhập lại...")
        if not login_and_get_cookies():
            return {'success': False, 'error': 'Đăng nhập thất bại'}
        print("✅ Đăng nhập lại thành công!")
    
    # Tạo mã đơn hàng ngẫu nhiên
    order_code = f"ORD-{''.join(random.choices(string.ascii_uppercase + string.digits, k=25))}"
    print(f"🎲 Mã đơn hàng: {order_code}")
    
    try:
        # Gửi request tạo
        url = f"{BASE_URL}/virtual-accounts"
        print(f"📤 URL: {url}")
        
        data = {
            '_token': csrf_token,
            'bank_name': bank_name,
            'order_code': order_code,
            'napas_display_name': customer_name.upper(),
            'amount': '1000',
            'collaborator_id': '1326',
            'expires_in_days': '1'
        }
        print(f"📦 Data: {data}")
        
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': BASE_URL,
            'referer': f"{BASE_URL}/virtual-accounts/create",
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"📤 Đang gửi POST request...")
        response = session.post(url, data=data, headers=headers, timeout=30, allow_redirects=True)
        
        # Cập nhật cookie từ response (quan trọng để giữ session đồng bộ)
        if response.cookies:
            session.cookies.update(response.cookies)
            print(f"🍪 Đã cập nhật session cookie từ response")
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📍 Final URL: {response.url}")
        print(f"📄 Response length: {len(response.text)} ký tự")
        
        # Tìm STK trong response
        stk = None
        bank_code = None
        account_name = None
        
        # Tìm URL VietQR
        urls = re.findall(r'https?://[^\s"\']+', response.text)
        print(f"🔗 Tìm thấy {len(urls)} URL trong response")
        
        for url in urls:
            if 'vietqr' in url or 'img.vietqr.io' in url:
                print(f"✅ Tìm thấy VietQR URL: {url[:100]}...")
                
                # Lấy STK từ URL
                match = re.search(r'/([A-Z]{2,4})-(\d{10,20})-', url)
                if match:
                    bank_code = match.group(1)
                    stk = match.group(2)
                    print(f"✅ Tìm thấy STK: {stk}")
                    print(f"✅ Ngân hàng: {bank_code}")
                
                # Lấy thông tin từ query
                if '?' in url:
                    parsed = urlparse(url)
                    params = parse_qs(parsed.query)
                    if 'accountName' in params:
                        account_name = params['accountName'][0].replace('%20', ' ')
                        print(f"👤 Chủ TK: {account_name}")
                break
        
        if stk:
            print("="*60)
            print(f"✅ THÀNH CÔNG! STK: {stk}")
            print("="*60)
            
            # LƯU ĐƠN HÀNG ĐỂ THEO DÕI
            if user_id:
                tracking_orders[order_code] = {
                    'user_id': user_id,
                    'customer_name': customer_name.upper(),
                    'bank': bank_code or bank_name,
                    'stk': stk,
                    'amount': 1000,
                    'status': 'pending',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                save_tracking()
                print(f"📝 Đã thêm đơn hàng {order_code} vào danh sách theo dõi")
                
                # ========== 1. GỬI CHO USER (BẤT ĐỒNG BỘ) ==========
                try:
                    user_message = (
                        f"<tg-emoji emoji-id='5440547189669516347'>✅</tg-emoji> <b>TẠO THÀNH CÔNG!</b>\n\n"
                        f"<tg-emoji emoji-id='5364109867156001787'>👤</tg-emoji> <b>Tên:</b> {customer_name.upper()}\n"
                        f"<tg-emoji emoji-id='5264895611517300926'>🏦</tg-emoji> <b>Ngân hàng:</b> {bank_code or bank_name}\n"
                        f"<tg-emoji emoji-id='5267300544094948794'>💳</tg-emoji> <b>STK:</b> <code>{stk}</code>\n"
                        f"<tg-emoji emoji-id='5226929552319594190'>🔢</tg-emoji> <b>Mã đơn:</b> <code>{order_code}</code>\n\n"
                        f"<tg-emoji emoji-id='5422439311196834318'>💡</tg-emoji> <b>Lưu ý:</b> Bot sẽ tự động thông báo khi có tiền chuyển đến!"
                    )
                    bot = Bot(token=BOT_TOKEN)
                    await bot.send_message(
                        chat_id=int(user_id), 
                        text=user_message, 
                        parse_mode='HTML'  # ✅ ĐỔI TỪ Markdown SANG HTML
                    )
                    print(f"📨 Đã gửi STK cho user {user_id}")
                except Exception as e:
                    print(f"❌ Lỗi gửi user: {e}")
                
                # ========== 2. GỬI CHO ADMIN (BẤT ĐỒNG BỘ, SONG SONG) ==========
                try:
                    admin_message = (
                        f"<tg-emoji emoji-id='5213394688735717942'>🆕</tg-emoji> USER VỪA TẠO ĐƠN MỚI!\n\n"
                        f"<tg-emoji emoji-id='5364109867156001787'>👤</tg-emoji> User ID: {user_id}\n"
                        f"<tg-emoji emoji-id='5317051465271881270'>📛</tg-emoji> Tên KH: {customer_name.upper()}\n"
                        f"<tg-emoji emoji-id='5264895611517300926'>🏦</tg-emoji> Ngân hàng: {bank_code or bank_name}\n"
                        f"<tg-emoji emoji-id='5267300544094948794'>💳</tg-emoji> STK: {stk}\n"
                        f"<tg-emoji emoji-id='5226929552319594190'>🔢</tg-emoji> Mã đơn: {order_code}\n"
                    )
                    
                    bot = Bot(token=BOT_TOKEN)
                    tasks = []
                    for admin_id in ADMIN_IDS:
                        tasks.append(bot.send_message(
                            chat_id=admin_id, 
                            text=admin_message,
                            parse_mode='HTML'  # ✅ THÊM DÒNG NÀY
                        ))
                    
                    await asyncio.gather(*tasks)
                    print(f"📨 Đã gửi thông báo tạo đơn đến {len(ADMIN_IDS)} admin")
                except Exception as e:
                    print(f"❌ Lỗi gửi thông báo admin: {e}")
            
            return {
                'success': True,
                'stk': stk,
                'name': customer_name.upper(),
                'bank': bank_code or bank_name,
                'account_name': account_name or customer_name.upper(),
                'order_code': order_code
            }
        else:
            print("="*60)
            print("❌ KHÔNG TÌM THẤY STK!")
            print("📄 500 ký tự đầu của response:")
            print("-"*40)
            print(response.text[:500])
            print("-"*40)
            return {'success': False, 'error': 'Không tìm thấy STK trong response'}
            
    except Exception as e:
        print(f"❌ Lỗi tạo: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}
def send_notification_to_admin(user_id, customer_name, bank_name, stk, order_code):
    """Gửi thông báo cho admin khi user tạo đơn thành công"""
    try:
        # Lấy thông tin user
        user_name = "Unknown"
        try:
            # Có thể lấy từ telegram hoặc để mặc định
            user_name = f"User_{user_id}"
        except:
            pass
        
        message = (
            f"🆕 USER VỪA TẠO ĐƠN MỚI!\n\n"
            f"👤 User ID: {user_id}\n"
            f"📛 Tên KH: {customer_name}\n"
            f"🏦 Ngân hàng: {bank_name}\n"
            f"💳 STK: {stk}\n"
            f"🔢 Mã đơn: {order_code}\n"
        )
        
        # Gửi cho tất cả admin
        for admin_id in ADMIN_IDS:
            try:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                requests.post(url, data={'chat_id': admin_id, 'text': message})
                print(f"📨 Đã gửi thông báo tạo đơn đến admin {admin_id}")
            except Exception as e:
                print(f"❌ Lỗi gửi thông báo admin {admin_id}: {e}")
                
    except Exception as e:
        print(f"❌ Lỗi send_notification_to_admin: {e}")

# ========== XỬ LÝ RÚT TIỀN ==========
def create_withdraw_request(user_id, amount, selected_bank_index=None):
    """Tạo yêu cầu rút tiền - có thông tin tài khoản nhận"""
    user_id_str = str(user_id)
    balance = user_balance.get(user_id_str, {}).get('balance', 0)
    
    if amount > balance:
        return {'success': False, 'error': f'Số dư không đủ! Số dư hiện tại: {balance:,.0f} VND'}
    
    if amount < 200000:
        return {'success': False, 'error': 'Số tiền rút tối thiểu là 200,000 VND'}
    
    # Lấy thông tin tài khoản nhận tiền
    withdraw_bank_info = None
    banks = user_withdraw_banks.get(user_id_str, [])
    
    if selected_bank_index is not None and 0 <= selected_bank_index < len(banks):
        withdraw_bank_info = banks[selected_bank_index]
    elif banks:
        withdraw_bank_info = banks[0]  # Mặc định chọn tài khoản đầu tiên
    
    if not withdraw_bank_info:
        return {'success': False, 'error': 'Bạn chưa có tài khoản rút tiền! Vui lòng thêm tài khoản trước.'}
    
    withdraw_info = calculate_withdraw_amount(amount)
    request_id = f"WD_{user_id}_{int(time.time())}"
    
    # TRỪ TIỀN NGAY LẬP TỨC
    old_balance = user_balance[user_id_str]['balance']
    new_balance = old_balance - amount
    
    user_balance[user_id_str]['balance'] = new_balance
    user_balance[user_id_str]['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Lưu lịch sử rút tiền
    if 'withdraw_history' not in user_balance[user_id_str]:
        user_balance[user_id_str]['withdraw_history'] = []
    
    user_balance[user_id_str]['withdraw_history'].append({
        'request_id': request_id,
        'amount': amount,
        'after_fee': withdraw_info['after_fee'],
        'fee': withdraw_info['fee'],
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'pending',
        'withdraw_bank': withdraw_bank_info  # LƯU THÔNG TIN BANK NHẬN
    })
    
    # Lưu yêu cầu rút
    withdraw_requests[request_id] = {
        'user_id': user_id,
        'original_amount': amount,
        'after_fee': withdraw_info['after_fee'],
        'fee': withdraw_info['fee'],
        'status': 'pending',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'user_name': f"User_{user_id}",
        'withdraw_bank': withdraw_bank_info  # THÊM THÔNG TIN BANK NHẬN
    }
    
    save_balance()
    save_withdraw_requests()
    
    print(f"💸 User {user_id} rút {amount:,} VND - Phí: {withdraw_info['fee']:,.0f} VND - Nhận: {withdraw_info['after_fee']:,.0f} VND")
    print(f"   Số dư cũ: {old_balance:,} VND → Số dư mới: {new_balance:,} VND")
    print(f"   Bank nhận: {withdraw_bank_info['bank']} - {withdraw_bank_info['stk']} - {withdraw_bank_info['name']}")
    
    return {
        'success': True,
        'request_id': request_id,
        'withdraw_info': withdraw_info,
        'old_balance': old_balance,
        'new_balance': new_balance,
        'withdraw_bank': withdraw_bank_info
    }

def approve_withdraw(request_id):
    """Admin xác nhận rút tiền - KHÔNG trừ tiền (đã trừ lúc tạo)"""
    if request_id not in withdraw_requests:
        return {'success': False, 'error': 'Không tìm thấy yêu cầu'}
    
    req = withdraw_requests[request_id]
    if req['status'] != 'pending':
        return {'success': False, 'error': 'Yêu cầu đã được xử lý'}
    
    user_id_str = str(req['user_id'])
    
    # KHÔNG KIỂM TRA SỐ DƯ VÀ KHÔNG TRỪ TIỀN (đã trừ lúc tạo yêu cầu)
    # Chỉ cập nhật trạng thái yêu cầu
    
    # Cập nhật trạng thái yêu cầu
    withdraw_requests[request_id]['status'] = 'approved'
    withdraw_requests[request_id]['approved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Cập nhật lịch sử user
    if user_id_str in user_balance:
        for item in user_balance[user_id_str].get('withdraw_history', []):
            if item['request_id'] == request_id:
                item['status'] = 'approved'
                item['approved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                break
    
    save_balance()
    save_withdraw_requests()
    
    print(f"✅ Admin đã xác nhận rút tiền cho user {user_id_str} - Mã: {request_id}")
    
    return {'success': True, 'amount': req['after_fee'], 'user_id': req['user_id']}

def reject_withdraw(request_id):
    """Admin từ chối rút tiền - HOÀN TIỀN LẠI CHO USER"""
    if request_id not in withdraw_requests:
        return {'success': False, 'error': 'Không tìm thấy yêu cầu'}
    
    req = withdraw_requests[request_id]
    if req['status'] != 'pending':
        return {'success': False, 'error': 'Yêu cầu đã được xử lý'}
    
    user_id_str = str(req['user_id'])
    original_amount = req['original_amount']
    
    # HOÀN TIỀN LẠI CHO USER
    if user_id_str in user_balance:
        old_balance = user_balance[user_id_str]['balance']
        user_balance[user_id_str]['balance'] += original_amount
        user_balance[user_id_str]['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Cập nhật lịch sử
        for item in user_balance[user_id_str].get('withdraw_history', []):
            if item['request_id'] == request_id:
                item['status'] = 'rejected'
                item['rejected_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                break
        
        print(f"💰 Hoàn tiền {original_amount:,} VND cho user {user_id_str}")
        print(f"   Số dư cũ: {old_balance:,} VND → Số dư mới: {user_balance[user_id_str]['balance']:,} VND")
    
    # Cập nhật trạng thái yêu cầu
    withdraw_requests[request_id]['status'] = 'rejected'
    withdraw_requests[request_id]['rejected_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    save_balance()
    save_withdraw_requests()
    
    return {'success': True, 'user_id': req['user_id'], 'refund_amount': original_amount}

# ========== TELEGRAM BOT HANDLERS ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if str(user_id) in approved_users:
        await update.message.reply_text(
            f"<tg-emoji emoji-id='5226639745106330551'>🤖</tg-emoji> <b>BOT VIP PROMAX</b>\n\n"
            f"<tg-emoji emoji-id='5461151367559141950'>👋</tg-emoji> Chào mừng bạn đã quay trở lại!\n"
            f"<tg-emoji emoji-id='5422439311196834318'>🆔</tg-emoji> User ID: {user_id}\n\n"
            f"<tg-emoji emoji-id='5397782960512444700'>📌</tg-emoji> Sử dụng menu bên dưới để điều khiển bot",
            parse_mode='HTML',
            reply_markup=get_main_menu(user_id)
        )
        return
    
    if str(user_id) in pending_users:
        await update.message.reply_text(
            f"<tg-emoji emoji-id='5454415424319931791'>⏳</tg-emoji> <b>YÊU CẦU CỦA BẠN ĐANG ĐƯỢC XỬ LÝ!</b>\n\n"
            f"<tg-emoji emoji-id='5364109867156001787'>🆔</tg-emoji> User ID: {user_id}\n"
            f"<tg-emoji emoji-id='5285026110348731539'>📝</tg-emoji> Vui lòng chờ admin duyệt trong ít phút!\n"
            f"<tg-emoji emoji-id='5440621591387980068'>🕐</tg-emoji> Thời gian: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}",
            parse_mode='HTML'
        )
        return
    
    pending_users.append(str(user_id))
    save_pending_users()
    
    # Gửi thông báo cho user
    await update.message.reply_text(
        f"<tg-emoji emoji-id='5285265460286217966'>✅</tg-emoji> <b>ĐÃ GỬI YÊU CẦU DUYỆT!</b>\n\n"
        f"<tg-emoji emoji-id='5364109867156001787'>🆔</tg-emoji> User ID: {user_id}\n"
        f"<tg-emoji emoji-id='5285026110348731539'>📝</tg-emoji> Vui lòng chờ admin duyệt trong ít phút!\n"
        f"<tg-emoji emoji-id='5454415424319931791'>⏳</tg-emoji> Bạn sẽ nhận được thông báo khi được duyệt.\n\n"
        f"<tg-emoji emoji-id='5422439311196834318'>💡</tg-emoji> Lưu ý: Nếu chưa được duyệt sau 5 phút, vui lòng liên hệ admin!",
        parse_mode='HTML'
    )
    
    # GỬI CHO ADMIN - CÓ NÚT BẤM DUYỆT NGAY
    admin_message = (
        f"<tg-emoji emoji-id='5213394688735717942'>🆕</tg-emoji> <b>USER MỚI ĐĂNG KÝ!</b>\n\n"
        f"<tg-emoji emoji-id='5364109867156001787'>👤</tg-emoji> User ID: <code>{user_id}</code>\n"
        f"<tg-emoji emoji-id='5422439311196834318'>📌</tg-emoji> Tên: {update.effective_user.first_name}\n"
        f"<tg-emoji emoji-id='5461151367559141950'>👋</tg-emoji> Username: @{update.effective_user.username if update.effective_user.username else 'Không có'}\n"
    )
    
    # Tạo nút bấm duyệt và từ chối
    keyboard = [[
        InlineKeyboardButton(
            text="DUYỆT",
            icon_custom_emoji_id="5440547189669516347",
            callback_data=f"approve_user_{user_id}"
        ),
        InlineKeyboardButton(
            text="TỪ CHỐI",
            icon_custom_emoji_id="5210952531676504517",
            callback_data=f"reject_user_{user_id}"
        )
    ]]
    
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            print(f"❌ Lỗi gửi thông báo admin {admin_id}: {e}")
async def approve_user(user_id, context):
    """Duyệt user"""
    user_id_str = str(user_id)
    
    # Xóa khỏi pending
    if user_id_str in pending_users:
        pending_users.remove(user_id_str)
        save_pending_users()
    
    # Thêm vào approved
    if user_id_str not in approved_users:
        approved_users.append(user_id_str)
        save_approved_users()
    
    # Thông báo cho user (thêm emoji động)
    try:
        await context.bot.send_message(
            chat_id=int(user_id),
            text=f"<tg-emoji emoji-id='5440547189669516347'>✅</tg-emoji> <b>TÀI KHOẢN CỦA BẠN ĐÃ ĐƯỢC DUYỆT!</b>\n\n"
                 f"<tg-emoji emoji-id='5325547803936572038'>🎉</tg-emoji> Chào mừng bạn đến với bot!\n"
                 f"<tg-emoji emoji-id='5397782960512444700'>📌</tg-emoji> Gửi /start để bắt đầu sử dụng.",
            parse_mode='HTML'
        )
    except:
        pass
    
    print(f"✅ Đã duyệt user {user_id}")

async def reject_user(user_id, context):
    """Từ chối user"""
    user_id_str = str(user_id)
    
    # Xóa khỏi pending
    if user_id_str in pending_users:
        pending_users.remove(user_id_str)
        save_pending_users()
    
    # Thông báo cho user
    try:
        await context.bot.send_message(
            chat_id=int(user_id),
            text=f"❌ YÊU CẦU DUYỆT CỦA BẠN ĐÃ BỊ TỪ CHỐI!\n\n"
                 f"📞 Vui lòng liên hệ admin để biết thêm chi tiết.\n"
                 f"🆔 User ID của bạn: {user_id}"
        )
    except:
        pass
    
    print(f"❌ Đã từ chối user {user_id}")
async def duyet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Kiểm tra admin
    if not is_admin(user_id):
        await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📌 CÁCH DÙNG:\n"
            "/duyet <user_id> - Duyệt user\n"
            "/duyet list - Xem danh sách chờ duyệt\n\n"
            "✨ Ví dụ:\n"
            "/duyet 5180190297\n"
            "/duyet list"
        )
        return
    
    action = context.args[0].lower()
    
    if action == "list":
        if not pending_users:
            await update.message.reply_text("📭 Không có user nào đang chờ duyệt!")
            return
        
        msg = "⏳ DANH SÁCH USER CHỜ DUYỆT:\n\n"
        for uid in pending_users:
            msg += f"🆔 User ID: {uid}\n"
        await update.message.reply_text(msg)
        return
    
    # Duyệt user theo ID
    try:
        target_id = int(action)
        if str(target_id) in pending_users:
            await approve_user(target_id, context)
            await update.message.reply_text(f"✅ Đã duyệt user {target_id} thành công!")
        else:
            await update.message.reply_text(f"⚠️ User {target_id} không có trong danh sách chờ duyệt!")
    except ValueError:
        await update.message.reply_text("❌ User ID không hợp lệ!")
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if is_banned(user_id):
        await query.edit_message_text("🚫 Bạn đã bị khóa sử dụng bot!", reply_markup=get_back_menu())
        return
    
    # ========== MENU CHÍNH ==========
    if data == "menu_main":
        await query.edit_message_text(
            f"<tg-emoji emoji-id='5416041192905265756'>🏠</tg-emoji> MENU CHÍNH\n\n"
            f"<tg-emoji emoji-id='5397782960512444700'>📌</tg-emoji> Chọn chức năng bạn muốn:",
            parse_mode='HTML',
            reply_markup=get_main_menu(user_id)
        )
    # ========== QUẢN LÝ TÀI KHOẢN RÚT TIỀN ==========
    elif data == "manage_withdraw_bank":
        await query.edit_message_text(
            f"🏦 QUẢN LÝ TÀI KHOẢN RÚT TIỀN\n\n"
            f"📌 Thêm tài khoản ngân hàng để nhận tiền rút.\n"
            f"💰 Số dư hiện tại: {user_balance.get(str(user_id), {}).get('balance', 0):,.0f} VND",
            reply_markup=get_withdraw_bank_menu(user_id)
        )
    elif data == "delete_withdraw_bank":
        user_id_str = str(user_id)
        banks = user_withdraw_banks.get(user_id_str, [])
        
        if not banks:
            await query.edit_message_text("📭 Bạn chưa có tài khoản nào để xóa!", reply_markup=get_withdraw_bank_menu(user_id))
            return
        
        keyboard = []
        for i, bank in enumerate(banks):
            keyboard.append([
                InlineKeyboardButton(
                    f"❌ {bank['bank']} - {bank['stk'][-6:]} - {bank['name'][:15]}", 
                    callback_data=f"delete_bank_{i}"
                )
            ])
        keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data="menu_withdraw")])
        
        await query.edit_message_text(
            "🗑️ CHỌN TÀI KHOẢN CẦN XÓA:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif data == "add_withdraw_bank":
        await query.edit_message_text(
            "🏦 THÊM TÀI KHOẢN RÚT TIỀN\n\n"
            "📝 Vui lòng nhập thông tin theo cú pháp:\n"
            "`NGAN_HANG|SO_STK|TEN_CHU_TK`\n\n"
            "✨ Ví dụ:\n"
            "`MSB|9686687660001499498|TRAN VAN A`\n"
            "`BIDV|963012001687637|NGUYEN VAN B`\n\n"
            "⏳ Gửi tin nhắn chứa thông tin để thêm tài khoản.",
            parse_mode='Markdown',
            reply_markup=get_back_menu()
        )
        context.user_data['pending_add_bank'] = True

    elif data.startswith("delete_withdraw_bank"):
        user_id_str = str(user_id)
        banks = user_withdraw_banks.get(user_id_str, [])
        
        if not banks:
            await query.edit_message_text("📭 Bạn chưa có tài khoản nào để xóa!", reply_markup=get_withdraw_bank_menu(user_id))
            return
        
        keyboard = []
        for i, bank in enumerate(banks):
            keyboard.append([
                InlineKeyboardButton(
                    f"❌ {bank['bank']} - {bank['stk'][-6:]} - {bank['name'][:15]}", 
                    callback_data=f"delete_bank_{i}"
                )
            ])
        keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data="manage_withdraw_bank")])
        
        await query.edit_message_text(
            "🗑️ CHỌN TÀI KHOẢN CẦN XÓA:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("delete_bank_"):
        user_id_str = str(user_id)
        bank_index = int(data.replace("delete_bank_", ""))
        banks = user_withdraw_banks.get(user_id_str, [])
        
        if 0 <= bank_index < len(banks):
            removed = banks.pop(bank_index)
            user_withdraw_banks[user_id_str] = banks
            save_withdraw_banks()
            await query.edit_message_text(
                f"✅ Đã xóa tài khoản:\n"
                f"🏦 {removed['bank']}\n"
                f"💳 {removed['stk']}\n"
                f"👤 {removed['name']}",
                reply_markup=get_withdraw_bank_menu(user_id)
            )
        else:
            await query.edit_message_text("❌ Không tìm thấy tài khoản!", reply_markup=get_withdraw_bank_menu(user_id))

    elif data.startswith("select_withdraw_bank_"):
        user_id_str = str(user_id)
        bank_index = int(data.replace("select_withdraw_bank_", ""))
        banks = user_withdraw_banks.get(user_id_str, [])
        
        if 0 <= bank_index < len(banks):
            bank = banks[bank_index]
            # Lưu bank được chọn
            context.user_data['selected_withdraw_bank_index'] = bank_index
            
            await query.edit_message_text(
                f"🏦 ĐÃ CHỌN TÀI KHOẢN:\n\n"
                f"🏦 Ngân hàng: {bank['bank']}\n"
                f"💳 STK: {bank['stk']}\n"
                f"👤 Chủ TK: {bank['name']}\n\n"
                f"💰 Số dư hiện tại: {user_balance.get(user_id_str, {}).get('balance', 0):,.0f} VND\n"
                f"💵 Phí rút: {WITHDRAW_FEE_PERCENT}% + {WITHDRAW_FIXED_FEE:,} VND\n\n"
                f"📝 VUI LÒNG NHẬP SỐ TIỀN CẦN RÚT:\n"
                f"✨ Ví dụ: 2000000\n\n"
                f"⏳ Gửi tin nhắn chứa số tiền để rút ngay!",
                reply_markup=get_back_menu()
            )
            context.user_data['pending_withdraw_amount'] = True
    elif data == "menu_new":
        await query.edit_message_text(
            f"<tg-emoji emoji-id='5264895611517300926'>🏦</tg-emoji> CHỌN NGÂN HÀNG\n\n"
            f"<tg-emoji emoji-id='5397782960512444700'>📌</tg-emoji> Chọn ngân hàng bạn muốn tạo tài khoản ảo:",
            parse_mode='HTML',
            reply_markup=get_bank_menu()
        )
    
    elif data == "menu_balance":
        user_id_str = str(user_id)
        
        try:
            await query.answer()
        except:
            pass
        
        # Lấy số dư mới nhất
        balance = user_balance.get(user_id_str, {}).get('balance', 0)
        total_orders = user_balance.get(user_id_str, {}).get('total_orders', 0)
        last_update = user_balance.get(user_id_str, {}).get('last_update', 'Chưa có')
        history = user_balance.get(user_id_str, {}).get('history', [])
        recent = history[-20:] if history else []
        
        msg = f"<tg-emoji emoji-id='5224257782013769471'>💰</tg-emoji> <b>SỐ DƯ CỦA BẠN</b>\n\n"
        msg += f"<tg-emoji emoji-id='5028746137645876535'>📊</tg-emoji> <b>Số dư:</b> {balance:,.0f} VND\n"
        msg += f"<tg-emoji emoji-id='5429651785352501917'>📈</tg-emoji> <b>Tổng đơn:</b> {total_orders} đơn\n"
        msg += f"<tg-emoji emoji-id='5440621591387980068'>🕐</tg-emoji> <b>Cập nhật:</b> {last_update}\n"

        if recent:
            msg += f"\n<tg-emoji emoji-id='5197269100878907942'>📋</tg-emoji> <b>20 ĐƠN GẦN NHẤT:</b>\n"
            for order in reversed(recent):
                msg += f"   • {order['amount']:,.0f} VND - {order['customer_name']}\n"
        
        # SỬA TRỰC TIẾP TRÊN TEXT CŨ (edit message)
        await query.edit_message_text(
            text=msg,
            parse_mode='HTML',
            reply_markup=get_back_menu()
        )
    # Xử lý duyệt/từ chối user
    elif data.startswith("approve_user_"):
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền!", reply_markup=get_back_menu())
            return
        
        target_id = data.replace("approve_user_", "")
        await approve_user(target_id, context)
        await query.edit_message_text(f"✅ Đã duyệt user {target_id} thành công!", reply_markup=get_back_menu())

    elif data.startswith("reject_user_"):
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền!", reply_markup=get_back_menu())
            return
        
        target_id = data.replace("reject_user_", "")
        await reject_user(target_id, context)
        await query.edit_message_text(f"❌ Đã từ chối user {target_id}!", reply_markup=get_back_menu())
    elif data == "menu_tracking":
        user_orders = {k: v for k, v in tracking_orders.items() if v.get('user_id') == user_id}
        if user_orders:
            msg = "📋 ĐƠN HÀNG ĐANG THEO DÕI\n\n"
            for order_code, info in user_orders.items():
                status_icon = "⏳" if info.get('status') == 'pending' else "✅"
                msg += f"{status_icon} {order_code}\n   👤 {info['customer_name']} - {info['bank']}\n"
            msg += f"\n📊 Tổng số: {len(user_orders)} đơn"
        else:
            msg = "📋 ĐƠN HÀNG ĐANG THEO DÕI\n\n🔍 Bạn chưa có đơn hàng nào đang theo dõi."
        
        await query.edit_message_text(msg, reply_markup=get_back_menu())
    # Xử lý duyệt/từ chối user từ nút bấm
    elif data.startswith("approve_user_"):
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền!", reply_markup=get_back_menu())
            return
        
        target_id = data.replace("approve_user_", "")
        
        # Duyệt user
        user_id_str = str(target_id)
        if user_id_str in pending_users:
            pending_users.remove(user_id_str)
            save_pending_users()
        
        if user_id_str not in approved_users:
            approved_users.append(user_id_str)
            save_approved_users()
        
        # Thông báo cho user
        try:
            await context.bot.send_message(
                chat_id=int(target_id),
                text=f"<tg-emoji emoji-id='5440547189669516347'>✅</tg-emoji> <b>TÀI KHOẢN CỦA BẠN ĐÃ ĐƯỢC DUYỆT!</b>\n\n"
                    f"<tg-emoji emoji-id='5325547803936572038'>🎉</tg-emoji> Chào mừng bạn đến với bot!\n"
                    f"<tg-emoji emoji-id='5397782960512444700'>📌</tg-emoji> Gửi /start để bắt đầu sử dụng.",
                parse_mode='HTML'
            )
        except:
            pass
        
        # Sửa tin nhắn admin
        await query.edit_message_text(
            f"<tg-emoji emoji-id='5440547189669516347'>✅</tg-emoji> <b>ĐÃ DUYỆT USER!</b>\n\n"
            f"<tg-emoji emoji-id='5364109867156001787'>👤</tg-emoji> User ID: {target_id}\n"
            f"<tg-emoji emoji-id='5285265460286217966'>✅</tg-emoji> User đã được kích hoạt.",
            parse_mode='HTML'
        )
        await query.answer("✅ Đã duyệt user thành công!")

    elif data.startswith("reject_user_"):
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền!", reply_markup=get_back_menu())
            return
        
        target_id = data.replace("reject_user_", "")
        
        # Từ chối user
        user_id_str = str(target_id)
        if user_id_str in pending_users:
            pending_users.remove(user_id_str)
            save_pending_users()
        
        # Thông báo cho user
        try:
            await context.bot.send_message(
                chat_id=int(target_id),
                text=f"<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> <b>YÊU CẦU DUYỆT CỦA BẠN ĐÃ BỊ TỪ CHỐI!</b>\n\n"
                    f"<tg-emoji emoji-id='5422439311196834318'>📞</tg-emoji> Vui lòng liên hệ admin để biết thêm chi tiết.\n"
                    f"<tg-emoji emoji-id='5364109867156001787'>🆔</tg-emoji> User ID của bạn: {target_id}",
                parse_mode='HTML'
            )
        except:
            pass
        
        # Sửa tin nhắn admin
        await query.edit_message_text(
            f"<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> <b>ĐÃ TỪ CHỐI USER!</b>\n\n"
            f"<tg-emoji emoji-id='5364109867156001787'>👤</tg-emoji> User ID: {target_id}\n"
            f"<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> User đã bị từ chối.",
            parse_mode='HTML'
        )
        await query.answer("❌ Đã từ chối user!")
    elif data == "menu_withdraw":
        user_id_str = str(user_id)
        balance = user_balance.get(user_id_str, {}).get('balance', 0)
        banks = user_withdraw_banks.get(user_id_str, [])
        
        # Tạo menu (luôn có nút thêm bank)
        keyboard = []
        
        # Nút thêm tài khoản (luôn hiển thị)
        keyboard.append([InlineKeyboardButton(
            text="THÊM TÀI KHOẢN RÚT",
            icon_custom_emoji_id="5397916757333654639",  # ➕
            callback_data="add_withdraw_bank"
        )])
        
        # Nếu có bank đã lưu, hiển thị danh sách
        if banks:
            keyboard.append([InlineKeyboardButton(
                text="DANH SÁCH TÀI KHOẢN",
                icon_custom_emoji_id="5408946052961170713",  # 📋
                callback_data="noop"
            )])
            for i, bank in enumerate(banks):
                keyboard.append([
                    InlineKeyboardButton(
                        text=f"{bank['bank']} - {bank['stk'][-6:]} - {bank['name'][:15]}",
                        icon_custom_emoji_id="5264895611517300926",  # 🏦
                        callback_data=f"select_withdraw_bank_{i}"
                    )
                ])
            keyboard.append([InlineKeyboardButton(
                text="XÓA TÀI KHOẢN",
                icon_custom_emoji_id="5210952531676504517",  # ❌
                callback_data="delete_withdraw_bank"
            )])
        
        # Kiểm tra số dư để hiển thị trạng thái rút tiền
        if balance >= 200000:
            if banks:
                keyboard.append([InlineKeyboardButton(
                    text="RÚT TIỀN",
                    icon_custom_emoji_id="5224257782013769471",  # 💰
                    callback_data="select_amount"
                )])
            else:
                keyboard.append([InlineKeyboardButton(
                    text="CẦN THÊM TÀI KHOẢN TRƯỚC",
                    icon_custom_emoji_id="5420323339723881652",  # ⚠️
                    callback_data="noop"
                )])
        else:
            keyboard.append([InlineKeyboardButton(
                text=f"SỐ DƯ {balance:,.0f} VND - CHƯA ĐỦ 50K",
                icon_custom_emoji_id="5420323339723881652",  # ⚠️
                callback_data="noop"
            )])
        
        keyboard.append([InlineKeyboardButton(
            text="Quay lại",
            icon_custom_emoji_id="5253997076169115797",  # 🔙
            callback_data="menu_main"
        )])
        
        # Tạo message phù hợp
        if balance >= 200000:
            msg = (
                f"<tg-emoji emoji-id='5373174941095050893'>💸</tg-emoji> RÚT TIỀN\n\n"
                f"<tg-emoji emoji-id='5028746137645876535'>📊</tg-emoji> Số dư hiện tại: {balance:,.0f} VND\n"
                f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> Phí rút: {WITHDRAW_FEE_PERCENT}% + {WITHDRAW_FIXED_FEE:,} VND\n\n"
                f"<tg-emoji emoji-id='5224257782013769471'>💰</tg-emoji> Sau khi trừ phí: {calculate_withdraw_amount(balance)['after_fee']:,.0f} VND\n\n"
                f"<tg-emoji emoji-id='5397782960512444700'>📌</tg-emoji> <b>Bước 1:</b> Thêm tài khoản ngân hàng nhận tiền\n"
                f"<tg-emoji emoji-id='5397782960512444700'>📌</tg-emoji> <b>Bước 2:</b> Chọn tài khoản và bấm RÚT TIỀN"
            )
        else:
            msg = (
                f"<tg-emoji emoji-id='5373174941095050893'>💸</tg-emoji> RÚT TIỀN\n\n"
                f"<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> Số dư của bạn ({balance:,.0f} VND) chưa đủ để rút!\n"
                f"<tg-emoji emoji-id='5224257782013769471'>💰</tg-emoji> Số tiền rút tối thiểu: 50,000 VND\n"
                f"<tg-emoji emoji-id='5422439311196834318'>💡</tg-emoji> Bạn cần thêm {(2000000 - balance):,.0f} VND nữa để có thể rút.\n\n"
                f"<tg-emoji emoji-id='5397782960512444700'>📌</tg-emoji> <b>Bạn vẫn có thể thêm tài khoản ngân hàng để sẵn sàng khi đủ tiền!</b>"
            )

        await query.edit_message_text(
            msg,
            parse_mode='HTML',  # ✅ ĐỔI TỪ Markdown SANG HTML
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # ========== CHỌN NGÂN HÀNG ==========
    elif data.startswith("bank_"):
        bank = data.split("_")[1]
        await query.edit_message_text(
            f"<tg-emoji emoji-id='5264895611517300926'>🏦</tg-emoji> TẠO TÀI KHOẢN {bank}\n\n"
            f"<tg-emoji emoji-id='5197269100878907942'>📝</tg-emoji> Vui lòng nhập tên khách hàng (gửi tin nhắn chứa tên):\n"
            f"<tg-emoji emoji-id='5325547803936572038'>✨</tg-emoji> Ví dụ: TRAN VAN A\n\n"
            f"<tg-emoji emoji-id='5454415424319931791'>⏳</tg-emoji> Sau khi gửi, bot sẽ tự động xử lý...",
            parse_mode='HTML',
            reply_markup=get_back_menu()
        )
        context.user_data['pending_bank'] = bank
    
    # ========== TẠO TÀI KHOẢN TỪ TIN NHẮN ==========
    elif data.startswith("create_"):
        bank = data.split("_")[1]
        await query.edit_message_text(
            f"<tg-emoji emoji-id='5264895611517300926'>🏦</tg-emoji> TẠO TÀI KHOẢN {bank}\n\n"
            f"<tg-emoji emoji-id='5197269100878907942'>📝</tg-emoji> Vui lòng nhập tên khách hàng (gửi tin nhắn chứa tên):\n"
            f"<tg-emoji emoji-id='5325547803936572038'>✨</tg-emoji> Ví dụ: TRAN VAN A\n\n"
            f"<tg-emoji emoji-id='5454415424319931791'>⏳</tg-emoji> Sau khi gửi, bot sẽ tự động xử lý...",
            parse_mode='HTML',
            reply_markup=get_back_menu()
        )
        context.user_data['pending_bank'] = bank
    
    # ========== RÚT TIỀN ==========
    elif data.startswith("withdraw_to_bank_"):
        # Rút tiền với tài khoản đã chọn
        bank_index = int(data.replace("withdraw_to_bank_", ""))
        context.user_data['selected_withdraw_bank'] = bank_index
        
        # Hiển thị menu chọn số tiền
        await query.edit_message_text(
            f"<tg-emoji emoji-id='5375312095346704820'>💸</tg-emoji> RÚT TIỀN\n\n"
            f"<tg-emoji emoji-id='5028746137645876535'>📊</tg-emoji> Số dư hiện tại: {user_balance.get(str(user_id), {}).get('balance', 0):,.0f} VND\n"
            f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> Phí rút: {WITHDRAW_FEE_PERCENT}% + {WITHDRAW_FIXED_FEE:,} VND\n\n"
            f"<tg-emoji emoji-id='5397782960512444700'>📌</tg-emoji> Chọn số tiền muốn rút:",
            parse_mode='HTML',
            reply_markup=get_withdraw_amount_menu(user_id, bank_index)
        )

    elif data.startswith("withdraw_"):
        parts = data.split("_")
        if len(parts) >= 2:
            amount_str = parts[1]
            bank_index = int(parts[2]) if len(parts) >= 3 else context.user_data.get('selected_withdraw_bank', 0)
            
            if amount_str == "custom":
                await query.edit_message_text(
                    f"<tg-emoji emoji-id='5375312095346704820'>💸</tg-emoji> RÚT TIỀN\n\n"
                    f"<tg-emoji emoji-id='5197269100878907942'>📝</tg-emoji> Vui lòng nhập số tiền muốn rút (gửi tin nhắn chứa số tiền):\n"
                    f"<tg-emoji emoji-id='5325547803936572038'>✨</tg-emoji> Ví dụ: 200000\n\n"
                    f"<tg-emoji emoji-id='5224257782013769471'>💰</tg-emoji> Số tiền tối thiểu: 200,000 VND",
                    parse_mode='HTML',
                    reply_markup=get_back_menu()
                )
                context.user_data['pending_withdraw'] = True
                context.user_data['selected_withdraw_bank'] = bank_index
            else:
                amount = int(amount_str)
                result = create_withdraw_request(user_id, amount, bank_index)
                
                if result['success']:
                    withdraw_info = result['withdraw_info']
                    msg = (
                        f"<tg-emoji emoji-id='5375312095346704820'>💸</tg-emoji> YÊU CẦU RÚT TIỀN ĐÃ GỬI!\n\n"
                        f"<tg-emoji emoji-id='5224257782013769471'>💰</tg-emoji> Số tiền yêu cầu: {withdraw_info['original']:,.0f} VND\n"
                        f"<tg-emoji emoji-id='5028746137645876535'>📊</tg-emoji> Phí rút ({WITHDRAW_FEE_PERCENT}% + {WITHDRAW_FIXED_FEE:,}): {withdraw_info['fee']:,.0f} VND\n"
                        f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> Số tiền nhận được: {withdraw_info['after_fee']:,.0f} VND\n"
                        f"<tg-emoji emoji-id='5246762912428603768'>📉</tg-emoji> Số dư sau khi trừ: {result['new_balance']:,.0f} VND\n\n"
                        f"<tg-emoji emoji-id='5264895611517300926'>🏦</tg-emoji> Tài khoản nhận:\n"
                        f"   <tg-emoji emoji-id='5264895611517300926'>🏦</tg-emoji> {result['withdraw_bank']['bank']}\n"
                        f"   <tg-emoji emoji-id='5267300544094948794'>💳</tg-emoji> {result['withdraw_bank']['stk']}\n"
                        f"   <tg-emoji emoji-id='5364109867156001787'>👤</tg-emoji> {result['withdraw_bank']['name']}\n\n"
                        f"<tg-emoji emoji-id='5454415424319931791'>⏳</tg-emoji> Vui lòng chờ admin xác nhận!"
                    )
                    await query.edit_message_text(
                        msg, 
                        parse_mode='HTML',
                        reply_markup=get_back_menu()
                    )
                    
                    # Gửi thông báo cho admin (CÓ THÔNG TIN BANK NHẬN)
                    for admin_id in ADMIN_IDS:
                        try:
                            admin_msg = (
                                f"<tg-emoji emoji-id='5213394688735717942'>🆕</tg-emoji> YÊU CẦU RÚT TIỀN MỚI!\n\n"
                                f"<tg-emoji emoji-id='5364109867156001787'>👤</tg-emoji> User ID: {user_id}\n"
                                f"<tg-emoji emoji-id='5224257782013769471'>💰</tg-emoji> Số tiền: {withdraw_info['original']:,.0f} VND\n"
                                f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> Sau phí: {withdraw_info['after_fee']:,.0f} VND\n"
                                f"<tg-emoji emoji-id='5028746137645876535'>📊</tg-emoji> Phí: {withdraw_info['fee']:,.0f} VND\n"
                                f"<tg-emoji emoji-id='5246762912428603768'>📉</tg-emoji> Số dư còn lại: {result['new_balance']:,.0f} VND\n\n"
                                f"<tg-emoji emoji-id='5264895611517300926'>🏦</tg-emoji> THÔNG TIN TÀI KHOẢN NHẬN TIỀN:\n"
                                f"   <tg-emoji emoji-id='5264895611517300926'>🏦</tg-emoji> Ngân hàng: {result['withdraw_bank']['bank']}\n"
                                f"   <tg-emoji emoji-id='5267300544094948794'>💳</tg-emoji> STK: {result['withdraw_bank']['stk']}\n"
                                f"   <tg-emoji emoji-id='5364109867156001787'>👤</tg-emoji> Chủ TK: {result['withdraw_bank']['name']}\n\n"
                                f"<tg-emoji emoji-id='5836782704686798781'>🆔</tg-emoji> Mã yêu cầu: {result['request_id']}"
                            )
                            keyboard = [[
                                InlineKeyboardButton(
                                    text="Xác nhận",
                                    icon_custom_emoji_id="5440547189669516347",
                                    callback_data=f"approve_withdraw_{result['request_id']}"
                                ),
                                InlineKeyboardButton(
                                    text="Từ chối",
                                    icon_custom_emoji_id="5210952531676504517",
                                    callback_data=f"reject_withdraw_{result['request_id']}"
                                )
                            ]]
                            await context.bot.send_message(
                                chat_id=admin_id, 
                                text=admin_msg,
                                parse_mode='HTML',
                                reply_markup=InlineKeyboardMarkup(keyboard)
                            )
                        except Exception as e:
                            print(f"❌ Lỗi gửi admin: {e}")
                else:
                    await query.edit_message_text(
                        f"<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> {result['error']}",
                        parse_mode='HTML',
                        reply_markup=get_back_menu()
                    )
    elif data == "select_amount":
        user_id_str = str(user_id)
        banks = user_withdraw_banks.get(user_id_str, [])
        balance = user_balance.get(user_id_str, {}).get('balance', 0)
        
        if not banks:
            await query.edit_message_text(
                f"<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> BẠN CHƯA CÓ TÀI KHOẢN RÚT TIỀN!\n\n"
                f"<tg-emoji emoji-id='5197269100878907942'>📝</tg-emoji> Vui lòng thêm tài khoản bằng nút '<tg-emoji emoji-id=''>➕</tg-emoji> THÊM TÀI KHOẢN RÚT' trước khi rút.",
                parse_mode='HTML',
                reply_markup=get_withdraw_bank_menu(user_id)
            )
            return
        
        # Kiểm tra xem đã chọn tài khoản chưa
        selected_index = context.user_data.get('selected_withdraw_bank_index')
        
        if selected_index is None:
            # Nếu chưa chọn, hiển thị danh sách để chọn
            keyboard = []
            for i, bank in enumerate(banks):
                keyboard.append([
                    InlineKeyboardButton(
                        f"🏦 {bank['bank']} - {bank['stk'][-6:]} - {bank['name'][:15]}",
                        callback_data=f"choose_bank_for_withdraw_{i}"
                    )
                ])
            keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data="menu_withdraw")])
            
            await query.edit_message_text(
                f"<tg-emoji emoji-id='5224257782013769471'>💰</tg-emoji> RÚT TIỀN\n\n"
                f"<tg-emoji emoji-id='5028746137645876535'>📊</tg-emoji> Số dư: {balance:,.0f} VND\n"
                f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> Phí: {WITHDRAW_FEE_PERCENT}% + {WITHDRAW_FIXED_FEE:,} VND\n\n"
                f"<tg-emoji emoji-id='5397782960512444700'>📌</tg-emoji> Vui lòng chọn tài khoản nhận tiền:",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # Đã chọn tài khoản, hiển thị menu chọn số tiền
            await query.edit_message_text(
                f"<tg-emoji emoji-id='5373174941095050893'>💸</tg-emoji> RÚT TIỀN\n\n"
                f"<tg-emoji emoji-id='5028746137645876535'>📊</tg-emoji> Số dư hiện tại: {balance:,.0f} VND\n"
                f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> Phí rút: {WITHDRAW_FEE_PERCENT}% + {WITHDRAW_FIXED_FEE:,} VND\n\n"
                f"<tg-emoji emoji-id='5224257782013769471'>💰</tg-emoji> Sau khi trừ phí: {calculate_withdraw_amount(balance)['after_fee']:,.0f} VND\n\n"
                f"<tg-emoji emoji-id='5397782960512444700'>📌</tg-emoji> Chọn số tiền muốn rút:",
                parse_mode='HTML',
                reply_markup=get_withdraw_amount_menu(user_id, selected_index)
            )

    elif data.startswith("choose_bank_for_withdraw_"):
        bank_index = int(data.replace("choose_bank_for_withdraw_", ""))
        context.user_data['selected_withdraw_bank_index'] = bank_index
        
        user_id_str = str(user_id)
        balance = user_balance.get(user_id_str, {}).get('balance', 0)
        banks = user_withdraw_banks.get(user_id_str, [])
        
        if 0 <= bank_index < len(banks):
            bank = banks[bank_index]
            await query.edit_message_text(
                f"<tg-emoji emoji-id='5440547189669516347'>✅</tg-emoji> ĐÃ CHỌN TÀI KHOẢN:\n\n"
                f"<tg-emoji emoji-id='5264895611517300926'>🏦</tg-emoji> Ngân hàng: {bank['bank']}\n"
                f"<tg-emoji emoji-id='5267300544094948794'>💳</tg-emoji> STK: {bank['stk']}\n"
                f"<tg-emoji emoji-id='5364109867156001787'>👤</tg-emoji> Chủ TK: {bank['name']}\n\n"
                f"<tg-emoji emoji-id='5224257782013769471'>💰</tg-emoji> Số dư: {balance:,.0f} VND\n"
                f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> Phí rút: {WITHDRAW_FEE_PERCENT}% + {WITHDRAW_FIXED_FEE:,} VND\n\n"
                f"<tg-emoji emoji-id='5397782960512444700'>📌</tg-emoji> Chọn số tiền muốn rút:",
                parse_mode='HTML',
                reply_markup=get_withdraw_amount_menu(user_id, bank_index)
            )
    # ========== ADMIN: MỞ BAN USER ==========
    elif data == "admin_unban":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền sử dụng chức năng này!", reply_markup=get_back_menu())
            return
        
        if not banned_users:
            await query.edit_message_text("📭 Không có user nào đang bị ban!", reply_markup=get_back_menu())
            return
        
        # Tạo danh sách user bị ban
        msg = "🔓 DANH SÁCH USER BỊ BAN\n\n"
        keyboard = []
        
        for uid in banned_users:
            msg += f"🆔 User ID: {uid}\n"
            # Lấy thông tin user nếu có trong user_balance
            if uid in user_balance:
                msg += f"💰 Số dư: {user_balance[uid]['balance']:,.0f} VND\n"
            msg += "─" * 20 + "\n"
            
            # Thêm nút mở ban cho từng user
            keyboard.append([InlineKeyboardButton(f"🔓 Mở ban {uid}", callback_data=f"unban_{uid}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data="menu_main")])
        
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    # ========== XỬ LÝ MỞ BAN ==========
    elif data.startswith("unban_"):
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền!", reply_markup=get_back_menu())
            return
        
        target_user_id = data.replace("unban_", "")
        
        if target_user_id in banned_users:
            banned_users.remove(target_user_id)
            save_banned()
            await query.edit_message_text(
                f"✅ Đã mở ban user {target_user_id}!\n"
                f"User này có thể sử dụng bot lại.",
                reply_markup=get_back_menu()
            )
            
            # Thông báo cho user được mở ban
            try:
                await context.bot.send_message(
                    chat_id=int(target_user_id),
                    text="✅ BẠN ĐÃ ĐƯỢC MỞ KHÓA!\n🎉 Chào mừng bạn quay trở lại sử dụng bot!"
                )
            except:
                pass
        else:
            await query.edit_message_text(
                f"⚠️ User {target_user_id} không có trong danh sách bị ban!",
                reply_markup=get_back_menu()
            )
    # ========== ADMIN: DANH SÁCH USER ==========
    elif data == "admin_users":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền sử dụng chức năng này!", reply_markup=get_back_menu())
            return
        
        msg = "👥 DANH SÁCH NGƯỜI DÙNG\n\n"
        for uid, data in user_balance.items():
            msg += f"🆔 User ID: {uid}\n"
            msg += f"💰 Số dư: {data['balance']:,.0f} VND\n"
            msg += f"📈 Tổng đơn: {data['total_orders']} đơn\n"
            msg += f"🕐 Cập nhật: {data['last_update']}\n"
            msg += "─" * 20 + "\n"
        
        if not user_balance:
            msg += "📭 Chưa có người dùng nào!"
        
        await query.edit_message_text(msg[:4000], reply_markup=get_back_menu())
    
    # ========== ADMIN: DOANH THU ==========
    elif data == "admin_revenue":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền sử dụng chức năng này!", reply_markup=get_back_menu())
            return
        
        day_revenue = get_revenue_by_period('day')
        week_revenue = get_revenue_by_period('week')
        month_revenue = get_revenue_by_period('month')
        all_revenue = calculate_revenue(get_all_history())
        
        msg = (
            f"📊 THỐNG KÊ DOANH THU\n\n"
            f"📅 HÔM NAY:\n"
            f"   💰 Tổng: {day_revenue['total']:,.0f} VND\n"
            f"   📊 Phí (15%+5k): {day_revenue['fee']:,.0f} VND\n"
            f"   💵 Sau phí: {day_revenue['after_fee']:,.0f} VND\n\n"
            f"📆 TUẦN NÀY:\n"
            f"   💰 Tổng: {week_revenue['total']:,.0f} VND\n"
            f"   📊 Phí: {week_revenue['fee']:,.0f} VND\n"
            f"   💵 Sau phí: {week_revenue['after_fee']:,.0f} VND\n\n"
            f"📅 THÁNG NÀY:\n"
            f"   💰 Tổng: {month_revenue['total']:,.0f} VND\n"
            f"   📊 Phí: {month_revenue['fee']:,.0f} VND\n"
            f"   💵 Sau phí: {month_revenue['after_fee']:,.0f} VND\n\n"
            f"📊 TỔNG CỘNG:\n"
            f"   💰 Tổng: {all_revenue['total']:,.0f} VND\n"
            f"   📊 Phí: {all_revenue['fee']:,.0f} VND\n"
            f"   💵 Sau phí: {all_revenue['after_fee']:,.0f} VND"
        )
        await query.edit_message_text(msg, reply_markup=get_back_menu())
    
    # ========== ADMIN: BAN USER ==========
    elif data == "admin_ban":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền sử dụng chức năng này!", reply_markup=get_back_menu())
            return
        
        await query.edit_message_text(
            "🚫 BAN USER\n\n"
            "📝 Vui lòng gửi tin nhắn chứa User ID cần ban:\n"
            "✨ Ví dụ: 5180190297\n\n"
            "📌 User ID có thể lấy từ lệnh /start hoặc danh sách user",
            reply_markup=get_back_menu()
        )
        context.user_data['pending_ban'] = True
    
    # ========== ADMIN: DUYỆT RÚT TIỀN ==========
    elif data == "admin_approve_withdraw":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền sử dụng chức năng này!", reply_markup=get_back_menu())
            return
        
        pending_requests = {k: v for k, v in withdraw_requests.items() if v['status'] == 'pending'}
        
        if not pending_requests:
            await query.edit_message_text("📭 Không có yêu cầu rút tiền nào đang chờ xử lý!", reply_markup=get_back_menu())
            return
        
        msg = "✅ DANH SÁCH YÊU CẦU RÚT TIỀN\n\n"
        for req_id, req in pending_requests.items():
            msg += f"🆔 Mã: {req_id}\n"
            msg += f"👤 User: {req['user_id']}\n"
            msg += f"💰 Số tiền: {req['original_amount']:,.0f} VND\n"
            msg += f"💵 Sau phí: {req['after_fee']:,.0f} VND\n"
            msg += f"🕐 Tạo lúc: {req['created_at']}\n"
            msg += "─" * 20 + "\n"
        
        keyboard = []
        for req_id in pending_requests.keys():
            keyboard.append([
                InlineKeyboardButton(f"✅ {req_id}", callback_data=f"approve_withdraw_{req_id}"),
                InlineKeyboardButton(f"❌ {req_id}", callback_data=f"reject_withdraw_{req_id}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data="menu_main")])
        
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    
    # ========== XỬ LÝ DUYỆT/TỪ CHỐI RÚT TIỀN ==========
    elif data.startswith("approve_withdraw_"):
        if not is_admin(user_id):
            await query.edit_message_text(
                f"<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> Bạn không có quyền!",
                parse_mode='HTML',
                reply_markup=get_back_menu()
            )
            return
        
        request_id = data.replace("approve_withdraw_", "")
        result = approve_withdraw(request_id)
        
        if result['success']:
            await query.edit_message_text(
                f"<tg-emoji emoji-id='5440547189669516347'>✅</tg-emoji> Đã xác nhận rút tiền!\n"
                f"<tg-emoji emoji-id='5836782704686798781'>🆔</tg-emoji> Mã: {request_id}\n"
                f"<tg-emoji emoji-id='5224257782013769471'>💰</tg-emoji> Số tiền đã chuyển: {result['amount']:,.0f} VND",
                parse_mode='HTML',
                reply_markup=get_back_menu()
            )
            
            # Thông báo cho user
            try:
                await context.bot.send_message(
                    chat_id=result['user_id'],
                    text=(
                        f"<tg-emoji emoji-id='5440547189669516347'>✅</tg-emoji> YÊU CẦU RÚT TIỀN ĐÃ ĐƯỢC XÁC NHẬN!\n\n"
                        f"<tg-emoji emoji-id='5224257782013769471'>💰</tg-emoji> Số tiền: {result['amount']:,.0f} VND đã được chuyển.\n"
                        f"<tg-emoji emoji-id='5028746137645876535'>📊</tg-emoji> Phí rút: {WITHDRAW_FEE_PERCENT}% + {WITHDRAW_FIXED_FEE:,} VND"
                    ),
                    parse_mode='HTML'
                )
            except:
                pass
        else:
            await query.edit_message_text(
                f"<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> {result['error']}",
                parse_mode='HTML',
                reply_markup=get_back_menu()
            )
    
    elif data.startswith("reject_withdraw_"):
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền!", reply_markup=get_back_menu())
            return
        
        request_id = data.replace("reject_withdraw_", "")
        result = reject_withdraw(request_id)
        
        if result['success']:
            await query.edit_message_text(
                f"✅ Đã từ chối yêu cầu rút tiền!\n"
                f"🆔 Mã: {request_id}\n"
                f"💰 Đã hoàn lại {result['refund_amount']:,.0f} VND cho user",
                reply_markup=get_back_menu()
            )
            
            # Thông báo cho user
            try:
                await context.bot.send_message(
                    chat_id=result['user_id'],
                    text=f"❌ YÊU CẦU RÚT TIỀN CỦA BẠN ĐÃ BỊ TỪ CHỐI!\n\n"
                         f"🆔 Mã: {request_id}\n"
                         f"💰 Số tiền đã được hoàn lại: {result['refund_amount']:,.0f} VND\n"
                         f"📞 Vui lòng liên hệ admin để biết thêm chi tiết."
                )
            except:
                pass
        else:
            await query.edit_message_text(f"❌ {result['error']}", reply_markup=get_back_menu())
    
    elif data == "admin_stats":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Bạn không có quyền!", reply_markup=get_back_menu())
            return
        
        total_users = len(user_balance)
        total_orders = sum(u.get('total_orders', 0) for u in user_balance.values())
        total_balance = sum(u.get('balance', 0) for u in user_balance.values())
        pending_orders = len([o for o in tracking_orders.values() if o.get('status') == 'pending'])
        pending_withdraws = len([r for r in withdraw_requests.values() if r['status'] == 'pending'])
        
        msg = (
            f"📈 THỐNG KÊ HỆ THỐNG\n\n"
            f"👥 Tổng người dùng: {total_users}\n"
            f"📦 Tổng đơn hàng: {total_orders}\n"
            f"💰 Tổng số dư: {total_balance:,.0f} VND\n"
            f"⏳ Đơn chờ thanh toán: {pending_orders}\n"
            f"💸 Yêu cầu rút chờ: {pending_withdraws}"
        )
        await query.edit_message_text(msg, reply_markup=get_back_menu())
    
    elif data == "menu_refresh":
        await query.edit_message_text(
            "🔄 ĐANG REFRESH...\n\n✅ Đã cập nhật dữ liệu mới nhất!",
            reply_markup=get_main_menu(user_id)
        )
    
    elif data == "noop":
        await query.answer()

# ========== XỬ LÝ TIN NHẮN THƯỜNG ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if is_banned(user_id):
        await update.message.reply_text("🚫 Bạn đã bị khóa sử dụng bot!")
        return
    
    # Xử lý nhập tên để tạo tài khoản
    if context.user_data.get('pending_bank'):
        bank = context.user_data.pop('pending_bank')
        customer_name = text.upper()
        
        # Kiểm tra đã duyệt chưa
        if str(user_id) not in approved_users:
            await update.message.reply_text(
                "❌ TÀI KHOẢN CỦA BẠN CHƯA ĐƯỢC DUYỆT!\n\n"
                "📝 Vui lòng gửi /start để gửi yêu cầu duyệt."
            )
            return
        
        status_msg = await update.message.reply_text(
            f"<tg-emoji emoji-id='5226702984204797593'>🔄</tg-emoji> Đang tạo tài khoản {bank} cho {customer_name}...",
            parse_mode='HTML'
        )
        
        # Chạy bất đồng bộ, không chờ
        asyncio.create_task(process_and_reply(status_msg, customer_name, bank, user_id))
        return

    # Trong hàm handle_message, thêm:
    if context.user_data.get('pending_add_bank'):
        context.user_data.pop('pending_add_bank')
        try:
            # Parse thông tin: NGAN_HANG|SO_STK|TEN_CHU_TK
            parts = text.split('|')
            if len(parts) != 3:
                await update.message.reply_text(
                    f"<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> Sai định dạng!\n\n"
                    f"<tg-emoji emoji-id='5285026110348731539'>📝</tg-emoji> Cú pháp: <code>NGAN_HANG|SO_STK|TEN_CHU_TK</code>\n"
                    f"<tg-emoji emoji-id='5325547803936572038'>✨</tg-emoji> Ví dụ: <code>MSB|9686687660001499498|TRAN VAN A</code>",
                    parse_mode='HTML',
                    reply_markup=get_back_menu()
                )
                return
            
            bank_name = parts[0].strip().upper()
            stk = parts[1].strip()
            account_name = parts[2].strip().upper()
            
            # ✅ ĐÃ XÓA PHẦN KIỂM TRA NGÂN HÀNG HỢP LỆ
            # Cho phép tất cả các ngân hàng: Vietcombank, Techcombank, VPBank, Sacombank, SHB, v.v...
            
            # Kiểm tra STK (8-20 số - linh hoạt hơn)
            if not stk.isdigit() or len(stk) < 8 or len(stk) > 20:
                await update.message.reply_text(
                    f"<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> Số tài khoản không hợp lệ!\n"
                    f"<tg-emoji emoji-id='5397782960512444700'>📌</tg-emoji> STK phải là số và có 8-20 chữ số.",
                    parse_mode='HTML',
                    reply_markup=get_back_menu()
                )
                return
            
            # Lưu thông tin
            user_id_str = str(user_id)
            if user_id_str not in user_withdraw_banks:
                user_withdraw_banks[user_id_str] = []
            
            # Kiểm tra trùng
            for existing in user_withdraw_banks[user_id_str]:
                if existing['stk'] == stk:
                    await update.message.reply_text(
                        f"<tg-emoji emoji-id='5420323339723881652'>⚠️</tg-emoji> Số tài khoản này đã được thêm trước đó!",
                        parse_mode='HTML',
                        reply_markup=get_back_menu()
                    )
                    return
            
            user_withdraw_banks[user_id_str].append({
                'bank': bank_name,
                'stk': stk,
                'name': account_name,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            save_withdraw_banks()
            
            await update.message.reply_text(
                f"<tg-emoji emoji-id='5440547189669516347'>✅</tg-emoji> ĐÃ THÊM TÀI KHOẢN THÀNH CÔNG!\n\n"
                f"<tg-emoji emoji-id='5264895611517300926'>🏦</tg-emoji> Ngân hàng: {bank_name}\n"
                f"<tg-emoji emoji-id='5267300544094948794'>💳</tg-emoji> STK: {stk}\n"
                f"<tg-emoji emoji-id='5364109867156001787'>👤</tg-emoji> Chủ TK: {account_name}\n\n"
                f"<tg-emoji emoji-id='5397782960512444700'>📌</tg-emoji> Giờ bạn có thể chọn tài khoản này để rút tiền.",
                parse_mode='HTML',
                reply_markup=get_withdraw_bank_menu(user_id)
            )
        except Exception as e:
            await update.message.reply_text(
                f"<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> Lỗi: {e}\n\nVui lòng thử lại!",
                parse_mode='HTML',
                reply_markup=get_back_menu()
            )
        return
    if context.user_data.get('pending_withdraw_amount'):
        context.user_data.pop('pending_withdraw_amount')
        try:
            amount = int(text.replace('.', '').replace(',', ''))
            if amount < 200000:
                await update.message.reply_text(
                    f"<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> Số tiền rút tối thiểu là 200,000 VND!",
                    parse_mode='HTML',
                    reply_markup=get_back_menu()
                )
                return
            
            # Lấy bank đã chọn
            bank_index = context.user_data.get('selected_withdraw_bank_index', 0)
            
            # Tạo yêu cầu rút
            result = create_withdraw_request(user_id, amount, bank_index)
            
            if result['success']:
                withdraw_info = result['withdraw_info']
                msg = (
                    f"<tg-emoji emoji-id='5375312095346704820'>💸</tg-emoji> YÊU CẦU RÚT TIỀN ĐÃ GỬI!\n\n"
                    f"<tg-emoji emoji-id='5224257782013769471'>💰</tg-emoji> Số tiền: {withdraw_info['original']:,.0f} VND\n"
                    f"<tg-emoji emoji-id='5028746137645876535'>📊</tg-emoji> Phí (15%+5k): {withdraw_info['fee']:,.0f} VND\n"
                    f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> Nhận được: {withdraw_info['after_fee']:,.0f} VND\n"
                    f"<tg-emoji emoji-id='5246762912428603768'>📉</tg-emoji> Số dư còn lại: {result['new_balance']:,.0f} VND\n\n"
                    f"<tg-emoji emoji-id='5454415424319931791'>⏳</tg-emoji> Chờ admin xác nhận!"
                )
                await update.message.reply_text(
                    msg,
                    parse_mode='HTML',
                    reply_markup=get_back_menu()
                )
                
                # Gửi thông báo cho admin
                for admin_id in ADMIN_IDS:
                    try:
                        admin_msg = (
                            f"<tg-emoji emoji-id='5213394688735717942'>🆕</tg-emoji> YÊU CẦU RÚT TIỀN MỚI!\n\n"
                            f"<tg-emoji emoji-id='5364109867156001787'>👤</tg-emoji> User ID: {user_id}\n"
                            f"<tg-emoji emoji-id='5224257782013769471'>💰</tg-emoji> Số tiền: {withdraw_info['original']:,.0f} VND\n"
                            f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> Sau phí: {withdraw_info['after_fee']:,.0f} VND\n"
                            f"<tg-emoji emoji-id='5264895611517300926'>🏦</tg-emoji> Bank: {result['withdraw_bank']['bank']}\n"
                            f"<tg-emoji emoji-id='5267300544094948794'>💳</tg-emoji> STK: {result['withdraw_bank']['stk']}\n"
                            f"<tg-emoji emoji-id='5364109867156001787'>👤</tg-emoji> Chủ TK: {result['withdraw_bank']['name']}\n"
                            f"<tg-emoji emoji-id='5246762912428603768'>📉</tg-emoji> Số dư còn lại: {result['new_balance']:,.0f} VND\n"
                            f"<tg-emoji emoji-id='5836782704686798781'>🆔</tg-emoji> Mã: {result['request_id']}"
                        )
                        keyboard = [[
                            InlineKeyboardButton(
                                text="Xác nhận",
                                icon_custom_emoji_id="5440547189669516347",
                                callback_data=f"approve_withdraw_{result['request_id']}"
                            ),
                            InlineKeyboardButton(
                                text="Từ chối",
                                icon_custom_emoji_id="5210952531676504517",
                                callback_data=f"reject_withdraw_{result['request_id']}"
                            )
                        ]]
                        await context.bot.send_message(
                            chat_id=admin_id, 
                            text=admin_msg,
                            parse_mode='HTML',
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )
                    except:
                        pass
            else:
                await update.message.reply_text(
                    f"<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> {result['error']}",
                    parse_mode='HTML',
                    reply_markup=get_back_menu()
                )
        except:
            await update.message.reply_text(
                f"<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> Số tiền không hợp lệ! Vui lòng nhập số.",
                parse_mode='HTML',
                reply_markup=get_back_menu()
            )
        return
    
    # Xử lý ban user (admin)
    if context.user_data.get('pending_ban'):
        context.user_data.pop('pending_ban')
        if not is_admin(user_id):
            await update.message.reply_text("❌ Bạn không có quyền!", reply_markup=get_back_menu())
            return
        
        try:
            target_user_id = int(text)
            if target_user_id in ADMIN_IDS:
                await update.message.reply_text("❌ Không thể ban admin!", reply_markup=get_back_menu())
                return
            
            if str(target_user_id) not in banned_users:
                banned_users.append(str(target_user_id))
                save_banned()
                await update.message.reply_text(f"✅ Đã ban user {target_user_id}!", reply_markup=get_back_menu())
                
                # Thông báo cho user bị ban
                try:
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text="🚫 BẠN ĐÃ BỊ KHÓA SỬ DỤNG BOT!\n📞 Liên hệ admin để biết thêm chi tiết."
                    )
                except:
                    pass
            else:
                await update.message.reply_text(f"⚠️ User {target_user_id} đã bị ban từ trước!", reply_markup=get_back_menu())
        except:
            await update.message.reply_text("❌ User ID không hợp lệ!", reply_markup=get_back_menu())
        return
async def process_and_reply(status_msg, customer_name, bank, user_id):
    # Gọi trực tiếp async function
    result = await create_virtual_account(customer_name, bank, user_id)
    
    if result and result.get('success'):
        await status_msg.delete()
    else:
        error = result.get('error', 'Lỗi không xác định') if result else 'Lỗi kết nối'
        await status_msg.edit_text(f"❌ TẠO THẤT BẠI!\n\n⚠️ Lỗi: {error}", reply_markup=get_back_menu())
def get_all_history():
    """Lấy tất cả lịch sử giao dịch"""
    all_history = []
    for user_id, data in user_balance.items():
        history = data.get('history', [])
        all_history.extend(history)
    return all_history

def get_revenue_by_period(period='day'):
    """Lấy doanh thu theo ngày/tuần/tháng"""
    now = datetime.now()
    if period == 'day':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = None
    
    all_history = []
    for user_id, data in user_balance.items():
        history = data.get('history', [])
        for item in history:
            item_time = datetime.strptime(item['time'], '%Y-%m-%d %H:%M:%S')
            if start_date and item_time >= start_date:
                all_history.append(item)
    
    return calculate_revenue(all_history)

def calculate_revenue(history):
    """Tính doanh thu sau khi trừ phí 15% + 5k"""
    total = sum(item['amount'] for item in history)
    fee = total * WITHDRAW_FEE_PERCENT / 100 + WITHDRAW_FIXED_FEE
    after_fee = total - fee
    return {
        'total': total,
        'fee': fee,
        'after_fee': after_fee,
        'fee_percent': WITHDRAW_FEE_PERCENT,
        'fixed_fee': WITHDRAW_FIXED_FEE
    }
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if user_id in user_balance:
        balance = user_balance[user_id]['balance']
        total_orders = user_balance[user_id]['total_orders']
        last_update = user_balance[user_id]['last_update']
        history = user_balance[user_id].get('history', [])
        recent = history[-20:] if history else []
        
        msg = f"💰 SỐ DƯ CỦA BẠN\n\n"
        msg += f"📊 Số dư: {balance:,.0f} VND\n"
        msg += f"📈 Tổng đơn: {total_orders} đơn\n"
        msg += f"🕐 Cập nhật: {last_update}\n"
        
        if recent:
            msg += f"\n📋 20 ĐƠN GẦN NHẤT:\n"
            for order in reversed(recent):
                msg += f"   • {order['amount']:,.0f} VND - {order['customer_name']}\n"
    else:
        msg = "💰 SỐ DƯ\n\n📊 Số dư hiện tại: 0 VND"
    
    await update.message.reply_text(msg, reply_markup=get_back_menu())

async def tracking_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_orders = {k: v for k, v in tracking_orders.items() if v.get('user_id') == user_id}
    
    if user_orders:
        msg = "📋 ĐƠN HÀNG ĐANG THEO DÕI\n\n"
        for order_code, info in user_orders.items():
            status_icon = "⏳" if info.get('status') == 'pending' else "✅"
            msg += f"{status_icon} {order_code}\n   👤 {info['customer_name']} - {info['bank']}\n"
        msg += f"\n📊 Tổng số: {len(user_orders)} đơn"
    else:
        msg = "📋 ĐƠN HÀNG ĐANG THEO DÕI\n\n🔍 Bạn chưa có đơn hàng nào đang theo dõi."
    
    await update.message.reply_text(msg, reply_markup=get_back_menu())

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = "🟢 Đã đăng nhập" if is_logged_in else "🔴 Chưa đăng nhập"
    tracking_count = len(tracking_orders)
    
    await update.message.reply_text(
        f"📊 TRẠNG THÁI BOT\n\n"
        f"🔐 Login: {status}\n"
        f"📦 Đang theo dõi: {tracking_count} đơn\n"
        f"⏱️ Chu kỳ check: {CHECK_INTERVAL} giây\n"
        f"🕐 Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        reply_markup=get_back_menu()
    )

async def withdraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /withdraw - chuyển hướng đến menu rút tiền"""
    user_id = update.effective_user.id
    
    if is_banned(user_id):
        await update.message.reply_text("🚫 Bạn đã bị khóa sử dụng bot!")
        return
    
    user_id_str = str(user_id)
    balance = user_balance.get(user_id_str, {}).get('balance', 0)
    
    if balance < 200000:
        await update.message.reply_text(
            f"💸 RÚT TIỀN\n\n"
            f"❌ Số dư của bạn ({balance:,.0f} VND) chưa đủ để rút!\n"
            f"💰 Số tiền rút tối thiểu: 200,000 VND\n\n"
            f"💡 Hãy tạo thêm đơn hàng để tăng số dư!",
            reply_markup=get_back_menu()
        )
    else:
        await update.message.reply_text(
            f"💸 RÚT TIỀN\n\n"
            f"📊 Số dư hiện tại: {balance:,.0f} VND\n"
            f"💵 Phí rút: {WITHDRAW_FEE_PERCENT}% + {WITHDRAW_FIXED_FEE:,} VND\n\n"
            f"💰 Sau khi trừ phí: {calculate_withdraw_amount(balance)['after_fee']:,.0f} VND\n\n"
            f"📌 Chọn số tiền muốn rút:",
            reply_markup=get_withdraw_amount_menu(user_id)
        )

def main():
    print("🚀 Khởi động Telegram Bot...")
    print("="*50)
    
    load_tracking()
    load_balance()
    load_banned()
    load_withdraw_requests()
    load_pending_users()
    load_approved_users()
    
    # Đăng nhập lấy cookies
    if not login_and_get_cookies():
        print("❌ Không thể đăng nhập!")
        return
    
    # Chạy check_orders_loop trong background thread
    import threading
    def run_async_loop():
        asyncio.run(check_orders_loop())
    
    thread = threading.Thread(target=run_async_loop, daemon=True)
    thread.start()
    
    # Tạo bot application
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("chat", chat_command))
    app.add_handler(CommandHandler("duyet", duyet_command))
    app.add_handler(CommandHandler("addmoney", addmoney_command))
    print("✅ Bot đang chạy! Kiểm tra đơn hàng mỗi 10 giây")
    print(f"👥 Admin IDs: {ADMIN_IDS}")
    print("="*50)
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()