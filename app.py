from flask import Flask, request, send_file, jsonify, Response
import os
import requests
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, ImageClip, CompositeVideoClip
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import io
import re
import textwrap

app = Flask(__name__)

# Ensure temp directory exists
TEMP_DIR = os.path.join(os.path.dirname(__file__), 'temp')
os.makedirs(TEMP_DIR, exist_ok=True)

def create_text_image(text, size, fontsize=30, max_chars_per_line=40):
    # Create a new image with a black background
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Use default font
    try:
        font = ImageFont.truetype("arial.ttf", fontsize)
    except:
        font = ImageFont.load_default()
    
    # Wrap text
    wrapped_text = textwrap.fill(text, width=max_chars_per_line)
    lines = wrapped_text.split('\n')
    
    # Calculate total text height
    line_height = fontsize + 5  # 5 pixels padding between lines
    total_height = line_height * len(lines)
    
    # Calculate position to center the text
    y = size[1] - total_height - 20  # 20 pixels from bottom
    
    # Draw each line
    for i, line in enumerate(lines):
        text_width = draw.textlength(line, font=font)
        x = (size[0] - text_width) // 2
        draw.text((x, y + (i * line_height)), line, font=font, fill='white')
    
    # Save to temporary file
    temp_path = os.path.join(TEMP_DIR, f'temp_text_{hash(text)}.png')
    img.save(temp_path)
    return temp_path

def split_script_into_sentences(script):
    # Split script into sentences (basic implementation)
    sentences = re.split(r'[.!?]+', script)
    return [s.strip() for s in sentences if s.strip()]

def estimate_sentence_duration(sentence, base_duration):
    # Estimate duration based on sentence length
    # Assuming average reading speed of 150 words per minute
    words = len(sentence.split())
    duration = (words / 135) * 60  # Convert to seconds
    return max(duration, base_duration)  # Ensure minimum duration

@app.route('/join-videos', methods=['POST'])
def join_videos():
    data = request.get_json()
    video_urls = data.get('video_urls')
    script = data.get('script', '')

    if not video_urls:
        return jsonify({'error': 'No video URLs provided'}), 400

    try:
        video_paths = []
        clips = []

        # Download videos and create clips
        for idx, url in enumerate(video_urls):
            video_path = os.path.join(TEMP_DIR, f"video{idx}.mp4")
            r = requests.get(url, stream=True)
            if r.status_code != 200:
                return jsonify({'error': f"Failed to download video: {url}"}), 400
            with open(video_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            video_paths.append(video_path)
            
            # Create clip
            clip = VideoFileClip(video_path)
            # Add fade in effect (1 second duration)
            clip = clip.fadein(1)
            clips.append(clip)

        # Concatenate video clips
        final_clip = concatenate_videoclips(clips)

        # Add audio and subtitles if script is provided
        if script:
            # Generate voiceover
            tts = gTTS(script)
            audio_path = os.path.join(TEMP_DIR, "voiceover.mp3")
            tts.save(audio_path)

            # Create audio clip
            audio_clip = AudioFileClip(audio_path)
            
            # Trim video to match audio duration if video is longer
            if final_clip.duration > audio_clip.duration:
                final_clip = final_clip.subclip(0, audio_clip.duration + 3)
                # Add fade out effect (2 seconds duration)
                final_clip = final_clip.fadeout(2)

            # Set the audio
            final_clip = final_clip.set_audio(audio_clip)

            # Create subtitles
            sentences = split_script_into_sentences(script)
            
            # Calculate timing for each sentence
            current_time = 0
            text_clips = []
            for sentence in sentences:
                # Estimate duration for this sentence
                duration = estimate_sentence_duration(sentence, 2.0)  # Minimum 2 seconds
                
                # Create text image
                text_image_path = create_text_image(sentence, final_clip.size)
                
                # Create image clip
                img_clip = ImageClip(text_image_path)
                img_clip = img_clip.set_duration(duration)
                img_clip = img_clip.set_start(current_time)
                
                text_clips.append(img_clip)
                current_time += duration
            
            # Combine video with subtitles
            final_clip = CompositeVideoClip([final_clip] + text_clips)

        # Create a BytesIO buffer for streaming
        buffer = io.BytesIO()
        
        # Write to temporary file
        temp_output = os.path.join(TEMP_DIR, 'final_output.mp4')
        final_clip.write_videofile(
            temp_output,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile=os.path.join(TEMP_DIR, 'temp-audio.m4a'),
            remove_temp=True,
            fps=24,
            preset='ultrafast'
        )
        
        # Read the file into buffer
        with open(temp_output, 'rb') as f:
            buffer.write(f.read())
        
        # Reset buffer position
        buffer.seek(0)

        # Clean up clips
        for clip in clips:
            clip.close()
        final_clip.close()
        if script:
            audio_clip.close()
            os.remove(audio_path)
            for clip in text_clips:
                clip.close()
            # Clean up text images
            for file in os.listdir(TEMP_DIR):
                if file.startswith('temp_text'):
                    try:
                        os.remove(os.path.join(TEMP_DIR, file))
                    except:
                        pass

        # Clean up temporary files
        for path in video_paths:
            try:
                os.remove(path)
            except:
                pass
        try:
            os.remove(temp_output)
        except:
            pass

        # Return the video as a stream
        return Response(
            buffer,
            mimetype='video/mp4',
            headers={
                'Content-Disposition': 'attachment; filename=final_output.mp4'
            }
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up any remaining temporary files
        for file in os.listdir(TEMP_DIR):
            try:
                os.remove(os.path.join(TEMP_DIR, file))
            except:
                pass

if __name__ == '__main__':
    app.run(debug=True, port=5000)
