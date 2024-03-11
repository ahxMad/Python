import re
import requests
import configparser
import openai


#Read Configuration from the config file
config = configparser.ConfigParser()
config.read('config.ini')

#Setup OpenAI API Key
openai.api_key = config['APIKEYS']['openai_api_key']

#Prompt the user to enter the link of the Youtube Video
youtube_link = input("Enter the link of the Youtube Video: ")

extracted_id = re.search(r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?]+)', youtube_link)
if extracted_id:
    video_id = extracted_id.group(1)
else:
    print("Invalid Youtube Link")
    exit()

#Get the API Key from the config file
api_key = config['APIKEYS']['youtube_api_key']
url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&key={api_key}&maxResults=100"

#Make request using the request library
response = requests.get(url)

#Get the comments from the response
comments = response.json()["items"]

# Extract comment texts
comment_texts = [comment["snippet"]["topLevelComment"]["snippet"]["textOriginal"] for comment in comments]

#Categorize the comments with OpenAI's GPT-3.5
