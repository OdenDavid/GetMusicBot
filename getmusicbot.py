import boto3
import os
import os.path as path
import io
import sys
import urllib.request
import json
import random
# Packages from layer
import tweepy
import requests
import moviepy.editor as mp
from googleapiclient.discovery import build

def lambda_handler(event, context):
    # TODO implement
    
    # Set working dir from file system
    file1 = '/mnt/root/Mentions_ID.txt' # This text files saves only the ID of the mention
    file2 = '/mnt/root/Respondtothis.txt' # This text file saves tweet info of mentions to be responded to
    
    # Twitter API and access keys
    API_KEY = os.environ['API_KEY']
    API_SECRET_KEY = os.environ['API_SECRET_KEY']
    ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
    SECRET_ACCESS_TOKEN = os.environ['SECRET_ACCESS_TOKEN']
    
    # Authenticate our application
    auth = tweepy.OAuthHandler(API_KEY, API_SECRET_KEY)
    auth.set_access_token(ACCESS_TOKEN, SECRET_ACCESS_TOKEN)
    
    api = tweepy.API(auth)
    
    try:
        api.verify_credentials()
    except Exception as e:
        print(e)
        
    # the screen name of this bot
    names = ["GetMusicBot"]
        
    # fetching the user
    user = api.get_user(screen_name=names[0])
    
    bot_id = user.id_str
    
    # Let's check for the last saved mention
    with open(file1, "r") as textfile:
        mention_id = textfile.read()
    
    # For the very first run the text file will be empty
    if mention_id == "":
        mention_id = 1
    
    # Fetch all mentions from the last mention i.e new mentions
    mentions = api.mentions_timeline(since_id=mention_id)
    
    # Loop through all mentions get their IDs return the last item in the list
    IDs = [mention.id_str for mention in mentions]
    
    print(IDs)
    
    if len(IDs) == 0: # If they are no new mentions
        pass
    else:
        # Let's save the last mentioned
        with open(file1, "w") as textfile:
            textfile.write(str(IDs[0]))
    
    for mention in mentions:
    
        if mention.in_reply_to_status_id is not None and mention.author.id != bot_id: # Check if it is reply to a tweet, and not from this bot
            
            try:
                tweet_above = api.get_status(mention.in_reply_to_status_id)
            except tweepy.errors.NotFound:
                continue
    
            # Check if there is a media
            if 'media_url_https' not in str(tweet_above): # If there is no media in the tweet at all
                pass # No media
            else:
                for medium in tweet_above.extended_entities['media']:
                    # Check for media type
                    if medium['type'] != 'video': # If the media type is not a video
                        pass # Not a video
                    else: # If media type is a video
                        for i in range(4):
                            if ".mp4" in medium['video_info']['variants'][i]['url']:
                                video_url = medium['video_info']['variants'][i]['url']
                                break
                            else:
                                continue
                            
                        with open(file2, "a") as textfile: # Text file to track who has tagged and should be responded to in append mode
                            textfile.write(mention.author.screen_name+"~"+mention.id_str+"~"+mention.text+"~"+video_url+"\n") # Append username, tweet id of reply, video url               
                
        else:
            pass
    
    
    # =========Download videos===========
    # AWS access tokens
    AWS_ACCESS_TOKEN = os.environ['AWS_ACCESS_TOKEN']
    AWS_SECRET = os.environ['AWS_SECRET']
    # Music recognition api key
    AUDIO_KEY = os.environ['AUDIO_KEY']
    
    # Read the content of textfile of mention history to be replied to
    with open(file2, "r") as textfile:
        contents = textfile.readlines()
    
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_TOKEN, aws_secret_access_key=AWS_SECRET) # Create AWS resource
    bucket = "get-music-bucket"
    s3_path_audio = "Audio"
    
    # Check for files within the audios folder in bucket
    s3_resource = boto3.resource("s3")
    s3_bucket = s3_resource.Bucket("get-music-bucket")
    audio_in_s3 = [f.key.split(s3_path_audio + "/")[1] for f in s3_bucket.objects.filter(Prefix=s3_path_audio).all()]
    
    # Check for files within the sys tmp folder
    filepath = '/tmp/'
    files_existing = os.listdir(filepath)
    
    # ========== Download and save video into sys path ==============
    #print(files_existing)
    for content in contents: # For as many replies we are to attend to
        url = content.split("~")[3] # Url of the video we want to recognize music
        save_video_as  = url.split('/')[4] # Video id so we don't save more than two
        
        # If video already exist in tmp folder
        if save_video_as+".mp4" in files_existing:
            pass
        # If audio already in s3, download it into tmp
        elif save_video_as+".mp3" in audio_in_s3:
            s3.download_file(Bucket=bucket, Key=f'{s3_path_audio}/{save_video_as}.mp3', Filename=f"{filepath}{save_video_as}.mp3")
        else:
            try:
                # Gets the file as an object, download it into tmp
                urllib.request.urlretrieve(url, f"{filepath}{save_video_as}.mp4")
            except Exception as e:
                print(f'File not saved', e)
                continue
                
    # ============ Now that file has been downloaded, Convert video to audio send to s3 =============== 
    s3_path_audio = "Audio" # Name of folder in s3 bucket
    url = "s3://get-music-bucket"# Url of s3 bucket
    
    recognized = {} # A dictionary to save info about recognized songs
    files_existing = os.listdir(filepath) # files currently in tmp
    for file in files_existing:
        if file == '' or file.split('.')[1] == 'mp3': # If file is empty or file is already an mp3, no need to convert
            pass
        else:
            # Convert video to audio, save to tmp
            videofilepath = f"{filepath}{file}"
            audiofilepath = f"{filepath}{file.split('.mp4')[0]}.mp3"
           
            clip = mp.VideoFileClip(videofilepath)
            clip.audio.write_audiofile(audiofilepath)
            
            # Now we are done converting, upload to s3
            s3_resource.Bucket(bucket).upload_file(audiofilepath, f"{s3_path_audio}/{file.split('.mp4')[0]}.mp3")
            
        
        # Now its time to recognize the audio we've converted
        if file == '' or file.split('.')[1] == 'mp4': # If file in tmp is empty or file is already an mp4, we can't recognize a video file
            pass
        else:
            
            print(file)
            data = {
                'api_token': AUDIO_KEY, # recognition API token
                'return': 'apple_music,spotify', # Return apple_music and spotify 
            }
            files = {
                'file': open(f"{filepath}{file}", "rb"),
            }
            result = requests.post('https://api.audd.io/', data=data, files=files) # API request
            try:
                s = result.text
                json_acceptable_string = s.replace("'", "\"")
                result = json.loads(json_acceptable_string)
            except ValueError:
                result = json.loads(s)
            except:
                api.update_status(f"{author} Hey, i'm sorry i couldn't do this.\n\nSomething is wrong with the video above, try another tweet", in_reply_to_status_id=tweet_id)
                continue
            
            if result['result'] == None: # if it wasn't able to recognize the audio
                r_data = "None"
            else:
                # Incase the song doesn't return any of the following links
                try:
                    sl = result['result']['song_link'] # link tn url
                except KeyError:
                    sl = None
                try:
                    am = result['result']['apple_music']['url'] # apple music url
                except KeyError:
                    am = None
                try:
                    so = result['result']['spotify']['external_urls']['spotify'] # spotify url
                except KeyError:
                    so = None 
                    
                
                r_data = [result['result']['artist'],\
                                result['result']['title'],\
                                sl,\
                                am,\
                                so]
            
            recognized[file.split('.')[0]] = [result['status'], r_data]
            
    # =============== Reply =================
    YOUTUBE_KEY = os.environ['YOUTUBE_KEY'] # Youtube API key 
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_KEY) # build a youtube client to interact with youtube data api
    
    message1 = "@{} Hey, i'm sorry i couldn't do this.\n\nYou can scold me now - ^ -"
    message2 = "@{} {}{}\n\n{} by {}\n\n{}"  #f"{author} {random.choice(messages)}\n\n{use[1][1]} by {use[1][0]}\n\n{link}"
    
    # Read the content of textfile of mention history to be replied to
    with open(file2, "r") as textfile:
        contents = textfile.readlines()

    for content in contents: # For as many replies we are to attend to
        author = content.split("~")[0] # the username of the user who tagged
        tweet_id = content.split("~")[1] # the id of the tweet the user tweeted, we'd use when replying
        text = content.split("~")[2] # the text in the user tweet, we want to know if they want apple music or spotify
        video_id = content.split("~")[3].split('/')[4] # the id of the video to be recognized
        
        messages  = ["I rock, find your song link below\n", "Too easy\n", "Here you go\n", "Not a problem\n", "Look what i found\n", "Happy listening\n"]
        
        # what response?
        use = recognized[str(video_id)]
        
        print(author, tweet_id, text, video_id)
        try:
            print("Attempting to reply")
            if use[1] == "None":
                api.update_status(message1.format(author), in_reply_to_status_id=tweet_id)
                print("Replied fine")
            else:
                link = use[1][2]
                add = ""
                if "spotify" in text.lower():
                    link = use[1][4] # link to the song on spotify
                    if link == None:
                        add = "But unfortunately this song isn't on spotify"
                    else:
                        pass
                elif "apple_music" in text.lower() or "apple music" in text.lower():
                    link = use[1][3] # link to the song on apple music
                    if link == None:
                        add = "But unfortunately this song isn't on apple music"
                    else:
                        pass
                else:
                    req = youtube.search().list(q=f"{use[1][1]} {use[1][0]}", part='snippet', type='video', maxResults=1)
                    res = req.execute()
                    link = f"https://www.youtube.com/watch?v={res['items'][0]['id']['videoId']}"
                    
                api.update_status(message2.format(author, random.choice(messages), add, use[1][1], use[1][0], link), in_reply_to_status_id=tweet_id)
                print("Replied fine")
        except Exception as e:
            print(e)

            
    # After all replies have been attended to
    #open(file2, "w").close() # clear the content of the text file, so we don't reply to people twice even though that isn't possible
    