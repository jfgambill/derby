from flask import Flask, request, render_template, flash
import sqlite3
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def load_odds_table():
    conn = get_db_connection()
    odds = conn.execute("""SELECT b.number, a.horse, a.odds 
                        FROM odds a
                        INNER JOIN horses b 
                        ON a.horse = b.horse 
                        ORDER BY odds """).fetchall()
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
        conn.execute("""INSERT INTO odds (horse, odds) VALUES (?, ?) 
                    ON CONFLICT (horse) DO UPDATE SET odds = EXCLUDED.odds;""",
                    (horse, odds)
                    )
    conn.commit()
    conn.close()

def load_horses():
    conn = get_db_connection()
    horses = conn.execute('SELECT * FROM horses').fetchall()
    conn.close()
    return horses

def load_bets(person=None):
    conn = get_db_connection()
    if (person == "ALL") or (person is None):
        bets = conn.execute('SELECT * FROM bets ORDER BY bettor, created').fetchall()
    else:
        bets = conn.execute(f"SELECT * FROM bets WHERE bettor = '{person}'").fetchall()

    conn.close()
    return bets

def save_bet(bettor, horse, amount):
    conn = get_db_connection()
    conn.execute("INSERT INTO bets (bettor, horse, amount) VALUES (?, ?, ?)",
                (bettor, horse, amount)
                )
    conn.commit()
    conn.close()

def delete_bet_id(bet_id):
    conn = get_db_connection()
    conn.execute(f"DELETE FROM bets WHERE id = '{bet_id}'")
    conn.commit()
    conn.close()

def calc_payouts(winner):
    conn = get_db_connection()
    bettors = conn.execute(f"""SELECT bettor, SUM(amount) as bet_sum
                               FROM bets 
                               WHERE horse = "{winner}"
                               GROUP BY bettor""").fetchall()

    horse_total = conn.execute(f"""SELECT SUM(amount)
                                   FROM bets 
                                   WHERE horse = "{winner}" """).fetchall()[0][0]
    conn.close()
    total = total_handle()
    payout_list = []
    for bettor in bettors:
        payout = total * (bettor["bet_sum"] / horse_total)
        payout_list.append({"bettor":bettor["bettor"], "wagered":bettor["bet_sum"], "payout":payout})
    return payout_list

NAMES = [
    "Ryan",
    "Jen",
    "Dean",
    "Mell",
    "Ross",
    "Jane",
    "Paul",
    "Jamie",
    "Hurry",
    "Craig",
    "Danielle",
    "Iesha",
    "Kalefe",
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
bet_stop = False

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
        amount = int(request.form['bet_amount'])
        save_bet(bettor, horse, amount)
        update_odds()
    return render_template('place-bet.html', names=NAMES, horses=HORSES, odds=odds, bet_stop=bet_stop)

@app.route('/view', methods=['GET', 'POST'])
def view_bets():
    selected_name = None
    bets = None
    total_bet = 0
    if request.method == 'POST':
        # Get the selected name from the form data
        selected_name = request.form['name']

        # Query the database for all bets made by the selected person
        bets = load_bets(selected_name)
        total_bet = sum(bet['amount'] for bet in bets)  # Calculate the total bet amount for the selected bettor

    return render_template('bets.html', bets=bets, names=["ALL"] + NAMES, selected_name=selected_name, total_bet=total_bet)

@app.route('/payouts', methods=['GET', 'POST'])
def payouts():
    winner = None
    payouts = None
    if request.method == 'POST':
        # Get the winner from the form data
        winner = request.form['winner']
        # Query the database payouts
        payouts = calc_payouts(winner)
    return render_template('payouts.html', horses=HORSES, winner=winner, payouts=payouts)

@app.route('/delete', methods=['GET', 'POST'])
def delete_bet():
    id_to_delete = None
    bets = load_bets()
    if request.method == 'POST':
        # Get the selected name from the form data
        id_to_delete = request.form['bet_id']

        delete_bet_id(id_to_delete)
        # Show confirmation message
        flash(f"Success! Bet id {id_to_delete} has been deleted.")

    return render_template('delete.html', bets=bets, id_to_delete=id_to_delete)


if __name__ == '__main__':
    # ip addr is 192.168.50.142
    app.run(host="0.0.0.0", port=5000)