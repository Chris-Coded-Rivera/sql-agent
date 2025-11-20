# SQL Agent

This repo contains an sql agent that has access to a sql command tool to answer queries regarding an uploaded database.

The jupyter notebook was used as a way to test out the model, tool usage and prompt. It can be found in this repo under `sql_agent.ipynb` file

### __Instructions__:<br><br>
- Clone repo
- Create .env file using template found in .env_example file within the repo
- run `python app.py` on cli to run gradio interface
- query away

### __Cool Use Cases__:
This application can help users get a quick insight on their database. If user is having a hard time getting the right sql command, the agent can give the proper sql command to get the job done. 

### __Difficulties/Problems__:
In building this application I ran into a few problems:

1. Local machine memory constraints: I've been working on serving this utility using an open-source model so that all users can use with no need for tokens. As it will be a work in progress, I believe `claude-sonnet-4-5` is an imporessive model and has given me very good outputs.

2.  Documentation Limits: I've had a hard time finding the documents as detailed as I liked but found myself reading the source code for the solutions I sought.

3.  Initial issues getting the ai messages to show on gradio UI. Expanded error handling to fascilitate locating the issues.

Hope you enjoy the sql agent!
