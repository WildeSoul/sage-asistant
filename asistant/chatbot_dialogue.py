import nltk
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from nlp_processor import NLPProcessor

# Download required NLTK data
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
nltk.download('maxent_ne_chunker')
nltk.download('words')

class ChatbotDialogue:
    def __init__(self):
        self.conversation_history = {}
        self.intents = self.load_intents()
        self.vectorizer = TfidfVectorizer()
        self.response_vectors = None
        self.command_synonyms = self.load_command_synonyms()
        self.nlp_processor = NLPProcessor()
        self.initialize_vectors()

    def load_intents(self):
        """Load or create default intents"""
        intents_file = "intents.json"
        if not os.path.exists(intents_file):
            default_intents = {
                "intents": [
                    {
                        "tag": "greeting",
                        "patterns": ["hi", "hello", "hey", "good morning", "good evening"],
                        "responses": ["Hello! I'm Sage, how can I help you?", "Hi there! Sage at your service!", "Hey! What can I do for you today?"]
                    },
                    {
                        "tag": "goodbye",
                        "patterns": ["bye", "goodbye", "see you", "see you later"],
                        "responses": ["Goodbye! Have a wonderful day!", "Take care! Call me if you need anything!", "Goodbye! It was nice talking to you!"]
                    },
                    {
                        "tag": "thanks",
                        "patterns": ["thank you", "thanks", "appreciate it"],
                        "responses": ["You're welcome!", "Happy to help!", "Anytime! That's what I'm here for!"]
                    },
                    {
                        "tag": "help",
                        "patterns": ["help", "what can you do", "how do you work"],
                        "responses": ["I'm Sage, your AI assistant! I can help you with tasks like playing music, taking screenshots, controlling your system, and much more. Just ask me what you need!", 
                                    "As Sage, I can assist you with various tasks including system control, music playback, web searches, and more. What would you like me to do?"]
                    },
                    {
                        "tag": "identity",
                        "patterns": ["who are you", "what's your name", "what are you"],
                        "responses": ["I'm Sage, your intelligent voice assistant! I can help you with various tasks like playing music, opening applications, and more.", 
                                    "My name is Sage, and I'm here to help you with tasks like controlling your computer, playing music, and answering questions!",
                                    "I'm Sage, a voice-enabled AI assistant designed to make your life easier!"]
                    },
                    {
                        "tag": "ai_info",
                        "patterns": ["what is ai", "what is artificial intelligence", "explain ai"],
                        "responses": ["AI, or Artificial Intelligence, is technology that enables computers to perform tasks that typically require human intelligence. I'm an AI assistant that can help you with various tasks!", 
                                    "Artificial Intelligence (AI) refers to computer systems that can perform tasks requiring human-like intelligence, such as understanding speech, making decisions, and solving problems. I'm an example of an AI assistant!",
                                    "AI is a field of computer science focused on creating intelligent machines that can learn and solve problems. I use AI to help you with tasks like playing music, controlling your computer, and answering questions!"]
                    }
                ]
            }
            with open(intents_file, 'w') as f:
                json.dump(default_intents, f, indent=4)
            return default_intents
        else:
            with open(intents_file, 'r') as f:
                return json.load(f)

    def load_command_synonyms(self):
        """Load or create default command synonyms"""
        synonyms_file = "command_synonyms.json"
        if not os.path.exists(synonyms_file):
            default_synonyms = {
                "time": ["time", "clock", "hour", "current time", "what time"],
                "open": ["open", "launch", "start", "run", "execute"],
                "close": ["close", "exit", "quit", "terminate", "stop"],
                "play": ["play", "start playing", "begin playing", "listen to"],
                "volume": ["volume", "sound", "audio level"],
                "screenshot": ["screenshot", "capture screen", "take picture", "snap"],
                "refresh": ["refresh", "reload", "update", "renew"],
                "search": ["search", "look up", "find", "google", "query"],
                "train": ["train", "teach", "educate", "learn"],
                "test": ["test", "check", "verify", "validate", "try"],
                "create": ["create", "make", "generate", "build", "establish"],
                "add": ["add", "insert", "include", "put in"],
                "show": ["show", "display", "present", "reveal"],
                "help": ["help", "assist", "support", "guide", "aid"]
            }
            with open(synonyms_file, 'w') as f:
                json.dump(default_synonyms, f, indent=4)
            return default_synonyms
        else:
            with open(synonyms_file, 'r') as f:
                return json.load(f)

    def initialize_vectors(self):
        """Initialize TF-IDF vectors for responses"""
        all_patterns = []
        for intent in self.intents['intents']:
            all_patterns.extend(intent['patterns'])
        if all_patterns:
            self.response_vectors = self.vectorizer.fit_transform(all_patterns)

    def get_wordnet_synonyms(self, word):
        """Get synonyms for a word using WordNet"""
        synonyms = set()
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                synonyms.add(lemma.name().lower())
        return list(synonyms)

    def normalize_command(self, command):
        """Normalize command by finding the base command for any variant"""
        # First, check direct matches in command_synonyms
        for base_command, variants in self.command_synonyms.items():
            if any(variant in command.lower() for variant in variants):
                return base_command

        # If no direct match, try fuzzy matching
        words = word_tokenize(command.lower())
        normalized_words = []
        
        for word in words:
            best_match = None
            highest_ratio = 0
            
            # Check each base command and its variants
            for base_command, variants in self.command_synonyms.items():
                # Try matching with base command
                ratio = fuzz.ratio(word, base_command)
                if ratio > highest_ratio and ratio > 80:  # 80% similarity threshold
                    highest_ratio = ratio
                    best_match = base_command
                
                # Try matching with variants
                for variant in variants:
                    ratio = fuzz.ratio(word, variant)
                    if ratio > highest_ratio and ratio > 80:
                        highest_ratio = ratio
                        best_match = base_command
            
            normalized_words.append(best_match if best_match else word)
        
        return ' '.join(normalized_words)

    def expand_patterns(self, patterns):
        """Expand patterns with synonyms"""
        expanded_patterns = set()
        for pattern in patterns:
            expanded_patterns.add(pattern)
            words = word_tokenize(pattern)
            
            # Generate variations using synonyms
            for word in words:
                synonyms = self.get_wordnet_synonyms(word)
                for synonym in synonyms:
                    new_pattern = pattern.replace(word, synonym)
                    expanded_patterns.add(new_pattern)
        
        return list(expanded_patterns)

    def preprocess_text(self, text):
        # Tokenize and lemmatize using NLTK
        tokens = word_tokenize(text.lower())
        return ' '.join([token for token in tokens if token.isalpha()])

    def understand(self, user_input):
        """Understand the user's input and determine the appropriate response"""
        # First, try to understand as a command
        analysis = self.nlp_processor.analyze_command(user_input)
        if analysis['command_type']:
            return {
                'command_type': analysis['command_type'],
                'response': analysis.get('response', 'Command understood.')
            }
            
        # If not a command, try to match with intents
        processed_input = self.preprocess_text(user_input)
        input_vector = self.vectorizer.transform([processed_input])
        similarities = cosine_similarity(input_vector, self.response_vectors)
        
        max_sim_idx = np.argmax(similarities)
        max_similarity = similarities[0][max_sim_idx]
        
        # If similarity is too low, try fuzzy matching
        if max_similarity < 0.3:
            all_patterns = []
            for intent in self.intents['intents']:
                all_patterns.extend([(pattern, intent) for pattern in intent['patterns']])
            
            best_match = process.extractOne(user_input, [p[0] for p in all_patterns])
            if best_match[1] > 70:
                pattern_idx = [p[0] for p in all_patterns].index(best_match[0])
                matched_intent = all_patterns[pattern_idx][1]
                return {
                    'command_type': 'chat',
                    'response': np.random.choice(matched_intent['responses'])
                }
            return {
                'command_type': 'chat',
                'response': "I'm not sure I understand. Could you please rephrase that?"
            }
        
        # Find the matching intent
        pattern_count = 0
        for intent in self.intents['intents']:
            if max_sim_idx < pattern_count + len(intent['patterns']):
                return {
                    'command_type': 'chat',
                    'response': np.random.choice(intent['responses'])
                }
            pattern_count += len(intent['patterns'])
        
        return {
            'command_type': 'chat',
            'response': "I'm not sure I understand. Could you please rephrase that?"
        }

    def add_command_pattern(self, command_type, verbs=None, nouns=None, phrases=None):
        """Add new command patterns to NLP processor"""
        self.nlp_processor.add_command_pattern(command_type, verbs, nouns, phrases)

    def add_context_pattern(self, context_type, patterns):
        """Add new context patterns to NLP processor"""
        self.nlp_processor.add_context_pattern(context_type, patterns)

    def get_command_context(self, command):
        """Get contextual information for a command"""
        return self.nlp_processor.extract_context(command)

    def get_command_entities(self, command):
        """Get entities from a command"""
        return self.nlp_processor.extract_entities(command)

    def respond(self, intent_tag):
        if not intent_tag:
            return "I'm not sure I understand. Could you please rephrase that?"
        
        # Find the matching intent
        for intent in self.intents['intents']:
            if intent['tag'] == intent_tag:
                # Randomly select a response
                return np.random.choice(intent['responses'])
        
        return "I'm not sure how to respond to that."

    def remember_state(self, user_input, response):
        # Generate a simple timestamp-based ID
        conversation_id = len(self.conversation_history)
        self.conversation_history[conversation_id] = {
            'input': user_input,
            'response': response,
            'intent': self.understand(user_input)
        }

    def add_intent(self, tag, patterns, responses):
        """Add a new intent with expanded patterns"""
        # Expand patterns with synonyms
        expanded_patterns = self.expand_patterns(patterns)
        
        new_intent = {
            "tag": tag,
            "patterns": expanded_patterns,
            "responses": responses
        }
        
        self.intents['intents'].append(new_intent)
        
        # Save updated intents to file
        with open('intents.json', 'w') as f:
            json.dump(self.intents, f, indent=4)
        
        # Reinitialize vectors with new patterns
        self.initialize_vectors()

    def add_command_synonym(self, base_command, synonyms):
        """Add new synonyms for a command"""
        if base_command not in self.command_synonyms:
            self.command_synonyms[base_command] = []
        
        self.command_synonyms[base_command].extend(synonyms)
        self.command_synonyms[base_command] = list(set(self.command_synonyms[base_command]))
        
        # Save updated synonyms
        with open('command_synonyms.json', 'w') as f:
            json.dump(self.command_synonyms, f, indent=4)

    def get_conversation_history(self):
        """Return the conversation history"""
        return self.conversation_history
