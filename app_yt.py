import streamlit as st
import re
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi

# Default prompt
default_prompt = """
# Mission

You are a learning, teaching and analysis bot extract key ideas, concepts, and actionable frameworks or methodologies from YouTube video transcripts.

# Context

The context involves the summarization of YouTube video transcripts for the purposes of practical education, focusing on the key ideas, concepts, and actionable frameworks or methodologies. You are expected to be comprehensive, accurate, and concise.

# Rules

Please read through the transcript carefully. Your task is to extract the key lessons, important details, and relevant specifics, and present them in a well-organized markdown format.

Look specifically for:
- ⁠  ⁠Key concepts, theories, mental models, frameworks, methods and ideas
- ⁠  ⁠Illuminating anecdotes, examples or stories that illustrate the main points
- ⁠  ⁠Specific action items, exercises, or how-to steps the viewer can take
- ⁠  ⁠Relevant details that add depth and context to the key lessons

# Expected Input

You will receive a YouTube video transcript.

<transcript>
{transcript}
</transcript>

# Output Format

1.⁠ ⁠Video Overview:
   - Provide a high-level executive summary of the video.

2.⁠ ⁠Key Topics and Lessons:
   - List the key topics and lessons covered in the video with brief descriptions.

3.⁠ ⁠Key Lessons/Topics Details:
   - Concepts, Theory, Mental Models, Frameworks, Methods, Ideas, and Required Background Knowledge:
     - Describe the main concepts, theories, mental models, frameworks, methods, and ideas introduced in the video.
     - Include any necessary background knowledge required to understand these elements.
  
   - Specific Anecdotes or Stories:
     - Summarize any specific anecdotes or stories mentioned in the video that illustrate the key points.

   - Action Items, Key Takeaways, and How-to's:
     - List actionable items and key takeaways from the video.
     - Provide step-by-step instructions or guidance on how to implement the advice or lessons from the video.

IMPORTANT!!! Output your response within <markdown></markdown> tags

---

Example Format:

<markdown>

Video Overview:
Provide a high-level executive summary of the video.

Key Topics and Lessons:
- ⁠ ⁠Topic 1: Brief description
- ⁠  ⁠Topic 2: Brief description
- ⁠  ⁠...

Key Lessons/Topics Details:

- ⁠  ⁠Concepts, Theory, Mental Models, Frameworks, Methods, Ideas, and Required Background Knowledge:
  - Concept 1: Description
  - Theory 1: Description
  - Mental Model 1: Description
  - Framework 1: Description
  - ...

- ⁠  ⁠Specific Anecdotes or Stories:
  - Anecdote 1: Short summary
  - Anecdote 2: Short summary
  - ...

- ⁠  ⁠Action Items, Key Takeaways, and How-to's:
  - Action Item 1: Step-by-step instructions
  - Action Item 2: Step-by-step instructions
  - …

</markdown>

"""

# Function to get YouTube video transcript
def get_youtube_transcript(video_url):
    try:
        video_id = re.findall(r"v=([a-zA-Z0-9_-]+)", video_url)[0]
        print(video_id)
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([item['text'] for item in transcript_list])
        return transcript_text
    except Exception as e:
        st.error(f"Error fetching transcript: {str(e)}")
        return None

# Function to get key ideas using Google Gemini API
def get_key_ideas(transcript_text, api_key, prompt):
    print(transcript_text)
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    prompt = prompt.replace("{transcript}", transcript_text)
    try:
        response = model.generate_content(prompt)
        result = response.candidates[0].content.parts[0].text
        print(result)
        match = re.search(r'<markdown>(.*?)</markdown>', result, re.IGNORECASE | re.DOTALL)
        if match:
            key_ideas = match.group(1).strip()
        else:
            key_ideas = None
        return key_ideas
    except Exception as e:
        st.error(f"Error in Gemini API call: {str(e)}")
        return None

# Initialize session state variables
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = ''

if 'custom_prompt' not in st.session_state:
    st.session_state['custom_prompt'] = default_prompt

if 'transcript_text' not in st.session_state:
    st.session_state['transcript_text'] = ''

# Streamlit app
st.title("YouTube Lesson Extractor")

# Sidebar selection
page = st.sidebar.radio("Select Page", ("Home", "Prompt"))

if page == "Home":
    video_url = st.text_input("Enter YouTube video URL")
    if st.button("Extract Lessons"):
        lessons_placeholder = st.empty()
        progress_text = st.empty()
        
        # Getting transcript
        progress_text.warning("Getting Transcript...")
        transcript_text = get_youtube_transcript(video_url)
        st.session_state['transcript_text'] = transcript_text
        
        if transcript_text:
            # Extracting lessons
            progress_text.warning("Extracting Lessons...")
            key_ideas = get_key_ideas(transcript_text, st.session_state['api_key'], st.session_state['custom_prompt'])
            
            if key_ideas:
                progress_text.empty()
                lessons_placeholder.markdown(key_ideas)
            else:
                progress_text.error("Could not extract the lessons.")
        else:
            progress_text.error("Could not get the transcript.")

    # Sidebar for API key input at the bottom
    st.session_state['api_key'] = st.sidebar.text_input("Enter your Google Gemini API key", value=st.session_state['api_key'], key="api_key_input")

elif page == "Prompt":
    st.markdown('<span style="color:yellow;">**WARNING:** Make sure to mention &lt;transcript&gt;&lt;/transcript&gt; and &lt;markdown&gt;&lt;/markdown&gt; tags in the prompt. Press Save to apply changes.</span>', unsafe_allow_html=True)
    prompt = st.text_area("Edit the prompt below:", value=st.session_state['custom_prompt'], height=400)
    
    if st.button("Save"):
        st.session_state['custom_prompt'] = prompt
        st.success("Prompt saved!")