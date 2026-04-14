"""
DietMate v4.0 — Complete Flask Application
Full backend: Auth + Email + Recipes + Smoothies + Progress + AI Scanner + Unique Features
"""
import os, sys, json, re, random, urllib.request, urllib.error
from datetime import datetime, timedelta, date
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify, abort)
from flask_mysqldb import MySQL

# ── add utils to path ─────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))
from auth_utils import (hash_password, check_password, generate_token, generate_otp,
                        validate_password_strength, mask_email,
                        get_client_ip, get_device_info,
                        send_password_reset_email, send_login_notification_email,
                        send_logout_notification_email, send_welcome_email,
                        send_streak_milestone_email, send_otp_email)
from db_helpers import (get_cursor, ensure_tables, get_streak, update_streak,
                        log_activity, add_notification, get_unread_notifications,
                        save_quiz_to_db, get_user_by_id, build_smart_plan)

# ─────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dietmate_ultra_secret_v4_change_in_prod')

app.config['MYSQL_HOST']     = os.environ.get('MYSQL_HOST',     'localhost')
app.config['MYSQL_USER']     = os.environ.get('MYSQL_USER',     'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', 'Harita@1234')
app.config['MYSQL_DB']       = os.environ.get('MYSQL_DB',       'dietmate_db')
app.config['MYSQL_CURSORCLASS'] = 'Cursor'

mysql = MySQL(app)

# ── Detect actual password column name at runtime ─────────────
_PW_COL = "password"  # will be updated on first request

def get_pw_col():
    """Detect whether users table uses 'password' or 'password_hash'."""
    global _PW_COL
    try:
        cur = get_cursor(mysql)
        cur.execute("SHOW COLUMNS FROM users LIKE 'password_hash'")
        if cur.fetchone():
            _PW_COL = "password_hash"
        else:
            _PW_COL = "password"
        cur.close()
    except Exception:
        pass
    return _PW_COL

# ── Image path resolver ────────────────────────────────────────
import os as _os

def resolve_image(filename, subfolder=None):
    """Resolve image filename to correct static path.
    Tries: as-is, meals/, recipes/, smoothies/ subfolders."""
    if not filename:
        return 'images/ui/default_recipe.jpg'
    filename = str(filename).strip()
    if filename.startswith('/'):
        return filename.lstrip('/')
    if filename.startswith('images/'):
        return filename
    if '/' in filename:
        return 'images/' + filename
    # Try to find in subfolders
    static_base = _os.path.join(_os.path.dirname(__file__), 'static', 'images')
    for sub in (subfolder, 'meals', 'recipes', 'smoothies', ''):
        if sub is None:
            continue
        path = _os.path.join(static_base, sub, filename) if sub else _os.path.join(static_base, filename)
        if _os.path.exists(path):
            return ('images/' + sub + '/' + filename) if sub else ('images/' + filename)
    # Default: assume smoothies subfolder when possible
    return ('images/' + subfolder.strip('/') + '/' + filename) if subfolder else ('images/' + filename)

@app.context_processor
def inject_image_helper():
    return dict(resolve_image=resolve_image)

# ─────────────────────────────────────────────────────────
#  GOOGLE CLOUD VISION API KEY  (for food image recognition)
#  Flow: Image → Google Vision → food labels → Ninjas Nutrition → Result
# ─────────────────────────────────────────────────────────
GOOGLE_VISION_API_KEY = os.environ.get('GOOGLE_VISION_API_KEY', 'AIzaSyDulJ11UJrJBc08Es1frKVloV9QeRTh-80')
NINJAS_API_KEY        = os.environ.get('NINJAS_API_KEY',        'lzdgzmik9cJCbpHdMUYOcCpUye2r89BCr2rUOB7r')

HEALTHY_TIPS = [
    "Drink a glass of water before every meal to naturally control portions.",
    "Protein at breakfast keeps you full longer and reduces mid-morning cravings.",
    "Add colour to your plate — eat the rainbow for more micronutrients.",
    "Chew slowly. It takes 20 minutes for your brain to register fullness.",
    "Meal prep on Sundays to avoid unhealthy last-minute weekday choices.",
    "Replace refined grains with whole grains for steady, sustained energy.",
    "Aim for 30 minutes of walking daily — burns ~150 kcal.",
    "Sleep 7-9 hours. Poor sleep raises hunger hormones (ghrelin) by 15%.",
    "Track your meals honestly — awareness alone reduces intake by 10-15%.",
    "Eat fibre-rich foods first — slows glucose absorption and prevents spikes.",
    "Strength training burns calories for 24-48 hours after your workout.",
    "Dark leafy greens are the most nutrient-dense foods on earth — eat them daily.",
    "Healthy fats from avocado and nuts help absorb fat-soluble vitamins A, D, E, K.",
    "Intermittent fasting helps many people — but it's not for everyone.",
    "Fermented foods like yogurt, idli, and kimchi support gut microbiome health.",
]


# ─────────────────────────────────────────────────────────
# HELPER: require login
# ─────────────────────────────────────────────────────────
def require_login():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return None


# ─────────────────────────────────────────────────────────
# HELPER: inject notifications count into every template
# ─────────────────────────────────────────────────────────
@app.context_processor
def inject_globals():
    notif_count = 0
    if 'user_id' in session:
        try:
            notifs = get_unread_notifications(mysql, session['user_id'])
            notif_count = len(notifs)
        except Exception:
            pass
    return dict(notif_count=notif_count)


# ─────────────────────────────────────────────────────────
# AI FOOD ANALYSIS
# ─────────────────────────────────────────────────────────
def analyze_food_with_google_vision(image_b64: str) -> str:
    """
    Step 1: Send image to Google Cloud Vision API.
    Returns the best food-related label detected in the image.
    Flow: Image (base64) → Google Vision labelDetection → food label string
    """
    url = (
        "https://vision.googleapis.com/v1/images:annotate"
        "?key=" + GOOGLE_VISION_API_KEY
    )
    payload = json.dumps({
        "requests": [{
            "image": {"content": image_b64},
            "features": [
                {"type": "LABEL_DETECTION",      "maxResults": 15},
                {"type": "WEB_DETECTION",         "maxResults": 5},
                {"type": "OBJECT_LOCALIZATION",   "maxResults": 5}
            ]
        }]
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json"
    }, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    responses = body.get("responses", [{}])[0]

    # ── Priority 1: Web detection bestGuessLabels (most accurate for food) ──
    web = responses.get("webDetection", {})
    best_guesses = web.get("bestGuessLabels", [])
    if best_guesses:
        label = best_guesses[0].get("label", "").strip()
        if label:
            return label

    # ── Priority 2: Label annotations — filter for food-related labels ──
    FOOD_KEYWORDS = {
        "food","dish","cuisine","meal","recipe","ingredient","vegetable","fruit",
        "bread","rice","pasta","soup","salad","meat","chicken","fish","seafood",
        "dessert","cake","pizza","burger","sandwich","curry","dal","roti","biryani",
        "snack","breakfast","lunch","dinner","drink","juice","smoothie","coffee","tea",
        "egg","cheese","milk","yogurt","noodle","sushi","taco","wrap","bowl","stew",
        "sauce","spice","herb","grain","bean","lentil","paneer","samosa","idli","dosa",
    }
    labels = responses.get("labelAnnotations", [])
    for lbl in labels:
        desc  = lbl.get("description", "").lower()
        score = lbl.get("score", 0)
        if score > 0.65 and any(kw in desc for kw in FOOD_KEYWORDS):
            return lbl["description"]

    # ── Priority 3: First high-confidence label regardless ──
    if labels:
        return labels[0].get("description", "food")

    return "food"


def analyze_food_with_vision_and_ninjas(image_b64: str) -> dict:
    """
    Complete pipeline: Image → Google Vision → food name → Ninjas Nutrition → structured result.
    This replaces the old Claude Vision pipeline.
    """
    # Step 1 — Identify food from image using Google Vision
    food_label = analyze_food_with_google_vision(image_b64)
    food_label_clean = food_label.strip().title()

    # Step 2 — Get nutrition data from Ninjas API using the identified label
    nutrition = get_nutrition_from_text(food_label)

    if nutrition and "error" not in nutrition:
        cal   = nutrition.get("calories", 0)
        prot  = nutrition.get("protein",  0)
        carbs = nutrition.get("carbs",    0)
        fat   = nutrition.get("fat",      0)
    else:
        # Fallback: try without title casing (API Ninjas is case-sensitive sometimes)
        nutrition2 = get_nutrition_from_text(food_label.lower())
        if nutrition2 and "error" not in nutrition2:
            cal   = nutrition2.get("calories", 0)
            prot  = nutrition2.get("protein",  0)
            carbs = nutrition2.get("carbs",    0)
            fat   = nutrition2.get("fat",      0)
        else:
            # Still no data — return identified name with zeroed nutrition
            cal = prot = carbs = fat = 0

    # Step 3 — Build health tags
    health_tags = _build_health_tags({
        "calories": cal, "protein": prot, "carbs": carbs, "fat": fat
    })

    # Step 4 — Build description
    description = (
        f"{food_label_clean} identified via Google Cloud Vision AI. "
        f"Nutritional values sourced from the API Ninjas database per standard serving."
    )

    return {
        "food_name":   food_label_clean,
        "description": description,
        "confidence":  "High" if cal > 0 else "Medium",
        "per_serving": {
            "calories":  int(cal),
            "protein_g": round(float(prot),  1),
            "carbs_g":   round(float(carbs), 1),
            "fat_g":     round(float(fat),   1),
            "fiber_g":   0,
            "sugar_g":   0,
        },
        "ingredients": [food_label_clean],
        "health_tags": health_tags,
        "notes": (
            f"Identified as '{food_label_clean}' by Google Vision. "
            "Values are per standard serving. Adjust quantities for your portion size."
        ),
    }

def get_nutrition_from_text(query: str) -> dict:
    url = "https://api.api-ninjas.com/v1/nutrition?query=" + urllib.request.quote(query)
    req = urllib.request.Request(url)
    req.add_header("X-Api-Key", NINJAS_API_KEY)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not data:
            return None
        item = data[0]
        return {"food_name": item.get("name","Unknown"),
                "calories": int(item.get("calories",0)),
                "protein":  int(item.get("protein_g",0)),
                "carbs":    int(item.get("carbohydrates_total_g",0)),
                "fat":      int(item.get("fat_total_g",0))}
    except Exception as e:
        return {"error": str(e)}


def normalize_food_queries(food_name: str) -> list:
    candidates = [food_name.strip()]
    if ',' in food_name:
        candidates.append(food_name.split(',')[0].strip())
    if '-' in food_name:
        candidates.append(food_name.split('-')[0].strip())
    words = [p for p in food_name.lower().replace(',', ' ').replace('-', ' ').split() if p]
    if len(words) > 1:
        candidates.append(' '.join(words[:2]))
        candidates.append(words[0])
        candidates.append(words[-1])
    seen = set(); results = []
    for s in candidates:
        if s and s not in seen:
            seen.add(s)
            results.append(s)
    return results


def search_open_food_facts(food_name: str) -> dict:
    for query in normalize_food_queries(food_name):
        try:
            search_url = (
                'https://world.openfoodfacts.org/cgi/search.pl?search_terms='
                + urllib.request.quote(query)
                + '&search_simple=1&action=process&json=1&page_size=2'
            )
            req = urllib.request.Request(search_url,
                headers={'User-Agent': 'DietMate/1.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                off_data = json.loads(resp.read().decode('utf-8'))
            products = off_data.get('products', [])
            if not products:
                continue
            p = products[0]
            n = p.get('nutriments', {})
            cal = int(n.get('energy-kcal_100g') or n.get('energy_100g') or 0)
            prot = round(float(n.get('proteins_100g', 0) or 0), 1)
            carbs = round(float(n.get('carbohydrates_100g', 0) or 0), 1)
            fat = round(float(n.get('fat_100g', 0) or 0), 1)
            fiber = round(float(n.get('fiber_100g', 0) or 0), 1)
            sugar = round(float(n.get('sugars_100g', 0) or 0), 1)
            name = p.get('product_name') or query
            return {
                'food_name': name.title(),
                'description': f'{name.title()} — data from Open Food Facts database.',
                'confidence': 'Medium',
                'per_serving': {
                    'calories': cal,
                    'protein_g': prot,
                    'carbs_g': carbs,
                    'fat_g': fat,
                    'fiber_g': fiber,
                    'sugar_g': sugar
                },
                'ingredients': [name.title()],
                'health_tags': _build_health_tags({'calories': cal, 'protein': prot, 'carbs': carbs, 'fat': fat}),
                'notes': 'Values are per 100g from Open Food Facts. Adjust for your portion.'
            }
        except Exception:
            continue
    return None


def search_local_recipe_nutrition(food_name: str) -> dict:
    q = food_name.strip().lower()
    if not q:
        return None
    patterns = [f'%{q}%']
    if q.split():
        patterns.append(f'%{q.split()[0]}%')
        if len(q.split()) > 1:
            patterns.append(f'%{q.split()[-1]}%')
    cur = get_cursor(mysql)
    for pat in patterns:
        cur.execute(
            "SELECT r.recipe_name, COALESCE(n.calories,0), COALESCE(n.protein,0), "
            "COALESCE(n.carbs,0), COALESCE(n.fat,0), COALESCE(n.fiber,0), "
            "COALESCE(n.sugar,0) "
            "FROM recipes r JOIN meals m ON r.meal_id=m.meal_id "
            "LEFT JOIN nutrition n ON n.meal_id=m.meal_id "
            "WHERE LOWER(r.recipe_name) LIKE %s LIMIT 1",
            (pat,))
        row = cur.fetchone()
        if row:
            cur.close()
            return {
                'food_name': str(row[0]).title(),
                'description': f'Nutritional estimate for {row[0]}.',
                'confidence': 'Medium',
                'per_serving': {
                    'calories': int(row[1]),
                    'protein_g': round(float(row[2]), 1),
                    'carbs_g': round(float(row[3]), 1),
                    'fat_g': round(float(row[4]), 1),
                    'fiber_g': round(float(row[5]), 1),
                    'sugar_g': round(float(row[6]), 1)
                },
                'ingredients': [str(row[0]).title()],
                'health_tags': _build_health_tags({'calories': row[1], 'protein': row[2], 'carbs': row[3], 'fat': row[4]}),
                'notes': 'Estimated from local recipe database. Adjust for your portion.'
            }
    cur.close()
    return None


# ═══════════════════════════════════════════════════════════
#  AUTH ROUTES
# ═══════════════════════════════════════════════════════════

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        email    = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        cur      = get_cursor(mysql)
        # Try both column names for compatibility
        user = None
        pw_col = "password"
        for col in ["password", "password_hash"]:
            try:
                cur.execute(
                    f"SELECT user_id, name, goal, food_type, {col} "
                    "FROM users WHERE LOWER(email)=%s",
                    (email,))
                user = cur.fetchone()
                pw_col = col
                break
            except Exception:
                cur = get_cursor(mysql)
        cur.close()

        if user and check_password(password, user[4]):
            uid = user[0]
            session.update({
                'user_id':      uid,
                'user_name':    user[1],
                'goal':         user[2] or '',
                'food_type':    user[3] or 'veg',
                'calories':     2000,
                'protein_goal': 120,
                'carbs_goal':   250,
                'fat_goal':     55,
                'bmi':          0.0,
                'quiz_done':    False,
            })
            # Update last login
            cur2 = get_cursor(mysql)
            cur2.execute(
                "UPDATE users SET last_login=NOW() WHERE user_id=%s",
                (uid,))
            mysql.connection.commit()
            cur2.close()

            ip     = get_client_ip()
            device = get_device_info()
            log_activity(mysql, uid, 'login', ip, device)
            ensure_tables(mysql)

            # Send login notification email (non-blocking)
            try:
                cur3 = get_cursor(mysql)
                cur3.execute("SELECT email,name FROM users WHERE user_id=%s", (uid,))
                u = cur3.fetchone(); cur3.close()
                if u:
                    send_login_notification_email(
                        u[0], u[1], device, ip,
                        datetime.now().strftime('%d %b %Y, %I:%M %p'))
            except Exception:
                pass

            flash(f'Welcome back, {user[1]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            # Log failed attempt
            if user:
                log_activity(mysql, user[0], 'failed', get_client_ip(), get_device_info())
            error = 'Invalid email or password. Please try again.'

    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    # Step 1: collect details
    if request.method == 'POST':
        step = request.form.get('step', '1')

        if step == '1':
            name     = request.form.get('name','').strip()
            email    = request.form.get('email','').strip().lower()
            password = request.form.get('password','')
            age      = request.form.get('age', 25)
            gender   = request.form.get('gender','')
            height   = request.form.get('height', 170)
            weight   = request.form.get('weight', 70)
            goal     = request.form.get('goal','')

            valid, msg = validate_password_strength(password)
            if not valid:
                return render_template('register.html', error=msg, step=1)

            cur = get_cursor(mysql)
            cur.execute("SELECT user_id FROM users WHERE LOWER(email)=%s", (email,))
            if cur.fetchone():
                cur.close()
                return render_template('register.html', error='Email already registered.', step=1)
            cur.close()

            # Generate OTP and store in session
            otp = generate_otp(6)
            session['reg_pending'] = {
                'name': name, 'email': email, 'password': password,
                'age': age, 'gender': gender, 'height': height,
                'weight': weight, 'goal': goal, 'otp': otp
            }
            # Send OTP email
            try:
                send_otp_email(email, name, otp)
                flash(f'Verification code sent to {mask_email(email)}. Check your inbox.', 'info')
            except Exception:
                # If email fails, skip verification
                session['reg_pending']['otp'] = 'SKIP'
                flash('Email sending failed — proceeding without verification.', 'info')
            from flask import get_flashed_messages
            get_flashed_messages()  # consume/clear any pending flashes
            return render_template('verify_email.html', email=mask_email(email))

        elif step == 'verify':
            pending = session.get('reg_pending')
            if not pending:
                return redirect(url_for('register'))
            entered_otp = request.form.get('otp','').strip()
            if pending['otp'] != 'SKIP' and entered_otp != pending['otp']:
                return render_template('verify_email.html',
                    email=mask_email(pending['email']),
                    error='Incorrect code. Please try again.')

            # Register the user
            pw_hash = hash_password(pending['password'])
            cur = get_cursor(mysql)
            try:
                pw_col = get_pw_col()
                cur.execute(
                    f"INSERT INTO users(name,email,{pw_col},age,gender,height,weight) "
                    f"VALUES(%s,%s,%s,%s,%s,%s,%s)",
                    (pending['name'], pending['email'], pw_hash,
                     pending['age'], pending['gender'],
                     pending['height'], pending['weight']))
                mysql.connection.commit()
                cur.close()
                session.pop('reg_pending', None)
                ensure_tables(mysql)
                try:
                    send_welcome_email(pending['email'], pending['name'])
                except Exception:
                    pass
                flash('Account created! Please sign in.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                cur.close()
                error = f'Registration failed: {str(e)}'
                return render_template('register.html', error=error, step=1)

        elif step == 'resend':
            pending = session.get('reg_pending')
            if pending:
                otp = generate_otp(6)
                pending['otp'] = otp
                session['reg_pending'] = pending
                try:
                    send_otp_email(pending['email'], pending['name'], otp)
                    flash('New code sent!', 'success')
                except Exception:
                    flash('Could not resend email.', 'error')
            return render_template('verify_email.html',
                email=mask_email(pending['email']) if pending else '')

    return render_template('register.html', error=error, step=1)


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    message = None
    error   = None
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        cur   = get_cursor(mysql)
        cur.execute("SELECT user_id, name FROM users WHERE LOWER(email)=%s", (email,))
        user = cur.fetchone()
        if user:
            token  = generate_token(48)
            expiry = datetime.now() + timedelta(hours=1)
            # Try to save reset token (columns may not exist in base schema)
            try:
                cur.execute(
                    "UPDATE users SET reset_token=%s, reset_expiry=%s WHERE user_id=%s",
                    (token, expiry, user[0]))
                mysql.connection.commit()
            except Exception:
                # Columns don't exist — store token in session as fallback
                session[f'reset_{user[0]}'] = {'token': token, 'expiry': str(expiry)}
            cur.close()
            # Try sending email
            try:
                from auth_utils import SMTP_USER, SMTP_PASSWORD
                if SMTP_USER == 'your_email@gmail.com':
                    # SMTP not configured — show token directly for dev
                    message = f'[DEV MODE] Your reset token: {token[:16]}... (Email not configured)'
                else:
                    base_url = request.host_url.rstrip('/')
                    import auth_utils as _au; _au.APP_URL = base_url
                    sent = send_password_reset_email(email, user[1], token)
                    message = ('Reset link sent to ' + mask_email(email) + '. Check your inbox.'
                               if sent else 'Email failed. Contact support.')
            except Exception as ex:
                error = f'Email error: {str(ex)}'
        else:
            cur.close()
            message = f'If {mask_email(email)} is registered, a reset link has been sent.'

    return render_template('forgot_password.html', message=message, error=error)


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    error = None
    cur   = get_cursor(mysql)
    user = None
    try:
        cur.execute(
            "SELECT user_id, name FROM users WHERE reset_token=%s AND reset_expiry > NOW()",
            (token,))
        user = cur.fetchone()
    except Exception:
        # reset_token column doesn't exist — check session fallback
        for key in list(session.keys()):
            if key.startswith('reset_') and isinstance(session[key], dict):
                if session[key].get('token') == token:
                    uid_str = key.replace('reset_', '')
                    try:
                        cur2 = get_cursor(mysql)
                        cur2.execute("SELECT user_id, name FROM users WHERE user_id=%s", (uid_str,))
                        user = cur2.fetchone()
                        cur2.close()
                    except Exception:
                        pass
                    break
    cur.close()

    if not user:
        flash('Reset link is invalid or has expired. Please request a new one.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password  = request.form.get('password','')
        password2 = request.form.get('confirm_password','')

        if password != password2:
            error = 'Passwords do not match.'
        else:
            valid, msg = validate_password_strength(password)
            if not valid:
                error = msg
            else:
                pw_hash = hash_password(password)
                cur2 = get_cursor(mysql)
                cur2.execute(
                    "UPDATE users SET password=%s WHERE user_id=%s", (pw_hash, user[0]))
                mysql.connection.commit()
                cur2.close()
                flash('Password reset successfully. Please sign in.', 'success')
                return redirect(url_for('login'))

    return render_template('reset_password.html', token=token, error=error, name=user[1])


@app.route('/logout')
def logout():
    if 'user_id' in session:
        uid  = session['user_id']
        name = session.get('user_name','')
        ip   = get_client_ip()
        device = get_device_info()
        log_activity(mysql, uid, 'logout', ip, device)
        # Send logout email
        try:
            cur = get_cursor(mysql)
            cur.execute("SELECT email FROM users WHERE user_id=%s", (uid,))
            row = cur.fetchone(); cur.close()
            if row:
                send_logout_notification_email(
                    row[0], name,
                    datetime.now().strftime('%d %b %Y, %I:%M %p'))
        except Exception:
            pass
    session.clear()
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('login'))


# ═══════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════
@app.route('/dashboard')
def dashboard():
    r = require_login()
    if r: return r
    uid = session['user_id']
    ensure_tables(mysql)
    cur = get_cursor(mysql)

    cur.execute("SELECT COUNT(*) FROM recipes")
    total_recipes = int(cur.fetchone()[0])
    cur.execute("SELECT COUNT(DISTINCT meal_time) FROM weekly_diet")
    meal_types = int(cur.fetchone()[0])
    cur.execute("SELECT COUNT(DISTINCT goal) FROM weekly_diet")
    diet_plans = int(cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM smoothies")
    total_smoothies = int(cur.fetchone()[0])
    cur.execute(
        "SELECT COALESCE(SUM(calories),0) FROM user_meal_progress "
        "WHERE user_id=%s AND log_date=CURDATE() AND completed=TRUE", (uid,))
    calories_today = int(cur.fetchone()[0])
    goal_cal = session.get('calories', 2000)
    remaining = max(0, goal_cal - calories_today)
    cur.execute(
        "SELECT COALESCE(glasses,0) FROM water_log WHERE user_id=%s AND log_date=CURDATE()", (uid,))
    row = cur.fetchone()
    water_today = int(row[0]) if row else 0

    # Days away
    cur.execute("SELECT last_login FROM users WHERE user_id=%s", (uid,))
    row = cur.fetchone()
    days_away = 0
    if row and row[0]:
        try:
            days_away = (datetime.now() - row[0]).days
        except Exception:
            pass
    cur.close()

    return render_template('dashboard.html',
        user_name       = session.get('user_name','Friend'),
        total_recipes   = total_recipes,
        meal_types      = meal_types,
        diet_plans      = diet_plans,
        total_smoothies = total_smoothies,
        calories_today  = calories_today,
        remaining_calories = remaining,
        water_today     = water_today,
        healthy_tips    = random.choice(HEALTHY_TIPS),
        streak          = get_streak(mysql, uid),
        days_away       = days_away,
        quiz_done       = session.get('quiz_done', False))


# ═══════════════════════════════════════════════════════════
#  PROGRESS API (JSON for dashboard macro bars)
# ═══════════════════════════════════════════════════════════
@app.route('/progress_api_today')
def progress_api_today():
    if 'user_id' not in session:
        return jsonify({'error': 'not logged in'}), 401
    uid      = session['user_id']
    goal_cal = session.get('calories', 2000)
    protein_goal = session.get('protein_goal', 120)
    fat_goal     = session.get('fat_goal', 55)
    carbs_goal   = session.get('carbs_goal', 250)

    ensure_tables(mysql)
    cur = get_cursor(mysql)
    cur.execute(
        "SELECT COALESCE(SUM(calories),0), COALESCE(SUM(protein),0), "
        "COALESCE(SUM(carbs),0), COALESCE(SUM(fat),0) "
        "FROM user_meal_progress WHERE user_id=%s AND log_date=CURDATE() AND completed=TRUE",
        (uid,))
    row = cur.fetchone()
    cal    = int(row[0] or 0)
    prot   = round(float(row[1] or 0), 1)
    carbs  = round(float(row[2] or 0), 1)
    fat    = round(float(row[3] or 0), 1)

    cur.execute(
        "SELECT meal_name, calories FROM user_meal_progress "
        "WHERE user_id=%s AND log_date=CURDATE() AND completed=TRUE ORDER BY logged_at LIMIT 8",
        (uid,))
    meals_rows = cur.fetchall()
    cur.close()

    return jsonify({
        'calories': cal, 'protein': prot, 'carbs': carbs, 'fat': fat,
        'calorie_goal': goal_cal, 'protein_goal': protein_goal,
        'fat_goal': fat_goal, 'carbs_goal': carbs_goal,
        'meals': [{'name': r[0], 'cal': int(r[1])} for r in meals_rows]
    })


# ═══════════════════════════════════════════════════════════
#  HEALTH QUIZ
# ═══════════════════════════════════════════════════════════
@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    r = require_login()
    if r: return r

    # If quiz already done, pre-fill with saved data
    user = get_user_by_id(mysql, session['user_id'])

    if request.method == 'POST':
        weight        = float(request.form.get('weight', user.get('weight', 70) or 70))
        height        = float(request.form.get('height', user.get('height', 170) or 170))
        age           = int(request.form.get('age', user.get('age', 25) or 25))
        target_weight = float(request.form.get('target_weight', weight))
        activity      = float(request.form.get('activity', 1.55))
        gender        = user.get('gender', 'Male') or 'Male'

        h_m  = height / 100
        bmi  = round(weight / (h_m ** 2), 1)
        if bmi < 18.5:   bmi_cat = 'Underweight'
        elif bmi < 25:   bmi_cat = 'Normal'
        elif bmi < 30:   bmi_cat = 'Overweight'
        else:            bmi_cat = 'Obese'

        diff = target_weight - weight
        if abs(diff) < 2:   goal = 'Muscle Gain'
        elif diff > 0:       goal = 'Weight Gain'
        else:                goal = 'Weight Loss'

        # Mifflin-St Jeor BMR
        if gender == 'Female':
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        tdee = bmr * activity

        if goal == 'Weight Loss':   cal = int(tdee - 500)
        elif goal == 'Weight Gain': cal = int(tdee + 300)
        else:                       cal = int(tdee)
        cal = max(1200, min(cal, 4500))

        protein = int(weight * 2.0)
        fat     = int(cal * 0.25 / 9)
        carbs   = int((cal - protein * 4 - fat * 9) / 4)

        # Save to session
        session.update({
            'calories': cal, 'goal': goal,
            'protein_goal': protein, 'fat_goal': fat,
            'carbs_goal': carbs, 'quiz_done': True,
            'bmi': bmi
        })

        # Persist to DB
        try:
            save_quiz_to_db(mysql, session['user_id'],
                            cal, goal, protein, carbs, fat, bmi, bmi_cat, weight)
        except Exception:
            pass
        add_notification(mysql, session['user_id'],
                         f'Health quiz completed — {goal} plan activated ({cal} kcal/day)',
                         'success', '/dietselect')

        return render_template('quiz_result.html',
            calories=cal, protein=protein, carbs=carbs, fat=fat,
            goal=goal, bmi=bmi, bmi_category=bmi_cat)

    return render_template('health_quiz.html', user=user)


# ═══════════════════════════════════════════════════════════
#  DIET SELECT & AUTO DIET
# ═══════════════════════════════════════════════════════════
@app.route('/dietselect')
def dietselect():
    r = require_login()
    if r: return r
    goal_cal = session.get('calories', 2000)
    goal     = session.get('goal', '')
    return render_template('dietselect.html', goal_cal=goal_cal, goal=goal)


@app.route('/auto_diet', methods=['GET', 'POST'])
def auto_diet():
    r = require_login()
    if r: return r
    uid       = session['user_id']
    goal      = session.get('goal', 'Weight Loss')
    target    = session.get('calories', 2000)
    diet_type = request.form.get('diet_type', session.get('food_type', 'veg'))
    session['food_type'] = diet_type

    ensure_tables(mysql)
    plan = build_smart_plan(mysql, goal, diet_type, target)

    # Mark already-logged meals
    cur = get_cursor(mysql)
    cur.execute(
        "SELECT LOWER(meal_name) FROM user_meal_progress "
        "WHERE user_id=%s AND log_date=CURDATE() AND completed=TRUE", (uid,))
    logged_names = {r[0] for r in cur.fetchall()}
    for slot, foods in plan.items():
        for food in foods:
            display = food.get('display_name', food['name'])
            food['logged'] = (display.lower() in logged_names or
                              food['name'].lower() in logged_names)

    cur.execute(
        "SELECT COALESCE(SUM(calories),0), COALESCE(SUM(protein),0), "
        "COALESCE(SUM(carbs),0), COALESCE(SUM(fat),0) "
        "FROM user_meal_progress WHERE user_id=%s AND log_date=CURDATE() AND completed=TRUE",
        (uid,))
    row = cur.fetchone()
    logged_today = int(row[0] or 0)
    prot_today   = float(row[1] or 0)
    carbs_today  = float(row[2] or 0)
    fat_today    = float(row[3] or 0)
    cur.close()

    planned_cal = sum(f['cal'] for foods in plan.values() for f in foods)
    remaining   = max(0, target - logged_today)

    return render_template('auto_diet.html',
        meals        = plan,
        goal         = goal,
        total        = target,
        logged_today = logged_today,
        remaining_cal= remaining,
        planned_cal  = planned_cal,
        prot_today   = round(prot_today, 1),
        carbs_today  = round(carbs_today, 1),
        fat_today    = round(fat_today, 1),
        protein_goal = session.get('protein_goal', 120),
        carbs_goal   = session.get('carbs_goal', 250),
        fat_goal     = session.get('fat_goal', 55))


@app.route('/complete_meal', methods=['POST'])
def complete_meal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    uid       = session['user_id']
    meal_id   = request.form.get('meal_id')
    meal_name = request.form.get('meal_name','')
    calories  = int(request.form.get('calories', 0))
    meal_time = request.form.get('meal_time','')
    ensure_tables(mysql)

    cur = get_cursor(mysql)
    # Get macros from nutrition table if meal_id available
    protein = carbs = fat = 0.0
    if meal_id:
        cur.execute(
            "SELECT COALESCE(protein,0), COALESCE(carbs,0), COALESCE(fat,0) "
            "FROM nutrition WHERE meal_id=%s", (meal_id,))
        nrow = cur.fetchone()
        if nrow:
            protein, carbs, fat = float(nrow[0]), float(nrow[1]), float(nrow[2])

    cur.execute(
        "INSERT INTO user_meal_progress(user_id,meal_id,meal_name,calories,protein,carbs,fat,"
        "meal_time,log_date,logged_at,completed) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,CURDATE(),NOW(),TRUE)",
        (uid, meal_id or None, meal_name, calories, protein, carbs, fat, meal_time))
    mysql.connection.commit()
    cur.close()
    update_streak(mysql, uid)
    # Check streak milestones
    streak_data = get_streak(mysql, uid)
    current_streak = streak_data.get('current', 0)
    milestones = {10: 'Bronze Streak', 25: 'Silver Streak', 50: 'Gold Streak', 75: 'Platinum Streak', 100: 'Diamond Streak'}
    if current_streak in milestones:
        badge = milestones[current_streak]
        add_notification(mysql, uid,
            f'Achievement unlocked: {badge}! You reached a {current_streak}-day streak!',
            'success', '/progress')
        try:
            cur3 = get_cursor(mysql)
            cur3.execute("SELECT email, name FROM users WHERE user_id=%s", (uid,))
            urow = cur3.fetchone()
            cur3.close()
            if urow:
                send_streak_milestone_email(urow[0], urow[1], current_streak, badge)
        except Exception:
            pass
    flash(f'Logged: {meal_name} — +{calories} kcal', 'success')
    return redirect(url_for('auto_diet'))


# ═══════════════════════════════════════════════════════════
#  RECIPES (full detail pages with ingredients, charts, ratings)
# ═══════════════════════════════════════════════════════════
@app.route('/recipes')
def recipes():
    r = require_login()
    if r: return r
    uid = session['user_id']
    cur = get_cursor(mysql)
    cur.execute("SHOW COLUMNS FROM recipes")
    r_cols = {row[0] for row in cur.fetchall()}
    cur.execute("SHOW COLUMNS FROM meals")
    m_cols = {row[0] for row in cur.fetchall()}

    img_c  = "r.image_url"  if "image_url"  in r_cols else "NULL"
    cuis_c = "r.cuisine"    if "cuisine"    in r_cols else "'Indian'"
    tags_c = "r.tags"       if "tags"       in r_cols else "'healthy'"
    prep_c = "m.prep_time"  if "prep_time"  in m_cols else "0"
    diff_c = "m.difficulty" if "difficulty" in m_cols else "'Easy'"
    cat_c  = "m.category"   if "category"   in m_cols else "'veg'"
    type_c = "m.meal_type"  if "meal_type"  in m_cols else "'lunch'"
    name_c = "m.meal_name"  if "meal_name"  in m_cols else "r.recipe_name"

    # Use ANY_VALUE() for non-aggregated columns to support only_full_group_by mode
    q = (
        "SELECT r.recipe_id, r.recipe_name, ANY_VALUE(" + name_c + "), "
        + "ANY_VALUE(" + img_c + "), ANY_VALUE(" + cuis_c + "), ANY_VALUE(" + tags_c + "), "
        + "ANY_VALUE(" + cat_c + "), ANY_VALUE(" + type_c + "), COALESCE(ANY_VALUE(" + prep_c + "),0), "
        + "ANY_VALUE(" + diff_c + "), COALESCE(ANY_VALUE(n.calories),0), COALESCE(ANY_VALUE(n.protein),0), "
        "COALESCE(ANY_VALUE(n.carbs),0), COALESCE(ANY_VALUE(n.fat),0), COALESCE(ANY_VALUE(n.fiber),0), "
        "COALESCE(AVG(mr.rating),0), COUNT(mr.rating_id), "
        "CASE WHEN f.id IS NOT NULL THEN 1 ELSE 0 END AS is_fav "
        "FROM recipes r "
        "JOIN meals m ON r.meal_id=m.meal_id "
        "LEFT JOIN nutrition n ON n.meal_id=m.meal_id "
        "LEFT JOIN meal_ratings mr ON mr.meal_id=m.meal_id "
        "LEFT JOIN user_favorites f ON f.recipe_id=r.recipe_id AND f.user_id=%s "
        "GROUP BY r.recipe_id, r.recipe_name "
        "ORDER BY r.recipe_name"
    )
    try:
        cur.execute(q, (uid,))
        rows = cur.fetchall()
    except Exception as e:
        app.logger.error("recipes query failed: " + str(e))
        cur.execute(
            "SELECT r.recipe_id, r.recipe_name, r.recipe_name, NULL, "
            "'Indian', 'healthy', 'veg', 'lunch', 0, 'Easy', "
            "COALESCE(ANY_VALUE(n.calories),0), COALESCE(ANY_VALUE(n.protein),0), "
            "COALESCE(ANY_VALUE(n.carbs),0), COALESCE(ANY_VALUE(n.fat),0), COALESCE(ANY_VALUE(n.fiber),0), 0, 0, 0 "
            "FROM recipes r JOIN meals m ON r.meal_id=m.meal_id "
            "LEFT JOIN nutrition n ON n.meal_id=m.meal_id "
            "GROUP BY r.recipe_id, r.recipe_name ORDER BY r.recipe_name")
        rows = cur.fetchall()
    cur.close()

    # Normalize difficulty values from DB to standard set
    def _norm_diff(d):
        d = str(d or 'Easy').strip()
        dl = d.lower()
        if dl in ('hard', 'difficult', 'advanced'): return 'Hard'
        if dl in ('medium', 'moderate', 'intermediate'): return 'Medium'
        return 'Easy'

    # Normalize meal_type values from DB to standard set
    def _norm_type(t):
        t = str(t or 'lunch').strip().lower()
        if t in ('breakfast', 'morning', 'early morning'): return 'breakfast'
        if t in ('dinner', 'supper', 'evening meal'): return 'dinner'
        if t in ('snack', 'snacks', 'mid snack', 'evening snack', 'morning snack'): return 'snack'
        return 'lunch'

    seen_ids = set()
    seen_names = set()
    recipes_list = []
    for row in rows:
        rid_val = int(row[0])
        name_lower = str(row[1] or '').strip().lower()
        # Deduplicate by recipe_id and normalized name
        if rid_val in seen_ids or (name_lower and name_lower in seen_names):
            continue
        seen_ids.add(rid_val)
        if name_lower:
            seen_names.add(name_lower)

        img = str(row[3] or '')
        # Build image path: try recipes/ subfolder
        if not img:
            img_path = ''
        elif img.startswith('images/'):
            img_path = img
        elif '/' in img:
            img_path = 'images/' + img.lstrip('/')
        else:
            img_path = 'images/recipes/' + img

        cat_raw = str(row[6] or 'veg').lower().strip()
        name_lower = str(row[1] or '').lower()
        # Smart veg/nonveg: check DB category first, then detect from recipe name
        NONVEG_KEYWORDS = [
            'chicken','mutton','beef','pork','lamb','prawn','shrimp','fish','salmon',
            'tuna','crab','lobster','egg','keema','mince','turkey','duck','meat',
            'anchovy','sardine','mackerel','bacon','ham','sausage','pepperoni',
            'biryani chicken','butter chicken','tikka','seekh','kabab','kheema',
            'rogan josh','nihari','haleem'
        ]
        if cat_raw in ('nonveg','non-veg','non veg','nonvegetarian','non-vegetarian'):
            cat = 'nonveg'
        elif any(kw in name_lower for kw in NONVEG_KEYWORDS):
            cat = 'nonveg'
        else:
            cat = 'veg'

        recipes_list.append({
            'recipe_id':    rid_val,
            'name':         str(row[1] or ''),
            'description':  str(row[2] or '')[:100],
            'image':        img_path,
            'cuisine':      str(row[4] or 'Indian'),
            'tags':         str(row[5] or ''),
            'category':     cat,
            'meal_type':    _norm_type(row[7]),
            'prep_time':    int(row[8] or 0),
            'difficulty':   _norm_diff(row[9]),
            'calories':     int(row[10] or 0),
            'protein':      round(float(row[11] or 0), 1),
            'carbs':        round(float(row[12] or 0), 1),
            'fat':          round(float(row[13] or 0), 1),
            'fiber':        round(float(row[14] or 0), 1),
            'rating':       round(float(row[15] or 0), 1),
            'rating_count': int(row[16] or 0),
            'is_fav':       bool(row[17] or 0),
        })

    return render_template('recipes.html',
        recipes=recipes_list, user_goal=session.get('goal',''))

@app.route('/recipe/<int:rid>')
def recipe_detail(rid):
    r = require_login()
    if r: return r
    uid = session['user_id']
    cur = get_cursor(mysql)

    cur.execute("SHOW COLUMNS FROM recipes")
    r_cols = {row[0] for row in cur.fetchall()}
    cur.execute("SHOW COLUMNS FROM meals")
    m_cols = {row[0] for row in cur.fetchall()}

    img_c   = "r.image_url"  if "image_url"  in r_cols else "NULL"
    cuis_c  = "r.cuisine"    if "cuisine"    in r_cols else "'Indian'"
    tags_c  = "r.tags"       if "tags"       in r_cols else "'healthy'"
    prep_c  = "m.prep_time"  if "prep_time"  in m_cols else "0"
    diff_c  = "m.difficulty" if "difficulty" in m_cols else "'Easy'"
    cat_c   = "m.category"   if "category"   in m_cols else "'veg'"
    type_c  = "m.meal_type"  if "meal_type"  in m_cols else "'lunch'"

    q = (
        "SELECT r.recipe_id,r.recipe_name,r.instructions,"
        + "ANY_VALUE(" + img_c  + ") AS img,"
        + "COALESCE(ANY_VALUE(" + prep_c + "),0),"
        + "ANY_VALUE(" + diff_c + "),ANY_VALUE(" + cat_c + "),ANY_VALUE(" + type_c + "),"
        + "ANY_VALUE(" + cuis_c + "),ANY_VALUE(" + tags_c + "),"
        + "COALESCE(ANY_VALUE(n.calories),0),COALESCE(ANY_VALUE(n.protein),0),"
        + "COALESCE(ANY_VALUE(n.carbs),0),COALESCE(ANY_VALUE(n.fat),0),"
        + "COALESCE(ANY_VALUE(n.fiber),0),COALESCE(ANY_VALUE(n.sugar),0),"
        + "COALESCE(AVG(mr.rating),0),COUNT(mr.rating_id)"
        + " FROM recipes r"
        + " JOIN meals m ON r.meal_id=m.meal_id"
        + " LEFT JOIN nutrition n ON n.meal_id=m.meal_id"
        + " LEFT JOIN meal_ratings mr ON mr.meal_id=m.meal_id"
        + " WHERE r.recipe_id=%s GROUP BY r.recipe_id, r.recipe_name, r.instructions"
    )
    try:
        cur.execute(q, (rid,))
        row = cur.fetchone()
    except Exception:
        cur.execute(
            "SELECT r.recipe_id,r.recipe_name,r.instructions,"
            "NULL,0,'Easy','veg','lunch','Indian','healthy',"
            "COALESCE(n.calories,0),COALESCE(n.protein,0),"
            "COALESCE(n.carbs,0),COALESCE(n.fat,0),"
            "COALESCE(n.fiber,0),COALESCE(n.sugar,0),0,0"
            " FROM recipes r JOIN meals m ON r.meal_id=m.meal_id"
            " LEFT JOIN nutrition n ON n.meal_id=m.meal_id"
            " WHERE r.recipe_id=%s", (rid,))
        row = cur.fetchone()

    if not row:
        cur.close()
        flash('Recipe not found.', 'error')
        return redirect(url_for('recipes'))

    try:
        cur.execute(
            "SELECT u.name,mr.rating,mr.comment,mr.rated_at"
            " FROM meal_ratings mr JOIN users u ON mr.user_id=u.user_id"
            " WHERE mr.meal_id=(SELECT meal_id FROM recipes WHERE recipe_id=%s)"
            " AND mr.comment IS NOT NULL AND mr.comment!=''"
            " ORDER BY mr.rated_at DESC LIMIT 5", (rid,))
        reviews = cur.fetchall()
    except Exception:
        reviews = []

    rel_img = ("r2.image_url" if "image_url" in r_cols else "NULL")
    try:
        cur.execute(
            "SELECT r2.recipe_id,r2.recipe_name,"
            + rel_img + ","
            + "COALESCE(n2.calories,0)"
            + " FROM recipes r2 JOIN meals m2 ON r2.meal_id=m2.meal_id"
            + " LEFT JOIN nutrition n2 ON n2.meal_id=m2.meal_id"
            + " WHERE r2.recipe_id!=%s ORDER BY RAND() LIMIT 4",
            (rid,))
        related = cur.fetchall()
    except Exception:
        related = []

    cur.execute(
        "SELECT id FROM user_favorites WHERE user_id=%s AND recipe_id=%s",
        (uid, rid))
    is_fav = bool(cur.fetchone())

    img = str(row[3] or '')
    img_path = resolve_image(img, 'recipes') if img else ''

    cat_raw = str(row[6] or 'veg').lower().strip()
    name_lower2 = str(row[1] or '').lower()
    NONVEG_KEYWORDS2 = [
        'chicken','mutton','beef','pork','lamb','prawn','shrimp','fish','salmon',
        'tuna','crab','lobster','egg','keema','mince','turkey','duck','meat',
        'anchovy','sardine','mackerel','bacon','ham','sausage','pepperoni'
    ]
    if cat_raw in ('nonveg','non-veg','non veg','nonvegetarian','non-vegetarian'):
        cat = 'nonveg'
    elif any(kw in name_lower2 for kw in NONVEG_KEYWORDS2):
        cat = 'nonveg'
    else:
        cat = 'veg'

    instructions_text = str(row[2] or row[1] or 'No instructions available.')
    steps = [s.strip() for s in instructions_text.split('\n') if s.strip()]

    recipe = {
        'recipe_id':    int(row[0]),
        'name':         str(row[1] or ''),
        'description':  instructions_text[:150],
        'instructions': instructions_text,
        'image':        img_path,
        'prep_time':    int(row[4] or 0),
        'is_fav':       is_fav,
        'cook_time':    int(row[4] or 0),
        'servings':     1,
        'difficulty':   str(row[5] or 'Easy'),
        'category':     cat,
        'diet_type':    cat,
        'meal_type':    str(row[7] or 'lunch').lower(),
        'cuisine':      str(row[8] or 'Indian'),
        'tags':         str(row[9] or ''),
        'calories':     int(row[10] or 0),
        'protein':      round(float(row[11] or 0), 1),
        'carbs':        round(float(row[12] or 0), 1),
        'fat':          round(float(row[13] or 0), 1),
        'fiber':        round(float(row[14] or 0), 1),
        'sugar':        round(float(row[15] or 0), 1),
        'rating':       round(float(row[16] or 0), 1),
        'rating_count': int(row[17] or 0),
        'goal':         session.get('goal', ''),
        'user_rating':  0,
    }
    cur.close()
    return render_template('recipe_detail.html',
        recipe=recipe, steps=steps,
        reviews=reviews, related=related,
        ingredients=[])

@app.route('/recipe/<int:rid>/rate', methods=['POST'])
def rate_recipe(rid):
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    uid    = session['user_id']
    rating = int(request.form.get('rating', 0))
    review = request.form.get('review','').strip()
    if not 1 <= rating <= 5:
        return jsonify({'error': 'Rating must be 1-5'}), 400
    cur = get_cursor(mysql)
    cur.execute(
        "INSERT INTO meal_ratings(user_id,recipe_id,rating,review) VALUES(%s,%s,%s,%s) "
        "ON DUPLICATE KEY UPDATE rating=%s, review=%s",
        (uid, rid, rating, review, rating, review))
    # Update recipe avg rating
    cur.execute(
        "UPDATE recipes SET rating=(SELECT AVG(rating) FROM meal_ratings WHERE recipe_id=%s) "
        "WHERE recipe_id=%s", (rid, rid))
    mysql.connection.commit()
    cur.close()
    flash('Your rating has been saved!', 'success')
    return redirect(url_for('recipe_detail', rid=rid))


@app.route('/favorite/toggle', methods=['POST'])
def toggle_favorite():
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    uid         = session['user_id']
    recipe_id   = request.json.get('recipe_id')
    smoothie_id = request.json.get('smoothie_id')
    cur = get_cursor(mysql)
    if recipe_id:
        cur.execute(
            "SELECT id FROM user_favorites WHERE user_id=%s AND recipe_id=%s",
            (uid, recipe_id))
        if cur.fetchone():
            cur.execute(
                "DELETE FROM user_favorites WHERE user_id=%s AND recipe_id=%s",
                (uid, recipe_id))
            status = 'removed'
        else:
            cur.execute(
                "INSERT INTO user_favorites(user_id,recipe_id) VALUES(%s,%s)",
                (uid, recipe_id))
            status = 'added'
    elif smoothie_id:
        cur.execute(
            "SELECT id FROM user_favorites WHERE user_id=%s AND smoothie_id=%s",
            (uid, smoothie_id))
        if cur.fetchone():
            cur.execute(
                "DELETE FROM user_favorites WHERE user_id=%s AND smoothie_id=%s",
                (uid, smoothie_id))
            status = 'removed'
        else:
            cur.execute(
                "INSERT INTO user_favorites(user_id,smoothie_id) VALUES(%s,%s)",
                (uid, smoothie_id))
            status = 'added'
    else:
        cur.close()
        return jsonify({'error': 'No item specified'}), 400
    mysql.connection.commit()
    cur.close()
    return jsonify({'status': status})


@app.route('/favorites')
def favorites():
    r = require_login()
    if r: return r
    uid = session['user_id']
    cur = get_cursor(mysql)

    # Detect image column
    cur.execute("SHOW COLUMNS FROM recipes")
    rc = {row[0] for row in cur.fetchall()}
    img_col = "r.image_url" if "image_url" in rc else "NULL"

    try:
        cur.execute(f"""
            SELECT r.recipe_id, r.recipe_name, {img_col} AS img,
                   COALESCE(n.calories,0), COALESCE(n.protein,0),
                   4.0, m.category, m.difficulty, f.saved_at
            FROM user_favorites f
            JOIN recipes r ON f.recipe_id = r.recipe_id
            JOIN meals m ON r.meal_id = m.meal_id
            LEFT JOIN nutrition n ON n.meal_id = m.meal_id
            WHERE f.user_id = %s AND f.recipe_id IS NOT NULL
            ORDER BY f.saved_at DESC
        """, (uid,))
        fav_recipes = cur.fetchall()
    except Exception:
        fav_recipes = []

    try:
        cur.execute("""
            SELECT s.smoothie_id, s.name, s.image_file, s.calories,
                   s.protein, s.rating, s.goal_tag, f.saved_at
            FROM user_favorites f JOIN smoothies s ON f.smoothie_id = s.smoothie_id
            WHERE f.user_id = %s AND f.smoothie_id IS NOT NULL
            ORDER BY f.saved_at DESC
        """, (uid,))
        fav_smoothies = cur.fetchall()
    except Exception:
        fav_smoothies = []
    cur.close()

    return render_template('favorites.html',
        fav_recipes=fav_recipes, fav_smoothies=fav_smoothies)

@app.route('/smoothies')
def smoothies():
    r = require_login()
    if r: return r
    uid = session['user_id']
    cur = get_cursor(mysql)
    cur.execute("""
        SELECT s.smoothie_id, s.name, s.description, s.image_file,
               s.calories, s.protein, s.carbs, s.fat, s.fiber,
               s.goal_tag, s.diet_type, s.prep_time, s.color_hex,
               s.is_featured, s.rating, s.tags,
               CASE WHEN f.id IS NOT NULL THEN 1 ELSE 0 END AS is_fav
        FROM smoothies s
        LEFT JOIN user_favorites f ON f.smoothie_id=s.smoothie_id AND f.user_id=%s
        ORDER BY s.is_featured DESC, s.rating DESC
    """, (uid,))
    raw = cur.fetchall()
    cur.close()

    smoothies_list = []
    seen_sids = set()
    for row in raw:
        sid = int(row[0])
        if sid in seen_sids:
            continue
        seen_sids.add(sid)
        # Fix image path: resolve file names and subfolder paths consistently
        img_file = row[3] or ''
        img_path = resolve_image(img_file, 'smoothies') if img_file else ''
        smoothies_list.append({
            'smoothie_id': sid, 'name': row[1], 'description': row[2],
            'image': img_path,
            'calories': row[4], 'protein': row[5], 'carbs': row[6],
            'fat': row[7], 'fiber': row[8],
            'goal': row[9], 'diet_type': row[10], 'prep_time': row[11],
            'color': row[12] or '#7cfc9a',
            'is_featured': bool(row[13]), 'rating': float(row[14] or 4.0),
            'tags': row[15] or '', 'is_fav': bool(row[16])
        })

    featured     = [s for s in smoothies_list if s['is_featured']]
    non_featured = [s for s in smoothies_list if not s['is_featured']]
    # If nothing is featured, show all in the main grid
    main_grid    = non_featured if featured else smoothies_list
    wl_smoothies = [s for s in smoothies_list if s['goal'] == 'Weight Loss']
    mg_smoothies = [s for s in smoothies_list if s['goal'] == 'Muscle Gain']

    return render_template('smoothies.html',
        smoothies=main_grid,
        all_smoothies=smoothies_list,
        featured=featured,
        wl_smoothies=wl_smoothies,
        mg_smoothies=mg_smoothies,
        user_goal=session.get('goal',''))


@app.route('/smoothie/<int:sid>')
def smoothie_detail(sid):
    r = require_login()
    if r: return r
    uid = session['user_id']
    cur = get_cursor(mysql)
    cur.execute("""
        SELECT s.smoothie_id, s.name, s.description, s.ingredients,
               s.instructions, s.calories, s.protein, s.carbs, s.fat,
               s.fiber, s.sugar, s.goal_tag, s.diet_type, s.prep_time,
               s.color_hex, s.image_file, s.is_featured, s.rating, s.tags,
               CASE WHEN f.id IS NOT NULL THEN 1 ELSE 0 END AS is_fav
        FROM smoothies s
        LEFT JOIN user_favorites f ON f.smoothie_id=s.smoothie_id AND f.user_id=%s
        WHERE s.smoothie_id=%s
    """, (uid, sid))
    row = cur.fetchone()
    if not row:
        cur.close()
        flash('Smoothie not found.', 'error')
        return redirect(url_for('smoothies'))

    # Related smoothies
    cur.execute(
        "SELECT smoothie_id, name, image_file, calories, rating, color_hex "
        "FROM smoothies WHERE smoothie_id != %s ORDER BY rating DESC LIMIT 4",
        (sid,))
    related = cur.fetchall()
    cur.close()

    smoothie = {
        'smoothie_id': row[0], 'name': row[1], 'description': row[2],
        'ingredients_raw': row[3] or '',
        'ingredients': [i.strip() for i in (row[3] or '').split('|') if i.strip()],
        'instructions': row[4],
        'steps': [s.strip() for s in (row[4] or '').split('\n') if s.strip()],
        'calories': row[5], 'protein': row[6], 'carbs': row[7],
        'fat': row[8], 'fiber': row[9], 'sugar': row[10],
        'goal': row[11], 'diet_type': row[12], 'prep_time': row[13],
        'color': row[14] or '#7cfc9a',
        'image': resolve_image(row[15], 'smoothies') if row[15] else '',
        'is_featured': bool(row[16]), 'rating': float(row[17] or 4.0),
        'tags': row[18] or '', 'is_fav': bool(row[19])
    }
    return render_template('smoothie_detail.html', smoothie=smoothie, related=related)


# ═══════════════════════════════════════════════════════════
#  MEAL PLANNER
# ═══════════════════════════════════════════════════════════
@app.route('/mealplanner')
def mealplanner():
    r = require_login()
    if r: return r
    uid = session['user_id']
    cur = get_cursor(mysql)
    cur.execute("""
        SELECT w.day_of_week, w.meal_time, m.meal_name,
               COALESCE(n.calories,0), COALESCE(n.protein,0),
               COALESCE(n.carbs,0), COALESCE(n.fat,0), w.goal, w.diet_type
        FROM weekly_diet w
        JOIN meals m ON w.meal_id=m.meal_id
        LEFT JOIN nutrition n ON m.meal_id=n.meal_id
        ORDER BY FIELD(w.day_of_week,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'),
                 FIELD(w.meal_time,'Early Morning','Breakfast','Mid Snack','Lunch','Evening Snack','Dinner')
    """)
    rows = cur.fetchall()
    cur.execute("SELECT food_type FROM users WHERE user_id=%s", (uid,))
    ur = cur.fetchone()
    raw_ft = (ur[0] if ur else 'veg') or 'veg'
    cur.close()

    from decimal import Decimal
    def _safe(v):
        return float(v) if isinstance(v, Decimal) else v
    safe_rows = [[_safe(c) for c in r] for r in rows]

    return render_template('mealplanner.html',
        meals_json  = json.dumps(safe_rows),
        user_goal   = session.get('goal',''),
        user_diet   = raw_ft,
        target_cal  = session.get('calories', 2000),
        is_nonveg   = (raw_ft == 'nonveg'))


# ═══════════════════════════════════════════════════════════
#  PROGRESS
# ═══════════════════════════════════════════════════════════
@app.route('/progress')
def progress():
    r = require_login()
    if r: return r
    uid = session['user_id']
    ensure_tables(mysql)
    cur = get_cursor(mysql)

    cur.execute(
        "SELECT COALESCE(SUM(calories),0), COALESCE(SUM(protein),0), "
        "COALESCE(SUM(carbs),0), COALESCE(SUM(fat),0) "
        "FROM user_meal_progress WHERE user_id=%s AND log_date=CURDATE() AND completed=TRUE",
        (uid,))
    row = cur.fetchone()
    cal_today   = int(row[0] or 0)
    prot_today  = round(float(row[1] or 0), 1)
    carbs_today = round(float(row[2] or 0), 1)
    fat_today   = round(float(row[3] or 0), 1)
    goal_cal    = session.get('calories', 2000)

    cur.execute(
        "SELECT meal_time, meal_name, calories FROM user_meal_progress "
        "WHERE user_id=%s AND log_date=CURDATE() AND completed=TRUE "
        "ORDER BY FIELD(meal_time,'Early Morning','Breakfast','Mid Snack','Lunch','Evening Snack','Dinner')",
        (uid,))
    meals = cur.fetchall()

    cur.execute(
        "SELECT log_date, COALESCE(SUM(calories),0) FROM user_meal_progress "
        "WHERE user_id=%s AND completed=TRUE AND log_date>=DATE_SUB(CURDATE(),INTERVAL 6 DAY) "
        "GROUP BY log_date ORDER BY log_date", (uid,))
    raw_weekly = cur.fetchall()

    # Weight log
    cur.execute(
        "SELECT weight, log_date FROM user_weight_log WHERE user_id=%s "
        "ORDER BY log_date DESC LIMIT 30", (uid,))
    weight_log = cur.fetchall()

    # Streak history for last 30 days
    cur.execute(
        "SELECT DISTINCT log_date FROM user_meal_progress "
        "WHERE user_id=%s AND completed=TRUE AND log_date>=DATE_SUB(CURDATE(),INTERVAL 30 DAY) "
        "ORDER BY log_date", (uid,))
    logged_dates = {str(r[0]) for r in cur.fetchall()}

    # Water today
    cur.execute("SELECT COALESCE(glasses,0) FROM water_log WHERE user_id=%s AND log_date=CURDATE()", (uid,))
    wrow = cur.fetchone()
    water_today = int(wrow[0]) if wrow else 0
    cur.close()

    wd = {str(r[0]): int(r[1]) for r in raw_weekly}
    weekly = []
    for i in range(6, -1, -1):
        d  = datetime.now() - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        c  = wd.get(ds, 0)
        st = "good" if c >= 1500 else "low" if c > 0 else "none"
        weekly.append((d.strftime("%a"), c, st))

    return render_template('progress.html',
        calories_today    = cal_today,
        remaining_calories= max(0, goal_cal - cal_today),
        goal              = goal_cal,
        meals             = meals,
        weekly_data       = weekly,
        protein_today     = prot_today,
        carbs_today       = carbs_today,
        fat_today         = fat_today,
        protein_goal      = session.get('protein_goal', 120),
        carbs_goal        = session.get('carbs_goal', 250),
        fat_goal          = session.get('fat_goal', 55),
        streak            = get_streak(mysql, uid),
        weight_log        = weight_log,
        logged_dates      = json.dumps(list(logged_dates)),
        water_today       = water_today)


@app.route('/log_water', methods=['POST'])
def log_water():
    if 'user_id' not in session:
        return jsonify({'error': 'not logged in'}), 401
    uid = session['user_id']
    action = request.form.get('action', 'add')  # add or set
    ensure_tables(mysql)
    cur = get_cursor(mysql)
    cur.execute(
        "SELECT COALESCE(glasses,0) FROM water_log WHERE user_id=%s AND log_date=CURDATE()", (uid,))
    row = cur.fetchone()
    current = int(row[0]) if row else 0
    if action == 'add':
        new_val = min(current + 1, 20)
    elif action == 'remove':
        new_val = max(current - 1, 0)
    else:
        new_val = int(request.form.get('glasses', current))
    cur.execute(
        "INSERT INTO water_log(user_id, glasses, log_date) VALUES(%s,%s,CURDATE()) "
        "ON DUPLICATE KEY UPDATE glasses=%s",
        (uid, new_val, new_val))
    mysql.connection.commit()
    cur.close()
    return jsonify({'glasses': new_val, 'goal': 8})


@app.route('/log_weight', methods=['POST'])
def log_weight():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    uid    = session['user_id']
    weight = request.form.get('weight')
    note   = request.form.get('note', '')
    if weight:
        cur = get_cursor(mysql)
        cur.execute(
            "INSERT INTO user_weight_log(user_id,weight,log_date,note) VALUES(%s,%s,CURDATE(),%s) "
            "ON DUPLICATE KEY UPDATE weight=%s, note=%s",
            (uid, weight, note, weight, note))
        mysql.connection.commit()
        cur.close()
        flash(f'Weight logged: {weight} kg', 'success')
    return redirect(url_for('progress'))


# ═══════════════════════════════════════════════════════════
#  FOOD SCANNER
# ═══════════════════════════════════════════════════════════
@app.route('/food_scanner')
def food_scanner():
    r = require_login()
    if r: return r
    uid = session['user_id']
    cur = get_cursor(mysql)
    cur.execute(
        "SELECT food_name, calories, protein, carbs, fat, confidence, scanned_at "
        "FROM ai_food_scans WHERE user_id=%s ORDER BY scanned_at DESC LIMIT 10",
        (uid,))
    scan_history = cur.fetchall()
    cur.close()
    return render_template('food_scanner.html', scan_history=scan_history)


@app.route('/api/analyze_food', methods=['POST'])
def analyze_food():
    if 'user_id' not in session:
        return jsonify({'error': 'Login required'}), 401
    uid = session['user_id']
    data      = request.get_json() or {}
    image_b64 = data.get('image_base64', '')
    mime_type = data.get('media_type', 'image/jpeg')
    food_name = data.get('food_name', '').strip()

    # ── Path 1: Google Vision → Ninjas Nutrition (primary pipeline) ────
    # Flow: Image (base64) → Google Cloud Vision API (label detection)
    #       → food name string → Ninjas Nutrition API → structured result
    if GOOGLE_VISION_API_KEY and image_b64:
        try:
            result = analyze_food_with_vision_and_ninjas(image_b64)
            ensure_tables(mysql)
            cur = get_cursor(mysql)
            ps = result.get('per_serving', {})
            try:
                cur.execute(
                    "INSERT INTO ai_food_scans(user_id,food_name,calories,protein,carbs,fat,confidence)"
                    " VALUES(%s,%s,%s,%s,%s,%s,%s)",
                    (uid, result.get('food_name', 'Unknown'),
                     ps.get('calories', 0), ps.get('protein_g', 0),
                     ps.get('carbs_g', 0), ps.get('fat_g', 0),
                     result.get('confidence', 'Medium')))
                mysql.connection.commit()
            except Exception:
                pass
            cur.close()
            return jsonify({'result': result})
        except Exception as e:
            # If Google Vision fails, show text input as fallback
            error_str = str(e)
            if 'HTTP Error 403' in error_str or '403' in error_str:
                # API key issue - prompt for manual entry
                return jsonify({'needs_text': True, 'error': 'Image analysis unavailable. Please enter the food name manually below.'}), 200
            if not food_name:
                # Other error - still offer text fallback
                return jsonify({'needs_text': True, 'error': f'Image analysis failed. Try entering the food name manually.'}), 200

    # ── Path 2: Text search via Ninjas API (free tier) ────────
    if food_name:
        # Try Ninjas nutrition API first
        if NINJAS_API_KEY:
            try:
                nd = get_nutrition_from_text(food_name)
                if nd and 'error' not in nd:
                    result = {
                        'food_name': nd['food_name'].title(),
                        'description': f'Nutritional data for {nd["food_name"]} per standard serving.',
                        'confidence': 'High',
                        'per_serving': {
                            'calories':  nd['calories'],
                            'protein_g': nd['protein'],
                            'carbs_g':   nd['carbs'],
                            'fat_g':     nd['fat'],
                            'fiber_g':   0, 'sugar_g': 0
                        },
                        'ingredients': [nd['food_name']],
                        'health_tags': _build_health_tags(nd),
                        'notes': 'Data from nutrition database. Values are per standard serving.'
                    }
                    return jsonify({'result': result})
            except Exception:
                pass

        # Try Open Food Facts (completely free, no key) ────────
        off_result = search_open_food_facts(food_name)
        if off_result:
            return jsonify({'result': off_result})

        # Try local recipe database as a final fallback
        local_result = search_local_recipe_nutrition(food_name)
        if local_result:
            return jsonify({'result': local_result})

        return jsonify({'error': f'No nutrition data found for "{food_name}". Try a different name.'}), 404

    # ── Path 3: No key, no food name — show text input ────────
    return jsonify({
        'error': 'Type a food name below to search nutrition data (or upload an image for Google Vision scan).',
        'needs_text': True
    }), 400


def _build_health_tags(nd):
    tags = []
    cal  = nd.get('calories', 0)
    prot = nd.get('protein', 0)
    fat  = nd.get('fat', 0)
    if cal < 200:   tags.append({'label': 'Low calorie', 'type': 'good'})
    if cal > 500:   tags.append({'label': 'High calorie', 'type': 'warn'})
    if prot > 20:   tags.append({'label': 'High protein', 'type': 'good'})
    if fat > 20:    tags.append({'label': 'High fat', 'type': 'warn'})
    if not tags:    tags.append({'label': 'Moderate nutrition', 'type': 'good'})
    return tags

@app.route('/api/notifications/read', methods=['POST'])
def mark_notification_read():
    if 'user_id' not in session:
        return jsonify({'ok': False}), 401
    uid   = session['user_id']
    notif_id = request.json.get('id')
    cur   = get_cursor(mysql)
    if notif_id:
        cur.execute("UPDATE notifications SET is_read=TRUE WHERE id=%s AND user_id=%s",
                    (notif_id, uid))
    else:
        cur.execute("UPDATE notifications SET is_read=TRUE WHERE user_id=%s", (uid,))
    mysql.connection.commit(); cur.close()
    return jsonify({'ok': True})


# ═══════════════════════════════════════════════════════════
#  UNIQUE FEATURE 1: NUTRITION DIARY (calorie timeline)
# ═══════════════════════════════════════════════════════════
@app.route('/diary')
def diary():
    r = require_login()
    if r: return r
    uid = session['user_id']
    date_str = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    ensure_tables(mysql)
    cur = get_cursor(mysql)
    cur.execute(
        "SELECT id, meal_time, meal_name, calories, protein, carbs, fat, logged_at "
        "FROM user_meal_progress WHERE user_id=%s AND log_date=%s AND completed=TRUE "
        "ORDER BY FIELD(meal_time,'Early Morning','Breakfast','Mid Snack','Lunch','Evening Snack','Dinner')",
        (uid, date_str))
    entries = cur.fetchall()
    cur.execute(
        "SELECT COALESCE(SUM(calories),0), COALESCE(SUM(protein),0), "
        "COALESCE(SUM(carbs),0), COALESCE(SUM(fat),0) "
        "FROM user_meal_progress WHERE user_id=%s AND log_date=%s AND completed=TRUE",
        (uid, date_str))
    totals = cur.fetchone()
    cur.close()
    goal_cal = session.get('calories', 2000)
    return render_template('diary.html',
        entries=entries, date=date_str, totals=totals,
        goal_cal=goal_cal,
        protein_goal=session.get('protein_goal',120),
        carbs_goal=session.get('carbs_goal',250),
        fat_goal=session.get('fat_goal',55))


# ═══════════════════════════════════════════════════════════
#  UNIQUE FEATURE 2: BODY METRICS TRACKER
# ═══════════════════════════════════════════════════════════
@app.route('/body-metrics')
def body_metrics():
    r = require_login()
    if r: return r
    uid  = session['user_id']
    user = get_user_by_id(mysql, uid)
    cur  = get_cursor(mysql)
    cur.execute(
        "SELECT weight, log_date, note FROM user_weight_log "
        "WHERE user_id=%s ORDER BY log_date DESC LIMIT 60", (uid,))
    weight_history = cur.fetchall()
    cur.execute(
        "SELECT goal, calories, protein_goal, carbs_goal, fat_goal, weight_at, changed_at "
        "FROM user_goals_history WHERE user_id=%s ORDER BY changed_at DESC LIMIT 5", (uid,))
    goal_history = cur.fetchall()
    cur.close()

    # Chart data
    weights_json = json.dumps([
        {'date': str(r[1]), 'weight': float(r[0] or 0)}
        for r in reversed(weight_history)
    ])
    return render_template('body_metrics.html',
        user=user, weight_history=weight_history,
        goal_history=goal_history, weights_json=weights_json)


# ═══════════════════════════════════════════════════════════
#  UNIQUE FEATURE 3: CALORIE SEARCH (text-based)
# ═══════════════════════════════════════════════════════════
@app.route('/calorie-search')
def calorie_search():
    r = require_login()
    if r: return r
    query  = request.args.get('q','').strip()
    result = None
    local_results = []
    if query:
        # Search local DB first
        cur = get_cursor(mysql)
        cur.execute("""
            SELECT m.meal_name, COALESCE(n.calories,0), COALESCE(n.protein,0),
                   COALESCE(n.carbs,0), COALESCE(n.fat,0), m.image AS image_file
            FROM meals m LEFT JOIN nutrition n ON m.meal_id=n.meal_id
            WHERE LOWER(m.meal_name) LIKE %s LIMIT 8
        """, (f'%{query.lower()}%',))
        local_results = cur.fetchall()
        cur.close()
        # If nothing local, try Ninjas API
        if not local_results and NINJAS_API_KEY:
            result = get_nutrition_from_text(query)
    return render_template('calorie_search.html',
        query=query, result=result, local_results=local_results)


# ═══════════════════════════════════════════════════════════
#  ACCOUNT / PROFILE
# ═══════════════════════════════════════════════════════════
@app.route('/account', methods=['GET','POST'])
def account():
    r = require_login()
    if r: return r
    uid  = session['user_id']
    user = get_user_by_id(mysql, uid)
    error = success = None

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_profile':
            name   = request.form.get('name','').strip()
            height = request.form.get('height', user.get('height',170))
            weight = request.form.get('weight', user.get('weight',70))
            age    = request.form.get('age', user.get('age',25))
            cur    = get_cursor(mysql)
            cur.execute(
                "UPDATE users SET name=%s, height=%s, weight=%s, age=%s WHERE user_id=%s",
                (name, height, weight, age, uid))
            mysql.connection.commit(); cur.close()
            session['user_name'] = name
            success = 'Profile updated successfully.'
            user = get_user_by_id(mysql, uid)

        elif action == 'change_password':
            old_pw  = request.form.get('old_password','')
            new_pw  = request.form.get('new_password','')
            conf_pw = request.form.get('confirm_password','')
            cur     = get_cursor(mysql)
            cur.execute("SELECT password FROM users WHERE user_id=%s", (uid,))
            row = cur.fetchone(); cur.close()
            if not row or not check_password(old_pw, row[0]):
                error = 'Current password is incorrect.'
            elif new_pw != conf_pw:
                error = 'New passwords do not match.'
            else:
                valid, msg = validate_password_strength(new_pw)
                if not valid:
                    error = msg
                else:
                    pw_hash = hash_password(new_pw)
                    cur2 = get_cursor(mysql)
                    cur2.execute("UPDATE users SET password=%s WHERE user_id=%s",
                                 (pw_hash, uid))
                    mysql.connection.commit(); cur2.close()
                    success = 'Password changed successfully.'

        elif action == 'update_food_pref':
            food_type = request.form.get('food_type','veg')
            cur = get_cursor(mysql)
            cur.execute("UPDATE users SET food_type=%s WHERE user_id=%s", (food_type, uid))
            mysql.connection.commit(); cur.close()
            session['food_type'] = food_type
            success = f'Food preference updated to {food_type}.'

    # Login activity
    cur = get_cursor(mysql)
    try:
        cur.execute(
            "SELECT action, ip_address, device, created_at FROM login_activity "
            "WHERE user_id=%s ORDER BY created_at DESC LIMIT 10", (uid,))
        _all_act = cur.fetchall()
        activity = _all_act[:3]
        activity_more = _all_act[3:]
    except Exception:
        activity = []
        activity_more = []
    cur.close()

    return render_template('account.html',
        user=user, activity=activity, activity_more=activity_more,
        error=error, success=success)


# ═══════════════════════════════════════════════════════════
#  DIETPLAN legacy route
# ═══════════════════════════════════════════════════════════
@app.route('/dietplan', methods=['POST'])
def dietplan():
    day  = request.form.get('day','')
    dt   = request.form.get('diet_type','').lower()
    goal = session.get('goal','')
    cur  = get_cursor(mysql)
    cur.execute("""
        SELECT w.meal_time, m.meal_id, m.meal_name FROM weekly_diet w
        JOIN meals m ON w.meal_id=m.meal_id
        WHERE w.day_of_week=%s AND LOWER(w.goal)=LOWER(%s) AND LOWER(w.diet_type)=LOWER(%s)
        ORDER BY FIELD(w.meal_time,'Early Morning','Breakfast','Mid Snack','Lunch','Evening Snack','Dinner')
    """, (day, goal, dt))
    rows = cur.fetchall(); cur.close()
    meals = {}
    for mt, mid, mn in rows:
        meals.setdefault(mt, []).append((mid, mn))
    return render_template('dietplan.html', meals=meals)


# ═══════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ═══════════════════════════════════════════════════════════
@app.route('/export/progress')
def export_progress():
    r = require_login()
    if r: return r
    uid = session['user_id']
    ensure_tables(mysql)
    cur = get_cursor(mysql)

    cur.execute(
        "SELECT log_date, SUM(calories), SUM(protein), SUM(carbs), SUM(fat) "
        "FROM user_meal_progress WHERE user_id=%s AND completed=TRUE "
        "AND log_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) "
        "GROUP BY log_date ORDER BY log_date DESC", (uid,))
    daily = cur.fetchall()

    cur.execute(
        "SELECT meal_name, meal_time, calories, log_date "
        "FROM user_meal_progress WHERE user_id=%s AND completed=TRUE "
        "ORDER BY log_date DESC, logged_at DESC LIMIT 50", (uid,))
    meals = cur.fetchall()

    cur.execute(
        "SELECT weight, log_date FROM user_weight_log "
        "WHERE user_id=%s ORDER BY log_date DESC LIMIT 30", (uid,))
    weights = cur.fetchall()

    streak = get_streak(mysql, uid)
    cur.close()

    goal_cal = session.get('calories', 2000)
    return render_template('export_progress.html',
        daily=daily, meals=meals, weights=weights,
        streak=streak, goal_cal=goal_cal,
        user_name=session.get('user_name',''),
        goal=session.get('goal',''),
        today=datetime.now().strftime('%d %b %Y'))


@app.route('/notifications/read', methods=['POST'])
def mark_notifications_read():
    if 'user_id' not in session:
        return jsonify({'error': 'not logged in'}), 401
    uid = session['user_id']
    try:
        ensure_tables(mysql)
        cur = get_cursor(mysql)
        cur.execute("UPDATE notifications SET is_read=TRUE WHERE user_id=%s", (uid,))
        mysql.connection.commit()
        cur.close()
    except Exception:
        pass
    return jsonify({'status': 'ok'})


@app.route('/notifications/list')
def list_notifications():
    if 'user_id' not in session:
        return jsonify([])
    uid = session['user_id']
    try:
        ensure_tables(mysql)
        notifs = get_unread_notifications(mysql, uid)
        return jsonify([{
            'id': n['id'], 'message': n['message'],
            'type': n['type'], 'link': n['link'] or '#',
            'time': str(n['time'])
        } for n in notifs])
    except Exception:
        return jsonify([])


@app.route('/allergy', methods=['GET', 'POST'])
def allergy_settings():
    r = require_login()
    if r: return r
    uid = session['user_id']
    if request.method == 'POST':
        allergies = request.form.getlist('allergies')
        other = request.form.get('other_allergy', '').strip()
        if other:
            allergies.append(other)
        allergy_str = ','.join(allergies)
        session['allergies'] = allergies
        try:
            cur = get_cursor(mysql)
            cur.execute(
                "UPDATE users SET allergies=%s WHERE user_id=%s",
                (allergy_str, uid))
            mysql.connection.commit()
            cur.close()
        except Exception:
            pass  # column may not exist yet
        flash('Allergy settings saved!', 'success')
        return redirect(url_for('account'))
    # Load existing
    allergies = session.get('allergies', [])
    return jsonify({'allergies': allergies})



# ═══════════════════════════════════════════════════════════
#  FASTING MODE TRACKER
# ═══════════════════════════════════════════════════════════
@app.route('/fasting', methods=['GET', 'POST'])
def fasting():
    r = require_login()
    if r: return r
    uid = session['user_id']
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'start':
            session['fast_start']      = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            session['fast_goal_hours'] = int(request.form.get('hours', 16))
            flash('Fasting started! Stay strong.', 'success')
        elif action == 'stop':
            session.pop('fast_start', None)
            session.pop('fast_goal_hours', None)
            flash('Fast ended. Great job!', 'success')
        return redirect(url_for('fasting'))

    fast_start   = session.get('fast_start')
    fast_goal_h  = session.get('fast_goal_hours', 16)
    elapsed_mins = 0
    elapsed_pct  = 0
    if fast_start:
        try:
            start_dt     = datetime.strptime(fast_start, '%Y-%m-%d %H:%M:%S')
            elapsed_mins = int((datetime.now() - start_dt).total_seconds() / 60)
            elapsed_pct  = min(int(elapsed_mins / (fast_goal_h * 60) * 100), 100)
        except Exception:
            pass

    return render_template('fasting.html',
        fast_start=fast_start, fast_goal_hours=fast_goal_h,
        elapsed_mins=elapsed_mins, elapsed_pct=elapsed_pct)


# ═══════════════════════════════════════════════════════════
#  MINI CHALLENGES
# ═══════════════════════════════════════════════════════════
CHALLENGES = [
    {'id':1, 'title':'7-Day No Sugar',      'desc':'Avoid added sugar for 7 days.',           'days':7},
    {'id':2, 'title':'30-Day Water Goal',   'desc':'Drink 8 glasses every day for 30 days.',  'days':30},
    {'id':3, 'title':'14-Day Protein Focus','desc':'Hit your protein goal every day for 14 days.','days':14},
    {'id':4, 'title':'7-Day Meal Logging',  'desc':'Log every meal for 7 days straight.',     'days':7},
    {'id':5, 'title':'21-Day No Junk Food', 'desc':'Zero junk food for 21 days.',             'days':21},
    {'id':6, 'title':'10-Day Veggie Boost', 'desc':'Eat 5 servings of vegetables daily.',     'days':10},
]

@app.route('/challenges')
def challenges():
    r = require_login()
    if r: return r
    uc   = session.get('user_challenges', {})
    data = []
    for c in CHALLENGES:
        cid  = str(c['id'])
        prog = uc.get(cid, {'active':False,'start':None,'days_done':0})
        days_done = prog.get('days_done', 0)
        if prog.get('start') and prog.get('active'):
            try:
                st = datetime.strptime(prog['start'], '%Y-%m-%d')
                days_done = min((datetime.now().date() - st.date()).days + 1, c['days'])
            except Exception:
                pass
        data.append({**c,
            'active':    prog.get('active', False),
            'days_done': days_done,
            'pct':       min(int(days_done/c['days']*100),100) if prog.get('active') else 0,
            'completed': days_done >= c['days'] and prog.get('active', False),
        })
    return render_template('challenges.html', challenges=data)

@app.route('/challenges/<int:cid>/join', methods=['POST'])
def join_challenge(cid):
    r = require_login()
    if r: return r
    uc = session.get('user_challenges', {})
    uc[str(cid)] = {'active':True, 'start':datetime.now().strftime('%Y-%m-%d'), 'days_done':0}
    session['user_challenges'] = uc
    flash('Challenge started! Check in daily.', 'success')
    return redirect(url_for('challenges'))

@app.route('/challenges/<int:cid>/leave', methods=['POST'])
def leave_challenge(cid):
    r = require_login()
    if r: return r
    uc = session.get('user_challenges', {})
    uc.pop(str(cid), None)
    session['user_challenges'] = uc
    flash('Challenge ended.', 'info')
    return redirect(url_for('challenges'))


# ═══════════════════════════════════════════════════════════
#  UNDO MEAL
# ═══════════════════════════════════════════════════════════
@app.route('/undo_meal', methods=['POST'])
def undo_meal():
    if 'user_id' not in session:
        return jsonify({'error':'not logged in'}), 401
    uid = session['user_id']
    ensure_tables(mysql)
    cur = get_cursor(mysql)
    try:
        cur.execute(
            "SELECT id,meal_name,calories FROM user_meal_progress "
            "WHERE user_id=%s AND log_date=CURDATE() AND completed=TRUE "
            "ORDER BY logged_at DESC LIMIT 1", (uid,))
        last = cur.fetchone()
        if last:
            cur.execute("DELETE FROM user_meal_progress WHERE id=%s", (last[0],))
            mysql.connection.commit()
            cur.close()
            return jsonify({'status':'ok','removed':last[1],'calories':int(last[2] or 0)})
        cur.close()
        return jsonify({'status':'empty','message':'No meals logged today.'})
    except Exception as e:
        cur.close()
        return jsonify({'error':str(e)}), 500


# ═══════════════════════════════════════════════════════════
#  KNOWLEDGE SECTION
# ═══════════════════════════════════════════════════════════════════════════
# Edit article text here: "summary" appears on the knowledge list and "content" is the full page body.
KNOWLEDGE_ARTICLES = [
    {'id':1,'category':'Nutrition','title':'Why Protein is King for Weight Loss',
     'summary':'Protein keeps you full, boosts metabolism, and preserves muscle during a deficit.',
     'read_time':'3 min',
     'content':'Protein keeps you full, boosts metabolism, and preserves muscle during a deficit.\n\nLean protein sources like chicken, fish, eggs, and legumes slow digestion so you eat less and feel satisfied longer. Every meal should include a protein portion to support recovery and maintain lean body mass while losing fat.'},
    {'id':2,'category':'Habits','title':'The 80/20 Rule of Nutrition',
     'summary':'Perfect nutrition 100% of the time is impossible. Consistency beats perfection.',
     'read_time':'2 min',
     'content':'Perfect nutrition 100% of the time is impossible. Consistency beats perfection.\n\nUse the 80/20 rule by eating whole foods most of the week, then allowing room for favorite treats. This reduces stress, prevents bingeing, and helps you build habits that last.'},
    {'id':3,'category':'Science','title':'How Sleep Affects Your Weight',
     'summary':'Poor sleep increases hunger hormones by 15% and reduces willpower for healthy choices.',
     'read_time':'4 min',
     'content':'Poor sleep increases hunger hormones by 15% and reduces willpower for healthy choices.\n\nQuality sleep helps regulate appetite, supports recovery, and keeps cravings under control. Aim for 7-9 hours so your body can repair and your diet choices stay on track.'},
    {'id':4,'category':'Indian Food','title':'Superfoods in Your Indian Kitchen',
     'summary':'Turmeric, ghee, dal, and fermented foods are nutritional powerhouses hiding in plain sight.',
     'read_time':'3 min',
     'content':'Turmeric, ghee, dal, and fermented foods are nutritional powerhouses hiding in plain sight.\n\nUse spices like turmeric, cumin, and fenugreek to boost flavor and digestion. Traditional dishes such as dal, idli, curd, and dosa can support gut health and steady energy when paired with vegetables and lean protein.'},
    {'id':5,'category':'Exercise','title':'Best Time to Eat Around Your Workout',
     'summary':'Pre and post workout nutrition significantly improves performance and recovery.',
     'read_time':'3 min',
     'content':'Pre and post workout nutrition significantly improves performance and recovery.\n\nHave a balanced snack with carbs and protein 1-2 hours before exercise, then refuel after training with protein and a small portion of carbohydrates. This helps muscle repair and keeps energy stable throughout the day.'},
    {'id':6,'category':'Mindset','title':'Breaking Through a Weight Loss Plateau',
     'summary':'Plateaus are normal. Here is the science of why they happen and how to overcome them.',
     'read_time':'4 min',
     'content':'Plateaus are normal. Here is the science of why they happen and how to overcome them.\n\nIf progress stalls, check portion sizes, protein intake, sleep quality, and stress. Small changes like adjusting calorie intake, varying workouts, or improving recovery often restart progress without drastic dieting.'},
]

@app.route('/knowledge')
def knowledge():
    r = require_login()
    if r: return r
    cat    = request.args.get('cat', 'All')
    search = request.args.get('q', '').lower()
    cats   = ['All'] + sorted(set(a['category'] for a in KNOWLEDGE_ARTICLES))
    arts   = KNOWLEDGE_ARTICLES
    if cat != 'All':
        arts = [a for a in arts if a['category'] == cat]
    if search:
        arts = [a for a in arts if search in a['title'].lower() or search in a['summary'].lower()]
    return render_template('knowledge.html', articles=arts, categories=cats, active_cat=cat)

@app.route('/knowledge/<int:aid>')
def knowledge_article(aid):
    r = require_login()
    if r: return r
    art = next((a for a in KNOWLEDGE_ARTICLES if a['id'] == aid), None)
    if not art:
        return redirect(url_for('knowledge'))
    related = [a for a in KNOWLEDGE_ARTICLES if a['id'] != aid][:3]
    return render_template('knowledge_article.html', article=art, related=related)


# ═══════════════════════════════════════════════════════════
#  CALENDAR VIEW
# ═══════════════════════════════════════════════════════════
@app.route('/calendar')
def calendar_view():
    r = require_login()
    if r: return r
    uid   = session['user_id']
    year  = int(request.args.get('year',  datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))
    ensure_tables(mysql)
    cur   = get_cursor(mysql)
    cur.execute(
        "SELECT log_date,SUM(calories),COUNT(*) FROM user_meal_progress "
        "WHERE user_id=%s AND YEAR(log_date)=%s AND MONTH(log_date)=%s AND completed=TRUE "
        "GROUP BY log_date", (uid, year, month))
    rows     = cur.fetchall()
    cur.close()
    cal_data = {str(row[0]): {'calories':int(row[1] or 0),'meals':int(row[2] or 0)} for row in rows}
    goal_cal = session.get('calories', 2000)
    import calendar as cal_mod
    weeks      = cal_mod.monthcalendar(year, month)
    month_name = cal_mod.month_name[month]
    prev_y, prev_m = (year-1, 12) if month==1 else (year, month-1)
    next_y, next_m = (year+1, 1)  if month==12 else (year, month+1)
    return render_template('calendar_view.html',
        weeks=weeks, cal_data=cal_data, goal_cal=goal_cal,
        year=year, month=month, month_name=month_name,
        prev_year=prev_y, prev_month=prev_m,
        next_year=next_y, next_month=next_m,
        today=str(date.today()))

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

# ═══════════════════════════════════════════════════════════
#  CHEAT MEAL TRACKING
# ═══════════════════════════════════════════════════════════
@app.route('/cheat-meal')
def cheat_meal():
    r = require_login()
    if r: return r
    uid = session['user_id']
    ensure_tables(mysql)
    cur = get_cursor(mysql)
    
    # Get user's cheat meals tracked in meal_name (prefixed with [CHEAT])
    cur.execute(
        "SELECT id, meal_name, calories, log_date, meal_time "
        "FROM user_meal_progress "
        "WHERE user_id=%s AND completed=TRUE AND meal_time='cheat-meal' "
        "AND log_date >= DATE_SUB(NOW(), INTERVAL 30 DAY) "
        "ORDER BY log_date DESC",
        (uid,))
    meals_raw = cur.fetchall()
    
    # Transform to match template expectations: id, meal_name, category, calories, log_date, notes
    cheat_meals = []
    for m in meals_raw:
        # Extract category from meal_name (format: "{meal_name} | {category}")
        meal_display = m[1]
        category = 'other'
        if '|' in m[1]:
            parts = m[1].split('|')
            meal_display = parts[0].strip()
            category = parts[1].strip().lower() if len(parts) > 1 else 'other'
        cheat_meals.append((m[0], meal_display, category, m[2], m[3], m[4]))
    
    total_logged = len(cheat_meals)
    extra_calories = sum(int(m[3] or 0) for m in cheat_meals if m[3])
    
    # Get consecutive clean days (no cheat meals)
    cur.execute(
        "SELECT COUNT(*) FROM ("
        "SELECT DISTINCT log_date FROM user_meal_progress "
        "WHERE user_id=%s AND completed=TRUE "
        "AND log_date NOT IN ("
        "SELECT DISTINCT log_date FROM user_meal_progress "
        "WHERE user_id=%s AND meal_time='cheat-meal' AND completed=TRUE) "
        "ORDER BY log_date DESC) t",
        (uid, uid))
    clean_days = cur.fetchone()[0] or 0
    
    # Calculate recovery score (0-100)
    recovery_score = min(100, int((clean_days * 10) - (extra_calories / 100)))
    
    # Get cheat meals by day of week
    cur.execute(
        "SELECT DAYNAME(log_date) as day, COUNT(*) as count FROM user_meal_progress "
        "WHERE user_id=%s AND meal_time='cheat-meal' AND completed=TRUE "
        "AND log_date >= DATE_SUB(NOW(), INTERVAL 30 DAY) "
        "GROUP BY DAYNAME(log_date)",
        (uid,))
    day_pattern = cur.fetchall()
    day_dict = {row[0]: row[1] for row in day_pattern}
    cheat_by_day = [day_dict.get(day, 0) for day in ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']]
    
    # Most common cheat day
    most_cheat_day = 'N/A'
    if cheat_by_day and max(cheat_by_day) > 0:
        days_list = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
        most_cheat_day = days_list[cheat_by_day.index(max(cheat_by_day))]
    
    cur.close()
    
    return render_template('cheat_meal.html',
        cheat_meals=cheat_meals,
        cheat_days_clean=clean_days,
        cheat_recovery_score=recovery_score,
        cheat_by_day=cheat_by_day,
        most_cheat_day=most_cheat_day)

@app.route('/cheat-meal/log', methods=['POST'])
def log_cheat_meal():
    r = require_login()
    if r: return r
    uid = session['user_id']
    meal_name = request.form.get('meal_name', 'Cheat Meal')
    try:
        calories = int(request.form.get('calories', '0'))
    except:
        calories = 0
    category = request.form.get('category', 'other')
    mood = request.form.get('mood', '')
    note = request.form.get('note', '')
    
    # Store meal with category separator (no notes column needed)
    full_meal_name = f"{meal_name} | {category}"
    
    ensure_tables(mysql)
    cur = get_cursor(mysql)
    cur.execute(
        "INSERT INTO user_meal_progress(user_id, meal_name, calories, meal_time, completed) "
        "VALUES(%s, %s, %s, %s, TRUE)",
        (uid, full_meal_name, calories, 'cheat-meal'))
    mysql.connection.commit()
    cur.close()
    
    return redirect('/cheat-meal')

# ═══════════════════════════════════════════════════════════
#  BEST DAY ANALYSIS
# ═══════════════════════════════════════════════════════════
@app.route('/best-day-analysis')
def best_day_analysis():
    r = require_login()
    if r: return r
    uid = session['user_id']
    goal_cal = session.get('calories', 2000)
    ensure_tables(mysql)
    cur = get_cursor(mysql)
 
    # Use log_date column (confirmed in ensure_tables schema)
    try:
        cur.execute(
            "SELECT log_date, COALESCE(SUM(calories),0) FROM user_meal_progress "
            "WHERE user_id=%s AND completed=TRUE AND log_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) "
            "GROUP BY log_date ORDER BY log_date", (uid,))
        daily_rows = cur.fetchall()
    except Exception:
        # Fallback: try logged_at
        try:
            cur.execute(
                "SELECT DATE(logged_at), COALESCE(SUM(calories),0) FROM user_meal_progress "
                "WHERE user_id=%s AND completed=TRUE AND logged_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) "
                "GROUP BY DATE(logged_at) ORDER BY DATE(logged_at)", (uid,))
            daily_rows = cur.fetchall()
        except Exception:
            daily_rows = []
 
    days_logged = len(daily_rows)
    days_total  = 30
    consistency_pct = round(days_logged / days_total * 100) if days_total > 0 else 0
    avg_daily_cal = round(sum(int(r[1]) for r in daily_rows) / days_logged) if days_logged > 0 else 0
 
    best_day_name = worst_day_name = 'No data yet'
    best_day_cal  = worst_day_cal  = 0
    if daily_rows:
        best_row  = min(daily_rows, key=lambda r: abs(int(r[1]) - goal_cal))
        worst_row = max(daily_rows, key=lambda r: abs(int(r[1]) - goal_cal))
        best_day_name  = best_row[0].strftime('%A, %d %b') if best_row[0] else '—'
        best_day_cal   = int(best_row[1])
        worst_day_name = worst_row[0].strftime('%A, %d %b') if worst_row[0] else '—'
        worst_day_cal  = int(worst_row[1])
 
    from collections import defaultdict
    dow_sums   = defaultdict(int)
    dow_counts = defaultdict(int)
    for row in daily_rows:
        d = row[0].weekday() if row[0] else 0
        dow_sums[d]    += int(row[1])
        dow_counts[d]  += 1
    day_avg_cals = [round(dow_sums[i] / dow_counts[i]) if dow_counts[i] > 0 else 0 for i in range(7)]
 
    from datetime import date as date_cls, timedelta as td2
    daily_dict = {str(r[0]): int(r[1]) for r in daily_rows}
    heatmap_data = []
    for i in range(29, -1, -1):
        d  = date_cls.today() - td2(days=i)
        ds = str(d)
        cal = daily_dict.get(ds, 0)
        heatmap_data.append({'date': d.strftime('%d %b'), 'logged': cal > 0, 'cal': cal})
 
    chart_labels = json.dumps([item['date'] for item in heatmap_data])
    chart_vals   = json.dumps([item['cal']  for item in heatmap_data])
 
    try:
        cur.execute("SELECT longest_streak FROM user_streak WHERE user_id=%s", (uid,))
        sr = cur.fetchone()
        streak_best = int(sr[0]) if sr and sr[0] else 0
    except Exception:
        streak_best = 0
 
    insights = []
    if avg_daily_cal > goal_cal + 200:
        insights.append(('📈', 'Calorie surplus', f'You average {avg_daily_cal - goal_cal} kcal over goal. Reduce dinner portions.'))
    elif avg_daily_cal < goal_cal - 300:
        insights.append(('📉', 'Calorie deficit', f'You average {goal_cal - avg_daily_cal} kcal under goal. Add a protein-rich snack.'))
    else:
        insights.append(('✅', 'On target!', f'Avg {avg_daily_cal} kcal is very close to your {goal_cal} kcal goal. Keep it up!'))
 
    dow_names = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    if any(day_avg_cals):
        worst_dow = max(range(7), key=lambda i: abs(day_avg_cals[i] - goal_cal) if day_avg_cals[i] > 0 else 0)
        best_dow  = min(range(7), key=lambda i: abs(day_avg_cals[i] - goal_cal) if day_avg_cals[i] > 0 else 99999)
        insights.append(('⚠️', f'{dow_names[worst_dow]} is hardest', f'Most off-target on {dow_names[worst_dow]}. Pre-plan meals that day.'))
        insights.append(('🏆', f'{dow_names[best_dow]} is your best', f'{dow_names[best_dow]} is closest to your calorie goal. Replicate it!'))
 
    if consistency_pct >= 80:
        insights.append(('🔥', 'High consistency', f'{consistency_pct}% logging rate — you\'re building a powerful habit!'))
    elif consistency_pct >= 50:
        insights.append(('💪', 'Keep building', f'{consistency_pct}% consistency. Try to log every day this week.'))
    else:
        insights.append(('⏰', 'Log more often', f'Only {consistency_pct}% days logged. Daily tracking boosts results by 30%.'))
    insights.append(('💧', 'Hydration tip', 'Days with 8+ water glasses show better calorie control. Track water too!'))
 
    cur.close()
    return render_template('best_day_analysis.html',
        days_logged=days_logged, days_total=days_total,
        consistency_pct=consistency_pct, avg_daily_cal=avg_daily_cal,
        best_day_name=best_day_name, best_day_cal=best_day_cal,
        worst_day_name=worst_day_name, worst_day_cal=worst_day_cal,
        day_avg_cals=day_avg_cals, heatmap_data=heatmap_data,
        chart_labels=chart_labels, chart_vals=chart_vals,
        goal_cal=goal_cal, streak_best=streak_best, insights=insights)

# ═══════════════════════════════════════════════════════════
#  HEALTHY DAY TRACKING
# ═══════════════════════════════════════════════════════════
@app.route('/healthy-day')
def healthy_day():
    r = require_login()
    if r: return r
    uid = session['user_id']
    ensure_tables(mysql)
    cur = get_cursor(mysql)
    
    goal_cal = session.get('calories', 2000)
    goal_protein = session.get('protein', 150)
    goal_carbs = session.get('carbs', 250)
    goal_fat = session.get('fat', 60)
    goal = session.get('goal', 'Weight Loss')
    food_type = session.get('food_type', 'veg')
    
    # Get total healthy days (within calorie goal, no cheat meals)
    cur.execute(
        "SELECT COUNT(DISTINCT log_date) FROM user_meal_progress "
        "WHERE user_id=%s AND completed=TRUE AND meal_time != 'cheat-meal' "
        "AND log_date IN ("
        "SELECT log_date FROM user_meal_progress "
        "WHERE user_id=%s AND completed=TRUE "
        "GROUP BY log_date HAVING SUM(calories) <= %s)",
        (uid, uid, goal_cal))
    healthy_days_count = cur.fetchone()[0] or 0
    
    # Get current streak (consecutive healthy days)
    cur.execute(
        "SELECT COUNT(*) FROM ("
        "SELECT DISTINCT log_date FROM user_meal_progress "
        "WHERE user_id=%s AND completed=TRUE AND meal_time != 'cheat-meal' "
        "AND log_date IN ("
        "SELECT log_date FROM user_meal_progress "
        "WHERE user_id=%s AND completed=TRUE "
        "GROUP BY log_date HAVING SUM(calories) <= %s) "
        "ORDER BY log_date DESC LIMIT 30) t",
        (uid, uid, goal_cal))
    current_streak = cur.fetchone()[0] or 0
    
    # Get recent healthy meals
    cur.execute(
        "SELECT id, meal_name, calories, log_date, meal_time "
        "FROM user_meal_progress "
        "WHERE user_id=%s AND completed=TRUE AND meal_time != 'cheat-meal' "
        "AND log_date >= DATE_SUB(NOW(), INTERVAL 7 DAY) "
        "ORDER BY log_date DESC LIMIT 20",
        (uid,))
    recent_meals = cur.fetchall()
    
    # Get healthy day stats from last 30 days
    cur.execute(
        "SELECT log_date, SUM(calories) as daily_cal, COUNT(*) as meal_count "
        "FROM user_meal_progress "
        "WHERE user_id=%s AND completed=TRUE "
        "AND log_date >= DATE_SUB(NOW(), INTERVAL 30 DAY) "
        "GROUP BY log_date "
        "ORDER BY log_date DESC",
        (uid,))
    daily_stats = cur.fetchall()
    
    # Check if healthy day mode is activated (user has completed a healthy full day meal plan)
    activated = healthy_days_count > 0
    
    cur.close()
    
    # Format meals for template (empty by default - would be populated by meal selection logic)
    meals = []
    
    return render_template('healthy_day.html',
        healthy_days_count=healthy_days_count,
        current_streak=current_streak,
        goal_calories=goal_cal,
        goal_cal=goal_cal,
        protein_goal=goal_protein,
        carbs_goal=goal_carbs,
        fat_goal=goal_fat,
        goal=goal,
        food_type=food_type,
        activated=activated,
        meals=meals,
        recent_meals=recent_meals,
        daily_stats=daily_stats)

# ═══════════════════════════════════════════════════════════
#  HABIT ANALYSIS — check skipped meals & send notifications
# ═══════════════════════════════════════════════════════════
@app.route('/api/habit-check', methods=['POST'])
def habit_check():
    """Called by frontend periodically or on login to analyse habits."""
    if 'user_id' not in session:
        return jsonify({'ok': False}), 401
    uid = session['user_id']
    ensure_tables(mysql)
    cur = get_cursor(mysql)
 
    # Check breakfast skips in last 7 days
    try:
        cur.execute(
            "SELECT COUNT(*) FROM user_meal_progress "
            "WHERE user_id=%s AND LOWER(meal_time) IN ('breakfast','early morning') "
            "AND log_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) AND completed=TRUE", (uid,))
        breakfast_logged = int(cur.fetchone()[0] or 0)
        breakfast_skips = 7 - breakfast_logged
        if breakfast_skips >= 3:
            add_notification(mysql, uid,
                f'⚠️ Habit Alert: You skipped breakfast {breakfast_skips} times this week. Breakfast helps control hunger all day!',
                'warning', '/auto_diet')
    except Exception:
        pass
 
    # Check sedentary warning — no meal logged today
    try:
        cur.execute(
            "SELECT COUNT(*) FROM user_meal_progress "
            "WHERE user_id=%s AND log_date=CURDATE() AND completed=TRUE", (uid,))
        today_count = int(cur.fetchone()[0] or 0)
        from datetime import datetime as dt2
        hour_now = dt2.now().hour
        if today_count == 0 and hour_now >= 14:
            add_notification(mysql, uid,
                '🪑 Sedentary Warning: No meals logged today yet. Get moving and eat something nutritious!',
                'warning', '/auto_diet')
    except Exception:
        pass
 
    cur.close()
    return jsonify({'ok': True})


@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404,
        message='Page not found. It may have been moved or deleted.'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', code=500,
        message='Something went wrong on our end. Please try again.'), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)