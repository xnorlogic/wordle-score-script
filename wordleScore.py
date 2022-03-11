import requests
import os
import json
import pandas as pd

bearer_token = os.environ.get("BEARER_TOKEN")

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

def LoopThroughPlayers(Players):
    for Player in Players:
      print(Player + ' Latest Tweets------------------------')
	  
	  #START
	  #Obtain the latest tweets of the user
      Tweets = GetTweetsFromUser(Player)
	  #Filter tweets with the wordle identifier
	  #Parse wordle DATA: Wordle# Score
	  #Add the DATA to the DB
	  #END
	  
      print(Tweets['text'])

def main():
    Players = ['andresrbollain','Davidendum','monstrua_rosa','dondestalvizo','Mikeperezc'];
    LoopThroughPlayers(Players)
	
if __name__ == "__main__":
    main()