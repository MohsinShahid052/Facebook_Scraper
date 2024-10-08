
import streamlit as st
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import re
import pandas as pd
import time
from fuzzywuzzy import fuzz
from datetime import datetime
from selenium.webdriver.chrome.options import Options

# Function to run the web scraping for exact matches
def scrape_facebook_marketplace_exact(city, product, min_price, max_price, city_code_fb, sleep_time):
    return scrape_facebook_marketplace(city, product, min_price, max_price, city_code_fb, exact=True, sleep_time=sleep_time)

# Function to run the web scraping for partial matches
def scrape_facebook_marketplace_partial(city, product, min_price, max_price, city_code_fb, sleep_time):
    return scrape_facebook_marketplace(city, product, min_price, max_price, city_code_fb, exact=False, sleep_time=sleep_time)

# Main scraping function with an exact match flag
def scrape_facebook_marketplace(city, product, min_price, max_price, city_code_fb, exact, sleep_time=5):
    # Configure Chrome options
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--headless")  # Run in headless mode (without GUI)
    
    # If undetected_chromedriver cannot detect the version, explicitly set the Chrome binary path
    # Update this path according to your system's Chrome installation
    chrome_options.binary_location = "C:/Program Files/Google/Chrome/Application/chrome.exe"
    
    # Initialize the undetected Chrome WebDriver
    browser = uc.Chrome(options=chrome_options)
    
    # Setup URL
    exact_param = 'true' if exact else 'false'
    url = f"https://www.facebook.com/marketplace/{city_code_fb}/search?query={product}&minPrice={min_price}&maxPrice={max_price}&daysSinceListed=1&exact={exact_param}"
    browser.get(url)

    # Close cookies and pop-ups
    try:
        close_btn = browser.find_element(By.XPATH, '//div[@aria-label="Decline optional cookies" and @role="button"]')
        close_btn.click()
    except:
        pass

    try:
        close_btn = browser.find_element(By.XPATH, '//div[@aria-label="Close" and @role="button"]')
        close_btn.click()
    except:
        pass

    # Scroll down to load more items
    last_height = browser.execute_script("return document.body.scrollHeight")
    while True:
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_time)
        new_height = browser.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Retrieve the HTML
    html = browser.page_source
    browser.close()

    # Use BeautifulSoup to parse the HTML
    soup = BeautifulSoup(html, 'html.parser')
    links = soup.find_all('a')

    # Filter links based on search criteria
    if exact:
        final_links = [link for link in links if product.lower() in link.text.lower() and city.lower() in link.text.lower()]
    else:
        fuzz_threshold = 70
        final_links = [
            link for link in links 
            if fuzz.partial_ratio(product.lower(), link.text.lower()) > fuzz_threshold and city.lower() in link.text.lower()
        ]

    # Extract product data
    extracted_data = []
    for prod_link in final_links:
        url = prod_link.get('href')
        text = '\n'.join(prod_link.stripped_strings)
        lines = text.split('\n')

        numeric_pattern = re.compile(r'\d[\d, •]*')
        price = None

        for line in lines:
            match = numeric_pattern.search(line)
            if match:
                price_str = match.group()
                price = float(price_str.replace(',', ''))
                break

        title = lines[-2] if len(lines) > 1 else ""
        location = lines[-1] if lines else ""

        extracted_data.append({
            'title': title,
            'price': price,
            'location': location,
            'url': url
        })

    base = "https://web.facebook.com/"
    for items in extracted_data:
        items['url'] = base + items['url']

    # Create a DataFrame
    items_df = pd.DataFrame(extracted_data)
    return items_df, len(links)

# Streamlit UI
st.set_page_config(page_title="Facebook Marketplace Scraper", layout="wide")
st.title("🏷️ Facebook Marketplace Scraper")
st.markdown("""
Welcome to the Facebook Marketplace Scraper!  
Easily find products in your city and filter by price.  
""")

# Input fields with better layout and styling
with st.form(key='input_form'):
    col1, col2 = st.columns(2)
    
    with col1:
        city = st.text_input("City", placeholder="Enter city name...")
        product = st.text_input("Product", placeholder="What are you looking for?")
    
    with col2:
        min_price = st.number_input("Minimum Price", min_value=0, value=0, step=1)
        max_price = st.number_input("Maximum Price", min_value=0, value=1000, step=1)
    
    city_code_fb = st.number_input("City Code for Facebook Marketplace", value=0, min_value=0)
    sleep_time = st.number_input("Sleep Time (seconds)", min_value=0.0, value=2.0, step=0.1)

    submit_button = st.form_submit_button(label="🔍 Scrape Data")

# Buttons to trigger the scraping
if submit_button:
    if city and product and min_price <= max_price:
        with st.spinner("Scraping matches..."):
            items_df, total_links = scrape_facebook_marketplace_exact(city, product, min_price, max_price, city_code_fb, sleep_time)

        if not items_df.empty:
            st.success(f"Found {len(items_df)} match(es)! 🎉")
            st.write("### Match Results:")
            st.dataframe(items_df)

            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"{product}_{city}_{current_time}.csv"
            
            # Option to download the results
            csv = items_df.to_csv(index=False)
            st.download_button("💾 Download CSV", csv, csv_filename, "text/csv")
        else:
            st.warning("No match results found. Please try different parameters.")
    else:
        st.error("Please ensure all fields are filled correctly and that Minimum Price is less than or equal to Maximum Price.")
