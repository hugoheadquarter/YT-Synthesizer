import streamlit as st
import re
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi

# Default prompt
default_prompt = """
# Mission

You are an expert teacher extracting key concepts/lessons and actionable frameworks/methodologies from educational video transcripts or book chapters. Your job is to provide a comprehensive, accurate and detailed summary of the content with a focus on practical application. This should replace needing to read the original content. 

# Rules

Please read through the text carefully. Your task is to extract a comprehensive, accurate and detailed summary of the content and to present them in a well-organized markdown format.

Look specifically for:
•⁠  ⁠Practical concepts and lessons 
•⁠  ⁠Specific anecdotes or stories that help explain a concept or lesson
•⁠  ⁠Specific actionable steps, how-tos or frameworks/methodologies

# Expected Input

You will receive the full text from the file.

<transcript>
{transcript}
</transcript>


# Output Format (in markdown)

1.⁠ ⁠Summary:
   - Provide a high-level executive summary of the content including the overall topics, purpose and outcomes expected

2.⁠ ⁠Topics:
   - List the key topics, concepts and/or lessons in concise bullet points including specific outcomes for the learner

3.⁠ ⁠Content
•⁠  ⁠provide a comprehensive, accurate and detailed summary of ALL content with a focus on practical application for the learner
•⁠  ⁠include all relevant detail from the content 
 - Outline specific anecdotes or stories that support key concepts or lessons

4.⁠ ⁠Action Items
 - Provide a comprehensive list of specific action items, how-to steps or frameworks for applying the knowledge within the content

Go over your output and ensure accuracy and perfection, it is very important that this is an A grade output suitable for educated individuals with limited time but need for detail/accuracy.

IMPORTANT!!! Output your response within <markdown></markdown> tags.

Example Format:

<markdown>

*Summary:*
Provide a high-level executive summary.

*Topics:*
•⁠  ⁠Topic/lesson 1
•⁠  ⁠Topic/lesson 2
•⁠  ⁠...

*Content:*
  - Concept, lesson, insight or topic in comprehensive detail including any related anecdotes/stories
  - ...

*Action items:*

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
        st.write(response)
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
