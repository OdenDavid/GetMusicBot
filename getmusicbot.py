import tweepy
import time

with open("Keys.txt") as f:
    all_keys = f.readlines()

API_KEY = all_keys[0].split(":")[1].strip()
API_SECRET_KEY = all_keys[1].split(":")[1].strip()
ACCESS_TOKEN = all_keys[2].split(":")[1].strip()
SECRET_ACCESS_TOKEN = all_keys[3].split(":")[1].strip()

# Authenticate our application
auth = tweepy.OAuthHandler(API_KEY, API_SECRET_KEY)
auth.set_access_token(ACCESS_TOKEN, SECRET_ACCESS_TOKEN)

api = tweepy.API(auth)

try:
    api.verify_credentials()
    print("All set")
except Exception as e:
    print(e)


#bot_id = int(api.me().id_str)

while True:
    mentions = api.mentions_timeline()
    for mention in mentions:
        print("Bro what's good!")
        print(f"{mention.author.screen_name} - {mention.text}")

    time.sleep(15)