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

# the screen name of this bot
names = ["GetMusicBot"]
  
# fetching the user
user = api.get_user(screen_name=names[0])

bot_id = user.id_str

mention_id = 1

message = "This is a reply to you @{}"

while True:
    mentions = api.mentions_timeline(since_id=mention_id)
    for mention in mentions:
        #print("Bro what's good!")
        #print(f"{mention.author.screen_name} - {mention.text}")
        mention_id = mention.id
        if mention.in_reply_to_status_id is not None and mention.author.id != bot_id: # Check if it reply to a tweet, and not from this bot
            
            # 'entities': {'description': {'urls': []}}
            # 'media_url_https': 'https://pbs.twimg.com/media/FXGjNkXXgAEmixR.jpg'
            #print(mention)
            tweet_above = api.get_status(mention.in_reply_to_status_id)
            print(tweet_above)
            if 'media_url_https' not in str(tweet_above): # If there is no media in the tweet at all
                pass # No media
            else:
                for medium in tweet_above.extended_entities['media']:
                    if medium['type'] != 'video': # If the media type is not a video
                        pass # Not a video
                    else:
                        print("A video")
                        video_url = medium['video_info']['variants'][1]['url']

                        with open("Mentions.txt", "a") as textfile:
                            textfile.write(mention.author.screen_name+":"+mention.id_str+":"+video_url)

            """likelytexts = ["spotify", "apple music", "apple_music"]

            if any(text in mention.text.lower().replace("@getmusicbot", "") for text in likelytexts):
                print(test.lower().replace("@getmusicbot", ""))
            
            
            try:
                print("Attempting to reply")
                api.update_status(message.format(mention.author.screen_name), in_reply_to_status_id=mention.id_str)
                print("Replied fine")
            except Exception as e:
                print(e)"""
        else:
            pass
    time.sleep(15)