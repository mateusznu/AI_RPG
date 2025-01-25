import webbrowser
import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import time
from deep_translator import GoogleTranslator
import replicate
from replicate import Client
import os
import json
import pdfplumber
import docx
import pypandoc
import chardet
import logging
from dotenv import load_dotenv, set_key, unset_key

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

# Function to save API keys and other settings to .env file
def save_settings(gemini_api_key, replicate_api_key, prompt_obrazka, model_name):
    set_key(".env", "GEMINI_API", gemini_api_key)
    set_key(".env", "REPLICATE_API", replicate_api_key)
    set_key(".env", "PROMPT_OBRAZKA", prompt_obrazka)
    set_key(".env", "MODEL_NAME", model_name)

# Function to delete .env file
def delete_env_file():
    if os.path.exists(".env"):
        os.remove(".env")

# Ensure .env file is deleted on app shutdown
import atexit
atexit.register(delete_env_file)

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []

if "message_count" not in st.session_state:
    st.session_state.message_count = 0

if "disabled" not in st.session_state:
    st.session_state.disabled = False

if "button_disabled" not in st.session_state:
    st.session_state.button_disabled = False

if "app_started" not in st.session_state:
    st.session_state.app_started = False

if "model" not in st.session_state:
    st.session_state.model = None

if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = None

if "replicate_api_key" not in st.session_state:
    st.session_state.replicate_api_key = None

if "context_files" not in st.session_state:
    st.session_state.context_files = []

if "initial_prompt" not in st.session_state:
    st.session_state.initial_prompt = "Oto uniwersalny podręcznik Fate Core, którego zasady spisane są w plikach pdf podpisanych jako rulebook, potrzebne ci do bycia Mistrzem Gry i prowadzenia rozgrywki dla mnie, gracza. Rozgrywka ma toczyć się w świecie Gry o Tron, na podstawie załączonych części książki i zasad podręcznika. Podręcznik jest dostosowany do umieszczenia gry w różnych kontekstach, na przykłąd w świecie Gry o Tron. Ty, jako Mistrz Gry, prowadzisz historię i opisujesz mi, graczowi, lokacje i okoliczności w jakich się znajduje a ja odpowiadam co chce zrobić. Grę rozpoczyna się zawsze od ustalenia szczegółów postaci gracza bazując na karcie postaci. W grze obowiązuje mechanika rzutu kośćmi, opisana na stronie 130. Gdy ustalisz z Graczem że należy rzucić kośćmi nie pytaj go o wynik, tylko sam losowo go wygeneruj."

if "prompt_obrazka" not in st.session_state:
    st.session_state.prompt_obrazka = "Scene from Game of Thrones, warm south and bright colors, fantasy-like, not photorealistic."

if "model_name" not in st.session_state:
    st.session_state.model_name = "black-forest-labs/flux-schnell"

translator = GoogleTranslator(source='pl', target='en')

def save_history():
    logging.info("Saving chat history to history.json")
    with open("history.json", "w") as f:
        modified_messages = []
        for message in st.session_state.messages:
            if message["role"] == "assistant":
                modified_messages.append({
                    "role": "model",
                    "parts": [message["content"]]
                })
            else:  # Zakładamy, że to wiadomość użytkownika
                modified_messages.append({
                    "role": "user",
                    "parts": [message["content"]]
                })
        json.dump(modified_messages, f, indent=4)

# Title
st.title("A Great Adventure")

if not st.session_state.app_started:
    # Input fields for API keys
    gemini_api_key = st.text_input("Gemini API Key", type="password")
    replicate_api_key = st.text_input("Replicate API Key", type="password")

    # Input field for prompt obrazka
    prompt_obrazka = st.text_input("Image Prompt", value=st.session_state.prompt_obrazka, help="A couple of words to tune image generation to your liking. Fill using English language!")

    # Input field for model name
    model_name = st.text_input("Model Name", value=st.session_state.model_name, help="Another model from https://replicate.com/collections/text-to-image can be chosen, but the cost of image generation may differ.")

    # File uploader for context files
    uploaded_files = st.file_uploader("Upload Context Files", accept_multiple_files=True, type=["pdf", "rtf", "docx", "txt"], help="Upload TTRPG Rulebook of your choice and desired context files, for example favourite book. For best results, use a rulebook that does not impose a specific setting, ex. Fate Core.")

    # Input field for initial prompt
    initial_prompt = st.text_area("Initial Prompt", help="This will be the first message sent to the model. Percisely explain what you expect from the model, in which contex the game should be placed and what rules shall it obey.")

    def read_pdf(file):
        logging.info(f"Reading PDF file: {file.name}")
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text()
        return text

    def read_docx(file):
        logging.info(f"Reading DOCX file: {file.name}")
        doc = docx.Document(file)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text

    def read_rtf(file):
        logging.info(f"Reading RTF file: {file.name}")
        output = pypandoc.convert_text(file.read(), 'plain', format='rtf')
        return output

    def read_txt(file):
        logging.info(f"Reading TXT file: {file.name}")
        raw_data = file.read()
        result = chardet.detect(raw_data)
        text = raw_data.decode(result['encoding'])
        return text

    # Button to start the app
    if st.button("Start App"):
        logging.info("Starting the app")
        # Store inputs in session state
        st.session_state.gemini_api_key = gemini_api_key
        st.session_state.replicate_api_key = replicate_api_key
        st.session_state.initial_prompt = initial_prompt
        st.session_state.prompt_obrazka = prompt_obrazka
        st.session_state.model_name = model_name

        # Save settings to .env file
        save_settings(gemini_api_key, replicate_api_key, prompt_obrazka, model_name)

        # Read content from uploaded files
        context_files_content = []
        if uploaded_files:
            for uploaded_file in uploaded_files:
                content = ""
                if uploaded_file.type == "application/pdf":
                    content = read_pdf(uploaded_file)
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    content = read_docx(uploaded_file)
                elif uploaded_file.type == "application/rtf":
                    content = read_rtf(uploaded_file)
                elif uploaded_file.type == "text/plain":
                    content = read_txt(uploaded_file)
                context_files_content.append(content)
        st.session_state.context_files = context_files_content

        # Configure Gemini API
        logging.info("Configuring Gemini API")
        genai.configure(api_key=os.getenv("GEMINI_API"))
        replicate = Client(api_token=os.getenv("REPLICATE_API"))

        # Initialize the model
        logging.info("Initializing the model")
        st.session_state.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            system_instruction="Mistrz Gry do sesji w grze Tabletop RPG.",
        )

        # Initialize chat session with context files and initial prompt
        logging.info("Initializing chat session")
        st.session_state.chat_session = st.session_state.model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": st.session_state.context_files + [st.session_state.initial_prompt],
                }
            ]
        )

        # Set app started flag
        st.session_state.app_started = True

else:
    # Reload environment variables after saving settings
    load_dotenv()

    # Configure Gemini API
    logging.info("Configuring Gemini API")
    genai.configure(api_key=os.getenv("GEMINI_API"))
    api = os.getenv("REPLICATE_API")
    replicate = Client(api_token=api)

    # Ensure the model is initialized
    if st.session_state.model is None:
        logging.info("Re-initializing the model")
        st.session_state.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            system_instruction="Mistrz Gry do sesji w grze Tabletop RPG.",
        )

    # Create columns
    col1, col2 = st.columns([6, 1])

    # Column 1: Chat
    with col1:
        # Display messages from history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"], avatar=message["avatar"]):
                    st.markdown(message["content"])

    # Text input field at the bottom of the page
    with st.form("chat_input_form", clear_on_submit=True, enter_to_submit=True):
        prompt = st.text_input("Twoja kolej...")
        submitted = st.form_submit_button("Wyślij", disabled=st.session_state.button_disabled)

        if submitted:
            logging.info("User submitted a prompt")
            st.session_state.button_disabled = True
            logging.info("Submit button disabled")

            with chat_container:  # Add message to chat container
                with st.chat_message("user", avatar='images/gracz2.jpg'):
                    st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "images/gracz2.jpg"})

            if "chat_session" not in st.session_state:
                # Initialize chat session
                logging.info("Initializing chat session")
                st.session_state["chat_session"] = st.session_state.model.start_chat(
                    history=[
                        {
                            "role": "user",
                            "parts": st.session_state.context_files + [st.session_state.initial_prompt],
                        },
                    ]
                )
            chat_session = st.session_state["chat_session"]

            # Send message to Gemini and get response
            logging.info("Sending message to Gemini")
            response = chat_session.send_message(prompt)

            # Translate bot's response to English
            logging.info("Translating bot's response to English")
            odpowiedz_bota_en = translator.translate(response.text)

            # Increment message count
            st.session_state.message_count += 1

            # Generate image every 3 prompts
            if st.session_state.message_count % 3 == 0:
                logging.info("Generating image for the prompt")
                prompt_obrazka = f"{st.session_state.prompt_obrazka}: {odpowiedz_bota_en}"
                output = replicate.run(
                    f"{st.session_state.model_name}",
                    input={"prompt": prompt_obrazka}
                )
                image = Image.open(io.BytesIO(output[0].read()))

                # Save image temporarily
                logging.info("Saving generated image temporarily")
                image_path = "images/temp_image.jpg"
                image.save(image_path)

                full_image_path = os.path.abspath(image_path)
                # Open image in new browser tab
                logging.info("Opening generated image in new browser tab")
                webbrowser.open_new_tab(full_image_path)

                # Display image in chat line
                with chat_container:
                    with st.chat_message("assistant", avatar="images/avatar_gm.jpg"):
                        st.markdown(response.text)
                        # st.image(image, caption="Wygenerowany Obraz")

            # Display bot's response
            else:  # Display bot's response without image
                logging.info("Displaying bot's response without image")
                with chat_container:
                    with st.chat_message("assistant", avatar="images/avatar_new.jpg"):
                        st.markdown(response.text)

            st.session_state.messages.append({"role": "assistant", "content": response.text, "avatar": "images/avatar_new.jpg"})

            # Save prompts to file
            save_history()

            # Re-enable the submit button
            logging.info("Re-enabling the submit button")
            st.session_state.button_disabled = False
