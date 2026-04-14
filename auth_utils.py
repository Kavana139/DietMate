"""
auth_utils.py — DietMate Authentication Utilities
Handles: bcrypt hashing, JWT tokens, email sending, security logging
"""
import bcrypt
import secrets
import string
import smtplib
import hashlib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for, request, jsonify

# ─────────────────────────────────────────────────────────
# EMAIL CONFIG — update these with your SMTP details
# For Gmail: enable "App Passwords" in Google Account settings
# ─────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════
# EMAIL SETUP - REQUIRED FOR OTP/RESET EMAILS
# ══════════════════════════════════════════════════════════
# STEP 1: Use your Gmail account
# STEP 2: Go to myaccount.google.com → Security → 2-Step Verification → App Passwords
# STEP 3: Create App Password for "Mail" → copy the 16-char code
# STEP 4: Paste below (remove spaces from the 16-char code)
# Example: SMTP_USER = 'haritaboricha@gmail.com'
#          SMTP_PASSWORD = 'abcdabcdabcdabcd'  (no spaces)
# ══════════════════════════════════════════════════════════
SMTP_HOST     = 'smtp.gmail.com'
SMTP_PORT     = 587
SMTP_USER     = 'haritaboricha@gmail.com'       # ← YOUR Gmail here
SMTP_PASSWORD = 'hzsb rlth vydk bwoc'     # ← 16-char App Password (NOT your regular password)
FROM_NAME     = 'DietMate'
APP_URL       = 'http://127.0.0.1:5000'      # ← Change to your domain in production


# ─────────────────────────────────────────────────────────
# PASSWORD UTILITIES
# ─────────────────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """Hash a plain text password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def check_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def generate_token(length: int = 64) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP for verification."""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


# ─────────────────────────────────────────────────────────
# AUTH DECORATORS
# ─────────────────────────────────────────────────────────

def login_required(f):
    """Decorator: redirect to login if not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def api_login_required(f):
    """Decorator: return JSON 401 if not authenticated (for API routes)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required', 'code': 401}), 401
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────────────────
# EMAIL TEMPLATES
# ─────────────────────────────────────────────────────────

def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send an HTML email via SMTP. Returns True on success."""
    # Check if SMTP is configured
    if SMTP_USER == 'your_email@gmail.com' or SMTP_PASSWORD == 'your_app_password_here':
        print('[EMAIL] SMTP not configured — skipping email send.')
        print('[EMAIL] Set SMTP_USER and SMTP_PASSWORD in auth_utils.py')
        print(f'[EMAIL] Would have sent "{subject}" to {to_email}')
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'{FROM_NAME} <{SMTP_USER}>'
        msg['To']      = to_email
        part = MIMEText(html_body, 'html')
        msg.attach(part)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        print(f'[EMAIL] Sent "{subject}" to {to_email}')
        return True
    except smtplib.SMTPAuthenticationError:
        print('[EMAIL ERROR] Authentication failed. Check SMTP_USER and SMTP_PASSWORD.')
        print('[EMAIL] For Gmail: enable 2FA, then create an App Password at myaccount.google.com/apppasswords')
        return False
    except Exception as e:
        print(f'[EMAIL ERROR] {e}')
        return False


def send_password_reset_email(to_email: str, name: str, token: str) -> bool:
    """Send password reset email with secure link."""
    reset_url = f'{APP_URL}/reset-password/{token}'
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: 'Plus Jakarta Sans', Arial, sans-serif; background: #f4f6fb; padding: 40px 20px; margin: 0;">
      <div style="max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 20px; overflow: hidden; box-shadow: 0 8px 40px rgba(0,0,0,0.08);">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #059659, #047444); padding: 36px 40px; text-align: center;">
          <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 800; letter-spacing: -0.5px;">DietMate</h1>
          <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0; font-size: 14px;">Your Personal Nutrition Companion</p>
        </div>

        <!-- Body -->
        <div style="padding: 40px;">
          <h2 style="color: #111827; font-size: 22px; font-weight: 700; margin: 0 0 12px;">Reset Your Password</h2>
          <p style="color: #4b5563; font-size: 15px; line-height: 1.7; margin: 0 0 24px;">
            Hi <strong>{name}</strong>, we received a request to reset your DietMate password.
            Click the button below to create a new password. This link will expire in <strong>1 hour</strong>.
          </p>

          <div style="text-align: center; margin: 32px 0;">
            <a href="{reset_url}" 
               style="display: inline-block; background: linear-gradient(135deg, #059659, #047444); color: #ffffff;
                      padding: 16px 40px; border-radius: 12px; text-decoration: none;
                      font-weight: 700; font-size: 16px; letter-spacing: 0.3px;">
              Reset Password
            </a>
          </div>

          <p style="color: #9ca3af; font-size: 13px; line-height: 1.7;">
            If you didn't request this, you can safely ignore this email.
            Your password will remain unchanged.
          </p>

          <div style="margin-top: 24px; padding-top: 24px; border-top: 1px solid #e5e7eb;">
            <p style="color: #9ca3af; font-size: 12px; margin: 0;">
              Or copy and paste this link: <br>
              <span style="color: #059659; word-break: break-all;">{reset_url}</span>
            </p>
          </div>
        </div>

        <!-- Footer -->
        <div style="background: #f9fafb; padding: 24px 40px; text-align: center; border-top: 1px solid #e5e7eb;">
          <p style="color: #9ca3af; font-size: 12px; margin: 0;">
            © {datetime.now().year} DietMate. Your data is private and secure.
          </p>
        </div>
      </div>
    </body>
    </html>
    """
    return _send_email(to_email, 'Reset Your DietMate Password', html)


def send_login_notification_email(to_email: str, name: str, device: str, ip: str, time: str) -> bool:
    """Send security notification when user logs in."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; background: #f4f6fb; padding: 40px 20px; margin: 0;">
      <div style="max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 20px; overflow: hidden; box-shadow: 0 8px 40px rgba(0,0,0,0.08);">
        <div style="background: linear-gradient(135deg, #059659, #047444); padding: 30px 40px; text-align: center;">
          <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 800;">DietMate</h1>
        </div>
        <div style="padding: 36px 40px;">
          <h2 style="color: #111827; font-size: 20px; font-weight: 700;">New Login Detected</h2>
          <p style="color: #4b5563; font-size: 14px; line-height: 1.7;">
            Hi <strong>{name}</strong>, we noticed a new sign-in to your DietMate account.
          </p>
          <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; margin: 20px 0;">
            <table style="width: 100%; border-collapse: collapse;">
              <tr><td style="color: #9ca3af; font-size: 13px; padding: 6px 0;">Time</td><td style="color: #111827; font-size: 13px; font-weight: 600;">{time}</td></tr>
              <tr><td style="color: #9ca3af; font-size: 13px; padding: 6px 0;">Device</td><td style="color: #111827; font-size: 13px; font-weight: 600;">{device}</td></tr>
              <tr><td style="color: #9ca3af; font-size: 13px; padding: 6px 0;">IP Address</td><td style="color: #111827; font-size: 13px; font-weight: 600;">{ip}</td></tr>
            </table>
          </div>
          <p style="color: #dc2626; font-size: 14px; font-weight: 600;">
            If this wasn't you, please reset your password immediately.
          </p>
          <a href="{APP_URL}/forgot-password" style="display: inline-block; background: #dc2626; color: #fff; padding: 12px 28px; border-radius: 10px; text-decoration: none; font-weight: 700; font-size: 14px; margin-top: 8px;">
            Secure My Account
          </a>
        </div>
        <div style="background: #f9fafb; padding: 20px 40px; text-align: center; border-top: 1px solid #e5e7eb;">
          <p style="color: #9ca3af; font-size: 12px; margin: 0;">© {datetime.now().year} DietMate. Security first.</p>
        </div>
      </div>
    </body>
    </html>
    """
    return _send_email(to_email, 'New Login to Your DietMate Account', html)


def send_logout_notification_email(to_email: str, name: str, time: str) -> bool:
    """Send notification when user logs out."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; background: #f4f6fb; padding: 40px 20px; margin: 0;">
      <div style="max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 20px; overflow: hidden; box-shadow: 0 8px 40px rgba(0,0,0,0.08);">
        <div style="background: linear-gradient(135deg, #059659, #047444); padding: 30px 40px; text-align: center;">
          <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 800;">DietMate</h1>
        </div>
        <div style="padding: 36px 40px;">
          <h2 style="color: #111827; font-size: 20px; font-weight: 700;">You've Been Logged Out</h2>
          <p style="color: #4b5563; font-size: 14px; line-height: 1.7;">
            Hi <strong>{name}</strong>, you successfully logged out of DietMate at <strong>{time}</strong>.
          </p>
          <p style="color: #4b5563; font-size: 14px; line-height: 1.7;">
            Your nutrition data is safe. Come back anytime to continue your health journey!
          </p>
          <a href="{APP_URL}/" style="display: inline-block; background: linear-gradient(135deg,#059659,#047444); color: #fff; padding: 12px 28px; border-radius: 10px; text-decoration: none; font-weight: 700; font-size: 14px; margin-top: 8px;">
            Sign In Again
          </a>
        </div>
        <div style="background: #f9fafb; padding: 20px 40px; text-align: center; border-top: 1px solid #e5e7eb;">
          <p style="color: #9ca3af; font-size: 12px; margin: 0;">© {datetime.now().year} DietMate. Your privacy is protected.</p>
        </div>
      </div>
    </body>
    </html>
    """
    return _send_email(to_email, 'You Logged Out of DietMate', html)


def send_welcome_email(to_email: str, name: str) -> bool:
    """Send welcome email after registration."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; background: #f4f6fb; padding: 40px 20px; margin: 0;">
      <div style="max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 20px; overflow: hidden; box-shadow: 0 8px 40px rgba(0,0,0,0.08);">
        <div style="background: linear-gradient(135deg, #059659, #047444); padding: 36px 40px; text-align: center;">
          <h1 style="margin: 0; color: #ffffff; font-size: 32px; font-weight: 800;">DietMate</h1>
          <p style="color: rgba(255,255,255,0.85); margin: 8px 0 0; font-size: 15px;">Your Nutrition Journey Begins</p>
        </div>
        <div style="padding: 40px;">
          <h2 style="color: #111827; font-size: 22px; font-weight: 800;">Welcome, {name}!</h2>
          <p style="color: #4b5563; font-size: 15px; line-height: 1.75; margin: 12px 0 24px;">
            Your DietMate account is ready. Here's what you can do now:
          </p>
          <div style="display: flex; flex-direction: column; gap: 12px;">
            <div style="display: flex; align-items: flex-start; gap: 14px; padding: 14px; background: #f9fafb; border-radius: 12px;">
              <div style="font-size: 20px;">&#9776;</div>
              <div>
                <div style="font-weight: 700; color: #111827; font-size: 14px; margin-bottom: 3px;">Complete the Health Quiz</div>
                <div style="color: #6b7280; font-size: 13px;">Get personalised calorie and macro targets</div>
              </div>
            </div>
            <div style="display: flex; align-items: flex-start; gap: 14px; padding: 14px; background: #f9fafb; border-radius: 12px;">
              <div style="font-size: 20px;">&#9997;</div>
              <div>
                <div style="font-weight: 700; color: #111827; font-size: 14px; margin-bottom: 3px;">Generate Your Diet Plan</div>
                <div style="color: #6b7280; font-size: 13px;">Get 6 meals a day matched to your goal</div>
              </div>
            </div>
            <div style="display: flex; align-items: flex-start; gap: 14px; padding: 14px; background: #f9fafb; border-radius: 12px;">
              <div style="font-size: 20px;">&#128247;</div>
              <div>
                <div style="font-weight: 700; color: #111827; font-size: 14px; margin-bottom: 3px;">Try AI Food Scanner</div>
                <div style="color: #6b7280; font-size: 13px;">Snap a photo of any food for instant nutrition</div>
              </div>
            </div>
          </div>
          <div style="text-align: center; margin-top: 32px;">
            <a href="{APP_URL}/dashboard" style="display: inline-block; background: linear-gradient(135deg,#059659,#047444); color: #fff; padding: 16px 40px; border-radius: 12px; text-decoration: none; font-weight: 700; font-size: 16px;">
              Go to Dashboard
            </a>
          </div>
        </div>
        <div style="background: #f9fafb; padding: 24px 40px; text-align: center; border-top: 1px solid #e5e7eb;">
          <p style="color: #9ca3af; font-size: 12px; margin: 0;">© {datetime.now().year} DietMate. Built for your health.</p>
        </div>
      </div>
    </body>
    </html>
    """
    return _send_email(to_email, f'Welcome to DietMate, {name}!', html)


# ─────────────────────────────────────────────────────────
# SECURITY HELPERS
# ─────────────────────────────────────────────────────────

def get_client_ip() -> str:
    """Get the real client IP, handling proxies."""
    if request.headers.getlist('X-Forwarded-For'):
        return request.headers.getlist('X-Forwarded-For')[0].split(',')[0].strip()
    return request.remote_addr or 'Unknown'


def get_device_info() -> str:
    """Parse user agent for basic device info."""
    ua = request.headers.get('User-Agent', '')
    if 'Mobile' in ua or 'Android' in ua:
        return 'Mobile Device'
    elif 'iPad' in ua or 'Tablet' in ua:
        return 'Tablet'
    elif 'Chrome' in ua:
        return 'Chrome Browser'
    elif 'Firefox' in ua:
        return 'Firefox Browser'
    elif 'Safari' in ua:
        return 'Safari Browser'
    return 'Web Browser'


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    Returns (is_valid: bool, message: str)
    """
    if len(password) < 8:
        return False, 'Password must be at least 8 characters.'
    if not any(c.isupper() for c in password):
        return False, 'Password must contain at least one uppercase letter.'
    if not any(c.islower() for c in password):
        return False, 'Password must contain at least one lowercase letter.'
    if not any(c.isdigit() for c in password):
        return False, 'Password must contain at least one number.'
    return True, 'Strong password'


def mask_email(email: str) -> str:
    """Mask email for display: john@gmail.com -> j***@gmail.com"""
    try:
        local, domain = email.split('@')
        masked_local = local[0] + '***' if len(local) > 1 else '***'
        return f'{masked_local}@{domain}'
    except Exception:
        return '***@***'


def send_streak_milestone_email(to_email: str, name: str, streak: int, badge: str) -> bool:
    """Send streak milestone achievement email."""
    badge_colors = {
        'Bronze Streak': '#cd7f32',
        'Silver Streak': '#c0c0c0', 
        'Gold Streak':   '#ffd700',
        'Platinum Streak': '#e5e4e2',
        'Diamond Streak':  '#b9f2ff'
    }
    color = badge_colors.get(badge, '#7cfc9a')
    html = f"""<!DOCTYPE html>
    <html><body style="font-family:Arial,sans-serif;background:#f4f6fb;padding:40px 20px;margin:0;">
      <div style="max-width:560px;margin:0 auto;background:#fff;border-radius:20px;overflow:hidden;box-shadow:0 8px 40px rgba(0,0,0,0.08);">
        <div style="background:linear-gradient(135deg,#059659,#047444);padding:36px 40px;text-align:center;">
          <h1 style="margin:0;color:#fff;font-size:28px;font-weight:800;">DietMate</h1>
          <p style="color:rgba(255,255,255,0.85);margin:8px 0 0;font-size:15px;">Achievement Unlocked!</p>
        </div>
        <div style="padding:40px;text-align:center;">
          <div style="font-size:64px;margin-bottom:16px;">{"🥉" if "Bronze" in badge else "🥈" if "Silver" in badge else "🥇" if "Gold" in badge else "💎"}</div>
          <div style="display:inline-block;background:{color}22;border:2px solid {color};border-radius:12px;padding:10px 24px;margin-bottom:20px;">
            <div style="font-size:18px;font-weight:800;color:#111;">{badge}</div>
          </div>
          <h2 style="color:#111;font-size:22px;font-weight:800;margin:0 0 12px;">Congratulations, {name}!</h2>
          <p style="color:#4b5563;font-size:15px;line-height:1.7;margin:0 0 24px;">
            You have logged meals for <strong>{streak} consecutive days</strong>.<br>
            Consistency is the key to results — keep it up!
          </p>
          <a href="{APP_URL}/progress" style="display:inline-block;background:linear-gradient(135deg,#059659,#047444);color:#fff;padding:14px 36px;border-radius:12px;text-decoration:none;font-weight:700;font-size:15px;">
            View My Progress
          </a>
        </div>
        <div style="background:#f9fafb;padding:20px 40px;text-align:center;border-top:1px solid #e5e7eb;">
          <p style="color:#9ca3af;font-size:12px;margin:0;">© {datetime.now().year} DietMate. Keep going!</p>
        </div>
      </div>
    </body></html>"""
    return _send_email(to_email, f'You earned the {badge} on DietMate!', html)


def send_otp_email(to_email: str, name: str, otp: str) -> bool:
    """Send email verification OTP."""
    html = f"""<!DOCTYPE html>
    <html><body style="font-family:Arial,sans-serif;background:#f4f6fb;padding:40px 20px;margin:0;">
      <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:20px;overflow:hidden;box-shadow:0 8px 40px rgba(0,0,0,0.08);">
        <div style="background:linear-gradient(135deg,#059659,#047444);padding:32px 40px;text-align:center;">
          <h1 style="margin:0;color:#fff;font-size:26px;font-weight:800;">DietMate</h1>
          <p style="color:rgba(255,255,255,0.85);margin:6px 0 0;font-size:14px;">Verify your email</p>
        </div>
        <div style="padding:40px;text-align:center;">
          <h2 style="color:#111;font-size:20px;font-weight:800;margin:0 0 10px;">Hi {name}!</h2>
          <p style="color:#4b5563;font-size:14px;line-height:1.7;margin:0 0 28px;">
            Enter this 6-digit code to verify your email and create your DietMate account.
          </p>
          <div style="display:inline-block;background:#f9fafb;border:2px solid #e5e7eb;border-radius:16px;padding:20px 40px;margin-bottom:24px;">
            <div style="font-family:monospace;font-size:40px;font-weight:800;letter-spacing:12px;color:#059659;">{otp}</div>
          </div>
          <p style="color:#9ca3af;font-size:13px;">This code expires in <strong>10 minutes</strong>. Do not share it with anyone.</p>
        </div>
        <div style="background:#f9fafb;padding:20px 40px;text-align:center;border-top:1px solid #e5e7eb;">
          <p style="color:#9ca3af;font-size:12px;margin:0;">© {datetime.now().year} DietMate. Your privacy is protected.</p>
        </div>
      </div>
    </body></html>"""
    return _send_email(to_email, 'Your DietMate Verification Code', html)