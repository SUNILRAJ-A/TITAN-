import streamlit as st
import asyncio
from litellm import acompletion
import edge_tts
import base64
import os

# --- TITAN CONFIGURATION ---
# The four children Titan will manage
CHILDREN = [
    "gpt-4o-mini", 
    "claude-3-haiku-20240307", 
    "gemini/gemini-1.5-flash", 
    "groq/llama3-8b-8192"
]

async def call_titan(prompt):
    # 1. ORCHESTRATION: Ask all 4 children at the same time
    tasks = [
        acompletion(
            model=m, 
            messages=[{"role":"user","content":prompt}],
            timeout=10 # If one child is slow, Titan won't wait forever
        ) for m in CHILDREN
    ]
    
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 2. FILTERING: Collect only the successful answers
    valid_answers = []
    for i, res in enumerate(responses):
        if not isinstance(res, Exception):
            valid_answers.append(f"Answer from {CHILDREN[i]}:\n{res.choices[0].message.content}")
        else:
            st.warning(f"Child {CHILDREN[i]} is not responding. Skipping...")
    
    if not valid_answers:
        return "Titan's children are currently unreachable. Check your API credits."

    # 3. SYNTHESIS: Titan (The Parent) reviews and merges
    context = "\n---\n".join(valid_answers)
    master_prompt = f"""
    You are Titan, the Parent AI. 
    User Question: {prompt}
    
    Review these 4 responses from your children and merge them into one perfect, 
    highly accurate, and professional final answer:
    {context}
    """
    
    parent_res = await acompletion(
        model="gemini/gemini-1.5-flash", 
        messages=[{"role":"user","content":master_prompt}]
    )
    return parent_res.choices[0].message.content

# --- UI INTERFACE ---
st.set_page_config(page_title="TITAN AI", page_icon="⚡")
st.title("TITAN: The Quad-Core Parent")

# --- API KEY MAPPING ---
# This maps your Streamlit Secrets to the system environment
try:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    st.error("Missing Keys! Ensure all 4 keys are in your Streamlit Secrets.")
    st.stop()

user_input = st.chat_input("Command Titan...")

if user_input:
    st.chat_message("user").write(user_input)
    
    with st.spinner("Titan is consulting the 4 children..."):
        try:
            final_answer = asyncio.run(call_titan(user_input))
            st.chat_message("assistant").write(final_answer)
            
            # SPEECH GENERATION
            communicate = edge_tts.Communicate(final_answer, "en-US-GuyNeural")
            asyncio.run(communicate.save("out.mp3"))
            
            with open("out.mp3", "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                st.markdown(f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}">', unsafe_url_provided=True)
                
        except Exception as e:
            st.error(f"Titan encountered a system error: {str(e)}")
            
