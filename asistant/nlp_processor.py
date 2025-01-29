import nltk
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk import ne_chunk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from fuzzywuzzy import fuzz
import json
import os

# Download required NLTK data
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')

class NLPProcessor:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.load_language_patterns()
        
    def load_language_patterns(self):
        """Load or create language patterns for intent matching"""
        patterns_file = "language_patterns.json"
        if not os.path.exists(patterns_file):
            self.patterns = {
                "command_patterns": {
                    "time": {
                        "verbs": ["tell", "show", "give", "what"],
                        "nouns": ["time", "clock", "hour"],
                        "phrases": ["what time", "current time", "time now"]
                    },
                    "weather": {
                        "verbs": ["check", "tell", "what"],
                        "nouns": ["weather", "temperature", "forecast"],
                        "phrases": ["weather like", "temperature now", "going to rain"]
                    },
                    "music": {
                        "verbs": ["play", "start", "begin", "listen"],
                        "nouns": ["song", "music", "track", "audio"],
                        "phrases": ["play song", "start music", "play track"]
                    },
                    "system": {
                        "verbs": ["open", "close", "launch", "start", "stop", "terminate"],
                        "nouns": ["program", "app", "application", "window"],
                        "phrases": ["open program", "launch app", "start application"]
                    }
                },
                "context_patterns": {
                    "time": ["now", "current", "today", "tonight", "morning", "evening"],
                    "location": ["here", "there", "nearby", "around", "local"],
                    "quantity": ["one", "two", "three", "few", "many", "some", "all"]
                }
            }
            with open(patterns_file, 'w') as f:
                json.dump(self.patterns, f, indent=4)
        else:
            with open(patterns_file, 'r') as f:
                self.patterns = json.load(f)

    def tokenize_and_tag(self, text):
        """Tokenize and POS tag the input text"""
        try:
            tokens = word_tokenize(text.lower())
            return pos_tag(tokens)
        except LookupError:
            # Fallback to simple tokenization if NLTK resources are missing
            tokens = text.lower().split()
            return [(token, 'UNKNOWN') for token in tokens]

    def extract_entities(self, text):
        """Extract named entities from text using NLTK"""
        try:
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            try:
                named_entities = ne_chunk(pos_tags)
            except LookupError:
                named_entities = pos_tags
        except LookupError:
            tokens = text.split()
            pos_tags = [(token, 'UNKNOWN') for token in tokens]
            named_entities = pos_tags
        
        entities = {
            'numbers': [],
            'names': [],
            'other': []
        }
        
        current_number = []
        for word, tag in pos_tags:
            if tag.startswith('CD') or word.replace('.','',1).isdigit():  # Cardinal number or numeric string
                try:
                    num = float(word)
                    entities['numbers'].append(num)
                except ValueError:
                    entities['other'].append(word)
            elif tag.startswith('NN'):  # Noun
                entities['names'].append(word)
            else:
                entities['other'].append(word)
                
        return entities

    def get_synonyms(self, word):
        """Get synonyms for a word using WordNet"""
        synonyms = set()
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                synonyms.add(lemma.name().lower())
        return list(synonyms)

    def analyze_command(self, text):
        """Analyze the command and extract relevant information"""
        tokens_tags = self.tokenize_and_tag(text)
        words = [word.lower() for word, _ in tokens_tags]
        
        # Extract command type
        command_type = None
        highest_similarity = 0
        
        for cmd_type, patterns in self.patterns["command_patterns"].items():
            # Check verbs
            for verb in patterns["verbs"]:
                if verb in words:
                    similarity = fuzz.ratio(text.lower(), verb)
                    if similarity > highest_similarity:
                        highest_similarity = similarity
                        command_type = cmd_type
            
            # Check nouns
            for noun in patterns["nouns"]:
                if noun in words:
                    similarity = fuzz.ratio(text.lower(), noun)
                    if similarity > highest_similarity:
                        highest_similarity = similarity
                        command_type = cmd_type
            
            # Check phrases
            for phrase in patterns["phrases"]:
                if phrase in text.lower():
                    similarity = fuzz.ratio(text.lower(), phrase)
                    if similarity > highest_similarity:
                        highest_similarity = similarity
                        command_type = cmd_type
        
        # Extract entities and context
        entities = self.extract_entities(text)
        
        return {
            'command_type': command_type if highest_similarity > 60 else None,
            'entities': entities,
            'tokens': words
        }

    def get_context(self, text):
        """Extract contextual information from text"""
        context = {
            'time': None,
            'location': None,
            'quantity': None
        }
        
        words = word_tokenize(text.lower())
        
        for context_type, patterns in self.patterns["context_patterns"].items():
            for pattern in patterns:
                if pattern in words:
                    context[context_type] = pattern
                    break
        
        return context

    def add_command_pattern(self, command_type, verbs=None, nouns=None, phrases=None):
        """Add new command patterns"""
        if command_type not in self.patterns["command_patterns"]:
            self.patterns["command_patterns"][command_type] = {
                "verbs": [],
                "nouns": [],
                "phrases": []
            }
            
        if verbs:
            self.patterns["command_patterns"][command_type]["verbs"].extend(verbs)
        if nouns:
            self.patterns["command_patterns"][command_type]["nouns"].extend(nouns)
        if phrases:
            self.patterns["command_patterns"][command_type]["phrases"].extend(phrases)
            
        # Save updated patterns
        with open("language_patterns.json", 'w') as f:
            json.dump(self.patterns, f, indent=4)
    
    def add_context_pattern(self, context_type, patterns):
        """Add new context patterns"""
        if context_type not in self.patterns["context_patterns"]:
            self.patterns["context_patterns"][context_type] = []
            
        self.patterns["context_patterns"][context_type].extend(patterns)
        
        # Save updated patterns
        with open("language_patterns.json", 'w') as f:
            json.dump(self.patterns, f, indent=4)
