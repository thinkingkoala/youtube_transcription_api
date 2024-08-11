## YouTube Transcription API

This API is designed to transcribe YouTube videos using an unofficial YouTube API to retrieve the transcript, and GPT-4o-mini to enhance punctuation.

### Instructions

To use the API, create a **.env** file with the following keys:

- **OPENAI_API_KEY**
- **SECRET_CODE** (This is the value for the authentication header)
- **PROXY** (Any proxy server, such as those from Webshare, that allows you to scrape YouTube. Note that YouTube often blocks IP addresses from common cloud providers to prevent scraping.)

Since transcripts can be very long, many of them may exceed the default GPT-4o-mini output limit. To handle this, the transcript is split into chunks and sent for improvement in parts. Although this process is asynchronous, it may still take a significant amount of time. Ensure your server or request timeout settings can accommodate this.

This code does not handle rate limits, which depend on your API tier. However, it works fine for most videos under 1.5 hours.

### Note

This project is **not actively maintained** and is intended primarily for educational purposes.
