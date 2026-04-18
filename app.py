import streamlit as st
import asyncio
from litellm import acompletion
import edge_tts
import base64

# TITAN CHILD MODELS
CHILDREN = [
    "gpt-4o-mini", 
    "claude-3-haiku-20240307", 
    "gemini/gemini-1.5-flash", 
    "groq/llama3-8b-8192"
]

async def call_titan(prompt):
    # ORCHESTRATION: Ask all children at once
    tasks = [acompletion(model=m, messages=[{"role":"user","content":prompt}]) for m in CHILDREN]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # FILTERING: Get successful answers
    valid_answers = [r.choices[0].message.content for r in responses if not isinstance(r, Exception)]
    
    # SYNTHESIS: Titan (The Parent) merges the best points
    context = "\n---\n".join(valid_answers)
    master_prompt = f"User: {prompt}\n\nReview these AI answers and provide the single best verdict:\n{context}"
    
    parent_res = await acompletion(model="gemini/gemini-1.5-flash", messages=[{"role":"user","content":master_prompt}])
    return parent_res.choices[0].message.content

# --- UI INTERFACE ---
st.title("TITAN: The Parent AI")
user_input = st.chat_input("Command Titan...")

if user_input:
    with st.spinner("Titan is consulting the children..."):
        final_answer = asyncio.run(call_titan(user_input))
        st.write(f"**Titan:** {final_answer}")
        
        # SPEECH GENERATION (FREE)
        communicate = edge_tts.Communicate(final_answer, "en-US-GuyNeural")
        asyncio.run(communicate.save("out.mp3"))
        
        # Play audio in browser
        with open("out.mp3", "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            st.markdown(f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}">', unsafe_url_provided=True)
          
