from flask import Flask, render_template, request, flash, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import os
from moviepy.editor import VideoFileClip, AudioFileClip
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS

app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["ALLOWED_EXTENSIONS"] = {"mp4", "avi", "mov", "mkv"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

def extract_audio(video_path):
    try:
        audio_path = os.path.splitext(video_path)[0] + ".wav"
        clip = VideoFileClip(video_path)
        clip.audio.write_audiofile(audio_path)
        return audio_path
    except Exception as e:
        print(f"Error extracting audio from video: {e}")
        return None

def transcribe_audio(audio_file):
    try:
        r = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio_text = r.listen(source)
            try:
                rec_text = r.recognize_google(audio_text)
                print("Converting audio to text...")
            except:
                print("Run again...")
            print("Transcribing Done Successfully!")
        return rec_text
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None

def translate_text(rec_text, language_to_dub):
    try:
        translator = Translator()
        translated_text = translator.translate(rec_text, dest=language_to_dub).text
        print("Translation Done Successfully!")
        return translated_text
    except Exception as e:
        print(f"Error translating text: {e}")
        return None

def text_to_audio(translated_text, output_audio_file, language_to_dub):
    try:
        translated_audio = gTTS(translated_text, lang=language_to_dub)
        translated_audio.save(output_audio_file)
        print("Created translated audio successfully!")
        return output_audio_file
    except Exception as e:
        print(f"Error creating audio from text: {e}")
        return None

def merge_audio_to_video(video_file_path, output_audio_file):
    try:
        video_clip = VideoFileClip(video_file_path)
        audio_clip = AudioFileClip(output_audio_file)
        final_clip = video_clip.set_audio(audio_clip)
        dubbed_video_path = os.path.join(app.config["UPLOAD_FOLDER"], "Dubbed_video.mp4")
        final_clip.write_videofile(dubbed_video_path)
        print("Dubbed Video saved!")
        return dubbed_video_path
    except Exception as e:
        print(f"Error saving audio to video: {e}")
        return None




@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST" and "video" in request.files:
        uploaded_video = request.files["video"]
        language_to_dub = request.form["language"]

        if uploaded_video and allowed_file(uploaded_video.filename):
            filename = secure_filename(uploaded_video.filename)
            video_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            uploaded_video.save(video_path)

            audio_path = extract_audio(video_path)

            if audio_path:
                rec_text = transcribe_audio(audio_path)
                if rec_text:
                    translated_text = translate_text(rec_text, language_to_dub)
                    if translated_text:
                        output_audio_file = os.path.join(app.config["UPLOAD_FOLDER"], "translated_audio_file.wav")
                        text_to_audio(translated_text, output_audio_file, language_to_dub)
                        dubbed_video_path = merge_audio_to_video(video_path, output_audio_file)
                        if dubbed_video_path:
                            flash(f"Video uploaded successfully! Audio extracted, translated, and dubbed. Dubbed Video: {dubbed_video_path}", "success")
                        else:
                            flash("Error creating dubbed video. Please try again.", "danger")
                    else:
                        flash("Error translating text. Please try again.", "danger")
                else:
                    flash("Error transcribing audio. Please try again.", "danger")
            else:
                flash("Error extracting audio. Please try again.", "danger")

            return redirect(url_for("index"))

        flash("Invalid file format. Please upload a valid video file.", "danger")

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
