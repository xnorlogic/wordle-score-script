# wordle-score-script
Gather Wordle Scores for specific users from Twitter. The users are stored in t the twitterUsers file, it should be enough to add the Twitter user name to the list in order to gather the data.
Dependencies:
  - Twitter API BEARER_TOKEN (for now you need to get a BEARER_TOKEN from twitter dev account and add to your environment variables)
  - json
  - pandas
  - requests
  - sqlite3

Notes:
  1 It currently searched for the word "wordle" within the twitt and then performs some string splits, this may not be robust enough for a bunch of cases, so just share the score     as it comes from the share button from the Wordle game.
