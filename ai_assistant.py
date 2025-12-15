import os
import sys
import re
import subprocess
import glob
import time
import platform 
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError
from google.genai import types
# Requires: pip install SpeechRecognition pyaudio
import speech_recognition as sr
# --- GLOBAL CONSTANTS AND SETUP ---
MODEL_NAME = "gemini-2.5-flash-lite" 
HISTORY_LIMIT = 10 
TEMP_FILE_LIST = [] 

# Global state variables
CURRENT_LANGUAGE = 'en'  # Default language is English
HISTORY_PATTERN = "*.chat_history.txt"
CURRENT_HISTORY_FILE = None 

# Initialize Speech Recognizer
r = sr.Recognizer()

# Load environment variables from the .env file
load_dotenv() 

# --- LOCALIZATION STRINGS (RU, EN, TR) ---

LOCALIZATION_STRINGS = {
    'en': {
        'code': 'en', 'name': 'English',
        # General
        'app_title': "Gemini CLI Assistant: History Management, File Analysis & Voice Mode",
        'exit_command': "exit or quit",
        'error_api': "Gemini API Error: ",
        'error_unexpected': "Unexpected error: ",
        'error_init': "Gemini initialization error: ",
        'error_api_key': "Error: 'GEMINI_API_KEY' environment variable not found.",
        
        # History Selection
        'history_title': "History Selection",
        'history_available': "📚 Available histories in the current directory:",
        'history_none': "💡 No available histories found. A new one will be created.",
        'history_default_name': "   (Default name will be used: {default_name})",
        'history_prompt_1': "1. History number [1, 2, 3...] to load an existing dialogue.",
        'history_prompt_2': "2. New name (e.g., 'project_A.chat_history.txt') to create/continue.",
        'history_prompt_input': "Your choice (or Enter for a new history): ",
        'history_loading_existing': "Loading existing history: ",
        'history_creating_new': "Creating new history: ",
        'history_invalid_number_1': "Invalid number. Enter a number from 1 to ",
        
        # Runtime Instructions (Text Mode)
        'chat_mode_title': "Gemini CLI Chat Mode. History: ",
        'command_title': "COMMANDS:",
        'command_1': "1. Dialogue: Just type your question.",
        'command_2': "2. Analyze:  /analyze <folder_path> \"Your question\" (Supports code, text, PNG, JPG)",
        'command_3': "3. Exit:     exit or quit",
        'saving_history': "Saving history and ending session.",
        
        # Analyze/Upload
        'analyze_start': "Starting analysis of folder: ",
        'analyze_folder': "Analyzing folder: ",
        'upload_skipping_large': "Skipping large file: ",
        'upload_file': "  Uploading: {file_name} as {mime_type}...",
        'upload_fallback': "  [Fallback]: Uploading without explicit mime_type...",
        'upload_failed': "  Failed to upload {file_name}: {error}",
        'analyze_usage_error': "🛑 Usage Error: /analyze folder_name \"Your analysis prompt\"",
        'analyze_usage_note': "   NOTE: The prompt (question) must be enclosed in double quotes.",
        'error_folder_not_found': "Error: Folder path not found: ",
        'analyze_error_folder_check_exists': "Directory exists",
        'analyze_error_folder_check_not_found': "Directory not found",
        'analyze_failed_no_files': "🛑 Analysis failed for path '{path}'. Path check result: '{check}'. No valid files were uploaded.",
        'cleanup_start': "Cleaning up uploaded files...",
        'cleanup_warning': "  Warning: Failed to delete {file_name}: {error}",
        
        # Language Selection
        'lang_title': "Language Selection",
        'lang_prompt': "Please select your language (Default is English):",
        'lang_1': "[1] English",
        'lang_2': "[2] Russian",
        'lang_3': "[3] Turkish",
        'lang_input': "Your choice [1/2/3 or EN/RU/TR]: ",
        'lang_selected': "Selected language: {lang}",
        'lang_invalid': "Invalid choice. Please enter 1, 2, 3, or the language code.",
        'sysinfo_non_linux': "System info retrieval skipped (Non-Linux OS).",
        
        # --- NEW MODE STRINGS ---
        'mode_title': "Mode Selection",
        'mode_prompt': "Please select the interaction mode:",
        'mode_1': "[1] Standard Text Chat",
        'mode_2': "[2] Voice Chat (Listen and respond)",
        'mode_input': "Your choice [1/2]: ",
        'mode_selected_text': "Starting Standard Text Chat...",
        'mode_selected_voice': "Starting Voice Chat Mode (Listening for input)...",
        
        # --- VOICE SPECIFIC STRINGS ---
        'voice_prompt': ">> Speak: ",
        'voice_exit': "Say 'exit' or 'quit' to end the session.",
        'voice_listening': "🎙️ Listening...",
        'voice_recognizing': "🧠 Recognizing your speech...",
        'voice_error_speech': "❌ Could not understand audio. Please try again.",
        'voice_error_mic': "❌ No suitable microphone found or error during audio capture.",
        'voice_sending': "✨ Sending to Gemini: ",
        
        # System Instruction (For Gemini)
        'system_instruction': "You are a highly intelligent CLI assistant. Your task is to analyze the provided files (code, text, images) and command history, responding briefly, accurately, and using Markdown for code formatting. If files are attached, focus on their analysis. If the user attempts to upload files but the operation failed, politely explain that files could not be found or the folder does not exist, and ask them to check the path.",
    },
    'ru': {
        'code': 'ru', 'name': 'Русский',
        # General
        'app_title': "Gemini CLI Ассистент: Управление историей, анализ файлов и Голосовой Режим",
        'exit_command': "exit или quit",
        'error_api': "Ошибка API Gemini: ",
        'error_unexpected': "Непредвиденная ошибка: ",
        'error_init': "Ошибка инициализации Gemini: ",
        'error_api_key': "Ошибка: Не найдена переменная окружения 'GEMINI_API_KEY'.",
        
        # History Selection
        'history_title': "Выбор истории",
        'history_available': "📚 Доступные истории в текущей директории:",
        'history_none': "💡 Доступных историй не найдено. Будет создана новая история.",
        'history_default_name': "   (По умолчанию будет использовано имя: {default_name})",
        'history_prompt_1': "1. Номер истории [1, 2, 3...] для загрузки существующего диалога.",
        'history_prompt_2': "2. Новое имя (например, 'project_A.chat_history.txt') для создания/продолжения.",
        'history_prompt_input': "Ваш выбор (или Enter для новой истории): ",
        'history_loading_existing': "Загрузка существующей истории: ",
        'history_creating_new': "Создание новой истории: ",
        'history_invalid_number_1': "Неверный номер. Введите число от 1 до ",
        
        # Runtime Instructions (Text Mode)
        'chat_mode_title': "Gemini CLI Режим Чата. История: ",
        'command_title': "КОМАНДЫ:",
        'command_1': "1. Диалог: Просто введите ваш вопрос.",
        'command_2': "2. Анализ:  /analyze <путь_к_папке> \"Ваш вопрос\" (Поддерживает код, текст, PNG, JPG)",
        'command_3': "3. Выход:     exit или quit",
        'saving_history': "Сохранение истории и завершение сессии.",
        
        # Analyze/Upload
        'analyze_start': "Начало анализа папки: ",
        'analyze_folder': "Анализируется папка: ",
        'upload_skipping_large': "Пропуск большого файла: ",
        'upload_file': "  Загрузка: {file_name} как {mime_type}...",
        'upload_fallback': "  [Резерв]: Загрузка без явного mime_type из-за старой версии SDK...",
        'upload_failed': "  Не удалось загрузить {file_name}: {error}",
        'analyze_usage_error': "🛑 Ошибка использования: /analyze folder_name \"Ваш запрос анализа\"",
        'analyze_usage_note': "   ПРИМЕЧАНИЕ: Запрос (вопрос) должен быть заключен в двойные кавычки.",
        'error_folder_not_found': "Ошибка: Путь к папке не найден: ",
        'analyze_error_folder_check_exists': "Директория существует",
        'analyze_error_folder_check_not_found': "Директория не найдена",
        'analyze_failed_no_files': "🛑 Анализ не удался для пути '{path}'. Результат проверки пути: '{check}'. Файлы не были загружены.",
        'cleanup_start': "Очистка загруженных файлов...",
        'cleanup_warning': "  Предупреждение: Не удалось удалить {file_name}: {error}",

        # Language Selection
        'lang_title': "Выбор языка",
        'lang_prompt': "Пожалуйста, выберите ваш язык (По умолчанию английский):",
        'lang_1': "[1] Английский",
        'lang_2': "[2] Русский",
        'lang_3': "[3] Турецкий",
        'lang_input': "Ваш выбор [1/2/3 или EN/RU/TR]: ",
        'lang_selected': "Выбранный язык: {lang}",
        'lang_invalid': "Неверный выбор. Пожалуйста, введите 1, 2, 3, или код языка.",
        'sysinfo_non_linux': "Получение системной информации пропущено (ОС не Linux).",
        
        # --- NEW MODE STRINGS ---
        'mode_title': "Выбор Режима",
        'mode_prompt': "Пожалуйста, выберите режим взаимодействия:",
        'mode_1': "[1] Стандартный Текстовый Чат",
        'mode_2': "[2] Голосовой Чат (Слушает и отвечает текстом)",
        'mode_input': "Ваш выбор [1/2]: ",
        'mode_selected_text': "Запуск Стандартного Текстового Чата...",
        'mode_selected_voice': "Запуск Голосового Чата (Ожидание голосового ввода)...",
        
        # --- VOICE SPECIFIC STRINGS ---
        'voice_prompt': ">> Скажите: ",
        'voice_exit': "Скажите 'exit' или 'quit' для завершения сессии.",
        'voice_listening': "🎙️ Слушаю...",
        'voice_recognizing': "🧠 Распознаю вашу речь...",
        'voice_error_speech': "❌ Не удалось распознать речь. Попробуйте снова.",
        'voice_error_mic': "❌ Не найден подходящий микрофон или ошибка при захвате аудио.",
        'voice_sending': "✨ Отправляю в Gemini: ",
        
        # System Instruction (For Gemini)
        'system_instruction': "Ты — высокоинтеллектуальный CLI-ассистент. Твоя задача — анализировать предоставленные файлы (код, текст, изображения) и историю команд, отвечая кратко, точно и используя Markdown для форматирования кода. Если файлы прикреплены, фокусируйся на их анализе. Если пользователь пытается загрузить файлы, но операция завершилась с ошибкой, вежливо объясни, что не удалось найти файлы или папка не существует, и попроси проверить путь.",
    },
    'tr': {
        'code': 'tr', 'name': 'Türkçe',
        # General
        'app_title': "Gemini CLI Asistanı: Geçmiş Yönetimi, Dosya Analizi ve Ses Modu",
        'exit_command': "çıkış veya çık",
        'error_api': "Gemini API Hatası: ",
        'error_unexpected': "Beklenmeyen hata: ",
        'error_init': "Gemini başlatma hatası: ",
        'error_api_key': "Hata: 'GEMINI_API_KEY' ortam değişkeni bulunamadı.",
        
        # History Selection
        'history_title': "Geçmiş Seçimi",
        'history_available': "📚 Mevcut dizindeki geçmişler:",
        'history_none': "💡 Mevcut geçmiş dosyası bulunamadı. Yeni bir tane oluşturulacak.",
        'history_default_name': "   (Varsayılan ad kullanılacak: {default_name})",
        'history_prompt_1': "1. Mevcut bir diyaloğu yüklemek için geçmiş numarası [1, 2, 3...].",
        'history_prompt_2': "2. Yeni bir geçmiş oluşturmak/devam etmek için yeni ad (örn: 'project_A.chat_history.txt').",
        'history_prompt_input': "Seçiminiz (veya yeni bir geçmiş için Enter): ",
        'history_loading_existing': "Mevcut geçmiş yükleniyor: ",
        'history_creating_new': "Yeni geçmiş oluşturuluyor: ",
        'history_invalid_number_1': "Geçersiz numara. 1 ile ",
        
        # Runtime Instructions (Text Mode)
        'chat_mode_title': "Gemini CLI Sohbet Modu. Geçmiş: ",
        'command_title': "KOMUTLAR:",
        'command_1': "1. Diyalog: Sadece sorunuzu yazın.",
        'command_2': "2. Analiz:  /analyze <klasör_yolu> \"Sorunuz\" (Kod, metin, PNG, JPG destekler)",
        'command_3': "3. Çıkış:     çıkış veya çık",
        'saving_history': "Geçmiş kaydediliyor ve oturum sonlandırılıyor.",
        
        # Analyze/Upload
        'analyze_start': "Klasör analizi başlatılıyor: ",
        'analyze_folder': "Klasör analiz ediliyor: ",
        'upload_skipping_large': "Büyük dosya atlanıyor: ",
        'upload_file': "  Yükleniyor: {file_name}, tür: {mime_type}...",
        'upload_fallback': "  [Yedek]: Eski SDK sürümü nedeniyle açık mime_type olmadan yükleniyor...",
        'upload_failed': "  Yüklenemedi {file_name}: {error}",
        'analyze_usage_error': "🛑 Kullanım Hatası: /analyze klasör_adı \"Analiz sorgunuz\"",
        'analyze_usage_note': "   NOT: Sorgu (soru) çift tırnak içinde olmalıdır.",
        'error_folder_not_found': "Hata: Klasör yolu bulunamadı: ",
        'analyze_error_folder_check_exists': "Dizin mevcut",
        'analyze_error_folder_check_not_found': "Dizin bulunamadı",
        'analyze_failed_no_files': "🛑 Analiz başarısız oldu для пути '{path}'. Yol kontrol sonucu: '{check}'. Geçerli dosya yüklenemedi.",
        'cleanup_start': "Yüklenen dosyalar temizleniyor...",
        'cleanup_warning': "  Uyarı: {file_name} silinemedi: {error}",

        # Language Selection
        'lang_title': "Dil Seçimi",
        'lang_prompt': "Lütfen dilinizi seçin (Varsayılan İngilizce'dir):",
        'lang_1': "[1] İngilizce",
        'lang_2': "[2] Rusça",
        'lang_3': "[3] Türkçe",
        'lang_input': "Seçiminiz [1/2/3 или EN/RU/TR]: ",
        'lang_selected': "Seçilen dil: {lang}",
        'lang_invalid': "Geçersiz seçim. Lütfen 1, 2, 3, veya dil kodunu girin.",
        'sysinfo_non_linux': "Sistem bilgisi alımı atlandı (Linux dışı işletim sistemi).",
        
        # --- NEW MODE STRINGS ---
        'mode_title': "Mod Seçimi",
        'mode_prompt': "Lütfen etkileşim modunu seçin:",
        'mode_1': "[1] Standart Metin Sohbeti",
        'mode_2': "[2] Sesli Sohbet (Dinle ve yanıtla)",
        'mode_input': "Seçiminiz [1/2]: ",
        'mode_selected_text': "Standart Metin Sohbeti başlatılıyor...",
        'mode_selected_voice': "Sesli Sohbet Modu başlatılıyor (Giriş bekleniyor)...",
        
        # --- VOICE SPECIFIC STRINGS ---
        'voice_prompt': ">> Konuşun: ",
        'voice_exit': "Oturumu sonlandırmak için 'exit' veya 'quit' deyin.",
        'voice_listening': "🎙️ Dinleniyor...",
        'voice_recognizing': "🧠 Konuşmanız tanınıyor...",
        'voice_error_speech': "❌ Ses anlaşılamadı. Lütfen tekrar deneyin.",
        'voice_error_mic': "❌ Uygun mikrofon bulunamadı veya ses yakalama sırasında hata oluştu.",
        'voice_sending': "✨ Gemini'ye gönderiliyor: ",
        
        # System Instruction (For Gemini)
        'system_instruction': "Sen yüksek zekalı bir CLI asistanısın. Görevin, sağlanan dosyaları (kod, metin, görseller) ve komut geçmişini analiz etmek, kısa, doğru yanıtlar vermek и используя Markdown для форматирования кода. Dosyalar eklenmişse analize odaklan. Kullanıcı dosya yüklemeye çalışırsa ancak işlem başarısız olursa, dosyaların bulunamadığını veya klasörün mevcut olmadığını kibarca açıklayın ve yolu kontrol etmesini isteyin.",
    }
}

# --- HELPER FUNCTION FOR LOCALIZATION ---
def get_string(key):
    """Helper function to fetch localized strings."""
    return LOCALIZATION_STRINGS[CURRENT_LANGUAGE][key]

# --- LANGUAGE SELECTION ---
def select_language():
    """Prompts the user to select the interface language."""
    global CURRENT_LANGUAGE
    
    loc = LOCALIZATION_STRINGS['en'] # Always start with English prompt for safety
    
    print("\n" + "=" * 60)
    print(loc['lang_title'])
    print("-" * 60)
    print(loc['lang_prompt'])
    print(loc['lang_1'])
    print(loc['lang_2'])
    print(loc['lang_3'])
    print("-" * 60)
    
    while True:
        choice = input(loc['lang_input']).strip().lower()
        
        if choice in ['1', 'en']:
            CURRENT_LANGUAGE = 'en'
            break
        elif choice in ['2', 'ru']:
            CURRENT_LANGUAGE = 'ru'
            break
        elif choice in ['3', 'tr']:
            CURRENT_LANGUAGE = 'tr'
            break
        elif choice == '':
            # Default to English if Enter is pressed
            CURRENT_LANGUAGE = 'en'
            break
        else:
            print(loc['lang_invalid'])
            
    # Confirmation in the selected language
    loc = LOCALIZATION_STRINGS[CURRENT_LANGUAGE]
    print(loc['lang_selected'].format(lang=loc['name'].upper()))
    print("=" * 60)

# --- MODE SELECTION FUNCTION ---
def select_mode():
    """Prompts the user to select between Text Chat and Voice Chat modes."""
    loc = LOCALIZATION_STRINGS[CURRENT_LANGUAGE]
    
    print("\n" + "=" * 60)
    print(loc['mode_title'])
    print("-" * 60)
    print(loc['mode_prompt'])
    print(loc['mode_1'])
    print(loc['mode_2'])
    print("-" * 60)
    
    while True:
        choice = input(loc['mode_input']).strip()
        
        if choice == '1':
            print(loc['mode_selected_text'])
            return 'text'
        elif choice == '2':
            print(loc['mode_selected_voice'])
            return 'voice'
        elif not choice:
            print(loc['mode_selected_text']) # Default to text mode
            return 'text'
        else:
            print(loc['lang_invalid'])

# --- HISTORY MANAGEMENT FUNCTIONS ---

def select_history_file():
    """Prompts the user to select an existing history file or start a new one."""
    global CURRENT_LANGUAGE
    loc = LOCALIZATION_STRINGS[CURRENT_LANGUAGE]
    current_dir = os.getcwd()
    
    history_files = sorted(glob.glob(os.path.join(current_dir, HISTORY_PATTERN)))
    
    # --- Help message displayed on startup ---
    print("=" * 60)
    print(loc['app_title'])
    print("-" * 60)
    
    if not history_files:
        default_name = f"default_{int(time.time())}.chat_history.txt"
        print(loc['history_none'])
        print(loc['history_default_name'].format(default_name=default_name))
    else:
        print(loc['history_available'])
        for i, h_file in enumerate(history_files):
            filename = os.path.basename(h_file)
            print(f"  [{i+1}] {filename}")
    
    print("-" * 60)
    print("👉 " + loc['history_prompt_1'])
    print("   " + loc['history_prompt_2'])
    print("=" * 60)
    
    while True:
        choice = input(loc['history_prompt_input']).strip()
        
        if not choice:
            # Default to a unique filename if nothing is entered
            selected_file_name = f"default_{int(time.time())}.chat_history.txt"
            selected_file = os.path.join(current_dir, selected_file_name)
            print(loc['history_creating_new'] + os.path.basename(selected_file))
            return selected_file
        
        try:
            # 1. Check if user selected a number
            index = int(choice)
            
            # --- FIX: If no files exist, treat number input as a filename attempt ---
            if not history_files:
                raise ValueError
            
            if 1 <= index <= len(history_files):
                selected_file = history_files[index - 1]
                print(loc['history_loading_existing'] + os.path.basename(selected_file))
                return selected_file
            else:
                print(loc['history_invalid_number_1'] + str(len(history_files)) + ".")
                continue
        except ValueError:
            # 2. User entered a custom name (or failed number conversion/no files)
            
            if not choice.lower().endswith('.chat_history.txt'):
                choice = choice.split(".")[0] + ".chat_history.txt"
            
            selected_file = os.path.join(current_dir, choice)
            
            if os.path.exists(selected_file):
                print(loc['history_loading_existing'] + os.path.basename(selected_file))
            else:
                print(loc['history_creating_new'] + os.path.basename(selected_file))
            
            return selected_file

def load_chat_history(history_file_path):
    """Loads chat history from the specified file path."""
    history = []
    if os.path.exists(history_file_path):
        try:
            with open(history_file_path, "r") as f:
                lines = f.readlines()
            for i in range(0, len(lines), 2):
                if i + 1 < len(lines):
                    role_line = lines[i].strip()
                    if "role: system" in role_line.lower():
                        continue 
                    role_match = re.search(r'role: (user|model)', role_line)
                    if not role_match:
                        continue
                    role = role_match.group(1)
                    content = lines[i+1].strip()
                    history.append(types.Content(role=role, parts=[types.Part.from_text(text=content)]))
        except Exception:
            pass
    return history

def save_chat_history(chat, history_file_path):
    """Saves the entire current chat history (old + new messages) to the specified file path."""
    try:
        with open(history_file_path, "w") as f:
            for message in chat.get_history():
                if message.role not in ['user', 'model']:
                    continue
                
                f.write(f"role: {message.role}\n")
                if message.parts and hasattr(message.parts[0], 'text'):
                    f.write(f"{message.parts[0].text}\n")
    except Exception as e:
        # NOTE: This string is not localized because it's only an error fallback
        print(f"Error saving history: {e}") 

# --- FILE UPLOAD AND ANALYSIS FUNCTIONS ---

def upload_folder_contents(client, folder_path):
    """Recursively reads and uploads files from a folder to the Gemini API, with SDK version fallback."""
    loc = LOCALIZATION_STRINGS[CURRENT_LANGUAGE]
    
    if not os.path.isdir(folder_path):
        print(loc['error_folder_not_found'] + folder_path)
        return []
    
    uploaded_files = []
    allowed_extensions = ('.py', '.txt', '.md', '.html', '.css', '.js', '.json', '.sh', '.log', '.conf', '.png', '.jpg', '.jpeg')
    
    print(loc['analyze_folder'] + folder_path)

    for root, _, files in os.walk(folder_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            
            if os.path.getsize(file_path) > 20 * 1024 * 1024:
                print(loc['upload_skipping_large'] + file_name)
                continue
            
            file_extension = os.path.splitext(file_name)[1].lower()
            
            if file_extension in allowed_extensions:
                try:
                    # Determine MIME type
                    if file_extension in ('.png', '.jpg', '.jpeg'):
                        mime_type = {
                            '.png': 'image/png',
                            '.jpg': 'image/jpeg',
                            '.jpeg': 'image/jpeg'
                        }.get(file_extension, 'application/octet-stream')
                    else:
                        mime_type = "text/plain"
                    
                    print(loc['upload_file'].format(file_name=file_name, mime_type=mime_type))
                    
                    file_obj = None
                    try:
                        # Attempt 1: Use syntax with mime_type (for modern SDKs)
                        file_obj = client.files.upload(
                            file=file_path,
                            mime_type=mime_type
                        )
                    except TypeError as e:
                        # Fallback for "unexpected keyword argument" (older SDKs)
                        if 'unexpected keyword argument' in str(e):
                            print(loc['upload_fallback'])
                            file_obj = client.files.upload(
                                file=file_path
                            )
                        else:
                            raise 
                    
                    if file_obj:
                         uploaded_files.append(file_obj)
                         TEMP_FILE_LIST.append(file_obj) 
                    
                except Exception as e:
                    print(loc['upload_failed'].format(file_name=file_name, error=e))
                    
    return uploaded_files

def cleanup_uploaded_files(client):
    """Deletes temporary files uploaded to the Gemini service."""
    if not TEMP_FILE_LIST:
        return
    loc = LOCALIZATION_STRINGS[CURRENT_LANGUAGE]
    print("\n" + loc['cleanup_start'])
    for file_obj in TEMP_FILE_LIST:
        try:
            client.files.delete(name=file_obj.name)
        except Exception as e:
            print(loc['cleanup_warning'].format(file_name=file_obj.name, error=e))
    TEMP_FILE_LIST.clear()

# --- UTILITY AND CLIENT FUNCTIONS (System and Terminal History) ---

def get_system_info():
    """
    Retrieves system information using 'neofetch' on Linux/macOS. 
    Returns a localized fallback message on other OSs (like Windows).
    """
    loc = LOCALIZATION_STRINGS[CURRENT_LANGUAGE]
    
    if platform.system() != 'Linux': # Check for non-Linux system
        return loc['sysinfo_non_linux']
        
    try:
        output = subprocess.check_output(
            ['neofetch', '--stdout', '--disable', 'ascii'],
            stderr=subprocess.STDOUT
        ).decode('utf-8')
        clean_output = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', output).strip()
        return clean_output
    except (FileNotFoundError, Exception):
        return "System info retrieval failed. Neofetch not found or error occurred."

def get_terminal_history():
    """
    Retrieves the last commands from the shell history file on Linux/macOS. 
    Returns an empty list on other OSs (like Windows).
    """
    if platform.system() != 'Linux': # Check for non-Linux system
        return []

    shell = os.environ.get("SHELL", "").split('/')[-1]
    history_file = None
    if shell == 'bash':
        history_file = os.path.expanduser("~/.bash_history")
    elif shell == 'zsh':
        history_file = os.path.expanduser("~/.zsh_history")
    elif shell == 'fish':
        history_file = os.path.expanduser("~/.local/share/fish/fish_history")
    commands = []
    if history_file and os.path.exists(history_file):
        try:
            with open(history_file, "r") as file:
                history = file.readlines()
                if shell == 'fish':
                    commands = [line.strip()[6:] for line in history if line.startswith('- cmd: ')]
                else:
                    commands = [line.strip() for line in history if line.strip() and not line.strip().startswith('#')]
        except Exception:
            return []
    return commands[-HISTORY_LIMIT:]

# --- INITIALIZATION ---

def initialize_client_and_chat():
    """Initializes the Gemini client, selects history, and loads the chat session."""
    global CURRENT_HISTORY_FILE
    
    # 0. Select Language first
    select_language()
    loc = LOCALIZATION_STRINGS[CURRENT_LANGUAGE]

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(loc['error_api_key'])
        sys.exit(1)
        
    # 1. Interactive history file selection
    CURRENT_HISTORY_FILE = select_history_file()

    try:
        client = genai.Client(api_key=api_key)
        
        # 2. Load selected history
        history = load_chat_history(CURRENT_HISTORY_FILE)
        
        # 3. Use localized System Instruction
        config = types.GenerateContentConfig(
            system_instruction=loc['system_instruction']
        )
        
        # MODEL_NAME is gemini-2.5-flash-lite
        chat = client.chats.create(
            model=MODEL_NAME, 
            history=history,
            config=config
        )
        return client, chat
        
    except Exception as e:
        print(loc['error_init'] + str(e))
        sys.exit(1)

# --- NEW VOICE CHAT MODE ---

def voice_chat_mode(client, chat):
    """Runs a loop for voice-based user dialogue."""
    global CURRENT_HISTORY_FILE
    loc = LOCALIZATION_STRINGS[CURRENT_LANGUAGE]
    # Use selected language code for better speech recognition accuracy
    lang_code = loc['code'] 

    print("\n-------------------------------------------------------------")
    print(loc['chat_mode_title'] + os.path.basename(CURRENT_HISTORY_FILE))
    print(f"🎙️ {loc['voice_exit']}")
    print("-------------------------------------------------------------")

    terminal_history = get_terminal_history()
    system_info = get_system_info()
    
    context_data = (
        f"[CONTEXT: SYSTEM]: {system_info}\n"
        f"[CONTEXT: HISTORY (last {HISTORY_LIMIT} commands)]: {', '.join(terminal_history)}"
    )
    first_prompt_sent = False 

    try:
        # Check if there are microphones available
        if not sr.Microphone.list_microphone_names():
            print(loc['voice_error_mic'])
            return

        with sr.Microphone() as source:
            try:
                # Adjust ambient noise level only once
                r.adjust_for_ambient_noise(source)
                print("🔊 Noise level adjusted. Ready.")
            except Exception as e:
                # This often fails if pyaudio/portaudio isn't installed correctly
                print(loc['voice_error_mic'])
                print(f"Error details: {e}")
                return # Exit voice mode if mic fails

            while True:
                try:
                    print(loc['voice_prompt'], end="")
                    print(loc['voice_listening'])
                    
                    # Listen to the audio (10 second limit per phrase)
                    audio = r.listen(source, phrase_time_limit=10) 
                    
                    print(loc['voice_recognizing'])
                    
                    # Recognize speech using Google Speech Recognition
                    # Uses the localized language code for recognition
                    user_input = r.recognize_google(audio, language=lang_code)
                    print(f"✅ Recognized: {user_input}")

                    if user_input.lower() in ['exit', 'quit']:
                        break
                    
                    if not user_input.strip():
                        continue

                    # Prepare prompt for Gemini
                    if not first_prompt_sent:
                        # Send context data only with the very first prompt
                        full_prompt = f"{context_data}\n\n[USER QUESTION]: {user_input}"
                        first_prompt_sent = True
                    else:
                        full_prompt = user_input 

                    print(loc['voice_sending'] + full_prompt)
                    
                    # Send message to Gemini
                    response = chat.send_message(full_prompt)
                    print(f"✨ Gemini: {response.text}")

                except sr.UnknownValueError:
                    print(loc['voice_error_speech'])
                except sr.RequestError as e:
                    print(f"❌ Speech Recognition API Error: {e}")
                except APIError as e:
                    print(f"🛑 {loc['error_api']}{e.args[0]}")
                    break
                except Exception as e:
                    print(f"🛑 {loc['error_unexpected']}{e}")
                    break
                    
    except Exception as e:
        # Handle exceptions related to PyAudio/Microphone initialization
        print(loc['voice_error_mic'])
        print(f"Initialization error: {e}")


    print("-" * 35)
    print(loc['saving_history'])
    save_chat_history(chat, CURRENT_HISTORY_FILE) 
    cleanup_uploaded_files(client) 

# --- MAIN INTERACTIVE MODE (TEXT CHAT) ---

def interactive_chat_mode(client, chat):
    """Runs an infinite loop for user dialogue, handling the /analyze command."""
    global CURRENT_HISTORY_FILE
    loc = LOCALIZATION_STRINGS[CURRENT_LANGUAGE]

    # --- Run-time help message ---
    print("\n-------------------------------------------------------------")
    print(loc['chat_mode_title'] + os.path.basename(CURRENT_HISTORY_FILE))
    print("-------------------------------------------------------------")
    print("   " + loc['command_title'])
    print("   " + loc['command_1'])
    print("   " + loc['command_2'])
    print("   " + loc['command_3'])
    print("-------------------------------------------------------------")

    terminal_history = get_terminal_history()
    system_info = get_system_info()
    
    # Context data for the very first prompt
    context_data = (
        f"[CONTEXT: SYSTEM]: {system_info}\n"
        f"[CONTEXT: HISTORY (last {HISTORY_LIMIT} commands)]: {', '.join(terminal_history)}"
    )

    while True:
        try:
            user_input = input(">> You: ")
            
            if user_input.lower() in ['exit', 'quit', loc['exit_command'].split()[0], loc['exit_command'].split()[-1]]:
                break
            
            if not user_input.strip():
                continue

            # --- CHECK FOR FOLDER ANALYSIS COMMAND ---
            if user_input.strip().lower().startswith("/analyze ") or user_input.strip().lower().startswith("/analyse "):
                
                # Regex to extract path and quoted prompt, supporting anal[yi]ze
                match = re.match(r"/\s*anal[yi]ze\s+(\S+)\s+\"(.+)\"", user_input, re.IGNORECASE)
                
                if not match:
                    print(loc['analyze_usage_error'])
                    print(loc['analyze_usage_note'])
                    continue
                    
                relative_folder_path = match.group(1).strip()
                prompt = match.group(2).strip()
                
                folder_path = os.path.abspath(relative_folder_path)
                
                print(loc['analyze_start'] + folder_path)
                
                uploaded_files = upload_folder_contents(client, folder_path)
                
                content_parts = []
                if len(chat.get_history()) == 0:
                    content_parts.append(context_data)

                # Process upload result
                if not uploaded_files:
                    check_result = loc['analyze_error_folder_check_exists'] if os.path.isdir(folder_path) else loc['analyze_error_folder_check_not_found']
                    error_msg = loc['analyze_failed_no_files'].format(path=relative_folder_path, check=check_result)
                    print(error_msg)
                    
                    # Inform Gemini about the internal error so it can generate a polite response
                    content_parts.append(f"[INTERNAL_ERROR_FILE_UPLOAD]: {error_msg}. Please inform the user that no files could be found/uploaded and ask them to verify the path or file types.")
                
                else:
                    content_parts.extend(uploaded_files)
                    content_parts.append(prompt)

                try:
                    response = chat.send_message(content_parts)
                    print(f"✨ Gemini: {response.text}")
                except APIError as e:
                    print(f"🛑 {loc['error_api']}{e.args[0]}")
                except Exception as e:
                    print(f"🛑 {loc['error_unexpected']}{e}")
                
            # --- REGULAR CHAT MESSAGE ---
            else:
                if len(chat.get_history()) == 0:
                    full_prompt = f"{context_data}\n\n[USER QUESTION]: {user_input}"
                else:
                    full_prompt = user_input 

                response = chat.send_message(full_prompt)
                print(f"✨ Gemini: {response.text}")

        except APIError as e:
            print(f"🛑 {loc['error_api']}{e.args[0]}")
            break
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"🛑 {loc['error_unexpected']}{e}")
            break

    print("-" * 35)
    print(loc['saving_history'])
    save_chat_history(chat, CURRENT_HISTORY_FILE) 
    cleanup_uploaded_files(client) 

# --- MAIN EXECUTION BLOCK ---

if __name__ == "__main__":
    # 1. Initialize client and select history/language
    client, chat = initialize_client_and_chat()
    
    # 2. Select mode
    selected_mode = select_mode()
    
    # 3. Start selected mode
    if selected_mode == 'text':
        interactive_chat_mode(client, chat)
    elif selected_mode == 'voice':
        voice_chat_mode(client, chat)
