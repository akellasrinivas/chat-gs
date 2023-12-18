import nltk
nltk.download('punkt')
import pandas as pd
from nltk.tokenize import word_tokenize
from difflib import get_close_matches
import spacy



class LocationExtractor:

    def __init__(self, csv_file_path, threshold=0.8):
        # Load the English language model for spaCy
        self.nlp = spacy.load('en_core_web_trf')
        # Load the CSV file for fuzzy matching
        self.df = pd.read_csv(csv_file_path)
        self.threshold = threshold

    def fuzzy_match(self, token):
        # Use difflib to find the closest match
        matches = get_close_matches(token, self.df['ROI_Name'].str.lower().tolist(), n=1, cutoff=self.threshold)

        # Check if there is a match
        if matches:
            return matches[0]
        else:
            return None

    def extract_entities(self, user_input):
        # Convert user input to lowercase
        user_input_lower = user_input.lower()
        # Tokenize the user input
        tokens = word_tokenize(user_input_lower)

        # Initialize variables to store the best matching entity
        best_entity = None

        # Iterate through the tokens and perform fuzzy matching
        for token in tokens:
            matched_entity = self.fuzzy_match(token)
            if matched_entity:
                best_entity = matched_entity
                break  # Stop after finding the first match

        # Return the best matching entity
        return best_entity
