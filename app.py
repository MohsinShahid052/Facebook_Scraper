import os
import subprocess
import asyncio
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd

# Install necessary packages for Chromium
def install_chromium_dependencies():
    dependencies = [
        "libnss3", 
        "libxss1", 
        "libgconf-2-4", 
        "libxi6", 
        "libxrender1", 
        "libxtst6",
        "libxrandr2", 
        "libglib2.0-0", 
        "libasound2"
    ]

    for package in dependencies:
        try:
            subprocess.run(["apt-get", "install", "-y", package], check=True)
        except Exception as e:
            print(f"Failed to install {package}: {e}")

# Function to initialize the Chrome driver
def get_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service('/usr/bin/chromedriver')  # Update if necessary
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Function to scrape Facebook Marketplace
def scrape_facebook_marketplace(city, product, min_price, max_price, city_code_fb):
    driver = get_chrome_driver()
    url = f"https://www.facebook.com/marketplace/{city_code_fb}/search?query={product}&minPrice={min_price}&maxPrice={max_price}&daysSinceListed=1"
    
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Add your scraping logic here
    items = []
    listings = soup.find_all('div', class_='your_listing_class_here')  # Update with the correct class

    for listing in listings:
        title = listing.find('span', class_='your_title_class_here').text  # Update with correct class
        price = listing.find('span', class_='your_price_class_here').text  # Update with correct class
        link = listing.find('a', href=True)['href']

        items.append({
            'Title': title,
            'Price': price,
            'Link': link
        })

    driver.quit()  # Close the driver
    return items

# Streamlit UI
st.title('Facebook Marketplace Scraper')
city = st.text_input('Enter city:')
product = st.text_input('Enter product:')
min_price = st.number_input('Minimum price:', min_value=0)
max_price = st.number_input('Maximum price:', min_value=0)

if st.button('Search'):
    if city and product:
        city_code_fb = 'your_city_code_here'  # Update with the correct city code
        results = scrape_facebook_marketplace(city, product, min_price, max_price, city_code_fb)
        
        if results:
            df = pd.DataFrame(results)
            st.dataframe(df)  # Display the results in a table
        else:
            st.warning('No results found.')
    else:
        st.warning('Please enter both city and product.')

# Run the dependency installation (make sure you have necessary permissions in your environment)
install_chromium_dependencies()
