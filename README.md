# Gemini CLI Interview Framework.

This framework serves as a ready-made, modular foundation for building specialized AI tools capable of listening to verbal dialogue (an interview) and delivering structured, textual analysis or responses. 
#
# 📘 Deployment Guide: Gemini CLI Framework

This guide provides instructions for setting up and running the Gemini Command Line Interface (CLI) Assistant on both Linux (Ubuntu) and Windows operating systems.

Prerequisites

Python 3.10+ (Required).

An active internet connection.

An API Key from Google AI Studio.
#
🔑 Step 1: Obtain and Configure the API Key
#
The assistant requires a Gemini API key to function.

Get the Key: Register with Google AI Studio and obtain your Gemini API key.

Create the .env File: In the root folder of your project (e.g., ai_asistent), create a file named .env and add your key in the following format:

.env file

GEMINI_API_KEY="YOUR_KEY_HERE"
#
💻 Step 2: Deployment on Ubuntu (Linux)
#
2.1. Install System Dependencies

The Voice Mode (pyaudio) and system information retrieval (neofetch) require specific system packages.

Update package lists:

sudo apt update

Install PortAudio (for PyAudio) and Neofetch:

sudo apt install libasound-dev portaudio19-dev neofetch

2.2. Set Up Python Environment

Create a virtual environment (recommended):

python3 -m venv ai_asistent_env

Activate the environment:

source ai_asistent_env/bin/activate

Install all required Python libraries:

pip install google-genai python-dotenv SpeechRecognition pyaudio

2.3. Launch the Assistant

Ensure you are in the project directory and the ai_asistent.py file is present.

Run the assistant:

python3 ai_asistent.py

At the start of the session, you will be able to select Voice Chat Mode or Standard Text Chat.
#
🪟 Step 3: Deployment on Windows
#
3.1. Install System Dependencies

Python: Ensure you have Python 3.10+ installed and added to your system's PATH environment variable.

3.2. Set Up Python Environment

Create a virtual environment:

python -m venv ai_asistent_env

Activate the environment:

.\ai_asistent_env\Scripts\activate

Install all required Python libraries:

pip install google-genai python-dotenv SpeechRecognition pyaudio

Note on PyAudio: If pip install pyaudio fails, try installing it via Conda (if you are using Anaconda): conda install -c anaconda pyaudio.

3.3. Launch the Assistant

Ensure you are in the project directory and the ai_asistent.py file is present.

Run the assistant:

python ai_asistent.py

You will be prompted to select the chat mode (Voice or Text).

📝 Important Notes for Users

Microphone: For the Voice Mode to work on Windows or Ubuntu, ensure your microphone is properly connected and configured in your system settings.

History: All dialogues are saved in files with the .chat_history.txt extension in the project's root folder.

Analyze Command (Text Mode): Use the following command structure to analyze local files or folder contents:

/analyze <folder_path> "Your query in quotes"
#
# 🛠️ User Guide: Gemini CLI Framework

After launching the assistant, you will go through three main stages: Language Selection, History Selection, and Mode Selection.

1. Session Start-up

Step 1: Language Selection

On the first launch, you will be prompted to select the interface language (Russian, English, Turkish). Enter the corresponding number or code (RU, EN, TR).

Step 2: Dialogue History Selection

You will be presented with a list of previously created history files (*.chat_history.txt).

    • Load an existing one: Enter the number in square brackets (e.g., [1]) next to the file.
    
    • Create new/continue old: Enter a new file name (e.g., project_report.chat_history.txt).
    
    • Use default: Press Enter to create a new file with a unique name.

Step 3: Work Mode Selection

Choose how you want to interact with the assistant:

Option

Code

Description

Standard Text Chat

1

Exchange messages via keyboard. Supports the /analyze command.

Voice Chat

2

Communicate via microphone. Ideal for Hands-free operation.

2. Mode: Standard Text Chat

After selecting mode 1, you will enter the main command-line loop.

💬 Dialogue with the AI

Simply type your question into the command line.

Important: With the first request in each new session, the assistant automatically attaches system information (OS, recent terminal commands) to your query to provide a more relevant answer.

📂 The /analyze Command (File Analysis)

This command allows you to upload the contents of an entire folder for AI analysis.

    • Format:

/analyze <folder_path> "Your query enclosed in double quotes"

    • Example Usage:

>> You: /analyze ./src/my_project "Check this code for SQL injection vulnerabilities and suggest refactoring"

    • Supported Files: Code (.py, .js, .md, .sh, etc.), text, and images (.png, .jpg).
    
    • Limitations: Files larger than 20 MB will be skipped.

NOTE: All uploaded files are automatically deleted from the Gemini cloud after the session ends.

🚪 Ending the Session

To exit and save the dialogue history, enter:

>> You: exit

or

>> You: quit

3. Mode: Voice Chat

After selecting mode 2, the assistant will use your microphone.

🗣️ Voice Interaction

    1. Start: After the message 🎙️ Listening... appears, begin speaking.
    
    2. Recognition: The system listens for up to 10 seconds. After a pause or time expiry, you will see the recognized text.
    
    3. AI Response: The recognized text is sent to Gemini, and the response is outputted as text in the terminal.
    
    • Advantage: You can dictate long queries or describe problems without typing them.

🔴 Ending the Session by Voice

To end the voice chat and save the history, say one of the following words:

    • "exit"
    
    • "quit"
