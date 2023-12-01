import streamlit as st
import ee
import geemap

# Initialize the Earth Engine module.
ee.Initialize()

# Authentication
if not ee.data._credentials:
    st.warning("You need to authenticate Earth Engine. Click the button below to authenticate.")
    if st.button("Authenticate Earth Engine"):
        ee.Authenticate()
        ee.Initialize()

# Function to import a shapefile from GEE asset and add predefined layers
def import_and_add_layers(asset_id, predefined_layers=None):
    # Import the shapefile as an Earth Engine FeatureCollection
    shp = ee.FeatureCollection(asset_id)

    # Add predefined layers
    if predefined_layers:
        shp = shp.map(lambda feature: feature.set(predefined_layers))

    return shp

# Function to add JRC Global Surface Water Mapping Layer, v1.4, to a specific ROI
def add_jrc_layer_to_roi(shapefile, jrc_layer, map_obj):
    # Clip JRC layer to the current ROI
    jrc_layer_clipped = jrc_layer.clip(shapefile)

    # Add the clipped JRC layer to the map
    map_obj.addLayer(shapefile, {}, 'Selected ROI')
    map_obj.addLayer(jrc_layer_clipped, {'palette': 'blue'}, 'Clipped JRC Global Surface Water')

# Function to add SAR (COPERNICUS) layer mean for a specific date range to a given ROI
def add_sar_layer_to_clipped_roi(shapefile, date_range, map_obj):
    # Load the SAR (COPERNICUS) ImageCollection
    sar_collection = ee.ImageCollection('COPERNICUS/S1_GRD') \
        .filterBounds(shapefile) \
        .filterDate(ee.DateRange(date_range.split(' to ')[0], date_range.split(' to ')[1]))

    # Calculate the mean for the specified date range
    sar_mean = sar_collection.mean()

    # Clip SAR mean to the current ROI
    sar_mean_clipped = sar_mean.clip(shapefile)

    # Add the clipped SAR layer mean to the map
    map_obj.addLayer(sar_mean_clipped, {'bands': ['VV'], 'min': -20, 'max': 0, 'gamma': 1.4}, 'SAR (COPERNICUS) Mean')

# Main Streamlit app
def main():
    st.title("GEE Chatbot Interface")

    # List of asset IDs for the shapefiles in your GEE account
    asset_ids = [
        'projects/ee-my-srinivas/assets/himayatsagar',
        'projects/ee-my-srinivas/assets/hussansagar',
        'projects/ee-my-srinivas/assets/osmansagar',
        'projects/ee-my-srinivas/assets/sriramsagar',
        'projects/ee-my-srinivas/assets/karanja'
    ]

    # Import and add layers for each shapefile
    shapefiles = [import_and_add_layers(asset_id) for asset_id in asset_ids]

    # Add JRC Global Surface Water Mapping Layer, v1.4, only to the imported shapefiles
    jrc_layer = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence')

    # User input for selecting a specific ROI and date range
    user_query = st.text_input("Enter your query:")

    # Extract ROI name and date range from the user's query
    try:
        roi_name = user_query.split(" of ")[-1].split(" from ")[0].strip()
        date_range = user_query.split(" from ")[-1].strip()
    except IndexError:
        st.warning("Invalid query format. Please enter a valid query.")
        roi_name = None
        date_range = None

    # Check if ROI name and date range are extracted successfully
    if roi_name and date_range:
        # Check if the entered ROI name is valid
        valid_roi_names = ['himayatsagar', 'hussansagar', 'osmansagar', 'sriramsagar', 'karanja']
        if roi_name.lower() in valid_roi_names:
            # Filter shapefiles based on the user's specified ROI
            selected_roi = shapefiles[valid_roi_names.index(roi_name.lower())]

            # Visualize the shapefiles and add the clipped JRC layer to each ROI
            Map = geemap.Map()
            add_jrc_layer_to_roi(selected_roi, jrc_layer, Map)
            add_sar_layer_to_clipped_roi(selected_roi, date_range, Map)
            Map.centerObject(selected_roi, 10)  # Center the map on the selected ROI
            Map.addLayerControl()

            # Display the map using Streamlit's map function
            st.pydeck_chart(Map)

        else:
            st.warning("Invalid ROI name. Please enter a valid ROI name.")

    else:
        st.warning("Invalid query format. Please enter a valid query.")

if __name__ == "__main__":
    main()
