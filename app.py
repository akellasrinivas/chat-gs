import ee
import geemap
from datetime import datetime
import streamlit as st

service_account = 'service-nrsc@ee-my-srinivas.iam.gserviceaccount.com'
credentials = ee.ServiceAccountCredentials(service_account, 'ee-my-srinivas-ef2bfb61b2f9.json')
ee.Initialize(credentials)

# Define the SARAnalyzer class
class SARAnalyzer:
    def __init__(self):
        self.sar_collection = None
        self.selected_roi = None
        self.start_date = None
        self.end_date = None

    def import_and_add_layers(self, asset_id, predefined_layers=None):
        shp = ee.FeatureCollection(asset_id)

        if predefined_layers:
            shp = shp.map(lambda feature: feature.set(predefined_layers))

        return shp

    def add_sar_layer_to_roi(self, shapefile, start_date, end_date, map_obj):
        sar_collection = self.load_sar_collection(start_date, end_date)

        sar_vv = sar_collection.filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
            .filter(ee.Filter.eq('instrumentMode', 'IW')).mean().clip(shapefile.geometry())

        map_obj.addLayer(sar_vv, {'bands': ['VV'], 'min': -20, 'max': 0, 'gamma': 1.4}, 'Clipped SAR (VV) Layer')

        return sar_vv

    def load_sar_collection(self, start_date, end_date):
        sar_collection = ee.ImageCollection('COPERNICUS/S1_GRD') \
            .filterDate(ee.Date(start_date), ee.Date(end_date)) \
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
            .filter(ee.Filter.eq('instrumentMode', 'IW'))

        self.sar_collection = sar_collection
        return sar_collection

    def calculate_water_spread(self, image, threshold):
        water_mask = image.lt(threshold)

        water_area_m2 = water_mask.multiply(ee.Image.pixelArea()).reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=self.selected_roi.geometry(),
            scale=30
        ).getInfo()['VV']

        water_area_km2 = water_area_m2 / 1e6

        return water_area_km2

    def calculate_yearly_water_spread(self, image_collection, threshold):
        yearly_water_spread = []

        for year in range(self.start_date.year, self.end_date.year + 1):
            start_date = f"{year}-01-01"
            end_date = f"{year + 1}-01-01"

            year_collection = image_collection.filterDate(ee.Date(start_date), ee.Date(end_date))
            yearly_water_spread.append(self.calculate_water_spread(year_collection.mean(), threshold))

        return yearly_water_spread

    def calculate_max_water_spread(self, selected_roi_name):
        # Set a large date range to cover all available data
        start_date_max = self.start_date.strftime("%Y-%m-%d")
        end_date_max = self.end_date.strftime("%Y-%m-%d")

        sar_collection_max = self.load_sar_collection(start_date_max, end_date_max)

        # Calculate maximum water spread in the ROI
        sar_vv_max = self.add_sar_layer_to_roi(self.selected_roi, start_date_max, end_date_max, geemap.Map())
        max_water_spread = self.calculate_water_spread(sar_vv_max, -15)

        return max_water_spread

    def compare_water_spread(self, water_spread_user_input, max_water_spread):
        st.write(f'The waterspread of {self.selected_roi.getInfo()["id"].split("/")[-1].capitalize()} in the given duration is: {water_spread_user_input:.2f} square kilometers.')

        if water_spread_user_input > max_water_spread:
            st.write(f'Water spread increased in the user input duration by {water_spread_user_input - max_water_spread:.2f} square kilometers.')
        elif water_spread_user_input < max_water_spread:
            st.write(f'Water spread decreased in the user input duration by {max_water_spread - water_spread_user_input:.2f} square kilometers.')
        else:
            st.write('Water spread remained the same in the user input duration.')

    def run_analysis(self, asset_ids, selected_roi_name, start_date, end_date):
        valid_roi_names = ['himayatsagar', 'hussansagar', 'osmansagar', 'sriramsagar']
        if selected_roi_name in valid_roi_names:
            selected_roi_index = valid_roi_names.index(selected_roi_name)
            self.selected_roi = self.import_and_add_layers(asset_ids[selected_roi_index])

            static_map = geemap.Map(width=800, height=600)
            sar_vv = self.add_sar_layer_to_roi(self.selected_roi, start_date, end_date, static_map)
            static_map.centerObject(self.selected_roi, 10)

            # Display the map using Streamlit
            st.map(static_map)

            # Set the start_date and end_date attributes
            self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
            self.end_date = datetime.strptime(end_date, "%Y-%m-%d")

            # Calculate water spread for the user input duration
            water_spread_user_input = self.calculate_water_spread(sar_vv, -15)

            # Calculate maximum water spread in the ROI
            max_water_spread = self.calculate_max_water_spread(selected_roi_name)
            self.compare_water_spread(water_spread_user_input, max_water_spread)

            yearly_water_spread = self.calculate_yearly_water_spread(self.sar_collection, -15)

            # Generate chart for yearly water spread
            st.line_chart(data=yearly_water_spread, use_container_width=True)

        else:
            st.error("Invalid ROI name. Please enter a valid ROI name.")


# List of asset IDs for the shapefiles in your GEE account
asset_ids = [
    'projects/ee-my-srinivas/assets/himayatsagar',
    'projects/ee-my-srinivas/assets/hussansagar',
    'projects/ee-my-srinivas/assets/osmansagar',
    'projects/ee-my-srinivas/assets/sriramsagar'
]

# User input for selecting a specific ROI and specifying the date range for SAR data
selected_roi_name = st.sidebar.selectbox("Select ROI", ['himayatsagar', 'hussansagar', 'osmansagar', 'sriramsagar'])
start_date = st.sidebar.date_input("Start Date", datetime(2022, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime(2022, 12, 31))

sar_analyzer = SARAnalyzer()

if st.button("Run Analysis"):
    sar_analyzer.run_analysis(asset_ids, selected_roi_name, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

