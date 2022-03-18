import sqlite3
import pandas as pd
from datetime import datetime


InitialWN = 268
WN=[InitialWN,InitialWN + 1,InitialWN + 2,InitialWN + 3,InitialWN + 4]

#Global Data frame to hold the Wordle Scoreboard
data = {'User': ['None'], str(WN[0]): [0],str(WN[1]): [0],str(WN[2]): [0],str(WN[3]): [0],str(WN[4]): [0], 'Total': [0]}
WordleScoreBoardDataFrame = pd.DataFrame(data=data)

def GetDateandTime():
   now = datetime.now()
   time = now.strftime("%H:%M:%S")
   date = now.strftime("%d/%m/%Y")
   return [date,time]


def GetPlayersFromList(PlayerListFileName):		   
    Players = []
    Tmp = []
    with open(PlayerListFileName) as f:
      Tmp = f.readlines()
    for Player in Tmp:
      Players.append(Player.replace("\n", ""))
    return Players


def Generate_SELECT_QueryString(username):
   SELECT_QUERY = "SELECT username,wordlenumber,wordlescore FROM wordle_scores WHERE username = '" + username + "';"
   return SELECT_QUERY


def GetPlayerData(Player):
    #setup the DB connection
    conn = sqlite3.connect('wordleScores.db')
    #local scope data frame
    data = {'User': ['None'], 'WordleNumber': [0], 'WordleScore': [0]}
    WordleNumberDataFrame = pd.DataFrame(data=data)
    #get the table contents for users from the DB
    cursor = conn.execute(Generate_SELECT_QueryString(Player))
    #populate th data frame
    for row in cursor:
      WordleNumberDataFrame.loc[len(WordleNumberDataFrame.index)] = [row[0], row[1], row[2]]
    conn.close()
    return WordleNumberDataFrame


def GenerateScoreBoardDataFrame(Player):
    WeekWordleScoreIndex = 0
    WS=[7,7,7,7,7]
    #Obtain the player information from the Data Base
    PlayerData = GetPlayerData(Player)
    PlayerData = PlayerData.sort_values(by='WordleNumber', ascending=True)
    #Get the wordle scores for the given period
    for DataFrameRow in PlayerData.itertuples():
      if (DataFrameRow.WordleNumber == WN[0] or DataFrameRow.WordleNumber == WN[1] or 
          DataFrameRow.WordleNumber == WN[2] or DataFrameRow.WordleNumber == WN[3] or 
          DataFrameRow.WordleNumber == WN[4]):
        WS[WeekWordleScoreIndex] = DataFrameRow.WordleScore
        WeekWordleScoreIndex = WeekWordleScoreIndex + 1
      else:
        WS[WeekWordleScoreIndex] = 7
    #Populate the global Data Frame
    WordleScoreBoardDataFrame.loc[len(WordleScoreBoardDataFrame.index)] = [Player,WS[0],WS[1],WS[2],WS[3],WS[4],sum(WS)]
    return 0


def LoopThroughPlayers(Players):
    PlayerStatusInDB = 0
    for Player in Players:
      GenerateScoreBoardDataFrame(Player)
    return PlayerStatusInDB


def GenerateSortedScoreBoard():
    SortedScoreBoard = WordleScoreBoardDataFrame
    SortedScoreBoard = SortedScoreBoard.drop(index=(0))
    SortedScoreBoard = SortedScoreBoard.sort_values(by='Total', ascending=True)
    return SortedScoreBoard


def LogInformation(TheLogFile):
    FinalScoreBoard = GenerateSortedScoreBoard()
    #Print some info
    print(FinalScoreBoard)
    #Log the info
    LogFile = open(TheLogFile, "a")
    DateTime=GetDateandTime()
    LogFile.write("\n")
    LogFile.write('Score Board Date Generation: ' + DateTime[0] + ' --- ' + DateTime[1])
    LogFile.write("\n")
    LogFile.write(FinalScoreBoard.to_string())
    LogFile.close()
    return 0


def main():
   #Obtain the players from the external file
   Players = GetPlayersFromList('twitterUsers')
   #Loop through players
   LoopThroughPlayers(Players)
   #Log the information
   LogInformation('scoreboard')


if __name__ == "__main__":
    main()