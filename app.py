# Updated list in app.py
CHILDREN = [
    "gemini/gemini-1.5-flash", 
    "groq/llama3-8b-8192"
]

# ... inside call_titan function, change the final line to:
parent_res = await acompletion(
    model="gemini/gemini-1.5-flash", 
    messages=[{"role":"user","content":master_prompt}],
    api_key=os.environ["GEMINI_API_KEY"] # Explicitly tell it where the key is
)
