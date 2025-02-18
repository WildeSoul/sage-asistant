import os
import re
import logging
import psutil
import pyttsx3
import win32com.client
import speech_recognition as sr
import pyautogui
import webbrowser
import wikipedia
import pywhatkit
from datetime import datetime
from pathlib import Path
from googleapiclient.discovery import build
from typing import List, Tuple, Callable, Pattern
from pywinauto import Desktop
import threading
import requests
import time
from PIL import ImageGrab, Image
import pytesseract
import pyjokes

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Replace with your actual YouTube API key if needed
YOUTUBE_API_KEY: str = " AIzaSyCXCuVm0qyUONuF-OfAsVI49kXnTPmQouE "

class Sage:
    """
    Sage is a conversational voice assistant that processes natural language commands
    to control applications, perform file and web operations, read the screen via OCR,
    manage media/system controls, and automate desktop tasks.
    """
    # Pre-defined paths for common apps (if available)
    SYSTEM_APPS = {
        'notepad': 'notepad.exe',
        'calculator': 'calc.exe',
        'paint': 'mspaint.exe',
        'command prompt': 'cmd.exe',
        'task manager': 'taskmgr.exe',
        'chrome': 'chrome.exe',
        'edge': 'msedge.exe',
        # For Spotify installed via direct download (won't exist if installed via Microsoft Store)
        'spotify': os.path.join(os.getenv("APPDATA", ""), "Spotify", "Spotify.exe")
    }
    # Pre-defined process names for closing apps (if known)
    APP_PROCESSES = {
        'notepad': 'notepad.exe',
        'calculator': 'calc.exe',
        'paint': 'mspaint.exe',
        'chrome': 'chrome.exe',
        'edge': 'msedge.exe',
        'spotify': 'Spotify.exe'
    }
    CommandPattern = Tuple[Pattern, Callable[[re.Match], None]]
    
    def __init__(self) -> None:
        self.engine = pyttsx3.init()
        self.recognizer = sr.Recognizer()
        self.shell = win32com.client.Dispatch("WScript.Shell")
        self.active: bool = True
        self.standby: bool = False
        self.command_patterns: List[Sage.CommandPattern] = []
        self.configure_voice()
        self.register_commands()
        logging.info("Sage initialized successfully.")
    
    def configure_voice(self) -> None:
        """Configure TTS with a preferred female voice, rate, and volume."""
        self.engine.setProperty('rate', 175)
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if "female" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                logging.info(f"Selected female voice: {voice.name}")
                break
        else:
            self.engine.setProperty('voice', voices[0].id)
            logging.info("Default voice selected.")
        self.engine.setProperty('volume', 1.0)
    
    def speak(self, text: str) -> None:
        """Speak the provided text aloud and log it."""
        logging.info(f"Sage says: {text}")
        self.engine.say(text)
        self.engine.runAndWait()
    
    def listen(self) -> str:
        """Listen for a voice command and return the recognized text (in lowercase)."""
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.7)
            try:
                logging.info("Listening for command...")
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=12)
                command = self.recognizer.recognize_google(audio).lower()
                logging.info(f"Recognized: {command}")
                return command
            except sr.WaitTimeoutError:
                logging.warning("Listening timed out; no command detected.")
                return ""
            except sr.UnknownValueError:
                logging.warning("Could not understand audio.")
                return ""
            except Exception as e:
                logging.error(f"Listening error: {e}")
                return ""
    
    def confirm_action(self, prompt: str) -> bool:
        """Ask for confirmation for critical commands."""
        self.speak(prompt + " Please confirm with 'yes'.")
        answer = self.listen()
        return "yes" in answer
    
    def display_help(self) -> None:
        """Read out available commands to the user."""
        help_text = (
            "Here are some commands you can use: "
            "For conversation, say 'how are you' or 'tell me a joke'. "
            "To open an application, say 'open notepad', 'launch calculator', or 'open spotify'. "
            "To close an application, say 'close notepad'. "
            "To search on Google, say 'search google for cats'. "
            "To search Wikipedia, say 'tell me about Python programming'. "
            "To search or play on YouTube, say 'search youtube for' or 'play youtube for' followed by your query. "
            "For file operations, say 'read file filename' or 'write file filename'. "
            "For system control, say 'shutdown', 'restart', or 'lock'. "
            "To take a screenshot and read the screen, say 'read screen'. "
            "To exit, say 'exit' or 'goodbye'."
        )
        self.speak(help_text)
    
    def enter_standby(self) -> None:
        """Enter standby mode until a 'wake up' command is received."""
        self.speak("Entering standby mode. Say 'wake up' to resume.")
        self.standby = True
        while self.standby:
            command = self.listen()
            if "wake up" in command:
                self.speak("Resuming operations.")
                self.standby = False
                break

    # --- Universal Application Launch ---
    def open_application(self, app_name: str) -> None:
        """
        Attempt to open an application by name.
        First try any pre-defined path; if that fails, search the Start Menu directories
        for a matching shortcut (.lnk file) to launch the application regardless of its install location.
        Additionally, if the app is 'spotify' and the pre-defined path isn't found,
        attempt to launch the Microsoft Store version using its AppUserModelID.
        """
        self.speak(f"Opening {app_name}, one moment please...")
        success = False
        app_key = app_name.lower()

        # Special handling for Spotify
        if app_key == "spotify":
            # This is the typical AppUserModelID for Spotify installed via Microsoft Store.
            # Adjust the ID if necessary to match your system.
            command = r'explorer.exe shell:AppsFolder\SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify'
            ret = os.system(command)
            if ret == 0:
                success = True
            else:
                logging.error(f"Error launching Spotify via shell command, return code: {ret}")
        
        # Otherwise, try the pre-defined path if available.
        if not success and app_key in self.SYSTEM_APPS and os.path.exists(self.SYSTEM_APPS[app_key]):
            try:
                os.startfile(self.SYSTEM_APPS[app_key])
                success = True
            except Exception as e:
                logging.error(f"Error opening {app_name} from predefined path: {e}")
        
        # If still not successful, search for a shortcut in the Start Menu folders.
        if not success:
            start_menu_dirs = [
                os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "Microsoft", "Windows", "Start Menu", "Programs"),
                os.path.join(os.environ.get("APPDATA", os.path.join("C:\\Users", os.getlogin(), "AppData", "Roaming")), "Microsoft", "Windows", "Start Menu", "Programs")
            ]
            found_shortcut = None
            for directory in start_menu_dirs:
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if file.lower().endswith(".lnk") and app_name.lower() in file.lower():
                            found_shortcut = os.path.join(root, file)
                            break
                    if found_shortcut:
                        break
                if found_shortcut:
                    break
            if found_shortcut:
                try:
                    os.startfile(found_shortcut)
                    success = True
                except Exception as e:
                    logging.error(f"Error launching {app_name} from shortcut: {e}")
        if success:
            self.speak(f"{app_name} is ready!")
        else:
            self.speak("Hmm, I'm having trouble opening that")
    
    # --- Universal Application Close ---
    def close_application(self, app_name: str) -> None:
        """
        Close an application by searching for open windows whose titles contain the app name.
        Uses pywinauto to send a close command, which works regardless of the app's installation location.
        """
        try:
            desktop = Desktop(backend="uia")
            closed = False
            for window in desktop.windows():
                if app_name.lower() in window.window_text().lower():
                    window.close()
                    closed = True
            if closed:
                self.speak(f"Closed {app_name}")
            else:
                self.speak(f"Couldn't find {app_name} running")
        except Exception as e:
            logging.error(f"Close app error: {e}")
            self.speak("Error closing application.")
    
    # --- Enhanced Window Control ---
    def switch_to_window(self, window_title: str) -> None:
        """
        Switch focus to a window matching the given title.
        Finds the best match (shortest title that includes the search term) and sets focus.
        """
        try:
            windows = Desktop(backend="uia").windows()
            best_match = None
            for win in windows:
                if window_title.lower() in win.window_text().lower():
                    if not best_match or len(win.window_text()) < len(best_match.window_text()):
                        best_match = win
            if best_match:
                best_match.set_focus()
                self.speak(f"Focused on {best_match.window_text()}")
            else:
                self.speak("No matching windows found")
        except Exception as e:
            logging.error(f"Window switch error: {e}")
            self.speak("Error switching window.")
    
    # --- Smart Click Handling ---
    def smart_click(self, target: str) -> None:
        """
        Handle relative position clicks.
        Maps common targets (like 'start', 'close', 'maximize') to pre-defined screen coordinates.
        """
        positions = {
            "start": (50, 1060),
            "close": (1890, 10),
            "maximize": (960, 10)
        }
        if target.lower() in positions:
            pyautogui.click(*positions[target.lower()])
            self.speak(f"Clicked {target}")
        else:
            self.speak(f"Saved position for {target} not found")
    
    # --- OCR Screen Reading ---
    def read_screen(self, area: tuple = None) -> None:
        """Capture the screen (or a specific region) and read text using OCR."""
        try:
            screenshot = ImageGrab.grab(bbox=area)
            text = pytesseract.image_to_string(screenshot)
            if text.strip():
                self.speak("Here's what I can read:")
                self.speak(text)
            else:
                self.speak("No readable text found")
        except Exception as e:
            self.speak("Screen reading failed")
            logging.error(f"OCR error: {e}")
    
    # --- System Control with Safety Confirmation ---
    def system_control(self, command: str) -> None:
        """
        Execute system control commands like shutdown, restart, lock, sleep, or take a screenshot.
        For critical commands, ask for verbal confirmation.
        """
        cmd = command.lower()
        try:
            if "shutdown" in cmd or "restart" in cmd:
                if self.confirm_action("Are you absolutely sure?"):
                    if "shutdown" in cmd:
                        os.system("shutdown /s /t 0")
                    elif "restart" in cmd:
                        os.system("shutdown /r /t 0")
                else:
                    self.speak("Operation cancelled")
            elif "lock" in cmd:
                self.speak("Locking the system.")
                os.system("rundll32.exe user32.dll,LockWorkStation")
            elif "sleep" in cmd:
                if self.confirm_action("Do you want to put the system to sleep?"):
                    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                else:
                    self.speak("Operation cancelled")
            elif "screenshot" in cmd:
                screenshot = pyautogui.screenshot()
                filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                screenshot.save(filename)
                self.speak(f"Screenshot saved as {filename}.")
            else:
                self.speak("System command not recognized.")
        except Exception as e:
            self.speak("Error executing system control command.")
            logging.error(f"System control error: {e}")
    
    # --- File Operations ---
    def file_read(self, filename: str) -> None:
        """Read the contents of a file and speak a summary if long."""
        try:
            if os.path.exists(filename):
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                if len(content) > 1000:
                    summary = content[:500] + "..."
                    self.speak(f"Contents of {filename} (summary): {summary}")
                    self.speak("Would you like to hear the entire file? Please say yes or no.")
                    if "yes" in self.listen():
                        self.speak("Reading full contents.")
                        self.speak(content)
                else:
                    self.speak(f"Contents of {filename}: {content}")
            else:
                self.speak("File not found.")
        except Exception as e:
            self.speak("Error reading file.")
            logging.error(f"File read error: {e}")
    
    def file_write(self, filename: str, content: str, mode: str = "w") -> None:
        """Write text to a file; if the file exists, prompt whether to overwrite or append."""
        try:
            if os.path.exists(filename) and mode == "w":
                self.speak(f"File {filename} exists. Overwrite or append?")
                decision = self.listen()
                if "append" in decision:
                    mode = "a"
            with open(filename, mode, encoding="utf-8") as f:
                f.write(content + "\n")
            self.speak("File updated successfully.")
        except Exception as e:
            self.speak("Error writing to file.")
            logging.error(f"File write error: {e}")
    
    def interactive_file_edit(self, filename: str) -> None:
        """Interactively edit a file line by line."""
        if not os.path.exists(filename):
            self.speak("File not found.")
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()
            new_lines = []
            self.speak(f"The file {filename} has {len(lines)} lines. I will read each line.")
            for i, line in enumerate(lines):
                self.speak(f"Line {i+1}: {line.strip()}")
                self.speak("Say 'keep' to leave it unchanged, or provide new text for this line.")
                response = self.listen()
                if response and "keep" not in response:
                    new_lines.append(response + "\n")
                else:
                    new_lines.append(line)
            self.speak("Editing complete. Do you want to save these changes? Please say yes or no.")
            if "yes" in self.listen():
                with open(filename, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                self.speak("File updated successfully.")
            else:
                self.speak("Changes discarded.")
        except Exception as e:
            self.speak("Error during interactive file editing.")
            logging.error(f"Interactive file edit error: {e}")
    
    # --- YouTube Command Handler ---
    def handle_search_youtube_api(self, match: re.Match) -> None:
        """
        Search or play a video on YouTube using the API.
        This handler is triggered by commands like:
        'search youtube for <query>' or 'play youtube for <query>'.
        If no query is provided, it asks for clarification.
        """
        query = match.group(1).strip()  # Captured query (may be empty)
        if not query:
            self.speak("Please specify what you want to search or play on YouTube.")
            return
        try:
            youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
            request = youtube.search().list(q=query, part='snippet', type='video', maxResults=1)
            response = request.execute()
            items = response.get('items')
            if items:
                video_id = items[0]['id']['videoId']
                url = f"https://www.youtube.com/watch?v={video_id}"
                self.speak(f"Playing {query} on YouTube.")
                webbrowser.open(url)
            else:
                self.speak("No results found on YouTube.")
        except Exception as e:
            self.speak("Error searching YouTube via API.")
            logging.error(f"YouTube API error: {e}")
    
    # --- Handler Wrappers for Other Commands ---
    def handle_conversation(self, match: re.Match) -> None:
        self.speak("I'm doing well, thank you! How can I assist you today?")
    
    def handle_joke(self, match: re.Match) -> None:
        try:
            joke = pyjokes.get_joke()
            self.speak(joke)
        except Exception as e:
            self.speak("Sorry, I couldn't fetch a joke right now.")
            logging.error(f"Joke error: {e}")
    
    def handle_exit(self, match: re.Match) -> None:
        self.speak("Goodbye! Take care.")
        self.active = False
    
    def handle_help(self, match: re.Match) -> None:
        self.display_help()
    
    def handle_standby(self, match: re.Match) -> None:
        self.enter_standby()
    
    def handle_open_application(self, match: re.Match) -> None:
        app_name = match.group(2).strip()
        self.open_application(app_name)
    
    def handle_close_app_command(self, match: re.Match) -> None:
        app_name = match.group(2).strip()
        self.close_application(app_name)
    
    def handle_switch_window(self, match: re.Match) -> None:
        window_title = match.group(2).strip()
        self.switch_to_window(window_title)
    
    def handle_read_file(self, match: re.Match) -> None:
        filename = match.group(2).strip()
        self.file_read(filename)
    
    def handle_write_file(self, match: re.Match) -> None:
        filename = match.group(2).strip()
        self.speak("What would you like to write into the file?")
        text = self.listen()
        self.file_write(filename, text)
    
    def handle_append_file(self, match: re.Match) -> None:
        filename = match.group(2).strip()
        self.speak("What would you like to append to the file?")
        text = self.listen()
        self.file_write(filename, text, mode="a")
    
    def handle_edit_file(self, match: re.Match) -> None:
        filename = match.group(2).strip()
        self.interactive_file_edit(filename)
    
    def handle_read_screen(self, match: re.Match) -> None:
        self.read_screen()
    
    def handle_click_coords(self, match: re.Match) -> None:
        try:
            x = int(match.group(2))
            y = int(match.group(3))
            pyautogui.click(x, y)
            self.speak(f"Clicked at coordinates {x} and {y}.")
        except Exception as e:
            self.speak("Error clicking at the specified coordinates.")
            logging.error(f"Click coords error: {e}")
    
    def handle_smart_click(self, match: re.Match) -> None:
        target = match.group(2).strip()
        self.smart_click(target)
    
    def handle_google_search(self, match: re.Match) -> None:
        query = match.group(2).strip()
        if query:
            self.speak(f"Searching Google for {query}.")
            webbrowser.open(f"https://www.google.com/search?q={query}")
        else:
            self.speak("I didn't catch your search query.")
    
    def handle_search_wikipedia(self, match: re.Match) -> None:
        query = match.group(2).strip()
        try:
            summary = wikipedia.summary(query, sentences=2)
            self.speak(summary)
        except Exception as e:
            self.speak("Error fetching Wikipedia summary.")
            logging.error(f"Wikipedia search error: {e}")
    
    def handle_media_control(self, match: re.Match) -> None:
        command = match.group(1).strip().lower()
        try:
            if "play" in command or "pause" in command:
                pyautogui.press('playpause')
                self.speak("Toggled play/pause.")
            elif "stop" in command:
                pyautogui.press('stop')
                self.speak("Stopped media.")
            elif "next" in command:
                pyautogui.press('nexttrack')
                self.speak("Skipped to next track.")
            elif "previous" in command:
                pyautogui.press('prevtrack')
                self.speak("Went back to previous track.")
            elif "mute" in command:
                pyautogui.press('volumemute')
                self.speak("Toggled mute.")
            elif "volume up" in command:
                pyautogui.press('volumeup')
                self.speak("Increased volume.")
            elif "volume down" in command:
                pyautogui.press('volumedown')
                self.speak("Decreased volume.")
            else:
                self.speak("Media command not recognized.")
        except Exception as e:
            self.speak("Error controlling media.")
            logging.error(f"Media control error: {e}")
    
    def handle_system_control(self, match: re.Match) -> None:
        cmd = match.group(1).strip()
        self.system_control(cmd)
    
    def register_commands(self) -> None:
        """
        Register command patterns for natural language interaction.
        Note: The YouTube pattern is placed before the generic media control pattern to ensure proper matching.
        """
        self.command_patterns = [
            # Conversational commands
            (re.compile(r".*\b(how are you|what's up|how's it going)\b.*", re.IGNORECASE), self.handle_conversation),
            (re.compile(r".*\b(tell me a joke)\b.*", re.IGNORECASE), self.handle_joke),
            # General commands
            (re.compile(r".*\b(exit|goodbye|bye|see you later)\b.*", re.IGNORECASE), self.handle_exit),
            (re.compile(r".*\b(help|what can you do|commands|show commands)\b.*", re.IGNORECASE), self.handle_help),
            (re.compile(r".*\b(standby|go to sleep|sleep mode)\b.*", re.IGNORECASE), self.handle_standby),
            # Application control commands
            (re.compile(r".*\b(open|launch|start)\b.*\b(.+)\b.*", re.IGNORECASE), self.handle_open_application),
            (re.compile(r".*\b(close|quit|terminate)\b.*\b(.+)\b.*", re.IGNORECASE), self.handle_close_app_command),
            (re.compile(r".*\b(switch to|go to|focus on)\b.*\b(.+)\b.*", re.IGNORECASE), self.handle_switch_window),
            # File operations
            (re.compile(r".*\b(read|show)\b.*\bfile\b\s+(.+)", re.IGNORECASE), self.handle_read_file),
            (re.compile(r".*\b(write|save)\b.*\bfile\b\s+(.+)", re.IGNORECASE), self.handle_write_file),
            (re.compile(r".*\b(append)\b.*\bfile\b\s+(.+)", re.IGNORECASE), self.handle_append_file),
            (re.compile(r".*\b(edit)\b.*\bfile\b\s+(.+)", re.IGNORECASE), self.handle_edit_file),
            # OCR Screen reading
            (re.compile(r".*\b(read\s+(?:the\s+)?screen|what's\s+on\s+the\s+screen)\b.*", re.IGNORECASE), self.handle_read_screen),
            # YouTube search/play commands – placed before media control
            (re.compile(r".*\b(?:search|play)\s+(?:on\s+)?youtube\b(?:\s+(?:for|about))?\s*(.*)", re.IGNORECASE), self.handle_search_youtube_api),
            # Media control commands (generic)
            (re.compile(r".*\b(play|pause|stop|next|previous|mute|volume up|volume down)\b.*", re.IGNORECASE), self.handle_media_control),
            # System control commands
            (re.compile(r".*\b(shutdown|restart|lock|sleep|screenshot)\b.*", re.IGNORECASE), self.handle_system_control),
            # Smart click commands
            (re.compile(r".*\b(click\s+(?:at)?\s*(\d+)\s+(\d+))\b.*", re.IGNORECASE), self.handle_click_coords),
            (re.compile(r".*\b(click\s+(?:the)?\s*(.+))\b.*", re.IGNORECASE), self.handle_smart_click),
            # Web searches
            (re.compile(r".*\b(search\s+google\s+(?:for|about))\s+(.+)\b.*", re.IGNORECASE), self.handle_google_search),
            (re.compile(r".*\b(search\s+wikipedia\s+(?:for|about)|look\s+up\s+wikipedia\s+for|tell\s+me\s+about)\b\s+(.+)", re.IGNORECASE), self.handle_search_wikipedia)
        ]
        logging.info("Registered dynamic command patterns:")
        for pattern, _ in self.command_patterns:
            logging.info(pattern.pattern)
    
    def process_command(self, command: str) -> None:
        """Process an incoming command by matching it against registered patterns."""
        if not command:
            return
        command = command.lower()
        logging.info(f"Processing command: {command}")
        for pattern, handler in self.command_patterns:
            match = pattern.search(command)
            if match:
                logging.info(f"Matched pattern: {pattern.pattern}")
                try:
                    handler(match)
                except Exception as e:
                    self.speak("An error occurred while processing your command.")
                    logging.error(f"Handler error for pattern {pattern.pattern}: {e}")
                return
        self.speak("I'm sorry, I didn't understand that. Could you please rephrase?")
    
    def run(self) -> None:
        """Greet the user and continuously listen for commands until deactivated."""
        self.speak("Hi, I'm Sage. How can I help you today? Say 'help' to hear my commands.")
        while self.active:
            command = self.listen()
            self.process_command(command)
            time.sleep(0.1)

if __name__ == "__main__":
    sage = Sage()
    sage.run()
