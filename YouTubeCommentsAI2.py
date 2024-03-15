import configparser
import openai
import re
import requests

# Read configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Set up OpenAI API credentials
openai.api_key = config['Credentials']['openai_api_key']

# Prompt the user for a YouTube link
youtube_link = input("Paste your YouTube link: ")

# Extract video ID from the YouTube link
match = re.search(r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?]+)', youtube_link)
if match:
    video_id = match.group(1)
else:
    print("Invalid YouTube link. Please provide a valid link.")
    exit()

# Construct the API request URL
api_key = config['Credentials']['youtube_api_key']
url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&key={api_key}&maxResults=10"

# Make the request using the requests library
response = requests.get(url)

# Display the response
comments = response.json()["items"]

# Extract comment texts
comment_texts = [comment["snippet"]["topLevelComment"]["snippet"]["textOriginal"] for comment in comments]

# Categorize comments using OpenAI API
categorized_comments = []
for text in comment_texts:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Classify the sentiment of the following comment: '{text}'\n\nPossible responses: Positive, Negative, Neutral"}
        ]
    )
    sentiment = response["choices"][0]["message"]["content"].strip()
    
    # Check for very positive emojis
    positive_emojis = ["❤️", "😂", "😘", "😭", "🤣", "🔥", "💙", "🙏", "😅", "🎉", "😁"]
    if any(emoji in text for emoji in positive_emojis):
        sentiment = "Positive"

    # Check for specific phrases
    positive_keywords = ["thank you", "love", "thanks", "thx", "love"]
    if any(keyword in text.lower() for keyword in positive_keywords):
        sentiment = "Positive"

    # Ensure sentiment is one of the three categories
    if sentiment not in ["Positive", "Negative", "Neutral"]:
        sentiment = "Neutral"
    
    categorized_comments.append((sentiment, text))

# Print categorized comments
category_counts = {}

for i, (sentiment, comment) in enumerate(categorized_comments, 1):
    print(f"Comment {i}: {sentiment} - {comment}")
    print()

    # Count the categories
    if sentiment in category_counts:
        category_counts[sentiment] += 1
    else:
        category_counts[sentiment] = 1

# Print the category counts
for category, count in category_counts.items():
    print(f"{category}: {count}")

# Check for zero positive or negative comments
positive_count = category_counts.get("Positive", 0)
negative_count = category_counts.get("Negative", 0)

if positive_count == 0 and negative_count == 0:
    print("YOU HAVE NO POSITIVE OR NEGATIVE COMMENTS")
else:
    # Calculate the ratio of positive to negative comments
    ratio = positive_count / negative_count if negative_count != 0 else float('inf')

    # Print GOOD VIBE, BAD VIBE, or NEUTRAL VIBE based on the ratio
    if ratio > 1:
        print("GOOD VIBE")
    elif ratio < 1:
        print("BAD VIBE")
    else:
        print("MID VIBE")
