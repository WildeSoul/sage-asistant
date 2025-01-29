import datetime
import os
import subprocess
import sys
import webbrowser
from typing import Optional

# Required imports
import pyttsx3
import speech_recognition as sr
import pywhatkit
import wikipedia
import pyautogui  # For screenshot functionality

from chatbot_dialogue import ChatbotDialogue

class TextAssistant:
    """Base class for the virtual assistant"""
    def __init__(self):
        self.chatbot = ChatbotDialogue()
        # Initialize speech recognition with optimized settings
        try:
            self.recognizer = sr.Recognizer()
            # Optimize recognition settings
            self.recognizer.dynamic_energy_adjustment_damping = 0.3
            self.recognizer.dynamic_energy_ratio = 0.9
            self.recognizer.dynamic_energy_threshold = False
            self.recognizer.pause_threshold = 0.5
            self.recognizer.operation_timeout = None
            self.recognizer.non_speaking_duration = 0.5
            
            # Initialize text-to-speech with optimized settings
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 125)  # Slower, clearer speech rate
            voices = self.engine.getProperty('voices')
            self.engine.setProperty('voice', voices[1].id)  # Female voice
        except Exception as e:
            print(f"Error initializing voice components: {e}")
            raise e

    def speak(self, text):
        """Convert text to speech"""
        try:
            print(f"Assistant: {text}")
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")
            print(f"Assistant: {text}")  # Fallback to print if TTS fails

    def text_to_speech(self, text):
        """
        Convert text to speech using pyttsx3 with optimized voice settings.
        
        Args:
            text (str): The text to be converted to speech
        
        Returns:
            bool: True if speech was successful, False otherwise
        """
        if not text:
            return False
        
        try:
            # Configure voice properties
            self.engine.setProperty('rate', 125)  # Speed of speech
            self.engine.setProperty('volume', 1.0)  # Volume level
            
            # Use female voice
            voices = self.engine.getProperty('voices')
            if len(voices) > 1:
                self.engine.setProperty('voice', voices[1].id)
                
            # Convert and play speech
            self.engine.say(text)
            self.engine.runAndWait()
            return True
            
        except Exception as e:
            print(f"Text-to-speech error: {e}")
            
            # Try to reinitialize engine if there was an error
            try:
                self.engine = pyttsx3.init()
                self.engine.say(text)
                self.engine.runAndWait()
                return True
            except Exception as e:
                print(f"Failed to reinitialize text-to-speech engine: {e}")
                return False

    def take_command(self):
        """Take input from the user via voice or text"""
        try:
            with sr.Microphone() as source:
                print("Listening...", flush=True)
                try:
                    audio = self.recognizer.listen(source)
                    print("Processing...", flush=True)
                    command = self.recognizer.recognize_google(audio, language='en-IN')
                    print(f"You said: {command}")
                    return command.lower()
                except sr.UnknownValueError:
                    print("Sorry, I did not catch that.")
                    return "None"
                except sr.RequestError as e:
                    print(f"Could not request results; {e}")
                    return "None"
                except Exception as e:
                    print(f"Error: {e}")
                    return "None"
        except Exception as e:
            print("Voice input failed, falling back to text input")
            try:
                command = input("You: ")
                return command.lower()
            except KeyboardInterrupt:
                return "goodbye"

    def speech_to_text(self):
        """
        Convert speech to text using Google's Speech Recognition.
        Includes optimized microphone settings and comprehensive error handling.
        
        Returns:
            str: Transcribed text if successful, None otherwise
        """
        try:
            with sr.Microphone() as source:
                print("Listening...", flush=True)
                
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Get audio input
                try:
                    audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=5)
                    print("Processing...", flush=True)
                except sr.WaitTimeoutError:
                    print("No speech detected within timeout period")
                    return None
                    
                try:
                    # Use Google's speech recognition
                    text = self.recognizer.recognize_google(audio, language="en-IN")
                    print(f"You said: {text}")
                    return text.lower()  # Return lowercase for consistent command processing
                    
                except sr.UnknownValueError:
                    print("Could not understand the audio")
                except sr.RequestError as e:
                    print(f"Could not request results from speech recognition service; {e}")
                except Exception as e:
                    print(f"Speech recognition error: {e}")
                    
        except Exception as e:
            print(f"Error initializing microphone: {e}")
        
        return None

    def take_screenshot(self):
        """Take a screenshot and save it with timestamp"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshots_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        
        screenshot_path = os.path.join(screenshots_dir, f"screenshot_{timestamp}.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)
        return f"Screenshot saved as {screenshot_path}"

    def search_youtube(self, song_name):
        """Search for a song on YouTube"""
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        try:
            request = youtube.search().list(
                q=song_name,
                part='id,snippet',
                maxResults=1
            )
            response = request.execute()

            if 'items' in response and len(response['items']) > 0:
                item = response['items'][0]
                video_id = item['id'].get('videoId')
                video_title = item['snippet']['title']
                if video_id:
                    return f"https://www.youtube.com/watch?v={video_id}", video_title
            return None, None
        except Exception as e:
            print(f"Error occurred during YouTube search: {e}")
            return None, None

    def play_song(self, song_name):
        """Play a song on YouTube"""
        try:
            # Try playing directly with pywhatkit
            pywhatkit.playonyt(song_name)
        except Exception as e:
            # Fallback to manual search if pywhatkit fails
            video_url, video_title = self.search_youtube(song_name)
            if video_url:
                self.speak(f"Playing: {video_title}")
                try:
                    webbrowser.open(video_url)
                except Exception as e:
                    self.speak(f"Error playing video: {e}")
            else:
                self.speak("No results found.")

    def system_control(self, command):
        """Control system operations"""
        if 'restart' in command:
            self.speak("Restarting the system.")
            os.system("shutdown /r /t 1")
        elif 'shutdown' in command:
            self.speak("Shutting down the system.")
            os.system("shutdown /s /t 1")
        elif 'refresh' in command:
            self.speak("Refreshing the system.")
            pyautogui.hotkey('ctrl', 'r')

        elif 'screenshot' in command:
            self.speak("Taking a screenshot.")
            self.take_screenshot()

    def app_control(self, command):
        """Control applications"""
        command = command.lower()
        
        try:
            # Extract action (open/close) and app name
            action = "open" if "open" in command else "close" if "close" in command else None
            if not action:
                self.speak("Please specify whether to open or close the application")
                return
                
            app = command.replace(action, "").strip()
            
            # Common paths to look for applications
            search_paths = [
                os.path.expanduser("~/Desktop"),
                os.path.expanduser("~/AppData/Roaming/Microsoft/Windows/Start Menu/Programs"),
                os.path.expanduser("~/AppData/Local/Programs"),
                os.path.expanduser("~/AppData/Local"),
                "C:/Program Files",
                "C:/Program Files (x86)",
                os.path.expanduser("~/AppData/Roaming"),
                os.path.expanduser("~/AppData/Local/Microsoft/WindowsApps")
            ]
            
            # Common web applications and their URLs
            web_apps = {
                "youtube": "https://www.youtube.com",
                "google": "https://www.google.com",
                "spotify": "https://open.spotify.com",
                "gmail": "https://mail.google.com",
                "maps": "https://maps.google.com",
                "calendar": "https://calendar.google.com",
                "facebook": "https://www.facebook.com",
                "twitter": "https://twitter.com",
                "instagram": "https://www.instagram.com",
                "linkedin": "https://www.linkedin.com",
                "github": "https://github.com",
                "amazon": "https://www.amazon.com",
                "netflix": "https://www.netflix.com",
                "discord": "https://discord.com/app",
                "crunchyroll": "https://www.crunchyroll.com",
                "weather": "https://weather.com"
            }
            
            # Common executable names for popular apps
            app_executables = {
                "spotify": ["Spotify.exe"],
                "discord": ["Discord.exe", "Update.exe"],
                "steam": ["Steam.exe"],
                "epic": ["EpicGamesLauncher.exe"],
                "chrome": ["chrome.exe"],
                "firefox": ["firefox.exe"],
                "edge": ["msedge.exe"],
                "word": ["WINWORD.EXE"],
                "excel": ["EXCEL.EXE"],
                "powerpoint": ["POWERPNT.EXE"],
                "notepad": ["notepad.exe"],
                "paint": ["mspaint.exe"],
                "calculator": ["calc.exe"],
                "terminal": ["cmd.exe"],
                "explorer": ["explorer.exe"],
                "task manager": ["taskmgr.exe"],
                "control panel": ["control.exe"],
                "vlc": ["vlc.exe"],
                "visual studio": ["Code.exe", "devenv.exe"],
                "photoshop": ["Photoshop.exe"],
                "illustrator": ["Illustrator.exe"]
            }
            
            if action == "open":
                # First check if it's a web app
                if app in web_apps:
                    self.speak(f"Opening {app} in your browser")
                    webbrowser.open(web_apps[app])
                    return
                    
                # Check for special Windows apps
                if app in ["store", "microsoft store", "app store"]:
                    self.speak("Opening Microsoft Store")
                    os.system('start ms-windows-store:')
                    return
                    
                if app in ["settings", "windows settings"]:
                    self.speak("Opening Windows Settings")
                    os.system('start ms-settings:')
                    return
                
                # Search for the app in common paths
                found = False
                for path in search_paths:
                    if not os.path.exists(path):
                        continue
                        
                    # Search for executables
                    if app in app_executables:
                        for exe in app_executables[app]:
                            for root, dirs, files in os.walk(path):
                                if exe in files:
                                    try:
                                        self.speak(f"Starting {app}")
                                        subprocess.Popen(os.path.join(root, exe))
                                        found = True
                                        break
                                    except Exception as e:
                                        print(f"Error starting {exe}: {e}")
                    
                    # Search for shortcuts (.lnk files)
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if file.lower().endswith('.lnk') and app in file.lower():
                                try:
                                    self.speak(f"Opening {file.replace('.lnk', '')}")
                                    subprocess.Popen(['cmd', '/c', 'start', '', os.path.join(root, file)])
                                    found = True
                                    break
                                except Exception as e:
                                    print(f"Error opening shortcut: {e}")
                        
                        if found:
                            break
                    if found:
                        break
                
                if not found:
                    self.speak(f"Sorry, I couldn't find {app} on your system")
                    
            elif action == "close":
                if app in app_executables:
                    for exe in app_executables[app]:
                        try:
                            subprocess.run(['taskkill', '/F', '/IM', exe], capture_output=True)
                            self.speak(f"Closed {app}")
                            return
                        except Exception as e:
                            print(f"Error closing {exe}: {e}")
                
                self.speak(f"Sorry, I couldn't close {app}")
                
        except Exception as e:
            print(f"Error controlling application: {e}")
            self.speak("Sorry, I couldn't control that application")

    def media_control(self, command):
        """Control media playback"""
        if 'pause' in command or 'play' in command:
            pyautogui.press('playpause')
        elif 'next' in command:
            pyautogui.press('nexttrack')
        elif 'previous' in command:
            pyautogui.press('prevtrack')
        elif 'volume up' in command:
            pyautogui.press('volumeup')
        elif 'volume down' in command:
            pyautogui.press('volumedown')
        elif 'mute' in command:
            pyautogui.press('volumemute')

    def settings_control(self, command):
        """Control system settings"""
        if 'bluetooth' in command:
            self.speak("Opening Bluetooth settings.")
            os.system("start ms-settings:bluetooth")
        elif 'wifi' in command:
            self.speak("Opening Wi-Fi settings.")
            os.system("start ms-settings:network-wifi")

    def get_answer(self, query: str) -> Optional[str]:
        """
        Search for information using Wikipedia or open a Google search if Wikipedia fails.
        
        Args:
            query (str): The search query text
        
        Returns:
            Optional[str]: Wikipedia summary if found, None if web search is triggered
        """
        if not query:
            return None
            
        try:
            # Clean up the query
            query = query.strip()
            
            # Try Wikipedia first
            try:
                self.speak("Searching Wikipedia...")
                summary = wikipedia.summary(query, sentences=2)
                self.speak("According to Wikipedia...")
                return summary
                
            except wikipedia.DisambiguationError as e:
                # Handle multiple possible matches
                self.speak("Found multiple matches. Here's information about the most relevant one.")
                return wikipedia.summary(e.options[0], sentences=2)
                
            except wikipedia.PageError:
                # No Wikipedia match found, try Google search
                self.speak("No Wikipedia entry found. Searching Google instead...")
                search_url = f"https://www.google.com/search?q={query}"
                webbrowser.open(search_url)
                self.speak(f"I've opened a Google search for '{query}' in your browser.")
                return None
                
        except Exception as e:
            # Fallback to Google search for any other errors
            print(f"Search error: {e}")
            self.speak("I'll search that for you on Google.")
            search_url = f"https://www.google.com/search?q={query}"
            webbrowser.open(search_url)
            self.speak(f"You can see the search results for '{query}' in your browser.")
            return None

    def process_command(self, command):
        """Process user command"""
        if not command:
            return True
        
        command = command.lower().strip()
        
        try:
            # Exit commands
            if any(word in command for word in ["exit", "quit", "goodbye", "bye"]):
                self.speak("Goodbye! Have a great day!")
                return False
            
            # Screenshot command
            if "screenshot" in command:
                self.take_screenshot()
                return True
            
            # Play music/video commands
            if "play" in command:
                # Remove words like "play", "on youtube", etc.
                search_query = command.replace("play", "").replace("on youtube", "").replace("song", "").strip()
                if search_query:
                    self.speak(f"Playing {search_query} on YouTube")
                    try:
                        pywhatkit.playonyt(search_query)
                    except Exception as e:
                        print(f"Error playing music: {e}")
                        self.speak("Sorry, I couldn't play that. Please try again.")
                return True
            
            # YouTube search commands
            if "search" in command and "youtube" in command:
                # Extract the search query
                search_query = command.replace("search", "").replace("on youtube", "").replace("in youtube", "").replace("youtube", "").strip()
                if search_query:
                    self.speak(f"Searching YouTube for {search_query}")
                    search_url = f"https://www.youtube.com/results?search_query={'+'.join(search_query.split())}"
                    webbrowser.open(search_url)
                return True
            
            # Google search commands
            if "search" in command and ("google" in command or "web" in command):
                search_query = command.replace("search", "").replace("on google", "").replace("in google", "").replace("google", "").replace("web", "").strip()
                if search_query:
                    self.speak(f"Searching Google for {search_query}")
                    try:
                        pywhatkit.search(search_query)
                    except Exception as e:
                        print(f"Error searching Google: {e}")
                        webbrowser.open(f"https://www.google.com/search?q={'+'.join(search_query.split())}")
                return True
            
            # Wikipedia search
            if "wikipedia" in command or "who is" in command or "what is" in command:
                search_query = command
                for phrase in ["wikipedia", "who is", "what is", "tell me about"]:
                    search_query = search_query.replace(phrase, "")
                search_query = search_query.strip()
                
                if search_query:
                    self.speak(f"Searching Wikipedia for {search_query}")
                    try:
                        result = wikipedia.summary(search_query, sentences=2)
                        self.speak(result)
                    except Exception as e:
                        print(f"Error searching Wikipedia: {e}")
                        self.speak("Sorry, I couldn't find that information on Wikipedia")
                return True
            
            # Application control
            if "open" in command:
                self.app_control(command)
                return True
            
            # Default response for unknown commands
            self.speak("I'm not sure how to help with that. You can ask me to search the web, play music, open apps, or take screenshots.")
            return True
            
        except Exception as e:
            print(f"Error processing command: {e}")
            self.speak("Sorry, I couldn't process that command. Please try again.")
            return True

    def process_voice_command(self, command):
        """Process voice commands with improved handling"""
        try:
            command = command.lower()
            
            if "screenshot" in command or "take a picture" in command or "capture screen" in command:
                response = self.take_screenshot()
                return response
            elif 'time' in command:
                strTime = datetime.datetime.now().strftime("%H:%M:%S")
                return f"The time is {strTime}"
            
            elif 'wikipedia' in command:
                query = command.replace("wikipedia", "").strip()
                result = wikipedia.summary(query, sentences=1)
                return f"According to Wikipedia: {result}"
                
            elif 'who is' in command or 'what is' in command:
                query = command.replace("who is", "").replace("what is", "").strip()
                result = wikipedia.summary(query, sentences=1)
                return f"According to Wikipedia: {result}"
                
            elif 'search in youtube' in command or 'youtube search' in command:
                query = command.replace("search in youtube", "").replace("youtube search", "").strip()
                return f"Searching YouTube for {query}"
                
            elif 'search in google' in command or 'google search' in command:
                query = command.replace("search in google", "").replace("google search", "").strip()
                return f"Searching Google for {query}"
                
            elif 'play song' in command or 'play music' in command or 'music on youtube' in command:
                song_name = command.replace('play song', '').replace('play music', '')\
                                  .replace('music on youtube', '').replace('play', '').strip()
                if song_name:
                    return f"Playing {song_name}"
                else:
                    return "Which song would you like to play?"
                    
            elif any(word in command for word in ['restart', 'shutdown', 'refresh']):
                if 'restart' in command:
                    return "Restarting the system."
                elif 'shutdown' in command:
                    return "Shutting down the system."
                elif 'refresh' in command:
                    return "Refreshing the system."
                    
            elif any(word in command for word in ['open', 'close']):
                if 'open' in command:
                    app_name = command.replace('open', '').strip().lower()
                    return f"Opening {app_name}"
                elif 'close' in command:
                    app_name = command.replace('close', '').strip()
                    return f"Closing {app_name}"
                    
            elif any(word in command for word in ['pause', 'play', 'next', 'previous', 'volume']):
                if 'pause' in command or 'play' in command:
                    return "Playing/Pausing media"
                elif 'next' in command:
                    return "Playing next track"
                elif 'previous' in command:
                    return "Playing previous track"
                elif 'volume up' in command:
                    return "Increasing volume"
                elif 'volume down' in command:
                    return "Decreasing volume"
                elif 'mute' in command:
                    return "Muting volume"
                    
            elif any(word in command for word in ['bluetooth', 'wifi']):
                if 'bluetooth' in command:
                    return "Opening Bluetooth settings."
                elif 'wifi' in command:
                    return "Opening Wi-Fi settings."
                    
            elif 'goodbye' in command or 'exit' in command or 'quit' in command or 'bye' in command:
                return "Goodbye! Have a great day!"
                
            else:
                return "I'm not sure I understand. Could you please rephrase that?"
        except Exception as e:
            return f"An error occurred: {str(e)}"

    def listen(self):
        """Listen for voice input with improved error handling"""
        with sr.Microphone() as source:
            print("Listening...")
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                print("Processing...")
                try:
                    command = self.recognizer.recognize_google(audio)
                    print(f"You said: {command}")
                    response = self.process_voice_command(command)
                    print(f"Assistant: {response}")
                    return response
                except sr.UnknownValueError:
                    return "Sorry, I couldn't understand what you said."
                except sr.RequestError:
                    return "Sorry, there was an error with the speech recognition service."
            except sr.WaitTimeoutError:
                return "No speech detected. Please try again."

    def run(self):
        """Main loop for the voice assistant"""
        self.speak("Hello! I'm your virtual assistant. How may I help you today?")
        self.speak("I'm ready to help you! You can ask me to:")
        self.speak("- Search information on Wikipedia")
        self.speak("- Search on YouTube or Google")
        self.speak("- Play music on YouTube")
        self.speak("- Open applications and websites")
        self.speak("Just speak your command!")
        
        while True:
            try:
                command = self.speech_to_text()
                
                if not self.process_command(command):
                    break
                
            except KeyboardInterrupt:
                self.speak("Goodbye! Have a great day!")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                self.speak("Sorry, something went wrong. Please try again.")

if __name__ == "__main__":
    # Download all required NLTK data
    try:
        import nltk
        nltk.download('punkt')
        nltk.download('punkt_tab')
        nltk.download('wordnet')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('maxent_ne_chunker')
        nltk.download('words')
    except Exception as e:
        print(f"Error downloading NLTK data: {e}")
        
    assistant = TextAssistant()
    assistant.run()
