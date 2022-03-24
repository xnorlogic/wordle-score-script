#By Andy R.

import sqlite3
import requests
import os
import json
import pandas as pd
from datetime import datetime


bearer_token = os.environ.get("BEARER_TOKEN")


#Global Data frame to hold the Wordle scores
data = {'User': ['None'], 'WordleNumber': [0], 'Score': [0]}
wordle_df = pd.DataFrame(data=data)


def get_date_time():
   now = datetime.now()
   time = now.strftime("%H:%M:%S")
   date = now.strftime("%d/%m/%Y")
   return [date,time]


def get_players(players_file_name):		   
    players = []
    Tmp = []
    with open(players_file_name) as f:
      Tmp = f.readlines()
    for player in Tmp:
      players.append(player.replace("\n", ""))
    return players


def create_url(twitter_id):
    url = "https://api.twitter.com/2/tweets/search/recent?query=from:{}".format(
        twitter_id)
    return url


def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "twitter-apiV2-exploration"
    return r


def connect_to_endpoint(url):
    response = requests.request("GET", url, auth=bearer_oauth)
    #print(response.status_code)
    if response.status_code != 200:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )
    return response.json()


def get_tweets(TwiteerUserName):
    #create and make the API call
    url = create_url(TwiteerUserName)
    json_response = connect_to_endpoint(url)
    #create a JSON file from the response
    with open(TwiteerUserName + '.json', 'w') as json_file:
      json.dump(json_response, json_file, indent=4, sort_keys=True)
    #create a dictionary from the JSON file
    with open(TwiteerUserName + '.json') as f:
        ThoseTweets = json.load(f)
    #handle the no recent tweets from the user
    if(ThoseTweets['meta']['result_count'] != 0):
       TweetsFromUser_DataFrame = pd.json_normalize(
           ThoseTweets, record_path=['data'])
    else:
       TweetsFromUser_DataFrame = pd.DataFrame({'text': ['BLANK']})
    return TweetsFromUser_DataFrame


def parse_wordle_score(TweetText):
    if (TweetText.count('Wordle ') == 1):
      WordleScore = TweetText.split('Wordle ')[1]
      WordleScore = WordleScore.split('/')[0]
      WordleScore = WordleScore.split(' ')[1]
    else:
      WordleScore = 0
    return 7 if WordleScore == 'X' else int(WordleScore)


def parse_wordle_number(TweetText):
    if (TweetText.count('Wordle ') == 1):
      WordleNumber = TweetText.split('Wordle ')[1]
      WordleNumber = WordleNumber.split(' ')[0]
    else:
      WordleNumber = 0
    return int(WordleNumber)


def parse_wordle_data(Player, TweetsFromUser_DataFrame):
    #Locals
    WordleScoresCount = 0
    WordleNumberIndex = 0
    WordleScoreIndex  = 1
    #Loop through the dataframe looking for twits that have Wordle identifier 
    for DataFrameRow in TweetsFromUser_DataFrame.itertuples():
      #get the tweet text from the data frame
      TweetText = DataFrameRow.text
      #handle the Wordle score search in the tweets
      if(TweetText.find('Wordle') != -1):
        #Wordle score count from the tweets
        WordleScoresCount = WordleScoresCount + 1
        #Extract Wordle Data from the Tweet text
        WordleData = [parse_wordle_number(TweetText), parse_wordle_score(TweetText)]
        #Add the Wordle data to the Data Frame
        wordle_df.loc[len(wordle_df.index)] = [
            Player, WordleData[WordleNumberIndex], WordleData[WordleScoreIndex]]
    return WordleScoresCount if WordleScoresCount != 0 else -1


def generate_insert_query(wordle_data):
   date_and_time = get_date_time()
   import_type = 'Script'
   sqlite_insert_query = "INSERT INTO wordle_scores (username,wordlenumber,wordlescore,DBupdateDate,DBupdateTime,Importype) VALUES ('" + \
       wordle_data[0] + "'," + str(wordle_data[1]) + "," + \
       str(wordle_data[2]) + "," + "'" + date_and_time[0] + "'" + "," + \
       "'" + date_and_time[1] + "'" + "," + "'" + import_type + "'" + ");"
   return sqlite_insert_query


def generate_select_query(username):
   sqlite_select_query = "SELECT username,wordlenumber FROM wordle_scores WHERE username = '" + username + "';"
   return sqlite_select_query


def find_duplicates(wordle_number_df, wordle_number):
   #search the data frame for the wordle number
   wordle_score_found_flg = True
   for df_row in wordle_number_df.itertuples():
      if (df_row.WordleNumber == wordle_number):
        wordle_score_found_flg = True
        break
      else:
        wordle_score_found_flg = False
   return wordle_score_found_flg


def data_base_manipulation(wordle_data):
    #setup the DB connection
    conn = sqlite3.connect('wordleScores.db')
    db_update_flg = False
    #local scope data frame
    data = {'User': ['None'], 'WordleNumber': [0]}
    wordle_number_df = pd.DataFrame(data=data)
    #get the table contents for users from the DB
    cursor = conn.execute(generate_select_query(wordle_data[0]))
    #populate th data frame
    for row in cursor:
      wordle_number_df.loc[len(wordle_number_df.index)] = [
          row[0], row[1]]
    #check if the wordle number was found in the data frame
    if (find_duplicates(wordle_number_df, wordle_data[1]) == False):
      #add a new data row to the DB
      conn.execute(generate_insert_query(wordle_data))
      conn.commit()
      db_update_flg = True
    else:
      #dont add to the DB because the wordle number already exists
      db_update_flg = False
    conn.close()
    return db_update_flg


def data_base_update(player):
    db_updates = 0
    for df_row in wordle_df.itertuples():
      if (df_row.User == player):
        wordle_data = [df_row.User, df_row.WordleNumber, df_row.Score]
        if (data_base_manipulation(wordle_data) == True):
          db_updates += 1
        else:
          db_updates += 0
    return db_updates


def loop_players(players):
    data_base_updates = 0
    for player in players:
      wordle_scores_count = 0
      #Obtain the latest tweets of the user
      tweets = get_tweets(player)
      #Filter tweets with the wordle identifier and parse the wordle data
      wordle_scores_count = parse_wordle_data(player, tweets)
      #Attempt to Add the DATA to the DB only if Wordle scores are found
      if(wordle_scores_count != -1):
        print('User: ', player, ' has ', wordle_scores_count,
              ' Wordle Scores in the past 7 days!')
        data_base_updates = data_base_update(player) + data_base_updates
      else:
        data_base_updates = data_base_updates + 0
    return data_base_updates


def log_information(TheLogFile,PlayersWithDBupdates):
    #Print some info
    print('Number of players with DB Updates = ', PlayersWithDBupdates)
    print('Scores Extracted From Twitter...')
    print(wordle_df)
    #Log the info
    LogFile = open(TheLogFile, "a")
    DateTime = get_date_time()
    LogFile.write("\n")
    LogFile.write('Log created: ' + DateTime[0] + ' --- ' + DateTime[1])
    LogFile.write("\n")
    LogFile.write('Number of players with DB Updates = ' + str(PlayersWithDBupdates))
    LogFile.write("\n")
    LogFile.write('Scores Extracted From Twitter...')
    LogFile.write("\n")
    LogFile.write(wordle_df.to_string())
    LogFile.close()
    return 0


def main():
    #Obtain the players from the external file
    Players = get_players('twitterUsers')
    #Run through player data and add to the DB if needed
    PlayersWithDBupdates = loop_players(Players)
    #Log the information
    log_information('log',PlayersWithDBupdates)


if __name__ == "__main__":
    main()
