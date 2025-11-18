import os
from pathlib import Path
from langchain.agents import create_agent
from langchain_community.utilities import SQLDatabase
from langgraph.store.memory import InMemoryStore
from dotenv import load_dotenv
from tools import execute_sql, RuntimeContext
import shutil

import gradio as gr

load_dotenv()

# Initialize global variable at module level
db = None  # Store the SQLDatabase object

def load_prompt(path):
    """Load prompt from file"""
    return Path(path).read_text(encoding="utf-8").strip()

# Load system prompt
SYSTEM_PROMPT = load_prompt("./prompts/system.txt")

# Define tools - pass the function directly
tools = [execute_sql]

# Create agent
agent = create_agent(
    model="anthropic:claude-sonnet-4-5",
    system_prompt=SYSTEM_PROMPT,
    tools=tools,
    context_schema=RuntimeContext
)

def chat_with_agent(message, history):
    """
    Generator function that streams agent output to Gradio.
    Must have exactly (message, history) signature for gr.ChatInterface.
    """
    global db
    
    print(f"\n{'='*50}")
    print(f"CHAT - New message received: {message}")
    print(f"DB Connection status: {db is not None}")
    
    # Check if a database has been uploaded
    if db is None:
        print("ERROR: No database connection found")
        yield "**Please upload a database file first** using the upload button above."
        return
    
    print(f"DB Connection type: {type(db)}")
    
    full_response = ""

    try:
        print(f"Starting agent stream...")
        
        # Stream the agent's execution - matching your notebook code
        step_count = 0
        for step in agent.stream(
            {
                "messages": [
                    {"role": "user", "content": message}
                ]
            },
            context=RuntimeContext(db=db),
            stream_mode="values"
        ):
            step_count += 1
            print(f"\nStep {step_count}:")
            print(f"  Keys in step: {step.keys() if isinstance(step, dict) else 'Not a dict'}")
            
            # Get the last message from the step
            if "messages" in step and len(step["messages"]) > 0:
                last_message = step["messages"][-1]
                print(f"  Last message type: {type(last_message)}")
                print(f"  Last message role: {getattr(last_message, 'role', 'no role')}")
                
                # Extract content from the message
                if hasattr(last_message, 'content'):
                    content = last_message.content
                    print(f"  Content type: {type(content)}")
                    
                    # Handle string content
                    if isinstance(content, str):
                        full_response = content
                        print(f"  Yielding string content (length: {len(content)})")
                        yield full_response
                    
                    # Handle list content (tool calls, text blocks, etc.)
                    elif isinstance(content, list):
                        print(f"  Content is list with {len(content)} items")
                        message_parts = []
                        for idx, item in enumerate(content):
                            print(f"    Item {idx}: {type(item)}")
                            if isinstance(item, dict):
                                print(f"      Dict keys: {item.keys()}")
                                # Text content
                                if item.get('type') == 'text' and 'text' in item:
                                    message_parts.append(item['text'])
                                # Tool use
                                elif item.get('type') == 'tool_use':
                                    tool_name = item.get('name', 'unknown')
                                    message_parts.append(f"\n🔧 **Using tool**: `{tool_name}`\n")
                            elif hasattr(item, 'text'):
                                message_parts.append(item.text)
                            else:
                                message_parts.append(str(item))
                        
                        if message_parts:
                            full_response = "".join(message_parts)
                            print(f"  Yielding combined content (length: {len(full_response)})")
                            yield full_response
                else:
                    print(f"  No content attribute found")
        
        print(f"\nStream completed. Total steps: {step_count}")
        
        # Final yield to ensure we show the complete response
        if full_response:
            print(f"Final response length: {len(full_response)}")
            yield full_response
        else:
            print("WARNING: No response generated")
            yield "No response generated. Please try again."
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\nERROR in chat_with_agent:")
        print(error_details)
        
        error_msg = f"**Error**: {str(e)}\n\n"
        error_msg += "**Troubleshooting:**\n"
        error_msg += "- Make sure your database file is valid\n"
        error_msg += "- Try rephrasing your question\n"
        error_msg += "- Check if the database has the expected tables"
        yield error_msg

def handle_file_upload(file):
    """Handle file upload and create SQLDatabase connection"""
    global db
    
    if file is None:
        db = None
        return "No file uploaded."
    
    try:
        print(f"\n{'='*50}")
        print(f"FILE UPLOAD - Starting...")
        print(f"Temporary file path: {file.name}")
        print(f"File exists: {os.path.exists(file.name)}")
        
        # Create a permanent directory for uploaded databases
        upload_dir = "uploaded_databases"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Get the original filename and create permanent path
        original_filename = os.path.basename(file.name)
        permanent_path = os.path.join(upload_dir, original_filename)
        
        # Copy the file to permanent location
        shutil.copy(file.name, permanent_path)
        print(f"File copied to permanent location: {permanent_path}")
        print(f"Permanent file exists: {os.path.exists(permanent_path)}")
        
        # Create SQLDatabase object from the PERMANENT file path
        # CRITICAL: Assign to global AFTER declaring it
        db_connection = SQLDatabase.from_uri(f"sqlite:///{permanent_path}")
        
        print(f"Database connection created successfully")
        print(f"Connection type: {type(db_connection)}")
        
        # Test the connection
        try:
            tables = db_connection.get_usable_table_names()
            print(f"Available tables: {tables}")
            
            # Only assign to global AFTER successful validation
            db = db_connection
            print(f"Global db variable assigned: {db is not None}")
            
            return (f"✅ Database '{original_filename}' loaded successfully!\n"
                   f"🔗 Connection established and ready for queries.\n"
                   f"Found {len(tables)} table(s): {', '.join(tables)}")
        except Exception as table_error:
            print(f"Warning: Could not list tables - {table_error}")
            db = db_connection
            return f"✅ Database '{original_filename}' loaded (couldn't verify tables: {table_error})"
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR in handle_file_upload:\n{error_trace}")
        db = None
        return f"Error loading database: {str(e)}\n\nDetails: {error_trace}"

# Create Gradio interface
with gr.Blocks(theme=gr.themes.Soft(), title="SQL Agent Chat") as demo:
    gr.Markdown("# SQL AI Agent with Database Upload")
    gr.Markdown("Upload your SQLite database file and ask questions about your data!")
    
    # Upload section
    with gr.Row():
        with gr.Column(scale=2):
            upload_button = gr.File(
                label="Upload Database File",
                file_types=[".db", ".sqlite", ".sqlite3"],
                type="filepath"
            )
        with gr.Column(scale=3):
            upload_status = gr.Textbox(
                label="Upload Status",
                interactive=False,
                lines=3,
                placeholder="Upload a database file to get started..."
            )
    
    # Process file automatically when uploaded
    upload_button.change(
        fn=handle_file_upload,
        inputs=[upload_button],
        outputs=[upload_status]
    )
    
    gr.Markdown("---")
    gr.Markdown("### Chat with Your Database")
    
    # Chat interface with messages format
    chat_interface = gr.ChatInterface(
        fn=chat_with_agent,
        type="messages",
        chatbot=gr.Chatbot(height=500, show_copy_button=True),
        textbox=gr.Textbox(placeholder="Ask a question about your database...", scale=7),
        title=None,
        description="Ask questions in natural language and I'll query your database!",
    )

if __name__ == "__main__":
    demo.launch()