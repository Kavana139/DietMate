"""
db_helpers.py — DietMate Database Helper Functions
Centralized DB operations for cleaner app.py
"""
from datetime import datetime, timedelta, date
from flask import session


def get_cursor(mysql):
    return mysql.connection.cursor()


def ensure_tables(mysql):
    """Create optional/new tables if they don't exist."""
    cur = get_cursor(mysql)
    statements = [
        """CREATE TABLE IF NOT EXISTS user_meal_progress (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            meal_id INT,
            meal_name VARCHAR(255),
            calories INT DEFAULT 0,
            protein DECIMAL(6,2) DEFAULT 0,
            carbs DECIMAL(6,2) DEFAULT 0,
            fat DECIMAL(6,2) DEFAULT 0,
            meal_time VARCHAR(100),
            log_date DATE DEFAULT (CURDATE()),
            logged_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed BOOLEAN DEFAULT TRUE
        )""",
        """CREATE TABLE IF NOT EXISTS water_log (
            user_id INT NOT NULL,
            glasses INT DEFAULT 0,
            log_date DATE NOT NULL,
            PRIMARY KEY(user_id, log_date)
        )""",
        """CREATE TABLE IF NOT EXISTS user_streak (
            user_id INT PRIMARY KEY,
            current_streak INT DEFAULT 0,
            longest_streak INT DEFAULT 0,
            last_log_date DATE,
            total_days INT DEFAULT 0,
            freeze_available BOOLEAN DEFAULT FALSE
        )""",
        """CREATE TABLE IF NOT EXISTS user_weight_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            weight DECIMAL(5,2),
            log_date DATE NOT NULL,
            note VARCHAR(255)
        )""",
        """CREATE TABLE IF NOT EXISTS ai_food_scans (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            food_name VARCHAR(200),
            calories INT DEFAULT 0,
            protein DECIMAL(6,2) DEFAULT 0,
            carbs DECIMAL(6,2) DEFAULT 0,
            fat DECIMAL(6,2) DEFAULT 0,
            confidence VARCHAR(20),
            scanned_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            message TEXT,
            type VARCHAR(50) DEFAULT 'info',
            link VARCHAR(200),
            is_read BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS login_activity (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            action VARCHAR(50) DEFAULT 'login',
            ip_address VARCHAR(45),
            user_agent VARCHAR(500),
            device VARCHAR(100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS user_favorites (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            recipe_id INT,
            smoothie_id INT,
            saved_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS meal_ratings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            recipe_id INT NOT NULL,
            rating INT,
            review TEXT,
            rated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_user_recipe (user_id, recipe_id)
        )""",
        """CREATE TABLE IF NOT EXISTS user_goals_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            goal VARCHAR(50),
            calories INT,
            protein_goal INT,
            carbs_goal INT,
            fat_goal INT,
            weight_at DECIMAL(5,2),
            changed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
    ]
    for stmt in statements:
        try:
            cur.execute(stmt)
        except Exception:
            pass

    # Support legacy or partial schemas where log_date may be missing
    try:
        cur.execute("SHOW COLUMNS FROM user_meal_progress LIKE %s", ('log_date',))
        if not cur.fetchone():
            cur.execute("SHOW COLUMNS FROM user_meal_progress LIKE %s", ('date',))
            has_date_col = bool(cur.fetchone())
            cur.execute("ALTER TABLE user_meal_progress ADD COLUMN log_date DATE")
            if has_date_col:
                cur.execute(
                    "UPDATE user_meal_progress SET log_date = `date` WHERE log_date IS NULL"
                )
            else:
                cur.execute(
                    "UPDATE user_meal_progress SET log_date = DATE(logged_at) WHERE log_date IS NULL"
                )
            cur.execute(
                "ALTER TABLE user_meal_progress MODIFY log_date DATE NOT NULL DEFAULT (CURDATE())"
            )
    except Exception:
        pass

    mysql.connection.commit()
    cur.close()


def get_streak(mysql, uid: int) -> dict:
    """Get user streak data."""
    ensure_tables(mysql)
    cur = get_cursor(mysql)
    try:
        cur.execute(
            "SELECT current_streak, longest_streak, last_log_date, total_days, freeze_available "
            "FROM user_streak WHERE user_id=%s", (uid,))
        row = cur.fetchone()
        if not row:
            return {
                'current': 0, 'longest': 0, 'total': 0,
                'active_today': False, 'streak_broken': False, 'freeze_available': False
            }
        current, longest, last_date, total, freeze = row
        today     = date.today()
        yesterday = today - timedelta(days=1)
        active_today  = (last_date == today)
        streak_broken = (last_date is not None and last_date < yesterday and not freeze)
        return {
            'current': current or 0, 'longest': longest or 0,
            'total': total or 0, 'active_today': active_today,
            'streak_broken': streak_broken, 'freeze_available': bool(freeze)
        }
    except Exception:
        return {
            'current': 0, 'longest': 0, 'total': 0,
            'active_today': False, 'streak_broken': False, 'freeze_available': False
        }
    finally:
        cur.close()


def update_streak(mysql, uid: int):
    """Update streak when meal is logged."""
    ensure_tables(mysql)
    cur = get_cursor(mysql)
    try:
        today     = date.today()
        yesterday = today - timedelta(days=1)
        cur.execute(
            "SELECT current_streak, longest_streak, last_log_date, total_days "
            "FROM user_streak WHERE user_id=%s", (uid,))
        row = cur.fetchone()
        if not row:
            cur.execute(
                "INSERT INTO user_streak(user_id,current_streak,longest_streak,last_log_date,total_days) "
                "VALUES(%s,1,1,%s,1)", (uid, today))
        else:
            curr, longest, last_date, total = row
            if last_date == today:
                pass
            elif last_date == yesterday:
                curr    = (curr or 0) + 1
                longest = max(longest or 0, curr)
                total   = (total or 0) + 1
                cur.execute(
                    "UPDATE user_streak SET current_streak=%s,longest_streak=%s,"
                    "last_log_date=%s,total_days=%s WHERE user_id=%s",
                    (curr, longest, today, total, uid))
            else:
                cur.execute(
                    "UPDATE user_streak SET current_streak=1,last_log_date=%s,"
                    "total_days=total_days+1 WHERE user_id=%s", (today, uid))
        mysql.connection.commit()
    except Exception as e:
        print(f'[STREAK ERROR] {e}')
    finally:
        cur.close()


def log_activity(mysql, uid: int, action: str, ip: str, device: str):
    """Log login/logout activity for security."""
    try:
        cur = get_cursor(mysql)
        cur.execute(
            "INSERT INTO login_activity(user_id,action,ip_address,device) VALUES(%s,%s,%s,%s)",
            (uid, action, ip, device))
        mysql.connection.commit()
        cur.close()
    except Exception:
        pass


def add_notification(mysql, uid: int, message: str, ntype: str = 'info', link: str = None):
    """Add a notification for a user."""
    try:
        cur = get_cursor(mysql)
        cur.execute(
            "INSERT INTO notifications(user_id,message,type,link) VALUES(%s,%s,%s,%s)",
            (uid, message, ntype, link))
        mysql.connection.commit()
        cur.close()
    except Exception:
        pass


def get_unread_notifications(mysql, uid: int) -> list:
    """Get unread notifications for user."""
    try:
        cur = get_cursor(mysql)
        cur.execute(
            "SELECT id, message, type, link, created_at FROM notifications "
            "WHERE user_id=%s AND is_read=FALSE ORDER BY created_at DESC LIMIT 10", (uid,))
        rows = cur.fetchall()
        cur.close()
        return [
            {'id': r[0], 'message': r[1], 'type': r[2], 'link': r[3], 'time': r[4]}
            for r in rows
        ]
    except Exception:
        return []


def save_quiz_to_db(mysql, uid: int, calories: int, goal: str,
                    protein: int, carbs: int, fat: int,
                    bmi: float, bmi_cat: str, weight: float):
    """Persist quiz results to user record and history."""
    try:
        cur = get_cursor(mysql)
        # Only update goal column (exists in base schema)
        cur.execute("UPDATE users SET goal=%s WHERE user_id=%s", (goal, uid))
        # Log weight if table exists
        try:
            cur.execute(
                "INSERT INTO user_weight_log(user_id,weight,log_date) VALUES(%s,%s,CURDATE())"
                " ON DUPLICATE KEY UPDATE weight=%s",
                (uid, weight, weight))
        except Exception:
            pass
        # Save history if table exists
        try:
            cur.execute(
                """INSERT INTO user_goals_history(user_id,goal,calories,protein_goal,carbs_goal,fat_goal,weight_at)
                   VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                (uid, goal, calories, protein, carbs, fat, weight))
        except Exception:
            pass
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        print(f'[QUIZ SAVE ERROR] {e}')


def get_user_by_id(mysql, uid: int) -> dict:
    """Get full user record as dict."""
    try:
        cur = get_cursor(mysql)
        cur.execute(
            "SELECT user_id, name, email, age, gender, height, weight, goal, "
            "food_type, created_at, last_login "
            "FROM users WHERE user_id=%s", (uid,))
        row = cur.fetchone()
        cur.close()
        if not row:
            return {}
        return {
            'user_id': row[0], 'name': row[1], 'email': row[2],
            'age': row[3], 'gender': row[4], 'height': row[5],
            'weight': row[6], 'goal': row[7], 'food_type': row[8],
            'calories': 2000, 'protein_goal': 120,
            'carbs_goal': 250, 'fat_goal': 55,
            'bmi': None, 'bmi_category': None,
            'quiz_done': False,
            'created_at': row[9], 'last_login': row[10]
        }
    except Exception:
        return {}


SLOT_ORDER = ['Early Morning', 'Breakfast', 'Mid Snack', 'Lunch', 'Evening Snack', 'Dinner']
SLOT_MAX   = 2
SLOT_SHARE = {
    'Early Morning': 0.05, 'Breakfast': 0.25, 'Mid Snack': 0.10,
    'Lunch': 0.30, 'Evening Snack': 0.10, 'Dinner': 0.20,
}
QUANTIFIABLE = {
    'whole wheat roti':    ('Roti',   80),
    'soft whole wheat rotis': ('Roti', 80),
    'perfect brown rice':  ('Bowl',   215),
    'perfect fluffy brown rice': ('Bowl', 215),
    'idli sambar':         ('Idli',   55),
    'boiled eggs with toast': ('Egg', 70),
    'hard boiled eggs':    ('Egg',    70),
    'banana oat pancakes': ('Pancake', 65),
}

import random

def build_smart_plan(mysql, goal: str, diet_type: str, target_cal: int) -> dict:
    """Build a smart meal plan based on goal, diet type, and calorie target."""
    cur = get_cursor(mysql)
    if diet_type == 'nonveg':
        cur.execute("""
            SELECT DISTINCT w.meal_time, m.meal_name, COALESCE(n.calories,0), m.meal_id,
                   COALESCE(n.protein,0), COALESCE(n.carbs,0), COALESCE(n.fat,0), w.diet_type
            FROM weekly_diet w
            JOIN meals m ON w.meal_id=m.meal_id
            LEFT JOIN nutrition n ON m.meal_id=n.meal_id
            WHERE LOWER(w.goal)=LOWER(%s)
            ORDER BY FIELD(w.meal_time,'Early Morning','Breakfast','Mid Snack','Lunch','Evening Snack','Dinner'),
                CASE WHEN LOWER(w.diet_type)='veg' THEN 1 ELSE 0 END
        """, (goal,))
    else:
        cur.execute("""
            SELECT DISTINCT w.meal_time, m.meal_name, COALESCE(n.calories,0), m.meal_id,
                   COALESCE(n.protein,0), COALESCE(n.carbs,0), COALESCE(n.fat,0), w.diet_type
            FROM weekly_diet w
            JOIN meals m ON w.meal_id=m.meal_id
            LEFT JOIN nutrition n ON m.meal_id=n.meal_id
            WHERE LOWER(w.goal)=LOWER(%s) AND LOWER(w.diet_type)='veg'
            ORDER BY FIELD(w.meal_time,'Early Morning','Breakfast','Mid Snack','Lunch','Evening Snack','Dinner')
        """, (goal,))

    rows = cur.fetchall()
    cur.close()

    slot_pool = {}
    seen = set()
    for mt, mn, cal, mid, prot, carbs, fat, dtype in rows:
        key = (mt, mn)
        if key in seen:
            continue
        seen.add(key)
        slot_pool.setdefault(mt, []).append({
            'name': mn, 'cal': int(cal or 0), 'meal_id': int(mid) if mid else 0,
            'protein': float(prot or 0), 'carbs': float(carbs or 0),
            'fat': float(fat or 0), 'dtype': dtype or '',
        })

    plan = {}
    for slot in SLOT_ORDER:
        pool = slot_pool.get(slot, [])
        if not pool:
            continue
        target_slot = int(target_cal * SLOT_SHARE.get(slot, 0.16))
        random.shuffle(pool)
        chosen  = []
        running = 0
        for item in pool:
            if len(chosen) >= SLOT_MAX:
                break
            key_lower = item['name'].lower()
            if key_lower in QUANTIFIABLE and item['cal'] > 0:
                unit_name, unit_cal = QUANTIFIABLE[key_lower]
                qty = max(1, round(target_slot * 0.4 / unit_cal)) if running == 0 else 1
                display    = f"{qty} {unit_name}{'s' if qty > 1 else ''}"
                scaled_cal = unit_cal * qty
                chosen.append({**item, 'display_name': display, 'cal': scaled_cal})
                running += scaled_cal
            else:
                chosen.append(item)
                running += item['cal']
        plan[slot] = chosen

    return plan