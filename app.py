import streamlit as st
import pandas as pd
import plotly.express as px

# NOTE: Setting up a wide page layout to ensure charts and metrics are easily readable on a single screen.
st.set_page_config(page_title="Hotel Revenue Optimizer", layout="wide")

st.title("🏨 Hotel Length of Stay (LoS) Optimizer")
st.markdown("### Metric 19: Revenue Optimization Index")
st.write("Identify the 'Sweet Spot' for booking durations by balancing high ADR against cancellation risk.")

# --- SECTION 1: DATA LOADING ---
# NOTE: Using st.file_uploader to allow any hotel organization to upload their specific dataset.
uploaded_file = st.file_uploader("Upload Hotel Booking CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # NOTE: Displaying a 10-row preview to confirm successful data ingestion (Requirement 5.2).
    st.subheader("Data Preview")
    st.dataframe(df.head(10))

    # --- SECTION 2: COLUMN MAPPING (REUSABILITY) ---
    st.sidebar.header("🛠️ Column Mapping")
    # NOTE: Using selectboxes to map user columns to the logic ensures the app remains functional 
    # even if the CSV headers are named differently (e.g., 'Price' instead of 'ADR').
    col_adr = st.sidebar.selectbox("ADR/Price Column", df.columns, index=df.columns.get_loc('adr') if 'adr' in df.columns else 0)
    col_cancel = st.sidebar.selectbox("Cancellation Column (0/1)", df.columns, index=df.columns.get_loc('is_canceled') if 'is_canceled' in df.columns else 0)
    col_week = st.sidebar.selectbox("Week Nights", df.columns, index=df.columns.get_loc('stays_in_week_nights') if 'stays_in_week_nights' in df.columns else 0)
    col_weekend = st.sidebar.selectbox("Weekend Nights", df.columns, index=df.columns.get_loc('stays_in_weekend_nights') if 'stays_in_weekend_nights' in df.columns else 0)
    col_segment = st.sidebar.selectbox("Market Segment", df.columns, index=df.columns.get_loc('market_segment') if 'market_segment' in df.columns else 0)

    # --- SECTION 3: INTERACTIVE FILTER ---
    st.sidebar.header("🔍 Analysis Filters")
    # NOTE: Adding a multi-select filter for Market Segment so the manager can compare Corporate vs. Leisure trends.
    segments = df[col_segment].unique().tolist()
    selected_segments = st.sidebar.multiselect("Filter by Segment", segments, default=segments)
    
    # NOTE: Filtering the dataframe based on the user's sidebar selection.
    df_filtered = df[df[col_segment].isin(selected_segments)].copy()

    # --- SECTION 4: METRIC COMPUTATION ---
    # NOTE: Calculating total duration by summing week and weekend nights.
    df_filtered['total_stay'] = df_filtered[col_week] + df_filtered[col_weekend]
    
    # NOTE: Removing 0-night or 0-ADR bookings to ensure the Optimization Index is based on actual revenue events.
    df_filtered = df_filtered[(df_filtered['total_stay'] > 0) & (df_filtered[col_adr] > 0)]

    # NOTE: Grouping by stay length to compute mean price and cancellation probability.
    # NOTE: A volume filter of >= 20 is applied in the app to keep the dashboard responsive and statistically relevant.
    analysis = df_filtered.groupby('total_stay').agg({
        col_adr: 'mean',
        col_cancel: 'mean',
        col_segment: 'count'
    }).rename(columns={col_segment: 'volume'}).reset_index()
    
    analysis = analysis[analysis['volume'] >= 20]

    # NOTE: The formula: ADR * (1 - Cancel Rate). This is the 'Expected Revenue' per night.
    # NOTE: This implementation prioritizes realized cash flow over just looking at the room price.
    analysis['opt_index'] = analysis[col_adr] * (1 - analysis[col_cancel])
    
    # --- SECTION 5: DASHBOARD VISUALS ---
    if not analysis.empty:
        # Find the best performing duration
        best_row = analysis.sort_values('opt_index', ascending=False).iloc[0]

        # Metric Cards
        c1, c2, c3 = st.columns(3)
        c1.metric("Optimal Stay Length", f"{int(best_row['total_stay'])} Nights")
        c2.metric("Expected Rev/Night", f"${best_row['opt_index']:.2f}")
        c3.metric("Cancellation Risk", f"{best_row[col_cancel]*100:.1f}%")

        # Optimization Chart
        # NOTE: Using the 'Icefire' color scale to match the exploratory analysis charts in the notebook.
        fig = px.bar(analysis, x='total_stay', y='opt_index', 
                     title="Revenue Optimization Index by Stay Duration",
                     labels={'opt_index': 'Expected Revenue ($)', 'total_stay': 'Nights'},
                     color='opt_index', color_continuous_scale='Icefire')
        st.plotly_chart(fig, use_container_width=True)

        # --- SECTION 6: ANALYST BRIEFING ---
        st.info(f"""
        **Insight Summary:**
        Bookings for **{int(best_row['total_stay'])} nights** represent your highest quality revenue. 
        Focus marketing efforts on this duration, as these guests are the least likely to leave 
        rooms empty due to cancellations.
        """)
    else:
        st.warning("Not enough data points found for the selected filters.")

else:
    st.info("Please upload the hotel_bookings.csv file to begin.")
