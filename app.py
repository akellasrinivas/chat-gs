import streamlit as st
import subprocess
from scipy.io.wavfile import write as wav_write
from sar_analysis import get_audio, date_parser, LocationExtractor, MapVisualizer

# Function to capture audio and return transcription
def transcribe_audio():
    audio, sr = get_audio()
    wav_write("audio.wav", sr, audio)

    # Use subprocess to run the existing code with the transcribed text
    result = subprocess.run(["python", "sar_analysis.py"], capture_output=True, text=True)
    return result.stdout

def main():
    st.title("SAR Analysis with Voice Input")

    # Button to trigger voice input and analysis
    if st.button("Start Voice Input"):
        st.info("Speak now...")
        transcription = transcribe_audio()
        st.success("Voice input transcribed successfully.")

        # Display transcribed text
        st.subheader("Transcribed Text:")
        st.text(transcription)

        # Extract information using existing code
        start_date, end_date = date_parser(transcription)
        location_extractor = LocationExtractor("/content/SF.csv")
        selected_roi_name = location_extractor.extract_entities(transcription)
        map_visualizer = MapVisualizer()
        static_map, conclusion = map_visualizer.run_analysis(asset_ids, selected_roi_name, start_date, end_date, "/content/SF.csv")

        # Display map and analysis results
        st.subheader("Map Visualization:")
        st.pyplot(static_map.to_pyplot())

        st.subheader("Analysis Results:")
        st.text(conclusion)

if __name__ == "__main__":
    main()
