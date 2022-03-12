import requests
import os
import json
import pandas as pd

bearer_token = os.environ.get("BEARER_TOKEN")

#Global Data frame to hold the Wordle scores
data = {'User': ['None'], 'WordleNumber': [0], 'Score': [0]}
WordleDataFrame = pd.DataFrame(data = data)
#Global Array of the players
Players = ['andresrbollain','Davidendum','monstrua_rosa','dondestalvizo','Mikeperezc']

def create_url(TwiteerUserName):
    Users = TwiteerUserName
    url = "https://api.twitter.com/2/tweets/search/recent?query=from:{}".format(Users)
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
    print(response.status_code)
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
       TweetsFromUser_DataFrame = pd.json_normalize(ThoseTweets, record_path = ['data'])
    else:
       TweetsFromUser_DataFrame = pd.DataFrame({'text' : ['BLANK']})
    return TweetsFromUser_DataFrame

def ExtractWordleDataFromTweet(TweetText):
    WrodleData = [0,0]
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
    WrodleData = [WordleNumber,WordleScore]
    return WrodleData

def ParseWordleDataFromUser(User,TweetsFromUser_DataFrame):
    ThisRow=0
    WordleScoresCount=0

    for row in TweetsFromUser_DataFrame.itertuples():
      #get the tweet text from the data frame
      TweetText = TweetsFromUser_DataFrame['text'][ThisRow]
      #handle the Wordle score search in the tweets
      if(TweetText.find('Wordle') != -1):
        #Wordle score count from the tweets
        WordleScoresCount = WordleScoresCount + 1
        #Extract Wordle Data from the Tweet text
        WrodleData = ExtractWordleDataFromTweet(TweetText)
        #Add the Wordle data to the Data Frame
        WordleDataFrame.loc[len(WordleDataFrame.index)] = [User,WrodleData[0],WrodleData[1]]
      ThisRow = ThisRow + 1
      
    if (WordleScoresCount == 0):
      WordleScoresCount = -1

    return WordleScoresCount

def LoopThroughPlayers(Players):
    for Player in Players:
      WordleScoresCount = 0
      #START
      #Obtain the latest tweets of the user
      Tweets = GetTweetsFromUser(Player)
      #Filter tweets with the wordle identifier and parse the wordle data
      WordleScoresCount = ParseWordleDataFromUser(Player,Tweets)
      if(WordleScoresCount != -1):
        #Add the DATA to the DB only if Wordle scores are found
        print('For User: ',Player,' Script found ', WordleScoresCount,' Wrodle Scores, Its time to add them to the DB')
      else:
        #Dont Add anyhting to the DB
        print('DB not modified')
      #END 

def main():
    LoopThroughPlayers(Players)
    print(WordleDataFrame)
	
if __name__ == "__main__":
    main()