import sqlite3

conn = sqlite3.connect('wordleScores.db')
conn.execute("INSERT INTO wordle_scores (username,wordlenumber,wordlescore) VALUES ('SomeUser',222,3);")
conn.commit()
cursor = conn.execute('SELECT * FROM wordle_scores;')
for row in cursor:
  print('user Name: ', row[1])
  print('wordle number: ', row[2])
  print('wordle score: ', row[3])
  
conn.close()
