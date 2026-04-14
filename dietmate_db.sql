DROP DATABASE IF EXISTS dietmate_db;
CREATE DATABASE dietmate_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE dietmate_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE dietmate_db;
CREATE TABLE users (
    user_id   INT AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(100)  NOT NULL,
    email     VARCHAR(120)  UNIQUE NOT NULL,
    password  VARCHAR(255)  NOT NULL,
    age       INT,
    gender    ENUM('Male','Female','Other'),
    height    FLOAT,
    weight    FLOAT,
    goal      ENUM('Weight Loss','Weight Gain','Muscle Gain'),
    food_type ENUM('veg','nonveg') DEFAULT 'veg',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);

CREATE TABLE diet_plan (
    plan_id   INT AUTO_INCREMENT PRIMARY KEY,
    goal      ENUM('Weight Loss','Weight Gain','Muscle Gain') NOT NULL,
    food_type ENUM('veg','nonveg') NOT NULL
);

INSERT INTO diet_plan (goal, food_type) VALUES
('Weight Loss','veg'),
('Weight Loss','nonveg'),
('Weight Gain','veg'),
('Weight Gain','nonveg'),
('Muscle Gain','veg'),
('Muscle Gain','nonveg');

CREATE TABLE meals (
    meal_id    INT AUTO_INCREMENT PRIMARY KEY,
    meal_name  VARCHAR(150) NOT NULL,
    recipe     TEXT,
    image      VARCHAR(255),
    category   ENUM('veg','nonveg') DEFAULT 'veg',
    meal_type  ENUM('breakfast','snack','lunch','dinner','drink','early_morning') DEFAULT 'lunch',
    prep_time  INT,
    difficulty ENUM('Easy','Medium','Hard') DEFAULT 'Easy'
);

INSERT INTO meals (meal_id, meal_name, recipe, image, category, meal_type, prep_time, difficulty) VALUES
(1,'Warm Lemon Water','Squeeze lemon in warm water','lemon_water.jpg','veg','drink',2,'Easy'),
(2,'Soaked Almonds','Soak almonds overnight','soaked_almonds.jpg','veg','early_morning',1,'Easy'),
(3,'Oats with Apple','Cook oats with apple','oats_apple.jpg','veg','breakfast',10,'Easy'),
(4,'Papaya Bowl','Cut papaya and serve','papaya_bowl.jpg','veg','breakfast',5,'Easy'),
(5,'Mixed Vegetable Curry','Cook vegetables with spices','mixed_veg_curry.jpg','veg','lunch',25,'Medium');

INSERT INTO meals (meal_id, meal_name, recipe, image, category, meal_type, prep_time, difficulty) VALUES
(6,'Whole Wheat Roti','Make roti from wheat flour','wheat_roti.jpg','veg','lunch',15,'Easy'),
(7,'Green Tea','Brew green tea','green_tea.jpg','veg','drink',3,'Easy'),
(8,'Roasted Chana','Roast chana','roasted_chana.jpg','veg','snack',8,'Easy'),
(9,'Vegetable Soup','Cook vegetables in water','vegetable_soup.jpg','veg','dinner',20,'Easy'),
(10,'Cucumber Salad','Mix cucumber and spices','cucumber_salad.jpg','veg','snack',5,'Easy');

INSERT INTO meals (meal_id, meal_name, recipe, image, category, meal_type, prep_time, difficulty) VALUES
(1, 'Warm Lemon Water',
 'Squeeze half a lemon into a glass of warm water. Add a pinch of Himalayan salt. Drink on an empty stomach.',
 'lemon_water.jpg','veg','drink',2,'Easy'),
 
(2, 'Soaked Almonds',
 'Soak 8–10 raw almonds in water overnight. Peel the skin in the morning and eat slowly.',
 'soaked_almonds.jpg','veg','early_morning',1,'Easy'),
 
(3, 'Oats with Apple',
 'Cook 50g rolled oats in 1 cup milk or water for 5 minutes. Top with a sliced apple, a pinch of cinnamon and 1 tsp honey.',
 'oats_apple.jpg','veg','breakfast',10,'Easy'),
 
(4, 'Papaya Bowl',
 'Cut half a ripe papaya into cubes. Squeeze lime juice over it and add a pinch of black salt.',
 'papaya_bowl.jpg','veg','breakfast',5,'Easy'),
 
(5, 'Mixed Vegetable Curry',
 'Heat 1 tsp oil. Add cumin, onion, tomato, ginger-garlic paste. Cook till soft. Add seasonal vegetables (carrot, potato, peas, beans). Add spices and 1/4 cup water. Simmer 15 minutes.',
 'mixed_veg_curry.jpg','veg','lunch',25,'Medium'),
 
(6, 'Whole Wheat Roti',
 'Knead whole wheat flour with water into soft dough. Rest 10 minutes. Roll into thin circles and cook on a hot tawa till golden spots appear on both sides.',
 'wheat_roti.jpg','veg','lunch',15,'Easy'),
 
(7, 'Green Tea',
 'Brew 1 tsp green tea leaves or 1 tea bag in 180 ml hot water (not boiling) for 2–3 minutes. Add lemon and honey if desired.',
 'green_tea.jpg','veg','drink',3,'Easy'),
 
(8, 'Roasted Chana',
 'Dry roast 40g Bengal gram (chana) in a pan until crisp. Season with chaat masala and lemon juice.',
 'roasted_chana.jpg','veg','snack',8,'Easy'),
 
(9, 'Vegetable Soup',
 'Boil carrot, tomato, celery, onion and garlic in 2 cups water. Blend half, mix back in. Season with salt, pepper and herbs.',
 'vegetable_soup.jpg','veg','dinner',20,'Easy'),
 
(10, 'Cucumber Salad',
 'Slice 1 cucumber. Add diced tomato, red onion. Toss with salt, lemon juice, chaat masala and fresh coriander.',
 'cucumber_salad.jpg','veg','snack',5,'Easy'),
 
(11, 'Vegetable Poha',
 'Rinse 1 cup poha (flattened rice) and drain. Heat oil, add mustard seeds, curry leaves, green chilli, onion. Add peas and poha. Mix turmeric, salt, lemon juice. Cook 5 minutes.',
 'veg_poha.jpg','veg','breakfast',15,'Easy'),
 
(12, 'Orange',
 'Peel one medium orange and separate into segments. Eat fresh. Can squeeze for juice.',
 'orange.jpg','veg','snack',2,'Easy'),
 
(13, 'Brown Rice',
 'Rinse 1/2 cup brown rice. Add 1.5 cups water and a pinch of salt. Bring to boil, reduce heat, cover and cook 40–45 minutes.',
 'brown_rice.jpg','veg','lunch',45,'Easy'),
 
(14, 'Dal (Lentil Soup)',
 'Wash 1/2 cup toor or masoor dal. Pressure cook with water, turmeric for 3 whistles. Prepare tadka: heat ghee, add cumin, onion, tomato, chilli, coriander. Mix into dal.',
 'dal.jpg','veg','lunch',25,'Medium'),
 
(15, 'Spinach Sabzi',
 'Blanch 2 cups spinach and chop. Heat oil, add garlic, onion, cook 3 minutes. Add spinach, salt, garam masala. Cook 5 minutes.',
 'spinach_sabzi.jpg','veg','lunch',15,'Easy'),
 
(16, 'Sprouts Salad',
 'Mix 1 cup boiled sprouts with diced tomato, onion, cucumber, green chilli, lemon juice and chaat masala.',
 'sprouts_salad.jpg','veg','snack',5,'Easy'),
 
(17, 'Paneer Salad',
 'Cube 80g fresh paneer. Mix with sliced bell peppers, tomatoes, onion. Toss with olive oil, lemon, cumin powder and rock salt.',
 'paneer_salad.jpg','veg','lunch',8,'Easy'),
 
(18, 'Idli',
 'Soak rice and urad dal overnight. Grind to smooth batter. Ferment 8 hours. Pour into greased idli moulds and steam 12 minutes.',
 'idli.jpg','veg','breakfast',20,'Hard'),
 
(19, 'Coconut Chutney',
 'Blend 1/2 cup grated coconut with green chilli, ginger, salt and water. Prepare tadka with mustard seeds, curry leaves in oil and pour over.',
 'coconut_chutney.jpg','veg','breakfast',5,'Easy'),
 
(20, 'Apple',
 'Wash and slice one medium apple. Can be eaten with peanut butter for extra protein.',
 'apple.jpg','veg','snack',2,'Easy'),
 
(21, 'Cabbage Sabzi',
 'Shred 2 cups cabbage. Heat oil, add mustard seeds, curry leaves, green chilli. Add cabbage, turmeric, salt. Cook 8–10 minutes.',
 'cabbage_sabzi.jpg','veg','lunch',15,'Easy'),
 
(22, 'Roasted Peanuts',
 'Dry roast 30g raw peanuts in a pan on low heat until shells turn slightly brown, about 8 minutes. Add salt.',
 'roasted_peanuts.jpg','veg','snack',10,'Easy'),
 
(23, 'Tomato Salad',
 'Slice 2 medium tomatoes. Add sliced onion, cucumber. Season with salt, black pepper and lemon juice.',
 'tomato_salad.jpg','veg','snack',3,'Easy'),
 
(24, 'Vegetable Upma',
 'Dry roast 1/2 cup semolina. Heat oil, add mustard seeds, cashews, onion, vegetables (carrot, peas, beans). Add 1.5 cups water, bring to boil. Add semolina while stirring. Cook 5 minutes.',
 'veg_upma.jpg','veg','breakfast',20,'Medium'),
 
(25, 'Banana',
 'Eat one medium ripe banana. Excellent pre-workout energy source.',
 'banana.jpg','veg','snack',1,'Easy'),
 
(26, 'Rajma (Kidney Bean Curry)',
 'Soak 1/2 cup rajma overnight. Pressure cook till soft. Prepare onion-tomato-spice gravy. Mix rajma and simmer 15 minutes.',
 'rajma.jpg','veg','lunch',40,'Medium'),
 
(27, 'Buttermilk',
 'Blend 1/2 cup yogurt with 1 cup water, roasted cumin, salt and fresh mint. Froth and serve chilled.',
 'buttermilk.jpg','veg','drink',3,'Easy'),
 
(28, 'Roasted Makhana',
 'Heat 1 tsp ghee in a pan. Add fox nuts (makhana) and roast on low heat 8–10 minutes until crunchy. Add salt and chaat masala.',
 'roasted_makhana.jpg','veg','snack',10,'Easy'),
 
(29, 'Paneer Stir Fry',
 'Cut 100g paneer into cubes. In a pan, heat oil and add cumin. Add diced bell peppers, onion, paneer. Season with jeera powder, amchur, salt. Stir fry 8 minutes.',
 'paneer_stir_fry.jpg','veg','lunch',15,'Easy'),
 
(30, 'Vegetable Khichdi',
 'Wash 1/4 cup rice and 1/4 cup moong dal. Cook with diced vegetables (carrot, peas, potato), turmeric, salt in 2.5 cups water for 3 whistles. Finish with ghee and cumin tadka.',
 'veg_khichdi.jpg','veg','dinner',30,'Easy'),
 
-- New Veg meals 31–43
(31, 'Moong Dal Chilla',
 'Soak yellow moong dal 2 hours. Grind with ginger, green chilli to batter. Add chopped onion, tomato, coriander. Make thin pancakes on non-stick pan.',
 'moong_chilla.jpg','veg','breakfast',20,'Medium'),
 
(32, 'Dahi (Curd) Bowl',
 'Take 150ml fresh low-fat curd. Add a pinch of roasted cumin, rock salt, and fresh mint leaves. Eat as a side dish.',
 'dahi_bowl.jpg','veg','lunch',2,'Easy'),
 
(33, 'Palak Paneer',
 'Blanch 2 cups spinach and puree. Sauté onion, tomato, ginger-garlic paste. Add paneer cubes and spinach puree. Simmer with cream and spices 10 minutes.',
 'palak_paneer.jpg','veg','dinner',30,'Medium'),
 
(34, 'Masala Oats',
 'Heat oil, add mustard seeds, curry leaves, onion. Add rolled oats, vegetables, spices and 1.5 cups water. Cook until thick.',
 'masala_oats.jpg','veg','breakfast',12,'Easy'),
 
(35, 'Peanut Butter Toast',
 'Toast 2 slices whole wheat bread. Spread 1 tbsp natural peanut butter. Top with banana slices.',
 'pb_toast.jpg','veg','breakfast',5,'Easy'),
 
(36, 'Mixed Fruit Bowl',
 'Chop seasonal fruits: papaya, apple, grapes, banana, pomegranate seeds. Mix with a squeeze of lemon and honey.',
 'fruit_bowl.jpg','veg','breakfast',8,'Easy'),
 
(37, 'Chole (Chickpea Curry)',
 'Soak chickpeas overnight. Pressure cook till soft. Prepare spiced onion-tomato gravy. Add chickpeas and sour pomegranate powder. Simmer 15 minutes.',
 'chole.jpg','veg','lunch',45,'Medium'),
 
(38, 'Baingan Bharta',
 'Roast brinjal on flame until charred. Peel and mash. Saute onion, tomato, garlic. Add mashed brinjal and spices. Cook 10 minutes.',
 'baingan_bharta.jpg','veg','dinner',25,'Medium'),
 
(39, 'Greek Yogurt with Berries',
 'Take 150g thick Greek yogurt. Top with mixed berries (strawberry, blueberry), granola, and drizzle of honey.',
 'greek_yogurt.jpg','veg','breakfast',3,'Easy'),
 
(40, 'Sweet Potato Chaat',
 'Boil 1 medium sweet potato, cube it. Toss with yogurt, tamarind chutney, chaat masala, pomegranate seeds.',
 'sweet_potato.jpg','veg','snack',15,'Easy'),
 
(41, 'Methi Thepla',
 'Mix whole wheat flour with chopped fenugreek leaves, yogurt, spices and minimal oil. Knead soft dough. Roll thin and cook on tawa.',
 'thepla.jpg','veg','breakfast',20,'Medium'),
 
(42, 'Sambar',
 'Cook toor dal with tamarind water, tomatoes and vegetables (drumstick, carrot, eggplant). Prepare sambar powder based tempering. Simmer 15 minutes.',
 'sambar.jpg','veg','lunch',30,'Medium'),
 
(43, 'Coconut Water',
 'Serve fresh tender coconut water. Natural electrolytes and hydration.',
 'coconut_water.jpg','veg','drink',1,'Easy');
 
 INSERT INTO meals (meal_id, meal_name, recipe, image, category, meal_type, prep_time, difficulty) VALUES
(1, 'Warm Lemon Water',
 'Squeeze half a lemon into a glass of warm water. Add a pinch of Himalayan salt. Drink on an empty stomach.',
 'lemon_water.jpg','veg','drink',2,'Easy'),
 
(2, 'Soaked Almonds',
 'Soak 8–10 raw almonds in water overnight. Peel the skin in the morning and eat slowly.',
 'soaked_almonds.jpg','veg','early_morning',1,'Easy'),
 
(3, 'Oats with Apple',
 'Cook 50g rolled oats in 1 cup milk or water for 5 minutes. Top with a sliced apple, a pinch of cinnamon and 1 tsp honey.',
 'oats_apple.jpg','veg','breakfast',10,'Easy'),
 
(4, 'Papaya Bowl',
 'Cut half a ripe papaya into cubes. Squeeze lime juice over it and add a pinch of black salt.',
 'papaya_bowl.jpg','veg','breakfast',5,'Easy'),
 
(5, 'Mixed Vegetable Curry',
 'Heat 1 tsp oil. Add cumin, onion, tomato, ginger-garlic paste. Cook till soft. Add seasonal vegetables (carrot, potato, peas, beans). Add spices and 1/4 cup water. Simmer 15 minutes.',
 'mixed_veg_curry.jpg','veg','lunch',25,'Medium'),
 
(6, 'Whole Wheat Roti',
 'Knead whole wheat flour with water into soft dough. Rest 10 minutes. Roll into thin circles and cook on a hot tawa till golden spots appear on both sides.',
 'wheat_roti.jpg','veg','lunch',15,'Easy'),
 
(7, 'Green Tea',
 'Brew 1 tsp green tea leaves or 1 tea bag in 180 ml hot water (not boiling) for 2–3 minutes. Add lemon and honey if desired.',
 'green_tea.jpg','veg','drink',3,'Easy'),
 
(8, 'Roasted Chana',
 'Dry roast 40g Bengal gram (chana) in a pan until crisp. Season with chaat masala and lemon juice.',
 'roasted_chana.jpg','veg','snack',8,'Easy'),
 
(9, 'Vegetable Soup',
 'Boil carrot, tomato, celery, onion and garlic in 2 cups water. Blend half, mix back in. Season with salt, pepper and herbs.',
 'vegetable_soup.jpg','veg','dinner',20,'Easy'),
 
(10, 'Cucumber Salad',
 'Slice 1 cucumber. Add diced tomato, red onion. Toss with salt, lemon juice, chaat masala and fresh coriander.',
 'cucumber_salad.jpg','veg','snack',5,'Easy'),
 
(11, 'Vegetable Poha',
 'Rinse 1 cup poha (flattened rice) and drain. Heat oil, add mustard seeds, curry leaves, green chilli, onion. Add peas and poha. Mix turmeric, salt, lemon juice. Cook 5 minutes.',
 'veg_poha.jpg','veg','breakfast',15,'Easy'),
 
(12, 'Orange',
 'Peel one medium orange and separate into segments. Eat fresh. Can squeeze for juice.',
 'orange.jpg','veg','snack',2,'Easy'),
 
(13, 'Brown Rice',
 'Rinse 1/2 cup brown rice. Add 1.5 cups water and a pinch of salt. Bring to boil, reduce heat, cover and cook 40–45 minutes.',
 'brown_rice.jpg','veg','lunch',45,'Easy'),
 
(14, 'Dal (Lentil Soup)',
 'Wash 1/2 cup toor or masoor dal. Pressure cook with water, turmeric for 3 whistles. Prepare tadka: heat ghee, add cumin, onion, tomato, chilli, coriander. Mix into dal.',
 'dal.jpg','veg','lunch',25,'Medium'),
 
(15, 'Spinach Sabzi',
 'Blanch 2 cups spinach and chop. Heat oil, add garlic, onion, cook 3 minutes. Add spinach, salt, garam masala. Cook 5 minutes.',
 'spinach_sabzi.jpg','veg','lunch',15,'Easy'),
 
(16, 'Sprouts Salad',
 'Mix 1 cup boiled sprouts with diced tomato, onion, cucumber, green chilli, lemon juice and chaat masala.',
 'sprouts_salad.jpg','veg','snack',5,'Easy'),
 
(17, 'Paneer Salad',
 'Cube 80g fresh paneer. Mix with sliced bell peppers, tomatoes, onion. Toss with olive oil, lemon, cumin powder and rock salt.',
 'paneer_salad.jpg','veg','lunch',8,'Easy'),
 
(18, 'Idli',
 'Soak rice and urad dal overnight. Grind to smooth batter. Ferment 8 hours. Pour into greased idli moulds and steam 12 minutes.',
 'idli.jpg','veg','breakfast',20,'Hard'),
 
(19, 'Coconut Chutney',
 'Blend 1/2 cup grated coconut with green chilli, ginger, salt and water. Prepare tadka with mustard seeds, curry leaves in oil and pour over.',
 'coconut_chutney.jpg','veg','breakfast',5,'Easy'),
 
(20, 'Apple',
 'Wash and slice one medium apple. Can be eaten with peanut butter for extra protein.',
 'apple.jpg','veg','snack',2,'Easy'),
 
(21, 'Cabbage Sabzi',
 'Shred 2 cups cabbage. Heat oil, add mustard seeds, curry leaves, green chilli. Add cabbage, turmeric, salt. Cook 8–10 minutes.',
 'cabbage_sabzi.jpg','veg','lunch',15,'Easy'),
 
(22, 'Roasted Peanuts',
 'Dry roast 30g raw peanuts in a pan on low heat until shells turn slightly brown, about 8 minutes. Add salt.',
 'roasted_peanuts.jpg','veg','snack',10,'Easy'),
 
(23, 'Tomato Salad',
 'Slice 2 medium tomatoes. Add sliced onion, cucumber. Season with salt, black pepper and lemon juice.',
 'tomato_salad.jpg','veg','snack',3,'Easy'),
 
(24, 'Vegetable Upma',
 'Dry roast 1/2 cup semolina. Heat oil, add mustard seeds, cashews, onion, vegetables (carrot, peas, beans). Add 1.5 cups water, bring to boil. Add semolina while stirring. Cook 5 minutes.',
 'veg_upma.jpg','veg','breakfast',20,'Medium'),
 
(25, 'Banana',
 'Eat one medium ripe banana. Excellent pre-workout energy source.',
 'banana.jpg','veg','snack',1,'Easy'),
 
(26, 'Rajma (Kidney Bean Curry)',
 'Soak 1/2 cup rajma overnight. Pressure cook till soft. Prepare onion-tomato-spice gravy. Mix rajma and simmer 15 minutes.',
 'rajma.jpg','veg','lunch',40,'Medium'),
 
(27, 'Buttermilk',
 'Blend 1/2 cup yogurt with 1 cup water, roasted cumin, salt and fresh mint. Froth and serve chilled.',
 'buttermilk.jpg','veg','drink',3,'Easy'),
 
(28, 'Roasted Makhana',
 'Heat 1 tsp ghee in a pan. Add fox nuts (makhana) and roast on low heat 8–10 minutes until crunchy. Add salt and chaat masala.',
 'roasted_makhana.jpg','veg','snack',10,'Easy'),
 
(29, 'Paneer Stir Fry',
 'Cut 100g paneer into cubes. In a pan, heat oil and add cumin. Add diced bell peppers, onion, paneer. Season with jeera powder, amchur, salt. Stir fry 8 minutes.',
 'paneer_stir_fry.jpg','veg','lunch',15,'Easy'),
 
(30, 'Vegetable Khichdi',
 'Wash 1/4 cup rice and 1/4 cup moong dal. Cook with diced vegetables (carrot, peas, potato), turmeric, salt in 2.5 cups water for 3 whistles. Finish with ghee and cumin tadka.',
 'veg_khichdi.jpg','veg','dinner',30,'Easy'),
 
-- New Veg meals 31–43
(31, 'Moong Dal Chilla',
 'Soak yellow moong dal 2 hours. Grind with ginger, green chilli to batter. Add chopped onion, tomato, coriander. Make thin pancakes on non-stick pan.',
 'moong_chilla.jpg','veg','breakfast',20,'Medium'),
 
(32, 'Dahi (Curd) Bowl',
 'Take 150ml fresh low-fat curd. Add a pinch of roasted cumin, rock salt, and fresh mint leaves. Eat as a side dish.',
 'dahi_bowl.jpg','veg','lunch',2,'Easy'),
 
(33, 'Palak Paneer',
 'Blanch 2 cups spinach and puree. Sauté onion, tomato, ginger-garlic paste. Add paneer cubes and spinach puree. Simmer with cream and spices 10 minutes.',
 'palak_paneer.jpg','veg','dinner',30,'Medium'),
 
(34, 'Masala Oats',
 'Heat oil, add mustard seeds, curry leaves, onion. Add rolled oats, vegetables, spices and 1.5 cups water. Cook until thick.',
 'masala_oats.jpg','veg','breakfast',12,'Easy'),
 
(35, 'Peanut Butter Toast',
 'Toast 2 slices whole wheat bread. Spread 1 tbsp natural peanut butter. Top with banana slices.',
 'pb_toast.jpg','veg','breakfast',5,'Easy'),
 
(36, 'Mixed Fruit Bowl',
 'Chop seasonal fruits: papaya, apple, grapes, banana, pomegranate seeds. Mix with a squeeze of lemon and honey.',
 'fruit_bowl.jpg','veg','breakfast',8,'Easy'),
 
(37, 'Chole (Chickpea Curry)',
 'Soak chickpeas overnight. Pressure cook till soft. Prepare spiced onion-tomato gravy. Add chickpeas and sour pomegranate powder. Simmer 15 minutes.',
 'chole.jpg','veg','lunch',45,'Medium'),
 
(38, 'Baingan Bharta',
 'Roast brinjal on flame until charred. Peel and mash. Saute onion, tomato, garlic. Add mashed brinjal and spices. Cook 10 minutes.',
 'baingan_bharta.jpg','veg','dinner',25,'Medium'),
 
(39, 'Greek Yogurt with Berries',
 'Take 150g thick Greek yogurt. Top with mixed berries (strawberry, blueberry), granola, and drizzle of honey.',
 'greek_yogurt.jpg','veg','breakfast',3,'Easy'),
 
(40, 'Sweet Potato Chaat',
 'Boil 1 medium sweet potato, cube it. Toss with yogurt, tamarind chutney, chaat masala, pomegranate seeds.',
 'sweet_potato.jpg','veg','snack',15,'Easy'),
 
(41, 'Methi Thepla',
 'Mix whole wheat flour with chopped fenugreek leaves, yogurt, spices and minimal oil. Knead soft dough. Roll thin and cook on tawa.',
 'thepla.jpg','veg','breakfast',20,'Medium'),
 
(42, 'Sambar',
 'Cook toor dal with tamarind water, tomatoes and vegetables (drumstick, carrot, eggplant). Prepare sambar powder based tempering. Simmer 15 minutes.',
 'sambar.jpg','veg','lunch',30,'Medium'),
 
(43, 'Coconut Water',
 'Serve fresh tender coconut water. Natural electrolytes and hydration.',
 'coconut_water.jpg','veg','drink',1,'Easy');
 DROP DATABASE IF EXISTS dietmate_db;
 CREATE DATABASE dietmate_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
 
 USE dietmate_db;
 
 CREATE TABLE users (
    user_id   INT AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(100)  NOT NULL,
    email     VARCHAR(120)  UNIQUE NOT NULL,
    password  VARCHAR(255)  NOT NULL,
    age       INT,
    gender    ENUM('Male','Female','Other'),
    height    FLOAT COMMENT 'cm',
    weight    FLOAT COMMENT 'kg',
    goal      ENUM('Weight Loss','Weight Gain','Muscle Gain'),
    food_type ENUM('veg','nonveg') DEFAULT 'veg',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);

INSERT INTO diet_plan (goal, food_type) VALUES
('Weight Loss','veg'),
('Weight Loss','nonveg'),
('Weight Gain','veg'),
('Weight Gain','nonveg'),
('Muscle Gain','veg'),
('Muscle Gain','nonveg');

CREATE TABLE diet_plan (
    plan_id   INT AUTO_INCREMENT PRIMARY KEY,
    goal      ENUM('Weight Loss','Weight Gain','Muscle Gain') NOT NULL,
    food_type ENUM('veg','nonveg') NOT NULL
);

INSERT INTO diet_plan (goal, food_type) VALUES
('Weight Loss','veg'),
('Weight Loss','nonveg'),
('Weight Gain','veg'),
('Weight Gain','nonveg'),
('Muscle Gain','veg'),
('Muscle Gain','nonveg');


CREATE TABLE meals (
    meal_id    INT AUTO_INCREMENT PRIMARY KEY,
    meal_name  VARCHAR(150) NOT NULL,
    recipe     TEXT,
    image      VARCHAR(255),
    category   ENUM('veg','nonveg') DEFAULT 'veg',
    meal_type  ENUM('breakfast','snack','lunch','dinner','drink','early_morning') DEFAULT 'lunch',
    prep_time  INT COMMENT 'minutes',
    difficulty ENUM('Easy','Medium','Hard') DEFAULT 'Easy'
);

INSERT INTO meals (meal_id, meal_name, recipe, image, category, meal_type, prep_time, difficulty) VALUES
(1, 'Warm Lemon Water',
 'Squeeze half a lemon into a glass of warm water. Add a pinch of Himalayan salt. Drink on an empty stomach.',
 'lemon_water.jpg','veg','drink',2,'Easy'),
 
(2, 'Soaked Almonds',
 'Soak 8–10 raw almonds in water overnight. Peel the skin in the morning and eat slowly.',
 'soaked_almonds.jpg','veg','early_morning',1,'Easy'),
 
(3, 'Oats with Apple',
 'Cook 50g rolled oats in 1 cup milk or water for 5 minutes. Top with a sliced apple, a pinch of cinnamon and 1 tsp honey.',
 'oats_apple.jpg','veg','breakfast',10,'Easy'),
 
(4, 'Papaya Bowl',
 'Cut half a ripe papaya into cubes. Squeeze lime juice over it and add a pinch of black salt.',
 'papaya_bowl.jpg','veg','breakfast',5,'Easy'),
 
(5, 'Mixed Vegetable Curry',
 'Heat 1 tsp oil. Add cumin, onion, tomato, ginger-garlic paste. Cook till soft. Add seasonal vegetables (carrot, potato, peas, beans). Add spices and 1/4 cup water. Simmer 15 minutes.',
 'mixed_veg_curry.jpg','veg','lunch',25,'Medium'),
 
(6, 'Whole Wheat Roti',
 'Knead whole wheat flour with water into soft dough. Rest 10 minutes. Roll into thin circles and cook on a hot tawa till golden spots appear on both sides.',
 'wheat_roti.jpg','veg','lunch',15,'Easy'),
 
(7, 'Green Tea',
 'Brew 1 tsp green tea leaves or 1 tea bag in 180 ml hot water (not boiling) for 2–3 minutes. Add lemon and honey if desired.',
 'green_tea.jpg','veg','drink',3,'Easy'),
 
(8, 'Roasted Chana',
 'Dry roast 40g Bengal gram (chana) in a pan until crisp. Season with chaat masala and lemon juice.',
 'roasted_chana.jpg','veg','snack',8,'Easy'),
 
(9, 'Vegetable Soup',
 'Boil carrot, tomato, celery, onion and garlic in 2 cups water. Blend half, mix back in. Season with salt, pepper and herbs.',
 'vegetable_soup.jpg','veg','dinner',20,'Easy'),
 
(10, 'Cucumber Salad',
 'Slice 1 cucumber. Add diced tomato, red onion. Toss with salt, lemon juice, chaat masala and fresh coriander.',
 'cucumber_salad.jpg','veg','snack',5,'Easy'),
 
(11, 'Vegetable Poha',
 'Rinse 1 cup poha (flattened rice) and drain. Heat oil, add mustard seeds, curry leaves, green chilli, onion. Add peas and poha. Mix turmeric, salt, lemon juice. Cook 5 minutes.',
 'veg_poha.jpg','veg','breakfast',15,'Easy'),
 
(12, 'Orange',
 'Peel one medium orange and separate into segments. Eat fresh. Can squeeze for juice.',
 'orange.jpg','veg','snack',2,'Easy'),
 
(13, 'Brown Rice',
 'Rinse 1/2 cup brown rice. Add 1.5 cups water and a pinch of salt. Bring to boil, reduce heat, cover and cook 40–45 minutes.',
 'brown_rice.jpg','veg','lunch',45,'Easy'),
 
(14, 'Dal (Lentil Soup)',
 'Wash 1/2 cup toor or masoor dal. Pressure cook with water, turmeric for 3 whistles. Prepare tadka: heat ghee, add cumin, onion, tomato, chilli, coriander. Mix into dal.',
 'dal.jpg','veg','lunch',25,'Medium'),
 
(15, 'Spinach Sabzi',
 'Blanch 2 cups spinach and chop. Heat oil, add garlic, onion, cook 3 minutes. Add spinach, salt, garam masala. Cook 5 minutes.',
 'spinach_sabzi.jpg','veg','lunch',15,'Easy'),
 
(16, 'Sprouts Salad',
 'Mix 1 cup boiled sprouts with diced tomato, onion, cucumber, green chilli, lemon juice and chaat masala.',
 'sprouts_salad.jpg','veg','snack',5,'Easy'),
 
(17, 'Paneer Salad',
 'Cube 80g fresh paneer. Mix with sliced bell peppers, tomatoes, onion. Toss with olive oil, lemon, cumin powder and rock salt.',
 'paneer_salad.jpg','veg','lunch',8,'Easy'),
 
(18, 'Idli',
 'Soak rice and urad dal overnight. Grind to smooth batter. Ferment 8 hours. Pour into greased idli moulds and steam 12 minutes.',
 'idli.jpg','veg','breakfast',20,'Hard'),
 
(19, 'Coconut Chutney',
 'Blend 1/2 cup grated coconut with green chilli, ginger, salt and water. Prepare tadka with mustard seeds, curry leaves in oil and pour over.',
 'coconut_chutney.jpg','veg','breakfast',5,'Easy'),
 
(20, 'Apple',
 'Wash and slice one medium apple. Can be eaten with peanut butter for extra protein.',
 'apple.jpg','veg','snack',2,'Easy'),
 
(21, 'Cabbage Sabzi',
 'Shred 2 cups cabbage. Heat oil, add mustard seeds, curry leaves, green chilli. Add cabbage, turmeric, salt. Cook 8–10 minutes.',
 'cabbage_sabzi.jpg','veg','lunch',15,'Easy'),
 
(22, 'Roasted Peanuts',
 'Dry roast 30g raw peanuts in a pan on low heat until shells turn slightly brown, about 8 minutes. Add salt.',
 'roasted_peanuts.jpg','veg','snack',10,'Easy'),
 
(23, 'Tomato Salad',
 'Slice 2 medium tomatoes. Add sliced onion, cucumber. Season with salt, black pepper and lemon juice.',
 'tomato_salad.jpg','veg','snack',3,'Easy'),
 
(24, 'Vegetable Upma',
 'Dry roast 1/2 cup semolina. Heat oil, add mustard seeds, cashews, onion, vegetables (carrot, peas, beans). Add 1.5 cups water, bring to boil. Add semolina while stirring. Cook 5 minutes.',
 'veg_upma.jpg','veg','breakfast',20,'Medium'),
 
(25, 'Banana',
 'Eat one medium ripe banana. Excellent pre-workout energy source.',
 'banana.jpg','veg','snack',1,'Easy'),
 
(26, 'Rajma (Kidney Bean Curry)',
 'Soak 1/2 cup rajma overnight. Pressure cook till soft. Prepare onion-tomato-spice gravy. Mix rajma and simmer 15 minutes.',
 'rajma.jpg','veg','lunch',40,'Medium'),
 
(27, 'Buttermilk',
 'Blend 1/2 cup yogurt with 1 cup water, roasted cumin, salt and fresh mint. Froth and serve chilled.',
 'buttermilk.jpg','veg','drink',3,'Easy'),
 
(28, 'Roasted Makhana',
 'Heat 1 tsp ghee in a pan. Add fox nuts (makhana) and roast on low heat 8–10 minutes until crunchy. Add salt and chaat masala.',
 'roasted_makhana.jpg','veg','snack',10,'Easy'),
 
(29, 'Paneer Stir Fry',
 'Cut 100g paneer into cubes. In a pan, heat oil and add cumin. Add diced bell peppers, onion, paneer. Season with jeera powder, amchur, salt. Stir fry 8 minutes.',
 'paneer_stir_fry.jpg','veg','lunch',15,'Easy'),
 
(30, 'Vegetable Khichdi',
 'Wash 1/4 cup rice and 1/4 cup moong dal. Cook with diced vegetables (carrot, peas, potato), turmeric, salt in 2.5 cups water for 3 whistles. Finish with ghee and cumin tadka.',
 'veg_khichdi.jpg','veg','dinner',30,'Easy'),
 
-- New Veg meals 31–43
(31, 'Moong Dal Chilla',
 'Soak yellow moong dal 2 hours. Grind with ginger, green chilli to batter. Add chopped onion, tomato, coriander. Make thin pancakes on non-stick pan.',
 'moong_chilla.jpg','veg','breakfast',20,'Medium'),
 
(32, 'Dahi (Curd) Bowl',
 'Take 150ml fresh low-fat curd. Add a pinch of roasted cumin, rock salt, and fresh mint leaves. Eat as a side dish.',
 'dahi_bowl.jpg','veg','lunch',2,'Easy'),
 
(33, 'Palak Paneer',
 'Blanch 2 cups spinach and puree. Sauté onion, tomato, ginger-garlic paste. Add paneer cubes and spinach puree. Simmer with cream and spices 10 minutes.',
 'palak_paneer.jpg','veg','dinner',30,'Medium'),
 
(34, 'Masala Oats',
 'Heat oil, add mustard seeds, curry leaves, onion. Add rolled oats, vegetables, spices and 1.5 cups water. Cook until thick.',
 'masala_oats.jpg','veg','breakfast',12,'Easy'),
 
(35, 'Peanut Butter Toast',
 'Toast 2 slices whole wheat bread. Spread 1 tbsp natural peanut butter. Top with banana slices.',
 'pb_toast.jpg','veg','breakfast',5,'Easy'),
 
(36, 'Mixed Fruit Bowl',
 'Chop seasonal fruits: papaya, apple, grapes, banana, pomegranate seeds. Mix with a squeeze of lemon and honey.',
 'fruit_bowl.jpg','veg','breakfast',8,'Easy'),
 
(37, 'Chole (Chickpea Curry)',
 'Soak chickpeas overnight. Pressure cook till soft. Prepare spiced onion-tomato gravy. Add chickpeas and sour pomegranate powder. Simmer 15 minutes.',
 'chole.jpg','veg','lunch',45,'Medium'),
 
(38, 'Baingan Bharta',
 'Roast brinjal on flame until charred. Peel and mash. Saute onion, tomato, garlic. Add mashed brinjal and spices. Cook 10 minutes.',
 'baingan_bharta.jpg','veg','dinner',25,'Medium'),
 
(39, 'Greek Yogurt with Berries',
 'Take 150g thick Greek yogurt. Top with mixed berries (strawberry, blueberry), granola, and drizzle of honey.',
 'greek_yogurt.jpg','veg','breakfast',3,'Easy'),
 
(40, 'Sweet Potato Chaat',
 'Boil 1 medium sweet potato, cube it. Toss with yogurt, tamarind chutney, chaat masala, pomegranate seeds.',
 'sweet_potato.jpg','veg','snack',15,'Easy'),
 
(41, 'Methi Thepla',
 'Mix whole wheat flour with chopped fenugreek leaves, yogurt, spices and minimal oil. Knead soft dough. Roll thin and cook on tawa.',
 'thepla.jpg','veg','breakfast',20,'Medium'),
 
(42, 'Sambar',
 'Cook toor dal with tamarind water, tomatoes and vegetables (drumstick, carrot, eggplant). Prepare sambar powder based tempering. Simmer 15 minutes.',
 'sambar.jpg','veg','lunch',30,'Medium'),
 
(43, 'Coconut Water',
 'Serve fresh tender coconut water. Natural electrolytes and hydration.',
 'coconut_water.jpg','veg','drink',1,'Easy');
 
 INSERT INTO meals (meal_id, meal_name, recipe, image, category, meal_type, prep_time, difficulty) VALUES
(44, 'Vegetable Omelette',
 'Beat 2 eggs with salt, pepper, chilli flakes. Chop onion, capsicum, tomato. Heat butter, pour egg mixture, add vegetables, fold over.',
 'veg_omelette.jpg','nonveg','breakfast',10,'Easy'),
 
(45, 'Boiled Egg',
 'Place eggs in cold water. Bring to boil, cook 10 minutes for hard-boiled. Peel and season with salt and pepper.',
 'boiled_egg.jpg','nonveg','early_morning',12,'Easy'),
 
(46, 'Grilled Chicken Breast',
 'Marinate chicken breast with lemon juice, garlic, olive oil, herbs, salt and pepper for 30 minutes. Grill on high heat 6–8 minutes each side.',
 'grilled_chicken.jpg','nonveg','lunch',45,'Medium'),
 
(47, 'Chicken Curry',
 'Brown chicken pieces in oil. Add onion, ginger-garlic paste, tomatoes, red chilli, coriander, garam masala. Add water and simmer 25–30 minutes.',
 'chicken_curry.jpg','nonveg','dinner',40,'Medium'),
 
(48, 'Fish Curry',
 'Marinate fish in turmeric, lemon, salt. Make spiced onion-tomato-coconut gravy. Add fish and simmer gently 12 minutes.',
 'fish_curry.jpg','nonveg','dinner',30,'Medium'),
 
(49, 'Grilled Fish',
 'Marinate fish fillet with lemon juice, garlic, herbs, olive oil. Grill 8 minutes per side. Serve with salad.',
 'grilled_fish.jpg','nonveg','lunch',35,'Easy'),
 
(50, 'Egg Sandwich',
 'Make vegetable omelette. Place between 2 slices whole wheat bread with lettuce, tomato, mustard sauce.',
 'egg_sandwich.jpg','nonveg','breakfast',12,'Easy'),
 
(51, 'Chicken Salad',
 'Grill chicken breast and slice. Mix with romaine lettuce, cherry tomatoes, cucumber, low-fat dressing and croutons.',
 'chicken_salad.jpg','nonveg','lunch',20,'Easy'),
 
(52, 'Chicken Soup',
 'Boil chicken with whole spices, vegetables (carrot, celery, onion) for 30 minutes. Strain, shred chicken, return to clear broth. Season and garnish.',
 'chicken_soup.jpg','nonveg','dinner',35,'Easy'),
 
(53, 'Scrambled Eggs',
 'Beat 2–3 eggs with milk, salt and pepper. Cook on low heat in butter, stirring constantly until just set. Serve on toast.',
 'scrambled_eggs.jpg','nonveg','breakfast',8,'Easy'),
 
-- New non-veg 54–70
(54, 'Egg Bhurji',
 'Heat oil, add onion, tomato, green chilli, ginger. Add beaten eggs and scramble continuously with spices till cooked. Garnish with coriander.',
 'egg_bhurji.jpg','nonveg','breakfast',10,'Easy'),
 
(55, 'Chicken Tikka',
 'Marinate chicken pieces in yogurt, lemon, ginger-garlic paste and tandoori masala for 1 hour. Skewer and bake or grill at 220°C for 20–25 minutes.',
 'chicken_tikka.jpg','nonveg','lunch',90,'Medium'),
 
(56, 'Egg Curry',
 'Hard-boil eggs and halve. Prepare spiced onion-tomato gravy. Add eggs and simmer 10 minutes.',
 'egg_curry.jpg','nonveg','dinner',25,'Medium'),
 
(57, 'Grilled Prawns',
 'Clean prawns. Marinate with garlic butter, lemon juice, paprika, salt. Grill on high heat 3–4 minutes each side.',
 'grilled_prawns.jpg','nonveg','dinner',25,'Medium'),
 
(58, 'Tuna Salad',
 'Mix canned tuna with diced cucumber, onion, tomato, Greek yogurt, mustard, lemon juice and black pepper.',
 'tuna_salad.jpg','nonveg','lunch',5,'Easy'),
 
(59, 'Chicken Stir Fry',
 'Slice chicken thin. Stir fry in hot oil with bell peppers, onion, garlic, soy sauce, ginger. Cook 8–10 minutes.',
 'chicken_stirfry.jpg','nonveg','dinner',20,'Medium'),
 
(60, 'Boiled Chicken Salad',
 'Shred boiled chicken breast. Mix with baby spinach, tomatoes, olives and lemon-olive oil dressing.',
 'boiled_chicken_salad.jpg','nonveg','lunch',20,'Easy'),
 
(61, 'Egg White Omelette',
 'Separate 3 egg whites. Beat with salt, pepper. Add spinach, mushroom. Cook in non-stick pan 5 minutes.',
 'egg_white_omelette.jpg','nonveg','breakfast',8,'Easy'),
 
(62, 'Mutton Soup',
 'Boil lean mutton pieces with onion, ginger, garlic, whole spices. Strain clear broth. Season with pepper and herbs.',
 'mutton_soup.jpg','nonveg','dinner',45,'Hard'),
 
(63, 'Salmon Steak',
 'Season salmon fillet with garlic, dill, lemon, olive oil. Pan-sear on medium heat 4 minutes each side.',
 'salmon.jpg','nonveg','dinner',15,'Easy'),
 
(64, 'Chicken Wrap',
 'Fill whole wheat tortilla with grilled chicken strips, lettuce, tomato, sliced avocado and hung curd dressing.',
 'chicken_wrap.jpg','nonveg','lunch',15,'Easy'),
 
(65, 'Egg Salad',
 'Chop boiled eggs. Mix with diced celery, mustard, Greek yogurt, lemon juice, salt and pepper.',
 'egg_salad.jpg','nonveg','lunch',10,'Easy'),
 
(66, 'Baked Chicken',
 'Marinate whole chicken pieces in yogurt, garlic, lemon and spices overnight. Bake at 200°C for 35–40 minutes.',
 'baked_chicken.jpg','nonveg','dinner',50,'Medium'),
 
(67, 'Prawn Masala',
 'Clean prawns. Make spiced onion-tomato-coconut masala. Add prawns and cook 8 minutes.',
 'prawn_masala.jpg','nonveg','dinner',30,'Medium'),
 
(68, 'Turkey Sandwich',
 'Layer sliced turkey, lettuce, tomato, cucumber and mustard between whole wheat bread slices.',
 'turkey_sandwich.jpg','nonveg','breakfast',5,'Easy'),
 
(69, 'Chicken Protein Bowl',
 'Grilled chicken breast over a base of brown rice or quinoa, topped with roasted vegetables and avocado. Drizzle with lemon-tahini dressing.',
 'protein_bowl.jpg','nonveg','lunch',30,'Medium'),
 
(70, 'Fish Tacos',
 'Season white fish fillet and pan-fry 5 minutes. Serve in corn tortillas with cabbage slaw, salsa, lime wedges.',
 'fish_tacos.jpg','nonveg','dinner',20,'Medium');
 
 CREATE TABLE nutrition (
    nutrition_id INT AUTO_INCREMENT PRIMARY KEY,
    meal_id      INT NOT NULL,
    calories     INT DEFAULT 0,
    protein      FLOAT DEFAULT 0,
    carbs        FLOAT DEFAULT 0,
    fat          FLOAT DEFAULT 0,
    fiber        FLOAT DEFAULT 0,
    sugar        FLOAT DEFAULT 0,
    sodium       FLOAT DEFAULT 0  COMMENT 'mg',
    FOREIGN KEY (meal_id) REFERENCES meals(meal_id) ON DELETE CASCADE
);

INSERT INTO nutrition (meal_id, calories, protein, carbs, fat, fiber, sugar, sodium) VALUES
-- Veg meals 1-30
(1,  10,  0.0,  2.0,  0.0,  0.0,  1.0,   5),
(2,  35,  1.2,  1.0,  3.0,  0.5,  0.0,   2),
(3, 250,  8.0, 45.0,  5.0,  5.0, 12.0,  80),
(4, 120,  1.5, 30.0,  0.2,  2.5, 22.0,  15),
(5, 180,  5.0, 20.0,  6.0,  4.5,  6.0, 320),
(6, 100,  3.0, 20.0,  1.0,  2.0,  0.0, 180),
(7,   5,  0.0,  0.5,  0.0,  0.0,  0.0,   0),
(8, 150,  8.0, 18.0,  4.0,  5.0,  1.0, 120),
(9,  90,  3.0, 15.0,  2.0,  3.5,  5.0, 380),
(10, 40,  1.0,  8.0,  0.2,  1.5,  3.0, 220),
(11,220,  6.0, 40.0,  4.0,  2.0,  2.0, 340),
(12, 80,  1.2, 18.0,  0.2,  2.5, 14.0,   2),
(13,215,  5.0, 45.0,  2.0,  3.5,  0.0,  10),
(14,180, 12.0, 30.0,  3.0,  8.0,  4.0, 260),
(15, 90,  4.0, 10.0,  2.0,  3.0,  2.0, 180),
(16,160,  9.0, 20.0,  3.0,  6.0,  3.0,  90),
(17,260, 18.0,  8.0, 18.0,  0.5,  3.0, 210),
(18,150,  5.0, 30.0,  1.0,  0.5,  0.0, 320),
(19, 80,  2.0,  4.0,  6.0,  2.0,  1.0, 140),
(20, 95,  0.5, 25.0,  0.3,  4.5, 19.0,   2),
(21, 80,  3.0, 10.0,  2.0,  3.5,  4.0, 190),
(22,170,  7.0,  6.0, 14.0,  2.5,  1.0,  80),
(23, 40,  1.0,  8.0,  0.2,  1.5,  5.0, 210),
(24,230,  6.0, 40.0,  5.0,  2.5,  3.0, 310),
(25,105,  1.3, 27.0,  0.4,  3.0, 14.0,   1),
(26,250, 15.0, 40.0,  3.0, 12.0,  4.0, 280),
(27, 60,  3.0,  5.0,  3.0,  0.0,  4.0, 230),
(28,110,  4.0, 12.0,  6.0,  0.5,  0.0,  80),
(29,280, 18.0,  6.0, 20.0,  1.0,  4.0, 290),
(30,300, 12.0, 50.0,  6.0,  4.0,  3.0, 340),
-- New veg 31-43
(31,180, 12.0, 22.0,  4.0,  3.0,  3.0, 200),
(32, 98,  7.0,  8.0,  4.0,  0.0,  6.0, 140),
(33,310, 20.0, 14.0, 20.0,  2.0,  5.0, 320),
(34,220,  7.0, 40.0,  4.0,  4.0,  3.0, 250),
(35,320, 12.0, 42.0, 12.0,  4.0, 10.0, 220),
(36,150,  2.0, 36.0,  1.0,  4.0, 28.0,  15),
(37,280, 14.0, 45.0,  5.0, 12.0,  8.0, 320),
(38,120,  4.0, 15.0,  5.0,  5.0,  6.0, 240),
(39,160, 14.0, 14.0,  5.0,  1.0, 10.0,  60),
(40,180,  4.0, 38.0,  2.0,  4.0, 10.0, 290),
(41,200,  6.0, 32.0,  5.0,  4.0,  2.0, 280),
(42,160, 10.0, 24.0,  3.0,  6.0,  5.0, 380),
(43, 45,  0.5, 11.0,  0.2,  0.5,  8.0,  25),
-- Non-veg 44-70
(44,180, 12.0,  5.0, 12.0,  0.5,  2.0, 280),
(45, 70,  6.0,  1.0,  5.0,  0.0,  0.0,  60),
(46,300, 35.0,  0.0, 10.0,  0.0,  0.0, 340),
(47,350, 30.0,  8.0, 18.0,  1.0,  5.0, 520),
(48,280, 28.0,  6.0, 15.0,  1.5,  4.0, 480),
(49,250, 30.0,  0.0, 12.0,  0.0,  0.0, 310),
(50,260, 16.0, 30.0, 10.0,  2.0,  3.0, 420),
(51,220, 28.0,  5.0,  8.0,  2.0,  3.0, 380),
(52,150, 18.0,  5.0,  6.0,  0.5,  2.0, 480),
(53,200, 14.0,  3.0, 15.0,  0.0,  1.0, 310),
(54,210, 14.0,  6.0, 14.0,  0.5,  3.0, 340),
(55,280, 32.0,  6.0, 12.0,  0.5,  3.0, 520),
(56,240, 16.0,  8.0, 16.0,  1.0,  4.0, 380),
(57,190, 22.0,  2.0,  9.0,  0.0,  1.0, 420),
(58,180, 26.0,  4.0,  6.0,  1.0,  2.0, 360),
(59,260, 30.0,  8.0, 12.0,  2.0,  4.0, 480),
(60,190, 28.0,  6.0,  6.0,  2.0,  3.0, 280),
(61, 90, 18.0,  2.0,  1.0,  0.5,  1.0, 180),
(62,200, 22.0,  5.0, 10.0,  0.5,  2.0, 420),
(63,350, 34.0,  0.0, 22.0,  0.0,  0.0, 280),
(64,320, 28.0, 30.0,  8.0,  4.0,  3.0, 480),
(65,200, 14.0,  4.0, 14.0,  0.5,  2.0, 320),
(66,380, 42.0,  4.0, 18.0,  0.5,  2.0, 520),
(67,240, 24.0,  8.0, 12.0,  1.5,  4.0, 480),
(68,280, 22.0, 30.0,  8.0,  2.0,  3.0, 520),
(69,420, 45.0, 38.0, 10.0,  5.0,  4.0, 480),
(70,310, 28.0, 28.0, 10.0,  3.0,  3.0, 420);

CREATE TABLE recipes (
    recipe_id    INT AUTO_INCREMENT PRIMARY KEY,
    meal_id      INT NOT NULL,
    recipe_name  VARCHAR(150),
    instructions TEXT,
    image_url    VARCHAR(255),
    cuisine      VARCHAR(80),
    tags         VARCHAR(255) COMMENT 'comma-separated e.g. high-protein,veg,quick',
    FOREIGN KEY (meal_id) REFERENCES meals(meal_id) ON DELETE CASCADE
);

INSERT INTO recipes (meal_id, recipe_name, instructions, image_url, cuisine, tags)
SELECT meal_id, meal_name, recipe, image,
       CASE WHEN meal_id IN (63,58,70) THEN 'Continental'
            WHEN meal_id IN (55,46,47,66) THEN 'Indian/Grilled'
            WHEN meal_id IN (1,2,7,27,43) THEN 'Indian'
            ELSE 'Indian' END,
       CASE WHEN category='nonveg' AND meal_id BETWEEN 44 AND 70 THEN 'non-veg,high-protein'
            WHEN meal_id IN (3,34,24) THEN 'breakfast,quick'
            WHEN meal_id IN (16,10,17,23,51,58,60,65) THEN 'salad,low-cal'
            WHEN meal_id IN (37,26,14) THEN 'high-protein,lunch'
            ELSE 'healthy' END
FROM meals;

CREATE TABLE weekly_diet (
    diet_id      INT AUTO_INCREMENT PRIMARY KEY,
    plan_id      INT NOT NULL,
    day_of_week  VARCHAR(12) NOT NULL,
    meal_time    VARCHAR(30) NOT NULL,
    meal_id      INT NOT NULL,
    goal         VARCHAR(50),
    diet_type    VARCHAR(20),
    FOREIGN KEY (plan_id)  REFERENCES diet_plan(plan_id),
    FOREIGN KEY (meal_id)  REFERENCES meals(meal_id)
);

INSERT INTO weekly_diet (plan_id,day_of_week,meal_time,meal_id,goal,diet_type) VALUES
(1,'Monday','Early Morning',1,'Weight Loss','Veg'),
(1,'Monday','Early Morning',2,'Weight Loss','Veg'),
(1,'Monday','Breakfast',3,'Weight Loss','Veg'),
(1,'Monday','Mid Snack',10,'Weight Loss','Veg'),
(1,'Monday','Lunch',6,'Weight Loss','Veg'),
(1,'Monday','Lunch',5,'Weight Loss','Veg'),
(1,'Monday','Evening Snack',7,'Weight Loss','Veg'),
(1,'Monday','Evening Snack',8,'Weight Loss','Veg'),
(1,'Monday','Dinner',9,'Weight Loss','Veg'),
(1,'Tuesday','Early Morning',1,'Weight Loss','Veg'),
(1,'Tuesday','Breakfast',11,'Weight Loss','Veg'),
(1,'Tuesday','Mid Snack',12,'Weight Loss','Veg'),
(1,'Tuesday','Lunch',13,'Weight Loss','Veg'),
(1,'Tuesday','Lunch',14,'Weight Loss','Veg'),
(1,'Tuesday','Lunch',15,'Weight Loss','Veg'),
(1,'Tuesday','Evening Snack',16,'Weight Loss','Veg'),
(1,'Tuesday','Dinner',9,'Weight Loss','Veg'),
(1,'Wednesday','Early Morning',7,'Weight Loss','Veg'),
(1,'Wednesday','Breakfast',18,'Weight Loss','Veg'),
(1,'Wednesday','Breakfast',19,'Weight Loss','Veg'),
(1,'Wednesday','Mid Snack',20,'Weight Loss','Veg'),
(1,'Wednesday','Lunch',6,'Weight Loss','Veg'),
(1,'Wednesday','Lunch',14,'Weight Loss','Veg'),
(1,'Wednesday','Lunch',21,'Weight Loss','Veg'),
(1,'Wednesday','Evening Snack',7,'Weight Loss','Veg'),
(1,'Wednesday','Evening Snack',8,'Weight Loss','Veg'),
(1,'Wednesday','Dinner',30,'Weight Loss','Veg'),
(1,'Thursday','Early Morning',1,'Weight Loss','Veg'),
(1,'Thursday','Breakfast',34,'Weight Loss','Veg'),
(1,'Thursday','Mid Snack',4,'Weight Loss','Veg'),
(1,'Thursday','Lunch',6,'Weight Loss','Veg'),
(1,'Thursday','Lunch',5,'Weight Loss','Veg'),
(1,'Thursday','Lunch',15,'Weight Loss','Veg'),
(1,'Thursday','Evening Snack',28,'Weight Loss','Veg'),
(1,'Thursday','Dinner',9,'Weight Loss','Veg'),
(1,'Thursday','Dinner',10,'Weight Loss','Veg'),
(1,'Friday','Early Morning',7,'Weight Loss','Veg'),
(1,'Friday','Breakfast',31,'Weight Loss','Veg'),
(1,'Friday','Mid Snack',12,'Weight Loss','Veg'),
(1,'Friday','Lunch',6,'Weight Loss','Veg'),
(1,'Friday','Lunch',14,'Weight Loss','Veg'),
(1,'Friday','Evening Snack',16,'Weight Loss','Veg'),
(1,'Friday','Dinner',30,'Weight Loss','Veg'),
(1,'Saturday','Early Morning',1,'Weight Loss','Veg'),
(1,'Saturday','Breakfast',39,'Weight Loss','Veg'),
(1,'Saturday','Mid Snack',20,'Weight Loss','Veg'),
(1,'Saturday','Lunch',13,'Weight Loss','Veg'),
(1,'Saturday','Lunch',38,'Weight Loss','Veg'),
(1,'Saturday','Evening Snack',27,'Weight Loss','Veg'),
(1,'Saturday','Dinner',9,'Weight Loss','Veg'),
(1,'Sunday','Early Morning',7,'Weight Loss','Veg'),
(1,'Sunday','Breakfast',4,'Weight Loss','Veg'),
(1,'Sunday','Mid Snack',8,'Weight Loss','Veg'),
(1,'Sunday','Lunch',37,'Weight Loss','Veg'),
(1,'Sunday','Lunch',6,'Weight Loss','Veg'),
(1,'Sunday','Evening Snack',10,'Weight Loss','Veg'),
(1,'Sunday','Dinner',14,'Weight Loss','Veg'),
(1,'Sunday','Dinner',15,'Weight Loss','Veg');

INSERT INTO weekly_diet (plan_id,day_of_week,meal_time,meal_id,goal,diet_type) VALUES
(2,'Monday','Early Morning',1,'Weight Loss','Non Veg'),
(2,'Monday','Early Morning',45,'Weight Loss','Non Veg'),
(2,'Monday','Breakfast',44,'Weight Loss','Non Veg'),
(2,'Monday','Mid Snack',12,'Weight Loss','Non Veg'),
(2,'Monday','Lunch',49,'Weight Loss','Non Veg'),
(2,'Monday','Lunch',10,'Weight Loss','Non Veg'),
(2,'Monday','Evening Snack',7,'Weight Loss','Non Veg'),
(2,'Monday','Dinner',52,'Weight Loss','Non Veg'),
(2,'Tuesday','Early Morning',1,'Weight Loss','Non Veg'),
(2,'Tuesday','Breakfast',50,'Weight Loss','Non Veg'),
(2,'Tuesday','Mid Snack',20,'Weight Loss','Non Veg'),
(2,'Tuesday','Lunch',46,'Weight Loss','Non Veg'),
(2,'Tuesday','Lunch',10,'Weight Loss','Non Veg'),
(2,'Tuesday','Evening Snack',8,'Weight Loss','Non Veg'),
(2,'Tuesday','Dinner',9,'Weight Loss','Non Veg'),
(2,'Wednesday','Early Morning',7,'Weight Loss','Non Veg'),
(2,'Wednesday','Breakfast',53,'Weight Loss','Non Veg'),
(2,'Wednesday','Mid Snack',58,'Weight Loss','Non Veg'),
(2,'Wednesday','Lunch',51,'Weight Loss','Non Veg'),
(2,'Wednesday','Lunch',13,'Weight Loss','Non Veg'),
(2,'Wednesday','Evening Snack',45,'Weight Loss','Non Veg'),
(2,'Wednesday','Dinner',48,'Weight Loss','Non Veg'),
(2,'Thursday','Early Morning',1,'Weight Loss','Non Veg'),
(2,'Thursday','Breakfast',61,'Weight Loss','Non Veg'),
(2,'Thursday','Mid Snack',12,'Weight Loss','Non Veg'),
(2,'Thursday','Lunch',58,'Weight Loss','Non Veg'),
(2,'Thursday','Lunch',6,'Weight Loss','Non Veg'),
(2,'Thursday','Evening Snack',16,'Weight Loss','Non Veg'),
(2,'Thursday','Dinner',52,'Weight Loss','Non Veg'),
(2,'Friday','Early Morning',7,'Weight Loss','Non Veg'),
(2,'Friday','Breakfast',44,'Weight Loss','Non Veg'),
(2,'Friday','Mid Snack',20,'Weight Loss','Non Veg'),
(2,'Friday','Lunch',49,'Weight Loss','Non Veg'),
(2,'Friday','Lunch',15,'Weight Loss','Non Veg'),
(2,'Friday','Evening Snack',8,'Weight Loss','Non Veg'),
(2,'Friday','Dinner',9,'Weight Loss','Non Veg'),
(2,'Saturday','Early Morning',1,'Weight Loss','Non Veg'),
(2,'Saturday','Breakfast',50,'Weight Loss','Non Veg'),
(2,'Saturday','Mid Snack',43,'Weight Loss','Non Veg'),
(2,'Saturday','Lunch',46,'Weight Loss','Non Veg'),
(2,'Saturday','Lunch',13,'Weight Loss','Non Veg'),
(2,'Saturday','Evening Snack',27,'Weight Loss','Non Veg'),
(2,'Saturday','Dinner',48,'Weight Loss','Non Veg'),
(2,'Sunday','Early Morning',7,'Weight Loss','Non Veg'),
(2,'Sunday','Breakfast',53,'Weight Loss','Non Veg'),
(2,'Sunday','Mid Snack',10,'Weight Loss','Non Veg'),
(2,'Sunday','Lunch',55,'Weight Loss','Non Veg'),
(2,'Sunday','Lunch',6,'Weight Loss','Non Veg'),
(2,'Sunday','Evening Snack',45,'Weight Loss','Non Veg'),
(2,'Sunday','Dinner',56,'Weight Loss','Non Veg');

INSERT INTO weekly_diet (plan_id,day_of_week,meal_time,meal_id,goal,diet_type) VALUES
(3,'Monday','Early Morning',2,'Weight Gain','Veg'),
(3,'Monday','Breakfast',3,'Weight Gain','Veg'),
(3,'Monday','Breakfast',35,'Weight Gain','Veg'),
(3,'Monday','Mid Snack',25,'Weight Gain','Veg'),
(3,'Monday','Mid Snack',22,'Weight Gain','Veg'),
(3,'Monday','Lunch',13,'Weight Gain','Veg'),
(3,'Monday','Lunch',26,'Weight Gain','Veg'),
(3,'Monday','Lunch',6,'Weight Gain','Veg'),
(3,'Monday','Evening Snack',28,'Weight Gain','Veg'),
(3,'Monday','Evening Snack',25,'Weight Gain','Veg'),
(3,'Monday','Dinner',33,'Weight Gain','Veg'),
(3,'Monday','Dinner',6,'Weight Gain','Veg'),
(3,'Tuesday','Early Morning',2,'Weight Gain','Veg'),
(3,'Tuesday','Breakfast',24,'Weight Gain','Veg'),
(3,'Tuesday','Breakfast',32,'Weight Gain','Veg'),
(3,'Tuesday','Mid Snack',36,'Weight Gain','Veg'),
(3,'Tuesday','Lunch',13,'Weight Gain','Veg'),
(3,'Tuesday','Lunch',29,'Weight Gain','Veg'),
(3,'Tuesday','Lunch',6,'Weight Gain','Veg'),
(3,'Tuesday','Evening Snack',25,'Weight Gain','Veg'),
(3,'Tuesday','Dinner',30,'Weight Gain','Veg'),
(3,'Wednesday','Early Morning',2,'Weight Gain','Veg'),
(3,'Wednesday','Breakfast',11,'Weight Gain','Veg'),
(3,'Wednesday','Breakfast',32,'Weight Gain','Veg'),
(3,'Wednesday','Mid Snack',25,'Weight Gain','Veg'),
(3,'Wednesday','Lunch',13,'Weight Gain','Veg'),
(3,'Wednesday','Lunch',37,'Weight Gain','Veg'),
(3,'Wednesday','Lunch',6,'Weight Gain','Veg'),
(3,'Wednesday','Evening Snack',22,'Weight Gain','Veg'),
(3,'Wednesday','Dinner',33,'Weight Gain','Veg'),
(3,'Thursday','Early Morning',2,'Weight Gain','Veg'),
(3,'Thursday','Breakfast',39,'Weight Gain','Veg'),
(3,'Thursday','Breakfast',3,'Weight Gain','Veg'),
(3,'Thursday','Mid Snack',40,'Weight Gain','Veg'),
(3,'Thursday','Mid Snack',25,'Weight Gain','Veg'),
(3,'Thursday','Lunch',13,'Weight Gain','Veg'),
(3,'Thursday','Lunch',29,'Weight Gain','Veg'),
(3,'Thursday','Evening Snack',28,'Weight Gain','Veg'),
(3,'Thursday','Dinner',26,'Weight Gain','Veg'),
(3,'Thursday','Dinner',6,'Weight Gain','Veg'),
(3,'Friday','Early Morning',43,'Weight Gain','Veg'),
(3,'Friday','Breakfast',41,'Weight Gain','Veg'),
(3,'Friday','Mid Snack',36,'Weight Gain','Veg'),
(3,'Friday','Lunch',13,'Weight Gain','Veg'),
(3,'Friday','Lunch',5,'Weight Gain','Veg'),
(3,'Friday','Lunch',6,'Weight Gain','Veg'),
(3,'Friday','Evening Snack',22,'Weight Gain','Veg'),
(3,'Friday','Dinner',30,'Weight Gain','Veg'),
(3,'Saturday','Early Morning',2,'Weight Gain','Veg'),
(3,'Saturday','Breakfast',35,'Weight Gain','Veg'),
(3,'Saturday','Mid Snack',25,'Weight Gain','Veg'),
(3,'Saturday','Lunch',13,'Weight Gain','Veg'),
(3,'Saturday','Lunch',29,'Weight Gain','Veg'),
(3,'Saturday','Lunch',6,'Weight Gain','Veg'),
(3,'Saturday','Evening Snack',28,'Weight Gain','Veg'),
(3,'Saturday','Dinner',33,'Weight Gain','Veg'),
(3,'Sunday','Early Morning',2,'Weight Gain','Veg'),
(3,'Sunday','Breakfast',31,'Weight Gain','Veg'),
(3,'Sunday','Mid Snack',25,'Weight Gain','Veg'),
(3,'Sunday','Lunch',37,'Weight Gain','Veg'),
(3,'Sunday','Lunch',6,'Weight Gain','Veg'),
(3,'Sunday','Evening Snack',32,'Weight Gain','Veg'),
(3,'Sunday','Dinner',26,'Weight Gain','Veg'),
(3,'Sunday','Dinner',6,'Weight Gain','Veg');

INSERT INTO weekly_diet (plan_id,day_of_week,meal_time,meal_id,goal,diet_type) VALUES
(4,'Monday','Early Morning',2,'Weight Gain','Non Veg'),
(4,'Monday','Breakfast',44,'Weight Gain','Non Veg'),
(4,'Monday','Breakfast',35,'Weight Gain','Non Veg'),
(4,'Monday','Mid Snack',25,'Weight Gain','Non Veg'),
(4,'Monday','Mid Snack',22,'Weight Gain','Non Veg'),
(4,'Monday','Lunch',13,'Weight Gain','Non Veg'),
(4,'Monday','Lunch',47,'Weight Gain','Non Veg'),
(4,'Monday','Lunch',6,'Weight Gain','Non Veg'),
(4,'Monday','Evening Snack',45,'Weight Gain','Non Veg'),
(4,'Monday','Dinner',48,'Weight Gain','Non Veg'),
(4,'Monday','Dinner',13,'Weight Gain','Non Veg'),
(4,'Tuesday','Early Morning',2,'Weight Gain','Non Veg'),
(4,'Tuesday','Breakfast',53,'Weight Gain','Non Veg'),
(4,'Tuesday','Breakfast',35,'Weight Gain','Non Veg'),
(4,'Tuesday','Mid Snack',25,'Weight Gain','Non Veg'),
(4,'Tuesday','Lunch',13,'Weight Gain','Non Veg'),
(4,'Tuesday','Lunch',46,'Weight Gain','Non Veg'),
(4,'Tuesday','Lunch',6,'Weight Gain','Non Veg'),
(4,'Tuesday','Evening Snack',22,'Weight Gain','Non Veg'),
(4,'Tuesday','Dinner',47,'Weight Gain','Non Veg'),
(4,'Wednesday','Early Morning',2,'Weight Gain','Non Veg'),
(4,'Wednesday','Breakfast',50,'Weight Gain','Non Veg'),
(4,'Wednesday','Mid Snack',36,'Weight Gain','Non Veg'),
(4,'Wednesday','Lunch',13,'Weight Gain','Non Veg'),
(4,'Wednesday','Lunch',66,'Weight Gain','Non Veg'),
(4,'Wednesday','Lunch',6,'Weight Gain','Non Veg'),
(4,'Wednesday','Evening Snack',45,'Weight Gain','Non Veg'),
(4,'Wednesday','Dinner',47,'Weight Gain','Non Veg'),
(4,'Thursday','Early Morning',2,'Weight Gain','Non Veg'),
(4,'Thursday','Breakfast',54,'Weight Gain','Non Veg'),
(4,'Thursday','Breakfast',6,'Weight Gain','Non Veg'),
(4,'Thursday','Mid Snack',25,'Weight Gain','Non Veg'),
(4,'Thursday','Lunch',13,'Weight Gain','Non Veg'),
(4,'Thursday','Lunch',47,'Weight Gain','Non Veg'),
(4,'Thursday','Evening Snack',22,'Weight Gain','Non Veg'),
(4,'Thursday','Dinner',48,'Weight Gain','Non Veg'),
(4,'Friday','Early Morning',43,'Weight Gain','Non Veg'),
(4,'Friday','Breakfast',44,'Weight Gain','Non Veg'),
(4,'Friday','Mid Snack',25,'Weight Gain','Non Veg'),
(4,'Friday','Lunch',13,'Weight Gain','Non Veg'),
(4,'Friday','Lunch',46,'Weight Gain','Non Veg'),
(4,'Friday','Evening Snack',45,'Weight Gain','Non Veg'),
(4,'Friday','Dinner',59,'Weight Gain','Non Veg'),
(4,'Saturday','Early Morning',2,'Weight Gain','Non Veg'),
(4,'Saturday','Breakfast',50,'Weight Gain','Non Veg'),
(4,'Saturday','Mid Snack',36,'Weight Gain','Non Veg'),
(4,'Saturday','Lunch',69,'Weight Gain','Non Veg'),
(4,'Saturday','Evening Snack',22,'Weight Gain','Non Veg'),
(4,'Saturday','Dinner',66,'Weight Gain','Non Veg'),
(4,'Sunday','Early Morning',2,'Weight Gain','Non Veg'),
(4,'Sunday','Breakfast',53,'Weight Gain','Non Veg'),
(4,'Sunday','Mid Snack',25,'Weight Gain','Non Veg'),
(4,'Sunday','Lunch',13,'Weight Gain','Non Veg'),
(4,'Sunday','Lunch',47,'Weight Gain','Non Veg'),
(4,'Sunday','Evening Snack',45,'Weight Gain','Non Veg'),
(4,'Sunday','Dinner',48,'Weight Gain','Non Veg');
 
 INSERT INTO weekly_diet (plan_id,day_of_week,meal_time,meal_id,goal,diet_type) VALUES
(5,'Monday','Early Morning',2,'Muscle Gain','Veg'),
(5,'Monday','Breakfast',31,'Muscle Gain','Veg'),
(5,'Monday','Breakfast',6,'Muscle Gain','Veg'),
(5,'Monday','Mid Snack',25,'Muscle Gain','Veg'),
(5,'Monday','Mid Snack',22,'Muscle Gain','Veg'),
(5,'Monday','Lunch',13,'Muscle Gain','Veg'),
(5,'Monday','Lunch',29,'Muscle Gain','Veg'),
(5,'Monday','Lunch',6,'Muscle Gain','Veg'),
(5,'Monday','Evening Snack',22,'Muscle Gain','Veg'),
(5,'Monday','Dinner',33,'Muscle Gain','Veg'),
(5,'Monday','Dinner',6,'Muscle Gain','Veg'),
(5,'Tuesday','Early Morning',2,'Muscle Gain','Veg'),
(5,'Tuesday','Breakfast',39,'Muscle Gain','Veg'),
(5,'Tuesday','Breakfast',3,'Muscle Gain','Veg'),
(5,'Tuesday','Mid Snack',25,'Muscle Gain','Veg'),
(5,'Tuesday','Lunch',13,'Muscle Gain','Veg'),
(5,'Tuesday','Lunch',37,'Muscle Gain','Veg'),
(5,'Tuesday','Lunch',6,'Muscle Gain','Veg'),
(5,'Tuesday','Evening Snack',28,'Muscle Gain','Veg'),
(5,'Tuesday','Dinner',29,'Muscle Gain','Veg'),
(5,'Tuesday','Dinner',6,'Muscle Gain','Veg'),
(5,'Wednesday','Early Morning',2,'Muscle Gain','Veg'),
(5,'Wednesday','Breakfast',41,'Muscle Gain','Veg'),
(5,'Wednesday','Mid Snack',36,'Muscle Gain','Veg'),
(5,'Wednesday','Mid Snack',22,'Muscle Gain','Veg'),
(5,'Wednesday','Lunch',13,'Muscle Gain','Veg'),
(5,'Wednesday','Lunch',26,'Muscle Gain','Veg'),
(5,'Wednesday','Lunch',6,'Muscle Gain','Veg'),
(5,'Wednesday','Evening Snack',32,'Muscle Gain','Veg'),
(5,'Wednesday','Dinner',33,'Muscle Gain','Veg'),
(5,'Thursday','Early Morning',2,'Muscle Gain','Veg'),
(5,'Thursday','Breakfast',3,'Muscle Gain','Veg'),
(5,'Thursday','Mid Snack',40,'Muscle Gain','Veg'),
(5,'Thursday','Mid Snack',22,'Muscle Gain','Veg'),
(5,'Thursday','Lunch',13,'Muscle Gain','Veg'),
(5,'Thursday','Lunch',29,'Muscle Gain','Veg'),
(5,'Thursday','Lunch',5,'Muscle Gain','Veg'),
(5,'Thursday','Evening Snack',25,'Muscle Gain','Veg'),
(5,'Thursday','Dinner',30,'Muscle Gain','Veg'),
(5,'Friday','Early Morning',2,'Muscle Gain','Veg'),
(5,'Friday','Breakfast',35,'Muscle Gain','Veg'),
(5,'Friday','Mid Snack',25,'Muscle Gain','Veg'),
(5,'Friday','Lunch',13,'Muscle Gain','Veg'),
(5,'Friday','Lunch',26,'Muscle Gain','Veg'),
(5,'Friday','Evening Snack',22,'Muscle Gain','Veg'),
(5,'Friday','Dinner',33,'Muscle Gain','Veg'),
(5,'Friday','Dinner',6,'Muscle Gain','Veg'),
(5,'Saturday','Early Morning',43,'Muscle Gain','Veg'),
(5,'Saturday','Breakfast',31,'Muscle Gain','Veg'),
(5,'Saturday','Breakfast',32,'Muscle Gain','Veg'),
(5,'Saturday','Mid Snack',25,'Muscle Gain','Veg'),
(5,'Saturday','Lunch',13,'Muscle Gain','Veg'),
(5,'Saturday','Lunch',29,'Muscle Gain','Veg'),
(5,'Saturday','Evening Snack',28,'Muscle Gain','Veg'),
(5,'Saturday','Dinner',37,'Muscle Gain','Veg'),
(5,'Saturday','Dinner',6,'Muscle Gain','Veg'),
(5,'Sunday','Early Morning',2,'Muscle Gain','Veg'),
(5,'Sunday','Breakfast',39,'Muscle Gain','Veg'),
(5,'Sunday','Mid Snack',36,'Muscle Gain','Veg'),
(5,'Sunday','Lunch',13,'Muscle Gain','Veg'),
(5,'Sunday','Lunch',29,'Muscle Gain','Veg'),
(5,'Sunday','Lunch',6,'Muscle Gain','Veg'),
(5,'Sunday','Evening Snack',22,'Muscle Gain','Veg'),
(5,'Sunday','Dinner',33,'Muscle Gain','Veg');

INSERT INTO weekly_diet (plan_id,day_of_week,meal_time,meal_id,goal,diet_type) VALUES
(6,'Monday','Early Morning',2,'Muscle Gain','Non Veg'),
(6,'Monday','Breakfast',53,'Muscle Gain','Non Veg'),
(6,'Monday','Breakfast',6,'Muscle Gain','Non Veg'),
(6,'Monday','Mid Snack',25,'Muscle Gain','Non Veg'),
(6,'Monday','Mid Snack',22,'Muscle Gain','Non Veg'),
(6,'Monday','Lunch',13,'Muscle Gain','Non Veg'),
(6,'Monday','Lunch',46,'Muscle Gain','Non Veg'),
(6,'Monday','Lunch',6,'Muscle Gain','Non Veg'),
(6,'Monday','Evening Snack',45,'Muscle Gain','Non Veg'),
(6,'Monday','Dinner',48,'Muscle Gain','Non Veg'),
(6,'Monday','Dinner',6,'Muscle Gain','Non Veg'),
(6,'Tuesday','Early Morning',2,'Muscle Gain','Non Veg'),
(6,'Tuesday','Breakfast',44,'Muscle Gain','Non Veg'),
(6,'Tuesday','Breakfast',6,'Muscle Gain','Non Veg'),
(6,'Tuesday','Mid Snack',25,'Muscle Gain','Non Veg'),
(6,'Tuesday','Lunch',13,'Muscle Gain','Non Veg'),
(6,'Tuesday','Lunch',55,'Muscle Gain','Non Veg'),
(6,'Tuesday','Lunch',6,'Muscle Gain','Non Veg'),
(6,'Tuesday','Evening Snack',45,'Muscle Gain','Non Veg'),
(6,'Tuesday','Dinner',47,'Muscle Gain','Non Veg'),
(6,'Wednesday','Early Morning',2,'Muscle Gain','Non Veg'),
(6,'Wednesday','Breakfast',61,'Muscle Gain','Non Veg'),
(6,'Wednesday','Breakfast',6,'Muscle Gain','Non Veg'),
(6,'Wednesday','Mid Snack',36,'Muscle Gain','Non Veg'),
(6,'Wednesday','Mid Snack',22,'Muscle Gain','Non Veg'),
(6,'Wednesday','Lunch',13,'Muscle Gain','Non Veg'),
(6,'Wednesday','Lunch',46,'Muscle Gain','Non Veg'),
(6,'Wednesday','Lunch',6,'Muscle Gain','Non Veg'),
(6,'Wednesday','Evening Snack',45,'Muscle Gain','Non Veg'),
(6,'Wednesday','Dinner',63,'Muscle Gain','Non Veg'),
(6,'Thursday','Early Morning',2,'Muscle Gain','Non Veg'),
(6,'Thursday','Breakfast',53,'Muscle Gain','Non Veg'),
(6,'Thursday','Breakfast',6,'Muscle Gain','Non Veg'),
(6,'Thursday','Mid Snack',25,'Muscle Gain','Non Veg'),
(6,'Thursday','Mid Snack',22,'Muscle Gain','Non Veg'),
(6,'Thursday','Lunch',69,'Muscle Gain','Non Veg'),
(6,'Thursday','Evening Snack',45,'Muscle Gain','Non Veg'),
(6,'Thursday','Dinner',48,'Muscle Gain','Non Veg'),
(6,'Friday','Early Morning',2,'Muscle Gain','Non Veg'),
(6,'Friday','Breakfast',54,'Muscle Gain','Non Veg'),
(6,'Friday','Breakfast',6,'Muscle Gain','Non Veg'),
(6,'Friday','Mid Snack',25,'Muscle Gain','Non Veg'),
(6,'Friday','Lunch',13,'Muscle Gain','Non Veg'),
(6,'Friday','Lunch',46,'Muscle Gain','Non Veg'),
(6,'Friday','Evening Snack',22,'Muscle Gain','Non Veg'),
(6,'Friday','Dinner',59,'Muscle Gain','Non Veg'),
(6,'Friday','Dinner',6,'Muscle Gain','Non Veg'),
(6,'Saturday','Early Morning',43,'Muscle Gain','Non Veg'),
(6,'Saturday','Breakfast',50,'Muscle Gain','Non Veg'),
(6,'Saturday','Mid Snack',36,'Muscle Gain','Non Veg'),
(6,'Saturday','Mid Snack',45,'Muscle Gain','Non Veg'),
(6,'Saturday','Lunch',69,'Muscle Gain','Non Veg'),
(6,'Saturday','Evening Snack',22,'Muscle Gain','Non Veg'),
(6,'Saturday','Dinner',66,'Muscle Gain','Non Veg'),
(6,'Sunday','Early Morning',2,'Muscle Gain','Non Veg'),
(6,'Sunday','Breakfast',44,'Muscle Gain','Non Veg'),
(6,'Sunday','Breakfast',6,'Muscle Gain','Non Veg'),
(6,'Sunday','Mid Snack',25,'Muscle Gain','Non Veg'),
(6,'Sunday','Lunch',13,'Muscle Gain','Non Veg'),
(6,'Sunday','Lunch',55,'Muscle Gain','Non Veg'),
(6,'Sunday','Evening Snack',45,'Muscle Gain','Non Veg'),
(6,'Sunday','Dinner',47,'Muscle Gain','Non Veg');

CREATE TABLE user_meal_progress (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    user_id   INT NOT NULL,
    meal_id   INT,
    meal_name VARCHAR(255),
    calories  INT DEFAULT 0,
    meal_time VARCHAR(100),
    date      DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed BOOLEAN DEFAULT TRUE,
    notes     VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE water_log (
    user_id  INT NOT NULL,
    glasses  INT DEFAULT 0,
    log_date DATE NOT NULL,
    PRIMARY KEY (user_id, log_date),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE user_streak (
    user_id         INT PRIMARY KEY,
    current_streak  INT DEFAULT 0,
    longest_streak  INT DEFAULT 0,
    last_log_date   DATE,
    total_days      INT DEFAULT 0,
    freeze_available BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE body_measurements (
    measure_id    INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL,
    log_date      DATE NOT NULL,
    weight        FLOAT COMMENT 'kg',
    body_fat_pct  FLOAT,
    waist_cm      FLOAT,
    chest_cm      FLOAT,
    hip_cm        FLOAT,
    notes         VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE achievements (
    ach_id      INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    icon        VARCHAR(10),
    condition_type ENUM('streak','calories_logged','days_logged','weight_lost','meals_count') NOT NULL,
    threshold   INT NOT NULL,
    xp_reward   INT DEFAULT 50
);

INSERT INTO achievements (name, description, icon, condition_type, threshold, xp_reward) VALUES
('First Step',    'Log your very first meal',                      '🌱', 'meals_count',    1,   50),
('Week Warrior',  'Maintain a 7-day streak',                       '🔥', 'streak',         7,  150),
('Month Master',  'Maintain a 30-day streak',                      '💎', 'streak',        30,  500),
('Calorie Crush', 'Log 10,000 total calories',                     '⚡', 'calories_logged',10000, 200),
('Consistent',    'Log meals for 10 days total',                   '📅', 'days_logged',   10,  100),
('Dedicated',     'Log meals for 30 days total',                   '🏆', 'days_logged',   30,  300),
('Featherweight', 'Log a 3-day streak',                            '🌟', 'streak',         3,   75),
('Iron Will',     'Log meals for 60 days total',                   '🦾', 'days_logged',   60,  600),
('Centurion',     'Log 100 total meals',                           '💯', 'meals_count',  100,  400),
('Drop Zone',     'Lose 2 kg from starting weight',               '📉', 'weight_lost',    2,  250);

CREATE TABLE user_achievements (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    ach_id     INT NOT NULL,
    earned_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_user_ach (user_id, ach_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (ach_id)  REFERENCES achievements(ach_id)
);

CREATE TABLE meal_ratings (
    rating_id  INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    meal_id    INT NOT NULL,
    rating     TINYINT CHECK (rating BETWEEN 1 AND 5),
    comment    VARCHAR(500),
    rated_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_user_meal_rating (user_id, meal_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (meal_id) REFERENCES meals(meal_id) ON DELETE CASCADE
);

CREATE TABLE user_daily_goals (
    goal_id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT UNIQUE NOT NULL,
    calorie_goal  INT DEFAULT 2000,
    protein_goal  INT DEFAULT 120,
    carbs_goal    INT DEFAULT 250,
    fat_goal      INT DEFAULT 65,
    water_goal    INT DEFAULT 8,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE OR REPLACE VIEW v_diet_plan AS
SELECT
    dp.goal, dp.food_type, wd.day_of_week, wd.meal_time,
    m.meal_name, m.category, m.prep_time,
    n.calories, n.protein, n.carbs, n.fat, n.fiber
FROM weekly_diet wd
JOIN diet_plan dp ON wd.plan_id = dp.plan_id
JOIN meals m ON wd.meal_id = m.meal_id
LEFT JOIN nutrition n ON m.meal_id = n.meal_id;

CREATE OR REPLACE VIEW v_user_today AS
SELECT
    ump.user_id,
    SUM(ump.calories) AS total_calories,
    COUNT(*) AS meals_logged
FROM user_meal_progress ump
WHERE DATE(ump.date) = CURDATE() AND ump.completed = TRUE
GROUP BY ump.user_id;

CREATE OR REPLACE VIEW v_top_meals AS
SELECT
    m.meal_id, m.meal_name, m.category,
    ROUND(AVG(mr.rating), 1) AS avg_rating,
    COUNT(mr.rating_id) AS rating_count,
    n.calories, n.protein
FROM meals m
LEFT JOIN meal_ratings mr ON m.meal_id = mr.meal_id
LEFT JOIN nutrition n ON m.meal_id = n.meal_id
GROUP BY m.meal_id
ORDER BY avg_rating DESC, rating_count DESC;

