import streamlit as st
import pymongo
from pymongo import MongoClient
import pandas as pd

# Configure Streamlit page
st.set_page_config(
    page_title="Hotel Finder",
    page_icon="🏨",
    layout="wide"
)

# MongoDB connection
@st.cache_resource
def init_connection():
    try:
        client = MongoClient("mongodb+srv://testdb:dbUsername@cluster.di9pq.mongodb.net/")
        return client
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        return None

# Fetch data from MongoDB
@st.cache_data(ttl=600)  # Cache for 10 minutes
def fetch_hotels():
    client = init_connection()
    if client is None:
        return []
    
    try:
        db = client.hotels
        collection = db.hotel_list
        hotels = list(collection.find({}, {"_id": 0}))  # Exclude _id field
        return hotels
    except Exception as e:
        st.error(f"Failed to fetch hotels: {e}")
        return []

def main():
    st.title("🏨 Hotel Finder")
    st.markdown("---")
    
    # Fetch hotels data
    hotels = fetch_hotels()
    
    if not hotels:
        st.warning("No hotels found or unable to connect to database.")
        return
    
    # Convert to DataFrame for easier filtering
    df = pd.DataFrame(hotels)
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Get unique values for filters
    places = sorted(df['place'].unique()) if 'place' in df.columns else []
    states = sorted(df['state'].unique()) if 'state' in df.columns else []
    
    # Place filter
    selected_places = st.sidebar.multiselect(
        "Select Places:",
        options=places,
        default=places
    )
    
    # State filter
    selected_states = st.sidebar.multiselect(
        "Select States:",
        options=states,
        default=states
    )
    
    # Rating filter
    if 'rating' in df.columns:
        min_rating = float(df['rating'].min())
        max_rating = float(df['rating'].max())
        rating_range = st.sidebar.slider(
            "Rating Range:",
            min_value=min_rating,
            max_value=max_rating,
            value=(min_rating, max_rating),
            step=0.1
        )
    else:
        rating_range = (0, 5)
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_places:
        filtered_df = filtered_df[filtered_df['place'].isin(selected_places)]
    
    if selected_states:
        filtered_df = filtered_df[filtered_df['state'].isin(selected_states)]
    
    if 'rating' in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df['rating'] >= rating_range[0]) & 
            (filtered_df['rating'] <= rating_range[1])
        ]
    
    # Display results
    st.subheader(f"Found {len(filtered_df)} hotels")
    
    if len(filtered_df) == 0:
        st.info("No hotels match your current filters. Try adjusting the filters.")
        return
    
    # Display hotels in a grid layout
    cols = st.columns(2)
    
    for idx, hotel in filtered_df.iterrows():
        col = cols[idx % 2]
        
        with col:
            with st.container():
                st.markdown(
                    f"""
                    <div style="
                        border: 1px solid #ddd; 
                        border-radius: 10px; 
                        padding: 20px; 
                        margin: 10px 0; 
                        background-color: #f9f9f9;
                    ">
                        <h3 style="color: #2E86AB; margin-top: 0;">{hotel.get('name', 'Unknown Hotel')}</h3>
                        <p><strong>📍 Location:</strong> {hotel.get('place', 'N/A')}, {hotel.get('state', 'N/A')}</p>
                        <p><strong>🌍 Country:</strong> {hotel.get('country', 'N/A')}</p>
                        <p><strong>⭐ Rating:</strong> {hotel.get('rating', 'N/A')}/5</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
    # Display summary statistics
    st.markdown("---")
    st.subheader("📊 Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Hotels", len(filtered_df))
    
    with col2:
        if 'rating' in filtered_df.columns:
            avg_rating = filtered_df['rating'].mean()
            st.metric("Average Rating", f"{avg_rating:.1f}")
        else:
            st.metric("Average Rating", "N/A")
    
    with col3:
        unique_places = filtered_df['place'].nunique() if 'place' in filtered_df.columns else 0
        st.metric("Unique Places", unique_places)
    
    with col4:
        unique_states = filtered_df['state'].nunique() if 'state' in filtered_df.columns else 0
        st.metric("Unique States", unique_states)
    
    # Show raw data option
    if st.checkbox("Show raw data"):
        st.dataframe(filtered_df, use_container_width=True)

if __name__ == "__main__":
    main()