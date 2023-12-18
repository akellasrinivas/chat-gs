import dateparser
import stanza
from datetime import datetime, timedelta




def date_parser(text):
    # Download and set up the neural pipeline for English
    stanza.download('en')
    nlp = stanza.Pipeline('en')

    # Process the input text using Stanza NLP
    doc = nlp(text)

    # Extract DATE entities
    ents = []
    for sent in doc.sentences:
        for ent in sent.ents:
            if ent.type == 'DATE':
                ents.append(ent.text)

    # Parse the dates using dateparser
    
    parsed_dates = [dateparser.parse(date) for date in ents]

    # Sort the parsed dates in ascending order
    sorted_dates = sorted(parsed_dates)

    # Set the smallest date as the start_date and the largest date as the end_date
    start_date = sorted_dates[0].strftime('%Y-%m-%d') if sorted_dates else None
    end_date = sorted_dates[-1].strftime('%Y-%m-%d') if sorted_dates else None

    # If both start_date and end_date are the same, set end_date to today's date
    if start_date == end_date and start_date is not None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    # If both start_date and end_date are None, set end_date to today's date and start_date to past 14 days
    if start_date is None and end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')

    return start_date, end_date   