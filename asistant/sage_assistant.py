import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import pyjokes
import wikipedia
import pyautogui
import os
import subprocess
from googleapiclient.discovery import build
import pywhatkit
from sage import TextAssistant

class VoiceAssistant(TextAssistant):
    def __init__(self):
        super().__init__()
        # Initialize speech recognition
        try:
            self.recognizer = sr.Recognizer()
            self.engine = pyttsx3.init()
            
            # Set the voice to female and adjust speech rate and volume
            voices = self.engine.getProperty('voices')
            self.engine.setProperty('voice', voices[1].id)  # Female voice
            self.engine.setProperty('rate', 150)  # Speed of speech
            self.engine.setProperty('volume', 1.0)  # Volume level (0.0 to 1.0)
            
            # YouTube API key
            self.API_KEY = '........'
        except Exception as e:
            print(f"Error initializing voice components: {e}")
            raise e

    def speak(self, text):
        """Override speak method to use voice"""
        print(f'Sage: {text}')
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Error in speech synthesis: {e}")

    def take_command(self):
        """Override take_command to use voice input"""
        with sr.Microphone() as source:
            print("Listening...")
            audio = self.recognizer.listen(source)
            try:
                print("Recognizing...")
                command = self.recognizer.recognize_google(audio, language='en-in')
                print(f"User said: {command}\n")
                return command.lower()
            except Exception as e:
                print("Sorry, I did not catch that.")
                return None

    def search_youtube(self, song_name):
        youtube = build('youtube', 'v3', developerKey=self.API_KEY)
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
        video_url, video_title = self.search_youtube(song_name)
        if video_url:
            self.speak(f"Playing: {video_title}")
            try:
                pywhatkit.playonyt(video_url)
            except Exception as e:
                self.speak(f"Error playing video: {e}")
        else:
            self.speak("No results found.")

    def screen_record(self):
        self.speak("Starting screen recording.")
        os.system("start /min ffmpeg -f gdigrab -i desktop -framerate 30 -vcodec libx264 -preset ultrafast screen_record.mp4")

    def system_control(self, command):
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
            screenshot = pyautogui.screenshot()
            screenshot.save("screenshot.png")
            self.speak("Screenshot taken.")
            self.speak("Screenshot saved.")

    def app_control(self, command):
        if 'open' in command:
            app_name = command.replace('open', '').strip()
            self.speak(f"Opening {app_name}.")
            subprocess.Popen(app_name)
        elif 'close youtube' in command:
            self.speak("Closing YouTube.")
            os.system("taskkill /f /im chrome.exe")
        elif 'close' in command:
            app_name = command.replace('close', '').strip()
            self.speak(f"Closing {app_name}.")
            os.system(f"taskkill /f /im {app_name}.exe")

    def media_control(self, command):
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
        if 'bluetooth' in command:
            self.speak("Opening Bluetooth settings.")
            os.system("start ms-settings:bluetooth")
        elif 'wifi' in command:
            self.speak("Opening Wi-Fi settings.")
            os.system("start ms-settings:network-wifi")

    def process_command(self, command):
        """Override process_command to handle voice commands"""
        if command is None:
            return

        command = command.lower()

        # First try neural network and chatbot understanding from parent class
        super().process_command(command)

        # Handle voice-specific commands
        if 'play song' in command:
            self.speak("Which song would you like to play?")
            song_name = self.take_command()
            if song_name:
                self.play_song(song_name)
        
        elif 'screen record' in command:
            self.screen_record()
        
        elif any(word in command for word in ['restart', 'shutdown', 'refresh']):
            self.system_control(command)
        
        elif any(word in command for word in ['open', 'close']):
            self.app_control(command)
        
        elif any(word in command for word in ['pause', 'play', 'next', 'previous', 'volume', 'mute']):
            self.media_control(command)
        
        elif any(word in command for word in ['bluetooth', 'wifi']):
            self.settings_control(command)
        
        elif 'screenshot' in command:
            screenshot = pyautogui.screenshot()
            screenshot.save("screenshot.png")
            self.speak("Screenshot taken.")

    def run(self):
        """Start the voice assistant"""
        self.speak("Hello! I am Sage, your intelligent voice assistant. How can I help you today?")
        while True:
            command = self.take_command()
            if command and 'exit' in command:
                self.speak("Goodbye! Have a great day!")
                break
            if command:  # Only process if command is not None
                self.process_command(command)

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()
