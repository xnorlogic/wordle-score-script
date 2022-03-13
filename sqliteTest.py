import sqlite3
import pandas as pd

def Generate_INSERT_QueryString(WordleData):
   username=WordleData[0]
   wordlenumber=WordleData[1]
   wordlescore=WordleData[2]
   INSERT_QUERY="INSERT INTO wordle_scores (username,wordlenumber,wordlescore) VALUES ('" + username + "'," + str(wordlenumber) + "," + str(wordlescore) + ");"
   return INSERT_QUERY

def Generate_SELECT_QueryString(username):
   SELECT_QUERY = "SELECT username,wordlenumber FROM wordle_scores WHERE username = '" + username + "';"
   return SELECT_QUERY

def SearchDataFameDuplicates(WordleNumberDataFrame):
   #seach the data frame for the wordle number
   WordleScoreFoundFlag = 1
   for i in range(len(WordleNumberDataFrame.User)):
      if (WordleNumberDataFrame.WordleNumber[i] == TestWordleNumber):
        WordleScoreFoundFlag = 1
        break
      else:
        WordleScoreFoundFlag = 0
   return WordleScoreFoundFlag

def UpdateDataBase(WordleData):
    #setup the DB connection
    conn = sqlite3.connect('wordleScores.db')
    DataBaseUpdatedFlag = 0
    
    #local scope data frame
    data = {'User': ['None'], 'WordleNumber': [0]}
    WordleNumberDataFrame = pd.DataFrame(data = data)

    #get the table contents for users from the DB
    cursor = conn.execute(Generate_SELECT_QueryString(WordleData[0]))

    #populate th data frame
    for row in cursor:
      WordleNumberDataFrame.loc[len(WordleNumberDataFrame.index)] = [row[0],row[1]]

    #check if the wordle number was found in the data frame
    if (SearchDataFameDuplicates(WordleNumberDataFrame) == 0):
      #add a new data row to the DB
      conn.execute(Generate_INSERT_QueryString(WordleData))
      conn.commit()
      DataBaseUpdatedFlag = 1
    else:
      #dont add to the DB because the wordle number already exists
      DataBaseUpdatedFlag = 0
    
    conn.close()
    return DataBaseUpdatedFlag

#wordle data to add into the table
TestWordleNumber=235
WordleData = ['andresrbollain',TestWordleNumber,4]

if (UpdateDataBase(WordleData) == 1):
  print("DB Updated with a new score")
else:
  print("DB not updated")