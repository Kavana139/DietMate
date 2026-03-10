from unittest import result

from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import random

app = Flask(__name__)
app.secret_key = "dietmate_secret"


# ---------------------------
# MySQL Configuration
# ---------------------------

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Harita@1234'
app.config['MYSQL_DB'] = 'dietmate_db'

mysql = MySQL(app)


# ---------------------------
# LOGIN PAGE
# ---------------------------

@app.route('/', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT user_id FROM users WHERE email=%s AND password=%s",
            (email, password)
        )

        user = cur.fetchone()

        if user:
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))
        else:
            return "Invalid Email or Password"

    return render_template("login.html")


# ---------------------------
# REGISTER
# ---------------------------

@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        age = request.form['age']
        gender = request.form['gender']
        height = request.form['height']
        weight = request.form['weight']
        goal = request.form['goal']
        food_type = request.form['food_type']

        cur = mysql.connection.cursor()

        cur.execute("""
        INSERT INTO users
        (name,email,password,age,gender,height,weight,goal,food_type)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,(name,email,password,age,gender,height,weight,goal,food_type))

        mysql.connection.commit()

        return redirect(url_for('login'))

    return render_template("register.html")


# ---------------------------
# DASHBOARD
# ---------------------------

@app.route('/dashboard')
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()

    # Total recipes
    cur.execute("SELECT COUNT(*) FROM meals")
    total_recipes = cur.fetchone()[0]

    # Total meal types
    cur.execute("SELECT COUNT(DISTINCT meal_time) FROM weekly_diet")
    meal_types = cur.fetchone()[0]

    # Diet plans
    cur.execute("SELECT COUNT(DISTINCT plan_id) FROM weekly_diet")
    diet_plans = cur.fetchone()[0]

    # Healthy tips list
    tips = [
        "Drink 2-3 liters of water daily",
        "Eat fruits every morning",
        "Avoid processed sugar",
        "Walk 30 minutes daily",
        "Sleep at least 7 hours"
    ]

    # Random tip
    healthy_tip = random.choice(tips)

    return render_template(
        "dashboard.html",
        total_recipes=total_recipes,
        meal_types=meal_types,
        diet_plans=diet_plans,
        healthy_tips=healthy_tip
    )

# ---------------------------
# DIET SELECT PAGE
# ---------------------------

@app.route('/dietselect')
def dietselect():
    return render_template("dietselect.html")


@app.route('/quiz', methods=['GET','POST'])
def quiz():

    if request.method == "POST":

        weight = float(request.form['weight'])
        target = float(request.form['target_weight'])
        height = float(request.form['height'])
        age = int(request.form['age'])
        activity = float(request.form['activity'])

        # BMR formula
        bmr = 10 * weight + 6.25 * height - 5 * age + 5

        calories = bmr * activity

        # detect goal automatically
        if target < weight:
            goal = "Weight Loss"
            calories -= 500
        elif target > weight:
            goal = "Weight Gain"
            calories += 500
        else:
            goal = "Muscle Gain"

        protein = weight * 1.8
        fat = calories * 0.25 / 9
        carbs = (calories - (protein*4 + fat*9)) / 4

        session["calories"] = int(calories)
        session["goal"] = goal

        return render_template(
            "quiz_result.html",
            calories=int(calories),
            protein=int(protein),
            carbs=int(carbs),
            fat=int(fat)
        )

    return render_template("health_quiz.html")



@app.route("/auto_diet", methods=["POST"])
def auto_diet():
    diet_type = request.form.get("diet_type")
    day = request.form.get("day")
    goal = session.get("goal")

    calories = session.get("calories")

    if not calories:
        return redirect("/quiz")

    # calorie distribution
    targets = {
        "Early Morning": calories * 0.07,
        "Breakfast": calories * 0.25,
        "Mid Snack": calories * 0.10,
        "Lunch": calories * 0.35,
        "Evening Snack": calories * 0.10,
        "Dinner": calories * 0.23
    }

    cur = mysql.connection.cursor()

    meals = {}

    for meal_time, cal in targets.items():

        cur.execute("""
        SELECT m.meal_name, n.calories, m.meal_id
        FROM meals m
        JOIN nutrition n ON m.meal_id = n.meal_id
        WHERE LOWER(m.diet_type) = LOWER(%s)
        AND LOWER(m.meal_time) = LOWER(%s)
        ORDER BY ABS(n.calories - %s)
        LIMIT 6
        """, (diet_type, meal_time, cal))

        result = cur.fetchall()
        if len(result) >= 2:
            result = random.sample(result, 2)

        meals[meal_time] = result
    return render_template("auto_diet.html", meals=meals, total=calories)


# ---------------------------
# GENERATE DIET PLAN
# ---------------------------

@app.route('/dietplan', methods=['POST'])
def dietplan():

    day = request.form.get('day')
    diet_type = request.form.get('diet_type').lower()

    goal = session.get("goal")

    cur = mysql.connection.cursor()

    cur.execute("""
    SELECT w.meal_time, m.meal_id, m.meal_name
    FROM weekly_diet w
    JOIN meals m ON w.meal_id = m.meal_id
    WHERE w.day_of_week=%s
    AND w.goal=%s
    AND w.diet_type=%s
    ORDER BY FIELD(w.meal_time,
        'Early Morning','Breakfast','Mid Snack','Lunch','Evening Snack','Dinner')
    """,(day,goal,diet_type))

    rows = cur.fetchall()

    meals = {}

    for time, meal_id, meal_name in rows:
        if time not in meals:
            meals[time] = []
        meals[time].append((meal_id, meal_name))

    return render_template("dietplan.html", meals=meals)
    
# ---------------------------
# RECIPE PAGE
# ---------------------------

@app.route("/recipe/<int:id>")
def recipe(id):

    cursor = mysql.connection.cursor()

    cursor.execute("""
            SELECT m.meal_id,
                m.meal_name,
                m.recipe,
                m.image,
                n.calories,
                n.protein,
                n.carbs,
                n.fat
            FROM meals m
            JOIN nutrition n
            ON m.meal_id = n.meal_id
            WHERE m.meal_id=%s
            """,(id,))
    recipe = cursor.fetchone()

    return render_template("recipe.html",recipe=recipe)


@app.route('/mealplanner')
def mealplanner():
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT w.day_of_week, w.meal_time, m.meal_name
        FROM weekly_diet w
        JOIN meals m ON w.meal_id = m.meal_id
        ORDER BY 
            FIELD(w.day_of_week,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'),
            FIELD(w.meal_time,'Early Morning','Breakfast','Mid Snack','Lunch','Evening Snack','Dinner')
    """)

    meals = cur.fetchall()

    return render_template("mealplanner.html", meals=meals)



@app.route('/recipes')
def recipes():

    cur = mysql.connection.cursor()

    cur.execute("""
    SELECT 
        meals.meal_id,
        meals.meal_name,
        nutrition.calories,
        nutrition.protein,
        nutrition.carbs,
        nutrition.fat
    FROM meals
    JOIN nutrition ON meals.meal_id = nutrition.meal_id
    """)

    recipes = cur.fetchall()

    return render_template("recipes.html", recipes=recipes)


@app.route("/complete_meal", methods=["GET","POST"])
def complete_meal():

    if request.method == "POST":

        user_id = session.get("user_id")

        meal_id = request.form.get("meal_id")
        meal_name = request.form.get("meal_name")
        calories = request.form.get("calories")
        meal_time = request.form.get("meal_time")

        cur = mysql.connection.cursor()

        cur.execute("""
        INSERT INTO user_meal_progress
        (user_id, meal_id, meal_name, meal_time, calories, completed, date)
        VALUES (%s,%s,%s,%s,%s,TRUE,CURDATE())
        """,(user_id, meal_id, meal_name, meal_time, calories))

        mysql.connection.commit()

        return redirect("/auto_diet")

    return redirect("/auto_diet")



@app.route("/progress")
def progress():

    user_id = session.get("user_id")

    cur = mysql.connection.cursor()

    # total calories eaten today
    cur.execute("""
        SELECT COALESCE(SUM(calories),0)
        FROM user_meal_progress
        WHERE user_id=%s
        AND completed=TRUE
        AND date = CURDATE()
    """,(user_id,))

    calories_today = cur.fetchone()[0]

    goal = 2000
    remaining_calories = goal - calories_today


    # completed meals
    cur.execute("""
        SELECT meal_name, meal_time, calories
        FROM user_meal_progress
        WHERE user_id=%s
        AND date = CURDATE()
        ORDER BY FIELD(meal_time,
        'Early Morning','Breakfast','Mid Snack','Lunch','Evening Snack','Dinner')
    """,(user_id,))

    meals = cur.fetchall()

    return render_template(
        "progress.html",
        calories_today=calories_today,
        remaining_calories=remaining_calories,
        goal=goal,
        meals=meals
    )

# ---------------------------
# RUN SERVER
# ---------------------------

if __name__ == "__main__":
    app.run(debug=True)