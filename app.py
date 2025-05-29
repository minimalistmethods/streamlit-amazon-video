import streamlit as st
from openai import OpenAI
from elevenlabs.client import ElevenLabs
import os
from moviepy.editor import ImageClip, VideoFileClip, AudioFileClip, concatenate_videoclips

# Set your API keys via Streamlit Secrets or text inputs (for dev only)
openai_api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else st.text_input("Enter OpenAI API Key", type="password")
eleven_api_key = st.secrets["ELEVEN_API_KEY"] if "ELEVEN_API_KEY" in st.secrets else st.text_input("Enter ElevenLabs API Key", type="password")

st.title("Amazon Product Video Generator")

# Step 1: Input Fields
amazon_url = st.text_input("Paste your Amazon product link:")

default_product_title = "Product Review"
product_title = st.text_input("Enter product title:", value=default_product_title)

features = st.text_area("Enter product features (one per line):", value="easy to use")
feature_list = [f.strip() for f in features.split('\n') if f.strip()]

script_type = st.radio("Choose script type:", ["review", "demo"])

# Step 2: Generate Script
if st.button("Generate Script"):
    client = OpenAI(api_key=openai_api_key)

    if script_type == "review":
        user_prompt = f"""
Write a 1-minute first-person **product review** script for the product titled '{product_title}'.
The script should describe before and after using the product.
Start with a unique, conversational intro.
Avoid section labels.
Make it at least one minute (~150–180 words).
"""
    else:
        user_prompt = f"""
Write a 1-minute first-person **product demo** script for the product titled '{product_title}'.
Walk the viewer through how to use the product in real time.
Use a friendly tone.
Make it at least one minute (~150–180 words).
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You write product scripts."},
            {"role": "user", "content": user_prompt}
        ]
    )

    script = response.choices[0].message.content
    st.session_state["script"] = script
    st.success("Script generated!")
    st.text_area("Generated Script", value=script, height=200)

# Step 3: Generate Voiceover
if "script" in st.session_state and st.button("Generate Voiceover"):
    el_client = ElevenLabs(api_key=eleven_api_key)

    audio_stream = el_client.text_to_speech.convert(
        voice_id="uYXf8XasLslADfZ2MB4u",
        model_id="eleven_monolingual_v1",
        text=st.session_state["script"],
        output_format="mp3_44100_128"
    )

    with open("review_audio.mp3", "wb") as f:
        for chunk in audio_stream:
            f.write(chunk)

    st.audio("review_audio.mp3")
    st.success("Voiceover created!")

# Step 4: Upload Images/Videos
uploaded_files = st.file_uploader("Upload images or videos", accept_multiple_files=True, type=["jpg", "jpeg", "png", "mp4", "mov"])

# Step 5: Generate Final Video
if uploaded_files and st.button("Generate Final Video"):
    clips = []
    num_files = len(uploaded_files)
    duration_per_clip = max(3, 60 / num_files)

    for uploaded_file in uploaded_files:
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        with open(uploaded_file.name, "wb") as f:
            f.write(uploaded_file.read())

        if ext in ['.jpg', '.jpeg', '.png']:
            clip = ImageClip(uploaded_file.name).set_duration(duration_per_clip).resize(width=720)
        elif ext in ['.mp4', '.mov']:
            clip = VideoFileClip(uploaded_file.name).subclip(0, duration_per_clip).resize(width=720)
        else:
            continue
        clips.append(clip)

    final_clip = concatenate_videoclips(clips, method="compose")
    final_audio = AudioFileClip("review_audio.mp3")
    final_video = final_clip.set_audio(final_audio)

    final_video.write_videofile("final_review_video.mp4", fps=24, audio_codec='aac')
    st.video("final_review_video.mp4")
    st.success("Final video generated!")
