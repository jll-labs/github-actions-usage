import requests
from requests.models import Response
import streamlit as st

@st.cache_data(ttl="24h", show_spinner=False)
def download(url, token: str, progress_label: str, query_params: list[str, str] = {}) -> Response:
    download_progress_bar = st.progress(0, text=progress_label) if progress_label else None
    params = query_params or {}
    
    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + token
    }
    if download_progress_bar:
        download_progress_bar.progress(0, text=f'{progress_label}')
    response = __get_data(url, params, headers)
        
    download_progress_bar.empty()
    
    # Check if the request was successful
    if response.status_code == 200:
        return response
    
    else:
        st.write(f"Failed to download data. HTTP Status Code: {response.status_code}\n{response.json()}")
        return None

def __get_data(url, params, headers):
    response = requests.get(url, params=params, headers=headers)
    return response
