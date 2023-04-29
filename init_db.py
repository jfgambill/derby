import sqlite3
import pandas as pd

connection = sqlite3.connect('database.db')

with open('schema.sql') as f:
    connection.executescript(f.read())

init_bets = pd.read_csv('init_bets.csv')
init_horses = pd.read_csv('horse_template.csv')

cur = connection.cursor()
for i, row in init_bets.iterrows():
    cur.execute("INSERT INTO bets (bettor, horse, amount) VALUES (?, ?, ?)",
                (row.bettor, row.horse, row.amount)
                )
connection.commit()

cur = connection.cursor()
for i, row in init_horses.iterrows():
    cur.execute("INSERT INTO horses (number, horse) VALUES (?, ?)",
                (row.number, row.horse)
                )
connection.commit()

# select sum on each horse from bets,
# select total
sums = cur.execute("""SELECT horse, SUM(amount) AS total_amount
                    FROM bets
                    GROUP BY horse;""").fetchall()

total = cur.execute("""SELECT SUM(amount) AS total_amount
                    FROM bets;""").fetchall()[0][0]

for horse, bet_sum in sums:
    odds = round(total / bet_sum, 2)
    cur.execute("INSERT INTO odds (horse, odds) VALUES (?, ?)",
                (horse, odds)
                )

connection.commit()
connection.close()