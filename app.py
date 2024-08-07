from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import re
from openai import OpenAI
from openai import OpenAIError
import os
from auth import require_custom_authentication
from dotenv import load_dotenv
import logging

load_dotenv()

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up OpenAI API key
client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def get_youtube_id(url):
    # Extract video ID from YouTube URL
    video_id = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    return video_id.group(1) if video_id else None

def process_transcript(video_id):
    proxy_address=os.environ.get("PROXY")
    transcript = YouTubeTranscriptApi.get_transcript(video_id, proxies = {"https": proxy_address})
    full_text = ' '.join([entry['text'] for entry in transcript])
    return full_text

def improve_text_with_gpt4(text):
    if not client.api_key:
        return "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """You are a helpful assistant that improves text formatting and adds punctuation. 
                 You will be given texts from YouTube transcriptions and your task is to apply good formatting.
                 Do NOT modify individual words."""},
                {"role": "user", "content": f"{text}"}
            ]
        )
        return response.choices[0].message.content
    except OpenAIError as e:
        return f"OpenAI API error: {str(e)}"

@app.route('/transcribe', methods=['POST'])
@require_custom_authentication
def transcribe():
    youtube_url = request.json.get('url')
    if not youtube_url:
        return jsonify({"error": "No YouTube URL provided"}), 400

    video_id = get_youtube_id(youtube_url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    try:
        logger.info(f"videoid = {video_id}")
        transcript_text = process_transcript(video_id)
        logger.info(f"text = {transcript_text}")
        improved_text = improve_text_with_gpt4(transcript_text)

        return jsonify({"result": improved_text})
    
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)