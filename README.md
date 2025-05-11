### CONTENT WORKFLOW FOR SCRIPT TO YT VIDEO

## Here's what I have so far in this repo: 

~ Personal Assistant (Doesn't really do much yet, but essentially I hope to make this work together with the telegram bot to work on the videos)

~ Upload to Youtube: Best way I found is with upload-post.com. works better than looking for integrations that will take forever to test.

What's left is to sort out how the videos would be generated, where to store them and how to retreive them for youtube upload.

EDIT: I've sorted out the joining of videos, adding audio and subtitles with moviepy.

# Video Processing API

This Flask API provides an endpoint for joining multiple videos, adding voiceover audio, and generating subtitles.

## Endpoint: `/join-videos`

### Method: POST

### Request Body (JSON)

```json
{
    "video_urls": [
        "https://example.com/video1.mp4",
        "https://example.com/video2.mp4",
        ...
    ],
    "script": "Optional text for voiceover and subtitles"
}
```

### Parameters

- `video_urls` (required): Array of URLs to the videos you want to join
- `script` (optional): Text that will be converted to voiceover audio and displayed as subtitles

### Features

1. **Video Processing**
   - Joins multiple videos in sequence
   - Adds a 1-second fade-in effect to each video
   - Adds a 2-second fade-out effect to the final video
   - Trims the final video to match audio duration (if script is provided)

2. **Audio Generation** (if script is provided)
   - Converts the script to voiceover using gTTS (Google Text-to-Speech)
   - Synchronizes the video duration with the audio

3. **Subtitle Generation** (if script is provided)
   - Splits the script into sentences
   - Creates subtitles with the following features:
     - Text wrapping for long sentences (40 characters per line)
     - Centered text positioning
     - White text on transparent background
     - Dynamic timing based on sentence length (135 words per minute)
     - Minimum display duration of 2 seconds per subtitle

### Response

Returns a video file stream with the following headers:
- Content-Type: video/mp4
- Content-Disposition: attachment; filename=final_output.mp4

### Error Handling

The API returns appropriate error responses for:
- Missing video URLs
- Failed video downloads
- Processing errors

### Example Usage

```python
import requests

url = "http://localhost:5000/join-videos"
data = {
    "video_urls": [
        "https://example.com/video1.mp4",
        "https://example.com/video2.mp4"
    ],
    "script": "This is an example script. It will be converted to voiceover and displayed as subtitles."
}

response = requests.post(url, json=data)
if response.status_code == 200:
    with open("output.mp4", "wb") as f:
        f.write(response.content)
```

### Setting up ngrok for Development

1. **Install ngrok**
   - Download ngrok from [https://ngrok.com/download](https://ngrok.com/download)
   - Extract the downloaded file
   - Sign up for a free ngrok account to get your authtoken

2. **Configure ngrok**
   ```bash
   # Add your authtoken (replace with your actual token)
   ngrok config add-authtoken your_auth_token_here
   ```

3. **Start your Flask server**
   ```bash
   python app.py
   ```

4. **Start ngrok tunnel**
   ```bash
   ngrok http 5000
   ```

5. **Using the ngrok URL**
   - After starting ngrok, you'll see a URL like `https://xxxx-xx-xx-xxx-xx.ngrok.io`
   - Use this URL instead of localhost in your requests:

   ```python
   import requests

   # Replace with your ngrok URL
   ngrok_url = "https://xxxx-xx-xx-xxx-xx.ngrok.io"
   url = f"{ngrok_url}/join-videos"
   
   data = {
       "video_urls": [
           "https://example.com/video1.mp4",
           "https://example.com/video2.mp4"
       ],
       "script": "This is an example script. It will be converted to voiceover and displayed as subtitles."
   }

   response = requests.post(url, json=data)
   if response.status_code == 200:
       with open("output.mp4", "wb") as f:
           f.write(response.content)
   ```

   Note: The ngrok URL changes each time you restart ngrok unless you have a paid account.

### Notes

- The API creates temporary files during processing and automatically cleans them up
- Video processing uses the following settings:
  - Codec: libx264
  - Audio codec: aac
  - FPS: 24
  - Preset: ultrafast
- Subtitles are positioned at the bottom of the video with proper spacing and timing
- The API handles resource cleanup automatically, including temporary files and video clips 

Cheers. 
