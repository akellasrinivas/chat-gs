import streamlit as st
import ee
import geemap
import stanza
import dateparser
from datetime import datetime, timedelta
import spacy
import pandas as pd
from nltk.tokenize import word_tokenize
from difflib import get_close_matches

# Set up Earth Engine credentials
service_account = 'isronrsc@isro-407105.iam.gserviceaccount.com'
credentials = ee.ServiceAccountCredentials(service_account, 'isro-407105-31fe627b6f09.json')
ee.Initialize(credentials)

# Module 1: Date Parser Code
def date_parser(text):
    stanza.download('en')
    nlp = stanza.Pipeline('en')
    doc = nlp(text)
    ents = []
    for sent in doc.sentences:
        for ent in sent.ents:
            if ent.type == 'DATE':
                ents.append(ent.text)
    parsed_dates = [dateparser.parse(date) for date in ents]
    sorted_dates = sorted(parsed_dates)
    start_date = sorted_dates[0].strftime('%y-%m-%d') if sorted_dates else None
    end_date = sorted_dates[-1].strftime('%y-%m-%d') if sorted_dates else None
    if start_date == end_date and start_date is not None:
        end_date = datetime.now().strftime('%y-%m-%d')
    if start_date is None and end_date is None:
        end_date = datetime.now().strftime('%y-%m-%d')
        start_date = (datetime.now() - timedelta(days=14)).strftime('%y-%m-%d')
    return start_date, end_date

# Module 2: ROI Extract Code
class LocationExtractor:
    def __init__(self, csv_file_path, threshold=0.8):
        self.nlp = spacy.load('en_core_web_trf')
        self.df = pd.read_csv(csv_file_path)
        self.threshold = threshold

    def fuzzy_match(self, token):
        matches = get_close_matches(token, self.df['ROI_Name'].str.lower().tolist(), n=1, cutoff=self.threshold)
        if matches:
            return matches[0]
        else:
            return None

    def extract_entities(self, user_input):
        user_input_lower = user_input.lower()
        tokens = word_tokenize(user_input_lower)
        best_entity = None
        for token in tokens:
            matched_entity = self.fuzzy_match(token)
            if matched_entity:
                best_entity = matched_entity
                break
        return best_entity

# Module 3: Map Visualizer Code
class MapVisualizer:
    def __init__(self):
        self.Map = geemap.Map()

    def import_and_add_layers(self, asset_id, predefined_layers=None):
        shp = ee.FeatureCollection(asset_id)
        if predefined_layers:
            shp = shp.map(lambda feature: feature.set(predefined_layers))
        return shp

    def add_layers_to_roi(self, shapefile, jrc_layer, sar_collection, start_date, end_date):
        jrc_layer_clipped = jrc_layer.clip(shapefile)
        sar_clipped = sar_collection.filterBounds(shapefile) \
            .filterDate(start_date, end_date).mean().clip(shapefile.geometry())
        self.Map.addLayer(jrc_layer_clipped, {'palette': 'blue'}, 'Clipped JRC Global Surface Water')
        sar_vv = sar_collection.filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
            .filter(ee.Filter.eq('instrumentMode', 'IW')).mean().clip(shapefile.geometry())
        self.Map.addLayer(sar_vv, {'bands': ['VV'], 'min': -20, 'max': 0, 'gamma': 1.4}, 'Clipped SAR (VV) Layer')
        sar_vh = sar_collection.filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
            .filter(ee.Filter.eq('instrumentMode', 'IW')).mean().clip(shapefile.geometry())
        self.Map.addLayer(sar_vh, {'bands': ['VH'], 'min': -20, 'max': 0, 'gamma': 1.4}, 'Clipped SAR (VH) Layer')

    def visualize_roi(self, selected_roi, center_object_zoom=10):
        self.Map.centerObject(selected_roi, center_object_zoom)
        self.Map.addLayerControl()

    def display_map(self):
        st.pyplot(self.Map.to_image())

    def map_roi(self, start_date, end_date, roi_name):
        df = pd.read_csv('/content/ISROP.csv')
        asset_ids = df['ROI_path'].tolist()
        shapefiles = [self.import_and_add_layers(asset_id) for asset_id in asset_ids]
        jrc_layer = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence')
        sar_collection = ee.ImageCollection('COPERNICUS/S1_GRD').filterDate('2020-06-01', '2020-10-01')
        valid_roi_names = df['ROI_Name'].tolist()
        if roi_name in valid_roi_names:
            selected_roi_index = valid_roi_names.index(roi_name)
            selected_roi = shapefiles[selected_roi_index]
            self.add_layers_to_roi(selected_roi, jrc_layer, sar_collection, start_date, end_date)
            self.visualize_roi(selected_roi)
            self.display_map()
        else:
            st.warning("Invalid ROI name. Please enter a valid ROI name.")

def main():
    st.title("Water Monitoring Application")

    # Get user input using Streamlit text input
    user_text = st.text_input("Enter text:")

    if st.button("Run Workflow"):
        # Module 1: Date Parser Code
        start_date, end_date = date_parser(user_text)

        # Module 2: ROI Extract Code
        location_extractor = LocationExtractor('/content/ISROP.csv')
        extracted_location = location_extractor.extract_entities(user_text)

        # Module 3: Map Visualizer Code
        map_visualizer = MapVisualizer()
        map_visualizer.map_roi(start_date, end_date, extracted_location)

if __name__ == "__main__":
    main()
