from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from datetime import datetime, timedelta, date
import random
import json
import anthropic

app = Flask(__name__)
app.secret_key = "dietmate_secret_v3"

app.config['MYSQL_HOST']     = 'localhost'
app.config['MYSQL_USER']     = 'root'
app.config['MYSQL_PASSWORD'] = 'Harita@1234'
app.config['MYSQL_DB']       = 'dietmate_db'

mysql = MySQL(app)

# ── Put your Anthropic API key here ───────────────────────────
ANTHROPIC_API_KEY = ''   # ← paste key here


def get_cursor():
    return mysql.connection.cursor()


def require_login():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return None


# ── Auto-create missing tables on first run ───────────────────
def ensure_tables():
    cur = get_cursor()

    # user_meal_progress (may not exist in original schema)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_meal_progress (
            id        INT AUTO_INCREMENT PRIMARY KEY,
            user_id   INT NOT NULL,
            meal_id   INT,
            meal_name VARCHAR(200),
            meal_time VARCHAR(50),
            calories  INT DEFAULT 0,
            completed BOOLEAN DEFAULT TRUE,
            date      DATE,
            INDEX (user_id, date)
        )
    """)

    # Streak tracking
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_streaks (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            user_id         INT NOT NULL UNIQUE,
            current_streak  INT DEFAULT 0,
            longest_streak  INT DEFAULT 0,
            last_active_date DATE,
            total_days      INT DEFAULT 0,
            INDEX (user_id)
        )
    """)

    # Water intake log (proper DB storage)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS water_log (
            id       INT AUTO_INCREMENT PRIMARY KEY,
            user_id  INT NOT NULL,
            glasses  INT DEFAULT 0,
            log_date DATE,
            UNIQUE KEY unique_user_date (user_id, log_date),
            INDEX (user_id, log_date)
        )
    """)

    # Re-engagement — store last notification sent
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_engagement (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            user_id         INT NOT NULL UNIQUE,
            last_visit      DATE,
            reminder_count  INT DEFAULT 0,
            INDEX (user_id)
        )
    """)

    mysql.connection.commit()
    cur.close()


# ── Streak helpers ────────────────────────────────────────────
def update_streak(user_id):
    """Call after any meaningful activity (meal logged, quiz done)."""
    cur = get_cursor()
    today = date.today()

    cur.execute("""
        SELECT current_streak, longest_streak, last_active_date, total_days
        FROM user_streaks WHERE user_id = %s
    """, (user_id,))
    row = cur.fetchone()

    if not row:
        cur.execute("""
            INSERT INTO user_streaks (user_id, current_streak, longest_streak, last_active_date, total_days)
            VALUES (%s, 1, 1, %s, 1)
        """, (user_id, today))
        mysql.connection.commit()
        cur.close()
        return

    current, longest, last_active, total = row

    if last_active is None:
        new_current = 1
    elif last_active == today:
        # Already counted today
        cur.close()
        return
    elif last_active == today - timedelta(days=1):
        new_current = current + 1
    else:
        # Streak broken
        new_current = 1

    new_longest = max(longest, new_current)
    new_total   = total + 1

    cur.execute("""
        UPDATE user_streaks
        SET current_streak=%, longest_streak=%, last_active_date=%, total_days=%
        WHERE user_id=%s
    """.replace('%,', '%s,').replace('=%', '=%s') , (new_current, new_longest, today, new_total, user_id))

    mysql.connection.commit()
    cur.close()


def get_streak(user_id):
    cur = get_cursor()
    cur.execute("""
        SELECT current_streak, longest_streak, total_days, last_active_date
        FROM user_streaks WHERE user_id = %s
    """, (user_id,))
    row = cur.fetchone()
    cur.close()
    if not row:
        return {'current': 0, 'longest': 0, 'total': 0, 'active_today': False, 'freeze_available': False}

    current, longest, total, last_active = row
    today = date.today()
    active_today = (last_active == today) if last_active else False

    # If last active was yesterday, streak is intact; if 2+ days ago, streak is broken
    streak_broken = False
    if last_active and last_active < today - timedelta(days=1):
        streak_broken = True

    return {
        'current':        0 if streak_broken else current,
        'longest':        longest,
        'total':          total,
        'active_today':   active_today,
        'streak_broken':  streak_broken,
        'freeze_available': (longest or 0) >= 7  # unlock freeze after 7-day streak
    }


def update_engagement(user_id):
    cur = get_cursor()
    today = date.today()
    cur.execute("""
        INSERT INTO user_engagement (user_id, last_visit)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE last_visit = %s
    """, (user_id, today, today))
    mysql.connection.commit()
    cur.close()


def days_since_last_visit(user_id):
    cur = get_cursor()
    cur.execute("SELECT last_visit FROM user_engagement WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    if not row or not row[0]:
        return 0
    delta = date.today() - row[0]
    return delta.days


# ── LOGIN ─────────────────────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not email or not password:
            return render_template('login.html', error='Please fill in all fields.')

        cur = get_cursor()
        cur.execute("SELECT user_id, password, name FROM users WHERE LOWER(email) = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and str(user[1]).strip() == password:
            session['user_id']   = user[0]
            session['user_name'] = user[2] or 'User'
            ensure_tables()
            update_engagement(user[0])

            # Days away — trigger re-engagement banner
            days_away = days_since_last_visit(user[0])
            session['days_away'] = days_away

            flash(f'Welcome back, {user[2]}!', 'success')
            return redirect(url_for('dashboard'))

        return render_template('login.html', error='Invalid email or password.')

    return render_template('login.html')


# ── REGISTER ──────────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name      = request.form.get('name', '').strip()
        email     = request.form.get('email', '').strip().lower()
        password  = request.form.get('password', '').strip()
        age       = request.form.get('age', '')
        gender    = request.form.get('gender', '')
        height    = request.form.get('height', '')
        weight    = request.form.get('weight', '')
        goal      = request.form.get('goal', '')
        food_type = request.form.get('food_type', '')

        if not all([name, email, password, age, gender, height, weight, goal, food_type]):
            return render_template('register.html', error='Please fill in all fields.')

        cur = get_cursor()
        cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            return render_template('register.html', error='An account with this email already exists.')

        cur.execute("""
            INSERT INTO users (name, email, password, age, gender, height, weight, goal, food_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, email, password, age, gender, height, weight, goal, food_type))
        mysql.connection.commit()
        cur.close()
        ensure_tables()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# ── LOGOUT ────────────────────────────────────────────────────
@app.route('/logout')
def logout():
    name = session.get('user_name', '')
    session.clear()
    flash(f'Goodbye{", " + name if name else ""}! See you tomorrow.', 'success')
    return redirect(url_for('login'))


# ── DASHBOARD ─────────────────────────────────────────────────
@app.route('/dashboard')
def dashboard():
    redir = require_login()
    if redir:
        return redir

    user_id = session['user_id']
    ensure_tables()
    update_engagement(user_id)
    cur = get_cursor()

    cur.execute("SELECT COUNT(*) FROM meals")
    total_recipes = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT meal_time) FROM weekly_diet")
    meal_types = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT plan_id) FROM weekly_diet")
    diet_plans = cur.fetchone()[0]

    cur.execute("""
        SELECT COALESCE(SUM(calories), 0)
        FROM user_meal_progress
        WHERE user_id = %s AND DATE(date) = CURDATE() AND completed = TRUE
    """, (user_id,))
    calories_today     = int(cur.fetchone()[0])
    remaining_calories = max(0, 2000 - calories_today)

    # Water today
    cur.execute("""
        SELECT glasses FROM water_log
        WHERE user_id = %s AND log_date = CURDATE()
    """, (user_id,))
    wrow = cur.fetchone()
    water_today = wrow[0] if wrow else 0

    cur.close()

    streak = get_streak(user_id)
    days_away = session.pop('days_away', 0)

    tips = [
        "Drink 2–3 litres of water daily to stay hydrated.",
        "Eat a piece of fruit every morning for a natural energy boost.",
        "Include a protein source in every meal to feel fuller, longer.",
        "Sleep at least 7–8 hours for proper recovery.",
        "Walk at least 30 minutes a day — even a short stroll counts.",
        "Eat slowly and chew your food well.",
        "Prep meals on Sundays to avoid unhealthy weekday choices.",
    ]

    return render_template(
        'dashboard.html',
        total_recipes=total_recipes,
        meal_types=meal_types,
        diet_plans=diet_plans,
        healthy_tips=random.choice(tips),
        calories_today=calories_today,
        remaining_calories=remaining_calories,
        water_today=water_today,
        streak=streak,
        days_away=days_away,
        user_name=session.get('user_name', 'User')
    )


# ── WATER LOG API (DB-backed, fixes the bug) ──────────────────
@app.route('/api/water', methods=['GET', 'POST'])
def water_api():
    redir = require_login()
    if redir:
        return jsonify({'error': 'Not logged in'}), 401

    user_id = session['user_id']
    cur = get_cursor()

    if request.method == 'GET':
        cur.execute("""
            SELECT glasses FROM water_log
            WHERE user_id = %s AND log_date = CURDATE()
        """, (user_id,))
        row = cur.fetchone()
        cur.close()
        return jsonify({'glasses': row[0] if row else 0})

    # POST — update glasses count
    data    = request.get_json()
    glasses = int(data.get('glasses', 0))
    glasses = max(0, min(8, glasses))

    cur.execute("""
        INSERT INTO water_log (user_id, glasses, log_date)
        VALUES (%s, %s, CURDATE())
        ON DUPLICATE KEY UPDATE glasses = %s
    """, (user_id, glasses, glasses))
    mysql.connection.commit()
    cur.close()

    # Log water as activity for streak
    if glasses > 0:
        update_streak(user_id)

    return jsonify({'glasses': glasses, 'ok': True})


# ── STREAK API ────────────────────────────────────────────────
@app.route('/api/streak')
def streak_api():
    redir = require_login()
    if redir:
        return jsonify({'error': 'Not logged in'}), 401
    return jsonify(get_streak(session['user_id']))


# ── HEALTH QUIZ ───────────────────────────────────────────────
@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        try:
            weight   = float(request.form['weight'])
            target   = float(request.form['target_weight'])
            height   = float(request.form['height'])
            age      = int(request.form['age'])
            activity = float(request.form['activity'])
        except (KeyError, ValueError):
            return render_template('health_quiz.html', error='Please fill in all fields correctly.')

        bmr      = 10 * weight + 6.25 * height - 5 * age + 5
        calories = bmr * activity

        if target < weight:
            goal = "Weight Loss"; calories -= 500
        elif target > weight:
            goal = "Weight Gain"; calories += 300
        else:
            goal = "Muscle Gain"

        calories = max(1200, int(calories))
        protein  = round(weight * 1.8)
        fat      = round(calories * 0.25 / 9)
        carbs    = round((calories - (protein * 4 + fat * 9)) / 4)

        bmi = round(weight / ((height / 100) ** 2), 1)

        if bmi < 18.5:   bmi_category, bmi_color = "Underweight", "#b5860a"
        elif bmi < 25:   bmi_category, bmi_color = "Normal weight", "#3a8a62"
        elif bmi < 30:   bmi_category, bmi_color = "Overweight",    "#b5860a"
        else:            bmi_category, bmi_color = "Obese",         "#c0392b"

        session['calories'] = calories
        session['goal']     = goal

        if 'user_id' in session:
            update_streak(session['user_id'])

        return render_template('quiz_result.html',
            calories=calories, protein=protein, carbs=carbs, fat=fat,
            goal=goal, bmi=bmi, bmi_category=bmi_category, bmi_color=bmi_color)

    return render_template('health_quiz.html')


# ── DIET SELECT ───────────────────────────────────────────────
@app.route('/dietselect')
def dietselect():
    return render_template('dietselect.html')


# ── AUTO DIET ─────────────────────────────────────────────────
@app.route('/auto_diet', methods=['GET', 'POST'])
def auto_diet():
    diet_type = request.form.get('diet_type') or request.args.get('diet_type')
    calories  = session.get('calories')

    if not calories:
        flash('Complete the Health Quiz first.', 'warning')
        return redirect(url_for('quiz'))

    if not diet_type:
        return redirect(url_for('dietselect'))

    targets = {
        "Early Morning": calories * 0.07,
        "Breakfast":     calories * 0.25,
        "Mid Snack":     calories * 0.10,
        "Lunch":         calories * 0.35,
        "Evening Snack": calories * 0.10,
        "Dinner":        calories * 0.23
    }

    cur = get_cursor()
    meals = {}

    for meal_time, cal_target in targets.items():
        cur.execute("""
            SELECT m.meal_name, n.calories, m.meal_id
            FROM meals m
            JOIN nutrition n ON m.meal_id = n.meal_id
            WHERE LOWER(m.diet_type) = LOWER(%s)
              AND LOWER(m.meal_time) = LOWER(%s)
            ORDER BY ABS(n.calories - %s)
            LIMIT 6
        """, (diet_type, meal_time, cal_target))
        rows = cur.fetchall()
        if not rows:
            cur.execute("""
                SELECT m.meal_name, n.calories, m.meal_id
                FROM meals m JOIN nutrition n ON m.meal_id = n.meal_id
                ORDER BY ABS(n.calories - %s) LIMIT 4
            """, (cal_target,))
            rows = cur.fetchall()
        meals[meal_time] = random.sample(rows, min(2, len(rows)))

    cur.close()
    return render_template('auto_diet.html', meals=meals, total=calories)


# ── COMPLETE MEAL ─────────────────────────────────────────────
@app.route('/complete_meal', methods=['POST'])
def complete_meal():
    redir = require_login()
    if redir: return redir

    user_id   = session['user_id']
    meal_id   = request.form.get('meal_id')
    meal_name = request.form.get('meal_name')
    calories  = request.form.get('calories')
    meal_time = request.form.get('meal_time')

    if not all([meal_id, meal_name, calories, meal_time]):
        flash('Could not log that meal.', 'error')
        return redirect(url_for('auto_diet'))

    cur = get_cursor()
    cur.execute("""
        INSERT INTO user_meal_progress
            (user_id, meal_id, meal_name, meal_time, calories, completed, date)
        VALUES (%s, %s, %s, %s, %s, TRUE, CURDATE())
    """, (user_id, meal_id, meal_name, meal_time, calories))
    mysql.connection.commit()
    cur.close()

    update_streak(user_id)
    flash(f'"{meal_name}" logged — {calories} kcal added!', 'success')
    return redirect(url_for('auto_diet'))


# ── RECIPES ───────────────────────────────────────────────────
@app.route('/recipes')
def recipes():
    cur = get_cursor()
    cur.execute("""
        SELECT m.meal_id, m.meal_name, n.calories, n.protein, n.carbs, n.fat
        FROM meals m JOIN nutrition n ON m.meal_id = n.meal_id
        ORDER BY m.meal_name
    """)
    recipes = cur.fetchall()
    cur.close()
    return render_template('recipes.html', recipes=recipes)


# ── RECIPE DETAIL ─────────────────────────────────────────────
@app.route('/recipe/<int:id>')
def recipe(id):
    cur = get_cursor()
    cur.execute("""
        SELECT m.meal_id, m.meal_name, m.recipe, m.image,
               n.calories, n.protein, n.carbs, n.fat
        FROM meals m JOIN nutrition n ON m.meal_id = n.meal_id
        WHERE m.meal_id = %s
    """, (id,))
    recipe = cur.fetchone()
    cur.close()
    if not recipe:
        flash('Recipe not found.', 'error')
        return redirect(url_for('recipes'))
    return render_template('recipe.html', recipe=recipe)


# ── MEAL PLANNER — dedup fix ──────────────────────────────────
@app.route('/mealplanner')
def mealplanner():
    cur = get_cursor()
    # Use GROUP BY to deduplicate identical meal+time+goal+diet combinations
    cur.execute("""
        SELECT
            w.day_of_week,
            w.meal_time,
            m.meal_name,
            COALESCE(n.calories, 0)  AS calories,
            COALESCE(n.protein,  0)  AS protein,
            COALESCE(n.carbs,    0)  AS carbs,
            COALESCE(n.fat,      0)  AS fat,
            COALESCE(w.goal,     '')  AS goal,
            COALESCE(w.diet_type,'') AS diet_type
        FROM weekly_diet w
        JOIN meals m ON w.meal_id = m.meal_id
        LEFT JOIN nutrition n ON m.meal_id = n.meal_id
        GROUP BY w.day_of_week, w.meal_time, m.meal_name, w.goal, w.diet_type,
                 n.calories, n.protein, n.carbs, n.fat
        ORDER BY
            FIELD(w.day_of_week,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'),
            FIELD(w.meal_time,'Early Morning','Breakfast','Mid Snack','Lunch','Evening Snack','Dinner')
    """)
    rows = cur.fetchall()
    cur.close()
    meals_json = json.dumps([list(r) for r in rows])
    return render_template('mealplanner.html', meals_json=meals_json)


# ── PROGRESS ──────────────────────────────────────────────────
@app.route('/progress')
def progress():
    redir = require_login()
    if redir: return redir

    user_id = session['user_id']
    ensure_tables()
    cur = get_cursor()

    cur.execute("""
        SELECT COALESCE(SUM(calories), 0) FROM user_meal_progress
        WHERE user_id = %s AND DATE(date) = CURDATE() AND completed = TRUE
    """, (user_id,))
    calories_today     = int(cur.fetchone()[0])
    goal               = 2000
    remaining_calories = max(0, goal - calories_today)

    cur.execute("""
        SELECT meal_time, meal_name, calories FROM user_meal_progress
        WHERE user_id = %s AND DATE(date) = CURDATE() AND completed = TRUE
        ORDER BY FIELD(meal_time,'Early Morning','Breakfast','Mid Snack','Lunch','Evening Snack','Dinner')
    """, (user_id,))
    meals = cur.fetchall()

    cur.execute("""
        SELECT DATE(date), COALESCE(SUM(calories), 0)
        FROM user_meal_progress
        WHERE user_id = %s AND completed = TRUE
          AND date >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
        GROUP BY DATE(date) ORDER BY DATE(date)
    """, (user_id,))
    raw_data = cur.fetchall()

    # Water from DB
    cur.execute("""
        SELECT glasses FROM water_log
        WHERE user_id = %s AND log_date = CURDATE()
    """, (user_id,))
    wrow = cur.fetchone()
    water_today = wrow[0] if wrow else 0

    cur.close()

    weekly_dict = {str(r[0]): int(r[1]) for r in raw_data}
    weekly_data = []
    for i in range(6, -1, -1):
        day     = datetime.now() - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        cals    = weekly_dict.get(day_str, 0)
        status  = "good" if cals >= 1500 else "low" if cals > 0 else "none"
        weekly_data.append((day.strftime("%a"), cals, status))

    streak = get_streak(user_id)

    return render_template('progress.html',
        calories_today=calories_today,
        remaining_calories=remaining_calories,
        goal=goal, meals=meals,
        weekly_data=weekly_data,
        water_today=water_today,
        streak=streak)


# ── DIET PLAN ─────────────────────────────────────────────────
@app.route('/dietplan', methods=['POST'])
def dietplan():
    day       = request.form.get('day', '')
    diet_type = request.form.get('diet_type', '').lower()
    goal      = session.get('goal', '')

    cur = get_cursor()
    cur.execute("""
        SELECT w.meal_time, m.meal_id, m.meal_name
        FROM weekly_diet w JOIN meals m ON w.meal_id = m.meal_id
        WHERE w.day_of_week = %s AND LOWER(w.goal) = LOWER(%s)
          AND LOWER(w.diet_type) = LOWER(%s)
        ORDER BY FIELD(w.meal_time,'Early Morning','Breakfast','Mid Snack','Lunch','Evening Snack','Dinner')
    """, (day, goal, diet_type))
    rows = cur.fetchall()
    cur.close()

    meals = {}
    for meal_time, meal_id, meal_name in rows:
        meals.setdefault(meal_time, []).append((meal_id, meal_name))

    return render_template('dietplan.html', meals=meals)


# ── AI FOOD SCANNER ───────────────────────────────────────────
@app.route('/food_scanner')
def food_scanner():
    return render_template('food_scanner.html')


@app.route('/api/analyze_food', methods=['POST'])
def analyze_food():
    try:
        data       = request.get_json()
        img_b64    = data.get('image_base64', '')
        media_type = data.get('media_type', 'image/jpeg')

        if not img_b64:
            return jsonify({'error': 'No image data provided'}), 400

        if media_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
            media_type = 'image/jpeg'

        if not ANTHROPIC_API_KEY:
            demo = {
                "food_name": "Demo Mode — Add Anthropic API Key",
                "description": "Set ANTHROPIC_API_KEY in app.py to enable real AI food analysis.",
                "confidence": "Demo",
                "per_serving": {"calories": 350, "protein_g": 18, "carbs_g": 42, "fat_g": 12, "fiber_g": 4, "sugar_g": 8},
                "ingredients": ["Example ingredient 1", "Example ingredient 2"],
                "health_tags": [{"label": "Demo Mode", "type": "warn"}],
                "notes": "Add your API key to see real analysis."
            }
            return jsonify({'result': demo})

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            system="""You are a professional nutritionist. Given a food image, respond ONLY with valid JSON — no markdown, no code fences.
JSON: {"food_name":"...","description":"...","confidence":"High/Medium/Low","per_serving":{"calories":0,"protein_g":0,"carbs_g":0,"fat_g":0,"fiber_g":0,"sugar_g":0},"ingredients":[],"health_tags":[{"label":"...","type":"good/warn/bad"}],"notes":"..."}""",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_b64}},
                    {"type": "text", "text": "Analyse this food image and return the nutrition JSON."}
                ]
            }]
        )

        raw = message.content[0].text.strip()
        if raw.startswith('```'):
            raw = raw.split('\n', 1)[1] if '\n' in raw else raw
            raw = raw.rsplit('```', 1)[0]

        result = json.loads(raw)
        return jsonify({'result': result})

    except json.JSONDecodeError:
        return jsonify({'error': 'AI returned invalid response. Please try again.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)