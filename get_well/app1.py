from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import datetime

# Define the Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize the database
def init_db():
    with sqlite3.connect('diet.db') as conn:
        conn.execute('''DROP TABLE IF EXISTS Diet;''')
        conn.execute('''CREATE TABLE Diet
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         food TEXT NOT NULL,
                         quantity INTEGER NOT NULL,
                         calories INTEGER NOT NULL,
                         type TEXT NOT NULL,
                         date TEXT NOT NULL);''')

# Calculate calories based on food type and quantity
def calculate_calories(food_type, quantity):
    type_calories = {
        'rice': 1.3,  # Moderate calorie value per gram
        'junk': 4.0,  # High calorie value per gram
        'sugar': 3.87,  # High calorie value per gram
        'vegetables': 0.35  # Low calorie value per gram
    }
    calorie_per_gram = type_calories.get(food_type.lower(), 0)
    return calorie_per_gram * quantity

@app.route('/')
def user_info():
    return render_template('user_info.html')

@app.route('/submit_user_info', methods=['POST'])
def submit_user_info():
    name = request.form['name']
    age = request.form['age']

    if not name or not age:
        return "Please provide both name and age."

    try:
        session['name'] = name
        session['age'] = int(age)
        return redirect(url_for('index'))
    except ValueError as e:
        print("Error: ", e)
        return "Invalid input. Please enter valid data."

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/submit_diet', methods=['POST'])
def submit_diet():
    food = request.form['food']
    quantity = request.form['quantity']
    food_type = request.form['type']
    date = request.form['date']

    if not food or not quantity or not date or not food_type:
        return "Please provide food, quantity, type, and date."

    try:
        quantity = int(quantity)
        calories = calculate_calories(food_type, quantity)
        with sqlite3.connect('diet.db') as conn:
            conn.execute('INSERT INTO Diet (food, quantity, calories, type, date) VALUES (?, ?, ?, ?, ?)', (food, quantity, calories, food_type, date))
        return redirect(url_for('index'))
    except ValueError as e:
        print("Error: ", e)
        return "Invalid input. Please enter valid data."

@app.route('/report')
def report():
    try:
        with sqlite3.connect('diet.db') as conn:
            cur = conn.execute('SELECT food, calories, type, date FROM Diet')
            diet_data = cur.fetchall()

        # Debug: Print the retrieved diet data
        print("Diet Data:", diet_data)

        if not diet_data:
            return "No data available."

        for item in diet_data:
            print("Item Length:", len(item), "Item:", item)
            if len(item) != 4:
                return "Error: Unexpected number of values in database record."

        foods = [item[0] for item in diet_data]
        calories = [item[1] for item in diet_data]
        food_types = [item[2] for item in diet_data]
        dates = [item[3] for item in diet_data]

        today = datetime.date.today()
        past_7_days = [(today - datetime.timedelta(days=i)).isoformat() for i in range(7)]

        # Debug: Print the past 7 days
        print("Past 7 Days:", past_7_days)

        filtered_diet_data = [item for item in diet_data if item[3] in past_7_days]

        # Debug: Print filtered diet data
        print("Filtered Diet Data:", filtered_diet_data)

        if not filtered_diet_data:
            return "No data available for the past 7 days."

        unique_dates = past_7_days
        date_calories = {
            date: sum(item[1] for item in filtered_diet_data if item[3] == date) 
            for date in unique_dates
        }

        # Debug: Print date_calories dictionary
        print("Date Calories:", date_calories)

        name = session.get('name', 'Guest')
        age = session.get('age', 0)

        suggestions = []
        if food_types.count('junk') > len(food_types) // 2:
            suggestions.append('Consider reducing junk food and adding more vegetables.')
        if food_types.count('sugar') > len(food_types) // 2:
            suggestions.append('Try to reduce sugary sweets.')
        if food_types.count('vegetables') > len(food_types) // 2:
            suggestions.append('Keep up with the vegetables and fruits! Consider incorporating some exercise.')

        potential_diseases = "None"
        suggested_diet = " ".join(suggestions) or "Balanced diet with more fruits and vegetables"
        return render_template('report.html', diet_data=filtered_diet_data, diseases=potential_diseases, suggestions=suggested_diet, name=name, age=age, unique_dates=unique_dates, date_calories=date_calories, foods=foods, calories=calories)

    except Exception as e:
        print("Error:", e)
        return str(e)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
