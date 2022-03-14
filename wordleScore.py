#By Andy R.

import sqlite3
import requests
import os
import json
import pandas as pd


bearer_token = os.environ.get("BEARER_TOKEN")


#Global Data frame to hold the Wordle scores
data = {'User': ['None'], 'WordleNumber': [0], 'Score': [0]}
WordleDataFrame = pd.DataFrame(data=data)


def GetPlayersFromList(PlayerListFileName):		   
    Players = []
    Tmp = []
    with open(PlayerListFileName) as f:
      Tmp = f.readlines()
    for Player in Tmp:
      Players.append(Player.replace("\n", ""))
    return Players


def create_url(TwiteerUserName):
    Users = TwiteerUserName
    url = "https://api.twitter.com/2/tweets/search/recent?query=from:{}".format(
        Users)
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


def GetTweetsFromUser(TwiteerUserName):
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


def ExtractWordleDataFromTweet(TweetText):
    WrodleData = [0, 0]
    #handle the score parse from the tweet
    WordleNumber = TweetText.split('Wordle ')[1]
    WordleNumber = WordleNumber.split(' ')[0]
    WordleNumber = int(WordleNumber)
    WordleScore = TweetText.split('Wordle ')[1]
    WordleScore = WordleScore.split('/')[0]
    WordleScore = WordleScore.split(' ')[1]
    #handle the conversion to integer and if the game was failed
    if(WordleScore == 'X'):
      WordleScore = 7
    else:
      WordleScore = int(WordleScore)
    WrodleData = [WordleNumber, WordleScore]
    return WrodleData


def ParseWordleDataFromUser(User, TweetsFromUser_DataFrame):
    WordleScoresCount = 0
    for DataFrameRow in TweetsFromUser_DataFrame.itertuples():
      #get the tweet text from the data frame
      TweetText = DataFrameRow.text
      #handle the Wordle score search in the tweets
      if(TweetText.find('Wordle') != -1):
        #Wordle score count from the tweets
        WordleScoresCount = WordleScoresCount + 1
        #Extract Wordle Data from the Tweet text
        WrodleData = ExtractWordleDataFromTweet(TweetText)
        #Add the Wordle data to the Data Frame
        WordleDataFrame.loc[len(WordleDataFrame.index)] = [
            User, WrodleData[0], WrodleData[1]]
    if (WordleScoresCount == 0):
      WordleScoresCount = -1
    return WordleScoresCount


def Generate_INSERT_QueryString(WordleData):
   username = WordleData[0]
   wordlenumber = WordleData[1]
   wordlescore = WordleData[2]
   INSERT_QUERY = "INSERT INTO wordle_scores (username,wordlenumber,wordlescore) VALUES ('" + \
       username + "'," + str(wordlenumber) + "," + str(wordlescore) + ");"
   return INSERT_QUERY


def Generate_SELECT_QueryString(username):
   SELECT_QUERY = "SELECT username,wordlenumber FROM wordle_scores WHERE username = '" + username + "';"
   return SELECT_QUERY


def SearchDataFrameDuplicates(WordleNumberDataFrame, WordleNumber):
   #seach the data frame for the wordle number
   WordleScoreFoundFlag = 1
   for i in range(len(WordleNumberDataFrame.User)):
      if (WordleNumberDataFrame.WordleNumber[i] == WordleNumber):
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
    WordleNumberDataFrame = pd.DataFrame(data=data)
    #get the table contents for users from the DB
    cursor = conn.execute(Generate_SELECT_QueryString(WordleData[0]))
    #populate th data frame
    for row in cursor:
      WordleNumberDataFrame.loc[len(WordleNumberDataFrame.index)] = [
          row[0], row[1]]
    #check if the wordle number was found in the data frame
    if (SearchDataFrameDuplicates(WordleNumberDataFrame, WordleData[1]) == 0):
      #add a new data row to the DB
      conn.execute(Generate_INSERT_QueryString(WordleData))
      conn.commit()
      DataBaseUpdatedFlag = 1
    else:
      #dont add to the DB because the wordle number already exists
      DataBaseUpdatedFlag = 0
    conn.close()
    return DataBaseUpdatedFlag


def DataBaseUpdateQuery(WordleDataFrame, Player):
    DataBaseUpdateFlag = 0
    WordleData = ['user', 000, 0]
    for i in range(len(WordleDataFrame.User)):
      if (WordleDataFrame.User[i] == Player):
        WordleData[0] = Player
        WordleData[1] = WordleDataFrame.WordleNumber[i]
        WordleData[2] = WordleDataFrame.Score[i]
        if (UpdateDataBase(WordleData) == 1):
          DataBaseUpdateFlag = 1
        else:
          DataBaseUpdateFlag = 0
    return DataBaseUpdateFlag


def LoopThroughPlayers(Players):
    PlayerStatusInDB = 0
    for Player in Players:
      WordleScoresCount = 0
      #START
      #Obtain the latest tweets of the user
      Tweets = GetTweetsFromUser(Player)
      #Filter tweets with the wordle identifier and parse the wordle data
      WordleScoresCount = ParseWordleDataFromUser(Player, Tweets)
      #Attempt to Add the DATA to the DB only if Wordle scores are found
      if(WordleScoresCount != -1):
        print('User: ', Player, ' has ', WordleScoresCount,' Wordle Scores in the past 7 days!')
        #Perform the DB operations, update the Data Base only when there is a NEW Wordle Score
        if(DataBaseUpdateQuery(WordleDataFrame, Player) == 1):
          PlayerStatusInDB = PlayerStatusInDB + 1
        else:
          PlayerStatusInDB = PlayerStatusInDB + 0
      else:
        PlayerStatusInDB = PlayerStatusInDB + 0
      #END
    return PlayerStatusInDB


def main():
    #Obtain the players from the external file
    Players = GetPlayersFromList('twitterUsers')
    #Run through player data and add to the DB if needed
    PlayersWithDBupdates = LoopThroughPlayers(Players)
    #Print some Information
    print('Number of players with DB Updates = ', PlayersWithDBupdates)
    print('Scores Extracted From Twitter...')
    print(WordleDataFrame)


if __name__ == "__main__":
    main()
