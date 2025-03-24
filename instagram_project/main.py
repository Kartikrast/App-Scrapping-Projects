"""
In this program we will be creating an instagram scrapper to send messages to users.
"""

# Library imports
import re
import time
import numpy as np
import pandas as pd
import os
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Local imports
from x_paths import x_paths

handler = RotatingFileHandler('app.log', maxBytes=5000, backupCount=2)
logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('appium').setLevel(logging.WARNING)


# Initializing Driver
# Device information (keep these as environment variables)
DEVICE_NAME = os.getenv('DEVICE_NAME', 'R9ZWA07928P')
DEVICE_UDID = os.getenv('DEVICE_UDID', 'R9ZWA07928P')

desired_caps = {
    'platformName': 'Android',
    'deviceName': DEVICE_NAME,
    'udid': DEVICE_UDID,
    'platformVersion': '14',
    'appPackage': 'com.instagram.android',
    'appActivity': '.activity.MainTabActivity',
    'automationName': 'UiAutomator2',
    'noReset': True,
    'newCommandTimeout': 6000,  # Reduced timeout
    'adbExecTimeout': 20000,  # Increased timeout
    'autoGrantPermissions': True,
    'disableWindowAnimation': True,
    'unicodeKeyboard': True,
    'resetKeyboard': True,
    "appium:ensureWebviewsHavePages": True
}

try:
    # First, check if device is connected
    logging.info("Checking if device is connected...")
    import subprocess
    adb_devices = subprocess.check_output('adb devices').decode()
    # logging.info(adb_devices)
    
    if DEVICE_UDID not in adb_devices:
        # logging.error(f"Device {DEVICE_UDID} not found. Please connect your device and enable USB debugging.")
        raise Exception(f"Device {DEVICE_UDID} not found.")
    
    options = UiAutomator2Options().load_capabilities(caps=desired_caps)
    driver = webdriver.Remote('http://127.0.0.1:4723/wd/hub', options=options)
    # logging.info("Driver initialized successfully")
    
    # Add a small delay to ensure the app is fully loaded
    import time
    time.sleep(5)
    
except Exception as e:
    # logging.error(f"Error initializing driver: {str(e)}")
    raise


# Function to find the element
def find_element(x_path_name):
    try:
        logging.info(f"Attempting to locate element: {x_path_name}")
        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, x_paths[x_path_name])))
        logging.info(f"Successfully located element: {x_path_name}")
        return element
    except Exception as e:
        logging.error(f"Failed to locate element {x_path_name}: {str(e)}")
        raise

# Function to save data incrementally
def save_data(user_id, message_sent, date):
    try:
        output = pd.DataFrame({
            'user_id': user_id,
            'message_sent': message_sent,
            'date': date
        })
        if os.path.exists('output.csv'):
            existing_data = pd.read_csv('output.csv')
            output = pd.concat([existing_data, output], ignore_index=True)
        output.to_csv('output.csv', index=False)
        logging.info("Data saved successfully")
    except Exception as e:
        logging.error(f"Failed to save data: {str(e)}")
        raise

# Main Program
user_names = ['navneet_ks_', 'candidpavscene', 'sevainternal']
user_id = []
message_sent = []
date = []

try:
    search_explore = find_element('search_explore')
    search_explore.click()
    logging.info("Successfully clicked search_explore")
    time.sleep(1)
    
    search_bar = find_element('search_bar')
    search_bar.click()
    logging.info("Successfully clicked search_bar")
    time.sleep(1)
    
    count = 0
    for username in user_names: 
        try:
            logging.info(f"Processing user: {username}")
            search_bar_text = find_element('search_bar_text')
            search_bar_text.click()
            search_bar_text.clear()
            search_bar_text.send_keys(username)
            user_id.append(username)
            logging.info(f"Successfully searched for user: {username}")
            
            search_result = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f'//android.widget.TextView[@resource-id="com.instagram.android:id/row_search_user_username"]'))
            )
            search_result.click()
            logging.info("Successfully selected search result")
            time.sleep(3)
            
            try:
                message_button = find_element('message_button')
                message_button.click()
                logging.info("Successfully clicked message button")
                time.sleep(2)
            except:
                logging.info("Message button not found, skipping to next profile...")
                driver.back()
                continue
            
            message_text = find_element('message_text')
            message_text.click()
            message = f'test: {count}'
            message_text.send_keys(message)
            message_sent.append(message)
            logging.info(f"Successfully entered message: {message}")
            time.sleep(2)
            
            send_button = find_element('send_button')
            send_button.click()
            logging.info("Successfully sent message")
            date.append(datetime.now())
            time.sleep(2)
            
            # Save data after each successful message
            save_data(user_id, message_sent, date)
            
            # Go back to search
            driver.back()
            driver.back()
            logging.info("Successfully returned to search page")
            
            count += 1
        except Exception as e:
            logging.error(f"Error processing user {username}: {str(e)}")
            # Continue with next user even if one fails
            continue

except Exception as e:
    logging.error(f"Critical error in main program: {str(e)}")
    raise

finally:
    # Ensure data is saved even if program crashes
    if user_id:
        try:
            save_data(user_id, message_sent, date)
        except Exception as e:
            logging.error(f"Failed to save final data: {str(e)}")

logging.info("Program execution completed")