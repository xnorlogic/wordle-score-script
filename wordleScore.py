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


def WordleScoreConditioning(WordleScore):
    return 7 if WordleScore == 'X' else int(WordleScore)


def ExtractWordleDataFromTweet(TweetText):
    WordleData = [0, 0]
    #handle the wordle number parse from the tweet
    WordleNumber = TweetText.split('Wordle ')[1]
    WordleNumber = WordleNumber.split(' ')[0]
    WordleNumber = int(WordleNumber)
    #handle the wordle socre parse from the tweet
    WordleScore = TweetText.split('Wordle ')[1]
    WordleScore = WordleScore.split('/')[0]
    WordleScore = WordleScore.split(' ')[1]
    #handle the conversion to integer and if the game was failed
    WordleData = [WordleNumber, WordleScoreConditioning(WordleScore)]
    return WordleData


def ParseWordleDataFromUser(Player, TweetsFromUser_DataFrame):
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
        WordleData = ExtractWordleDataFromTweet(TweetText)
        #Add the Wordle data to the Data Frame
        WordleDataFrame.loc[len(WordleDataFrame.index)] = [
            Player, WordleData[WordleNumberIndex], WordleData[WordleScoreIndex]]
    return WordleScoresCount if WordleScoresCount != 0 else -1


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
   WordleScoreFoundFlag = True
   for DataFrameRow in WordleNumberDataFrame.itertuples():
      if (DataFrameRow.WordleNumber == WordleNumber):
        WordleScoreFoundFlag = True
        break
      else:
        WordleScoreFoundFlag = False
   return WordleScoreFoundFlag


def UpdateDataBase(WordleData):
    #setup the DB connection
    conn = sqlite3.connect('wordleScores.db')
    DataBaseUpdatedFlag = False
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
    if (SearchDataFrameDuplicates(WordleNumberDataFrame, WordleData[1]) == False):
      #add a new data row to the DB
      conn.execute(Generate_INSERT_QueryString(WordleData))
      conn.commit()
      DataBaseUpdatedFlag = True
    else:
      #dont add to the DB because the wordle number already exists
      DataBaseUpdatedFlag = False
    conn.close()
    return DataBaseUpdatedFlag


def DataBaseUpdateQuery(WordleDataFrame, Player):
    DataBaseUpdateFlag = False
    WordleData = ['user', 000, 0]
    for DataFrameRow in WordleDataFrame.itertuples():
      if (DataFrameRow.User == Player):
        WordleData = [Player,DataFrameRow.WordleNumber,DataFrameRow.Score]
        if (UpdateDataBase(WordleData) == True):
          DataBaseUpdateFlag = True
        else:
          DataBaseUpdateFlag = False
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
        if(DataBaseUpdateQuery(WordleDataFrame, Player) == True):
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
