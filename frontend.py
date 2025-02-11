# Import required libraries
import streamlit as st
from apify_client import ApifyClient
import re
import os
import pandas as pd
import io

# Set page configuration
st.set_page_config(
    page_title="About Us Data Scraper",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Custom CSS styling using markdown
st.markdown("""
    <style>
        .main-title {
            color: #007BFF;
            font-size: 2.5em;
            text-align: center;
            padding: 20px;
        }
        .result-section {
            margin: 20px 0;
            padding: 15px;
            border-radius: 10px;
            background-color: #F8F9F9;
        }
        .footer {
            text-align: center;
            padding: 10px;
            color: #666;
        }
        .stButton>button {
            background-color: #007BFF !important;  /* Blue color */
            color: white !important;
            font-size: 18px !important;
            font-weight: bold !important;
            padding: 12px !important;
            border-radius: 8px !important;
            width: 100% !important;
            text-align: center !important;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.2) !important;
            border: none !important;
            cursor: pointer !important;
        }
        .stButton>button:hover {
            background-color: #0056b3 !important; /* Darker blue on hover */
        }
        .stDownloadButton>button {
            background-color: #007BFF !important;  /* Blue color */
            color: white !important;
            font-size: 18px !important;
            font-weight: bold !important;
            padding: 12px !important;
            border-radius: 8px !important;
            width: 100% !important;
            text-align: center !important;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.2) !important;
            border: none !important;
            cursor: pointer !important;
        }
        .stDownloadButton>button:hover {
            background-color: #0056b3 !important; /* Darker blue on hover */
        }
    </style>
""", unsafe_allow_html=True)

APIFY_TOKEN = st.secrets["APIFY_TOKEN"]

st.markdown('<h1 class="main-title">🔎 About Us Data Scraper</h1>', unsafe_allow_html=True)
st.markdown("""
    **Extract the 'About Us' page data from firms!**  
""")

# URL input section
with st.container():
    st.write("### 🖇️ Upload File or Enter URLs Manually")
    
    uploaded_file = st.file_uploader(
        "Upload a text or CSV file containing URLs (one per line):", 
        type=["txt", "csv"], 
        accept_multiple_files=False
    )

    uploaded_urls = []
    if uploaded_file is not None:
        try:
            file_content = uploaded_file.read().decode("utf-8").strip()
            uploaded_urls = file_content.split("\n") 
        except Exception as e:
            st.error(f"Error reading file: {e}")

    urls = st.text_area(
        "Or enter URLs manually (one per line):",
        value="\n".join(uploaded_urls) if uploaded_urls else "",
        height=150,
        placeholder="Example URLs:\nhttps://www.company-website.com\nhttps://www.another-company.com",
        help="Upload a file or manually enter URLs."
    )

def validate_urls(url_list):
    url_regex = re.compile(
        r'^(?:http|ftp)s?://'  
        r'(?:\S+(?::\S*)?@)?'
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
        r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return all(url_regex.match(url.strip()) for url in url_list if url.strip())

# Processing function
def run_apify_actor(urls):
    client = ApifyClient(APIFY_TOKEN)
    
    run_input = {
        "start_urls": [{"url": url.strip()} for url in urls if url.strip()],
        "extractDetailedInformation": True,
        "maxResults": 50,
    }
    
    with st.spinner("🚀 Gathering 'About Us' data..."):
        run = client.actor("winning_ics/guides-about-us").call(run_input=run_input)
    
    dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    return dataset_items

# Main processing flow
if st.button("Run Crawler 🚀"):
    url_list = urls.split('\n')
    if not urls.strip():
        st.error("Please enter at least one URL")
    elif not validate_urls(url_list):
        st.error("Invalid URL format detected. Please check your URLs.")
    else:
        try:
            results = run_apify_actor(url_list)
            
            if not results:
                st.warning("No data found. Try different URLs.")
            else:
                st.success(f"Found {len(results)} 'About Us' pages!")
                st.markdown("---")

                df = pd.DataFrame(results)

                df = df.rename(columns={
                    "content": "About Us Content",
                    "date": "Date",
                    "title": "Title",
                    "url": "URL"
                })

                for col in ["overseas_investment_related", "supporting_evidence"]:
                    if col in df.columns:
                        df.drop(col, axis=1, inplace=True)

                st.dataframe(df, use_container_width=True)

                excel_buffer = io.BytesIO()
                df.to_excel(excel_buffer, index=False, sheet_name="About Us Results")
                excel_buffer.seek(0)  

                st.markdown("### 📤 Export Results")

                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.download_button(
                        label="📥 Download Results as Excel",
                        data=excel_buffer,
                        file_name="AboutUsResults.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                st.markdown("### Results")
                for idx, item in enumerate(results, 1):
                    with st.expander(f"🏢 Company #{idx}: {item.get('title', 'Untitled')}"):
                        st.caption(f"**Date**: {item.get('date', 'N/A')}")
                        st.write(f"**About Us Content**: {item.get('content', 'No content available')}")
                        st.markdown(f"[🔗 Visit Page]({item.get('url', '#')})", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error running crawler: {str(e)}")

st.markdown("""
    <div class="footer">
        ℹ️ Results are not stored.
    </div>
""", unsafe_allow_html=True)
