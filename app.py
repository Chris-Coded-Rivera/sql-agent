import os
from pathlib import Path
from langchain.agents import create_agent
# from langchain.runtime import get_runtime
from langgraph.store.memory import InMemoryStore
from dotenv import load_dotenv
from tools import execute_sql, RuntimeContext
import shutil

import gradio as gr
from gradio import ChatMessage

load_dotenv()

def process_document(file):
    """
    This function takes the uploaded file object, saves it, and returns a message.
    """
    if file is None:
        return "No file uploaded."

    # Define a directory to save uploaded files
    upload_dir = "uploaded_documents"
    os.makedirs(upload_dir, exist_ok=True)

    # Get the original file name and construct the destination path
    file_name = os.path.basename(file.name)
    destination_path = os.path.join(upload_dir, file_name)

    # Copy the temporary file to the desired location
    shutil.copy(file.name, destination_path)

    return f"Document '{file_name}' uploaded and saved to '{upload_dir}'."


def load_prompt(path):
    return Path(path).read_text(encoding="utf-8").strip()


SYSTEM_PROMPT = load_prompt("./prompts/system.txt")

tools = [
    {
    "name": "execute_sql", 
    "description": "Execute SQLite commands and return results",
    "func": execute_sql,
    "return_direct": False
}]

agent = create_agent(
    model="anthropic:claude-sonnet-4-5",
    system_prompt= SYSTEM_PROMPT,
    tools = tools,
    context_schema=RuntimeContext
)

db = None

# Gradio interface
def chat(db, message, history):
    for step in agent.stream({
        "messages": [
            {"role":"user", "content": message}
        ]},
    stream_mode="values"
    ):
        keys_to_keep = ["role", "content"]
        response = [{k: d[k] for k in keys_to_keep if k in d} for d in history]
    return response

# demo = gr.ChatInterface(
#     fn=chat,
#     title="🔍 Multi-Tool AI Agent",
#     description="Ask me anything — I can search HF models, get time, or use OpenAI!"
# )



with gr.Blocks() as demo:
    gr.Markdown("Upload your data to the agent and submit your query")
    upload_button = gr.UploadButton("Upload file")
    db = upload_button.upload(process_document, upload_button, str("uploaded file"))

    gr.ChatInterface(
    fn=chat_with_agent,
    title="🔍 Multi-Tool AI Agent",
    description="Ask me anything — I can search HF models, get time, or use OpenAI!"
)

demo.launch()