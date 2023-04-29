from flask import Flask, request, render_template
from sqlalchemy import create_engine
import pandas as pd
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def load_odds_table():
    conn = get_db_connection()
    odds = conn.execute("""SELECT b.number, a.horse, a.odds 
                        FROM odds a
                        INNER JOIN horses b 
                        ON a.horse = b.horse """).fetchall()
    conn.close()
    return odds

def total_handle():
    conn = get_db_connection()
    total = conn.execute("""SELECT SUM(amount) AS total_amount
                            FROM bets;""").fetchall()[0][0]
    conn.close()
    return total

def update_odds():
    conn = get_db_connection()
    # select sum on each horse from bets,
    # select total
    sums = conn.execute("""SELECT horse, SUM(amount) AS total_amount
                        FROM bets
                        GROUP BY horse;""").fetchall()

    total = conn.execute("""SELECT SUM(amount) AS total_amount
                        FROM bets;""").fetchall()[0][0]

    for horse, bet_sum in sums:
        odds = round(total / bet_sum, 2)
        conn.execute("INSERT INTO odds (horse, odds) VALUES (?, ?)",
                    (horse, odds)
                    )
    conn.commit()
    conn.close()

def load_horses():
    conn = get_db_connection()
    horses = conn.execute('SELECT * FROM horses').fetchall()
    conn.close()
    return horses

def load_bets():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM bets').fetchall()
    conn.close()
    return posts

def save_bet(bettor, horse, amount):
    conn = get_db_connection()
    conn.execute("INSERT INTO bets (bettor, horse, amount) VALUES (?, ?, ?)",
                (bettor, horse, amount)
                )
    conn.commit()
    conn.close()


NAMES = [
    "Ryan",
    "Jen",
    "Dean",
    "Mel",
    "Ross",
    "Jane",
    "Paul",
    "Jamie",
    "Hurry",
    "Craig",
    "Erin",
    "Kate Jones",
    "Al",
    "Kate Vidal",
    "Jose",
    "Kate Martinez",
    "Melissa",
    "Adam",
    "Noelle",
    "Justin",
    "John",
    "Sherri",
]
NAMES = sorted(NAMES)
HORSES = load_horses()

@app.route('/', methods=['GET', 'POST'])
def index():
    odds = load_odds_table()
    total = total_handle()
    # Render the HTML template with the horse names and updated odds
    return render_template('index.html', odds=odds, total=total)

@app.route('/place', methods=['GET', 'POST'])
def place_bet():
    odds = load_odds_table()
    if request.method == 'POST':
        bettor = request.form['name']
        horse = request.form['horse']
        amount = int(request.form['amount'])
        save_bet(bettor, horse, amount)
        update_odds()
    return render_template('place-bet.html', names=NAMES, horses=HORSES, odds=odds)

@app.route('/view', methods=['GET', 'POST'])
def view_bets():
    bets = load_bets()
    return render_template('bets.html', bets=bets)

if __name__ == '__main__':
    app.run(debug=True)