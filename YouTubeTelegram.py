import configparser
import openai
import re
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Read configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Set up OpenAI API credentials
openai.api_key = config['Credentials']['openai_api_key']

# Telegram bot token
BOT_TOKEN = config['Credentials']['telegram_bot_token']

# Define the start command
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Welcome! Please provide a YouTube link to analyze.")

# Define the analyze command
def analyze(update: Update, context: CallbackContext) -> None:
    video_id = update.message.text

    # Extract video ID from the YouTube link
    match = re.search(r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?]+)', video_id)
    if match:
        video_id = match.group(1)
    else:
        update.message.reply_text("Invalid YouTube link. Please provide a valid link.")
        return

    # Construct the API request URL
    api_key = config['Credentials']['youtube_api_key']
    url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&key={api_key}&maxResults=20"

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
    result_message = ""
    for i, (sentiment, comment) in enumerate(categorized_comments, 1):
        result_message += f"Comment {i}: {sentiment} - {comment}\n\n"

    # Print the category counts
    category_counts = {}
    for sentiment, count in categorized_comments:
        if sentiment in category_counts:
            category_counts[sentiment] += 1
        else:
            category_counts[sentiment] = 1

    # Check for zero positive or negative comments
    positive_count = category_counts.get("Positive", 0)
    negative_count = category_counts.get("Negative", 0)

    if positive_count == 0 and negative_count == 0:
        result_message += "YOU HAVE NO POSITIVE OR NEGATIVE COMMENTS\n"
    else:
        # Calculate the ratio of positive to negative comments
        ratio = positive_count / negative_count if negative_count != 0 else float('inf')

        # Determine VIBE based on the ratio
        if ratio > 1:
            result_message += "GOOD VIBE\n"
        elif ratio < 1:
            result_message += "BAD VIBE\n"
        else:
            result_message += "MID VIBE\n"

    update.message.reply_text(result_message)

# Set up the Telegram bot
def main() -> None:
    updater = Updater(BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Define handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, analyze))
    dp.add_handler(CommandHandler('analyze', analyze))

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
