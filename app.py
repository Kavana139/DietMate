from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from datetime import datetime, timedelta
import random
import json
import anthropic
import base64

app = Flask(__name__)
app.secret_key = "dietmate_secret_v2"

app.config['MYSQL_HOST']     = 'localhost'
app.config['MYSQL_USER']     = 'root'
app.config['MYSQL_PASSWORD'] = 'Harita@1234'
app.config['MYSQL_DB']       = 'dietmate_db'

mysql = MySQL(app)

# ── Anthropic client for AI food scanner ──────────────────────
# Put your API key here or load from environment variable
# import os; ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
ANTHROPIC_API_KEY = ''   # ← paste your key here


def get_cursor():
    return mysql.connection.cursor()


def require_login():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return None


# ---------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------
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
        cur.execute(
            "SELECT user_id, password, name FROM users WHERE LOWER(email) = %s",
            (email,)
        )
        user = cur.fetchone()
        cur.close()

        if user and str(user[1]).strip() == password:
            session['user_id']   = user[0]
            session['user_name'] = user[2] or 'User'
            flash(f'Welcome back, {user[2]}! 👋', 'success')
            return redirect(url_for('dashboard'))

        return render_template('login.html', error='Invalid email or password.')

    return render_template('login.html')


# ---------------------------------------------------------------
# REGISTER
# ---------------------------------------------------------------
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

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# ---------------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------------
@app.route('/logout')
def logout():
    name = session.get('user_name', '')
    session.clear()
    flash(f'Goodbye{", " + name if name else ""}! See you soon. 👋', 'success')
    return redirect(url_for('login'))


# ---------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------
@app.route('/dashboard')
def dashboard():
    redir = require_login()
    if redir:
        return redir

    user_id = session['user_id']
    cur     = get_cursor()

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

    cur.close()

    tips = [
        "Drink 2–3 litres of water daily to stay hydrated.",
        "Eat a piece of fruit every morning for a natural energy boost.",
        "Avoid processed sugar wherever possible.",
        "Walk at least 30 minutes a day — even a short stroll counts.",
        "Sleep at least 7–8 hours for proper recovery and fat loss.",
        "Eat slowly and chew your food well — it aids digestion.",
        "Include a protein source in every meal to feel fuller, longer.",
        "Prep meals on Sundays to avoid unhealthy weekday choices.",
        "Swap refined grains for whole grains whenever you can.",
        "Add colour to your plate — more colourful means more nutrients.",
    ]

    return render_template(
        'dashboard.html',
        total_recipes=total_recipes,
        meal_types=meal_types,
        diet_plans=diet_plans,
        healthy_tips=random.choice(tips),
        calories_today=calories_today,
        remaining_calories=remaining_calories
    )


# ---------------------------------------------------------------
# HEALTH QUIZ
# ---------------------------------------------------------------
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
            goal      = "Weight Loss"
            calories -= 500
        elif target > weight:
            goal      = "Weight Gain"
            calories += 300
        else:
            goal      = "Muscle Gain"

        calories = max(1200, int(calories))
        protein  = round(weight * 1.8)
        fat      = round(calories * 0.25 / 9)
        carbs    = round((calories - (protein * 4 + fat * 9)) / 4)

        height_m = height / 100
        bmi      = round(weight / (height_m ** 2), 1)

        if bmi < 18.5:
            bmi_category, bmi_color = "Underweight", "#b5860a"
        elif bmi < 25:
            bmi_category, bmi_color = "Normal weight", "#3a8a62"
        elif bmi < 30:
            bmi_category, bmi_color = "Overweight",    "#b5860a"
        else:
            bmi_category, bmi_color = "Obese",         "#c0392b"

        session['calories'] = calories
        session['goal']     = goal

        return render_template(
            'quiz_result.html',
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            goal=goal,
            bmi=bmi,
            bmi_category=bmi_category,
            bmi_color=bmi_color
        )

    return render_template('health_quiz.html')


# ---------------------------------------------------------------
# DIET SELECT
# ---------------------------------------------------------------
@app.route('/dietselect')
def dietselect():
    return render_template('dietselect.html')


# ---------------------------------------------------------------
# AUTO DIET
# ---------------------------------------------------------------
@app.route('/auto_diet', methods=['GET', 'POST'])
def auto_diet():
    diet_type = request.form.get('diet_type') or request.args.get('diet_type')
    calories  = session.get('calories')

    if not calories:
        flash('Complete the Health Quiz first to get a calorie-matched plan.', 'warning')
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

    cur   = get_cursor()
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
            # Fallback: any meals closest to calorie target
            cur.execute("""
                SELECT m.meal_name, n.calories, m.meal_id
                FROM meals m
                JOIN nutrition n ON m.meal_id = n.meal_id
                ORDER BY ABS(n.calories - %s)
                LIMIT 4
            """, (cal_target,))
            rows = cur.fetchall()
        meals[meal_time] = random.sample(rows, min(2, len(rows)))

    cur.close()
    return render_template('auto_diet.html', meals=meals, total=calories)


# ---------------------------------------------------------------
# COMPLETE MEAL
# ---------------------------------------------------------------
@app.route('/complete_meal', methods=['POST'])
def complete_meal():
    redir = require_login()
    if redir:
        return redir

    user_id   = session['user_id']
    meal_id   = request.form.get('meal_id')
    meal_name = request.form.get('meal_name')
    calories  = request.form.get('calories')
    meal_time = request.form.get('meal_time')

    if not all([meal_id, meal_name, calories, meal_time]):
        flash('Could not log that meal — please try again.', 'error')
        return redirect(url_for('auto_diet'))

    cur = get_cursor()
    cur.execute("""
        INSERT INTO user_meal_progress
            (user_id, meal_id, meal_name, meal_time, calories, completed, date)
        VALUES (%s, %s, %s, %s, %s, TRUE, CURDATE())
    """, (user_id, meal_id, meal_name, meal_time, calories))
    mysql.connection.commit()
    cur.close()

    flash(f'✅ "{meal_name}" logged — {calories} kcal added to your daily total!', 'success')
    return redirect(url_for('auto_diet'))


# ---------------------------------------------------------------
# RECIPES
# ---------------------------------------------------------------
@app.route('/recipes')
def recipes():
    cur = get_cursor()
    cur.execute("""
        SELECT m.meal_id, m.meal_name,
               n.calories, n.protein, n.carbs, n.fat
        FROM meals m
        JOIN nutrition n ON m.meal_id = n.meal_id
        ORDER BY m.meal_name
    """)
    recipes = cur.fetchall()
    cur.close()
    return render_template('recipes.html', recipes=recipes)


# ---------------------------------------------------------------
# RECIPE DETAIL
# ---------------------------------------------------------------
@app.route('/recipe/<int:id>')
def recipe(id):
    cur = get_cursor()
    cur.execute("""
        SELECT m.meal_id, m.meal_name, m.recipe, m.image,
               n.calories, n.protein, n.carbs, n.fat
        FROM meals m
        JOIN nutrition n ON m.meal_id = n.meal_id
        WHERE m.meal_id = %s
    """, (id,))
    recipe = cur.fetchone()
    cur.close()

    if not recipe:
        flash('Recipe not found.', 'error')
        return redirect(url_for('recipes'))

    return render_template('recipe.html', recipe=recipe)


# ---------------------------------------------------------------
# MEAL PLANNER  ← FIXED: passes meals_json for JS rendering
# ---------------------------------------------------------------
@app.route('/mealplanner')
def mealplanner():
    cur = get_cursor()
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
        ORDER BY
            FIELD(w.day_of_week,
                'Monday','Tuesday','Wednesday','Thursday',
                'Friday','Saturday','Sunday'),
            FIELD(w.meal_time,
                'Early Morning','Breakfast','Mid Snack',
                'Lunch','Evening Snack','Dinner')
    """)
    rows = cur.fetchall()
    cur.close()

    # Convert to list of lists for JSON — JS expects:
    # [day, meal_time, meal_name, calories, protein, carbs, fat, goal, diet_type]
    meals_list = [list(row) for row in rows]
    meals_json = json.dumps(meals_list)

    return render_template('mealplanner.html', meals_json=meals_json)


# ---------------------------------------------------------------
# PROGRESS
# ---------------------------------------------------------------
@app.route('/progress')
def progress():
    redir = require_login()
    if redir:
        return redir

    user_id = session['user_id']
    cur     = get_cursor()

    cur.execute("""
        SELECT COALESCE(SUM(calories), 0)
        FROM user_meal_progress
        WHERE user_id = %s AND DATE(date) = CURDATE() AND completed = TRUE
    """, (user_id,))
    calories_today     = int(cur.fetchone()[0])
    goal               = 2000
    remaining_calories = max(0, goal - calories_today)

    cur.execute("""
        SELECT meal_time, meal_name, calories
        FROM user_meal_progress
        WHERE user_id = %s AND DATE(date) = CURDATE() AND completed = TRUE
        ORDER BY FIELD(meal_time,
            'Early Morning','Breakfast','Mid Snack',
            'Lunch','Evening Snack','Dinner')
    """, (user_id,))
    meals = cur.fetchall()

    cur.execute("""
        SELECT DATE(date), COALESCE(SUM(calories), 0)
        FROM user_meal_progress
        WHERE user_id = %s AND completed = TRUE
          AND date >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
        GROUP BY DATE(date)
        ORDER BY DATE(date)
    """, (user_id,))
    raw_data = cur.fetchall()
    cur.close()

    weekly_dict = {str(row[0]): int(row[1]) for row in raw_data}
    weekly_data = []

    for i in range(6, -1, -1):
        day     = datetime.now() - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        cals    = weekly_dict.get(day_str, 0)
        status  = "good" if cals >= 1500 else "low" if cals > 0 else "none"
        weekly_data.append((day.strftime("%a"), cals, status))

    return render_template(
        'progress.html',
        calories_today=calories_today,
        remaining_calories=remaining_calories,
        goal=goal,
        meals=meals,
        weekly_data=weekly_data
    )


# ---------------------------------------------------------------
# DIET PLAN
# ---------------------------------------------------------------
@app.route('/dietplan', methods=['POST'])
def dietplan():
    day       = request.form.get('day', '')
    diet_type = request.form.get('diet_type', '').lower()
    goal      = session.get('goal', '')

    cur = get_cursor()
    cur.execute("""
        SELECT w.meal_time, m.meal_id, m.meal_name
        FROM weekly_diet w
        JOIN meals m ON w.meal_id = m.meal_id
        WHERE w.day_of_week = %s
          AND LOWER(w.goal)      = LOWER(%s)
          AND LOWER(w.diet_type) = LOWER(%s)
        ORDER BY FIELD(w.meal_time,
            'Early Morning','Breakfast','Mid Snack',
            'Lunch','Evening Snack','Dinner')
    """, (day, goal, diet_type))

    rows  = cur.fetchall()
    cur.close()

    meals = {}
    for meal_time, meal_id, meal_name in rows:
        meals.setdefault(meal_time, []).append((meal_id, meal_name))

    return render_template('dietplan.html', meals=meals)


# ---------------------------------------------------------------
# AI FOOD SCANNER — page
# ---------------------------------------------------------------
@app.route('/food_scanner')
def food_scanner():
    return render_template('food_scanner.html')


# ---------------------------------------------------------------
# AI FOOD SCANNER — API endpoint
# POST /api/analyze_food
# Body: { image_base64: "...", media_type: "image/jpeg" }
# ---------------------------------------------------------------
@app.route('/api/analyze_food', methods=['POST'])
def analyze_food():
    try:
        data       = request.get_json()
        img_b64    = data.get('image_base64', '')
        media_type = data.get('media_type', 'image/jpeg')

        if not img_b64:
            return jsonify({'error': 'No image data provided'}), 400

        # Validate media type
        allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if media_type not in allowed:
            media_type = 'image/jpeg'

        if not ANTHROPIC_API_KEY:
            # Return demo data if no API key configured
            demo = {
                "food_name": "Demo — Add your Anthropic API key to app.py",
                "description": "Set ANTHROPIC_API_KEY in app.py to enable real AI food analysis.",
                "confidence": "Demo",
                "per_serving": {
                    "calories": 350, "protein_g": 18, "carbs_g": 42,
                    "fat_g": 12, "fiber_g": 4, "sugar_g": 8
                },
                "ingredients": ["Example ingredient 1", "Example ingredient 2"],
                "health_tags": [
                    {"label": "Demo Mode", "type": "warn"}
                ],
                "notes": "Add your ANTHROPIC_API_KEY to see real analysis."
            }
            return jsonify({'result': demo})

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        system_prompt = """You are a professional nutritionist and food analysis expert. 
When given a food image, respond ONLY with valid JSON — no markdown, no code fences, no extra text.

JSON structure:
{
  "food_name": "Name of the food/dish",
  "description": "Brief 1-2 sentence description",
  "confidence": "High / Medium / Low",
  "per_serving": {
    "calories": number,
    "protein_g": number,
    "carbs_g": number,
    "fat_g": number,
    "fiber_g": number,
    "sugar_g": number
  },
  "ingredients": ["ingredient1", "ingredient2"],
  "health_tags": [
    {"label": "High Protein", "type": "good"},
    {"label": "High Sugar", "type": "warn"},
    {"label": "High Calories", "type": "bad"}
  ],
  "notes": "Important note about the estimate"
}

Be as accurate as possible. If not a food, set food_name to "Not a food item" and all numbers to 0."""

        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": img_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": "Analyse this food image and return the nutrition JSON."
                        }
                    ]
                }
            ]
        )

        raw_text = message.content[0].text.strip()

        # Strip code fences if model adds them
        if raw_text.startswith('```'):
            raw_text = raw_text.split('\n', 1)[1] if '\n' in raw_text else raw_text
            raw_text = raw_text.rsplit('```', 1)[0]

        result = json.loads(raw_text)
        return jsonify({'result': result})

    except json.JSONDecodeError as e:
        return jsonify({'error': 'AI returned invalid response. Please try again.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)