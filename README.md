# Tabletop Role-Playing Game with LLM
***
This application uses a language model to play a Tabletop Role-Playing Game (TTRPG). TTRPGs are games where players create characters and go on adventures in a fictional world. The game is usually facilitated by a Game Master (GM), who controls the world and its inhabitants. The GM also adjudicates the rules of the game based on a rulebook.

In this application, the language model takes on the role of the GM. This allows players to have a TTRPG experience without the need for a human GM. The language model is able to generate stories, create characters, and resolve actions. This makes it possible to have a truly unique and immersive Role-Playing experience.
***
The application runs on Google's **GEMINI AI** because of its largest, cutting edge context window and **Replicate**, which simplifies the process of running AI models to generate images. **API keys for both services are essential** for the application to work.

## Requirements:
- python >= 3.11.\* and pip

## Setting up:
Create a virtual environment:

```console
python -m venv .venv
```
Activate the created environment:
- Linux/Mac command: `source .venv/bin/activate`
- Windows Command: `.venv\Scripts\activate`

Install dependencies inside the environment
```console
pip install -r requirements.txt
```
## Start the application
```console
streamlit run main.py
```
