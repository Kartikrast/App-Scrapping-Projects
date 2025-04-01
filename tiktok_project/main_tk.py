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

class TikTokScraper:
    def __init__(self, counter, input_file):
        self.input_file = input_file
        self.output_file = "tiktok_scraped_data.xlsx"
        self.progress_file = "scraping_progress.json"
        self.data = pd.read_excel(self.input_file)
        self.user_name = []
        self.video_link = []
        self.timestamp = []
        self.counter = counter
        self.setup_driver()
        self.x_paths = {
            'inbox':'//android.widget.TextView[@text="Inbox"]',
            'video_element':'(//android.widget.ImageView[@resource-id="com.zhiliaoapp.musically:id/dd0"])[2]',
            'share_element':'//android.widget.ImageView[@resource-id="com.zhiliaoapp.musically:id/p9x"]',
            'copy_link':'//android.widget.Button[@content-desc="Copy link"]'
        }
        self.load_progress()
    
    def load_progress(self):
        """Load progress from file if it exists"""
        try:
            with open(self.progress_file, 'r') as f:
                progress = json.load(f)
                self.user_name = progress.get('user_name', [])
                self.video_link = progress.get('video_link', [])
                self.timestamp = progress.get('timestamp', [])
        except FileNotFoundError:
            pass
    
    def save_progress(self):
        """Save current progress to file"""
        progress = {
            'user_name': self.user_name,
            'video_link': self.video_link,
            'timestamp': [str(t) for t in self.timestamp]  # Convert datetime to string
        }
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f)

    def setup_driver(self):
        print("Initializing Appium driver...")
        DEVICE_NAME = os.getenv('DEVICE_NAME', '5a7e2e5d')
        DEVICE_UDID = os.getenv('DEVICE_UDID', '5a7e2e5d')
        
        desired_caps = {
            'platformName': 'Android',
            'deviceName': DEVICE_NAME,
            'udid': DEVICE_UDID,
            'platformVersion': '14',
            'appPackage': 'com.zhiliaoapp.musically',
            'appActivity': 'com.ss.android.ugc.aweme.splash.SplashActivity',
            'automationName': 'UiAutomator2',
            'noReset': True,
            'newCommandTimeout': 6000,
            'adbExecTimeout': 20000,
            'autoGrantPermissions': True,
            'disableWindowAnimation': True,
            'unicodeKeyboard': True,
            'resetKeyboard': True,
            "appium:ensureWebviewsHavePages": True,
            "ignoreHiddenApiPolicyError": True
        }
        
        options = UiAutomator2Options().load_capabilities(caps=desired_caps)
        self.driver = webdriver.Remote('http://127.0.0.1:4723/wd/hub', options=options)
        time.sleep(5)

    def swipe(self, direction):
        # Screen dimensions
        screen_size = self.driver.get_window_size()

        width = screen_size['width']
        height = screen_size['height']
        # Calculate start and end points for swipes
        if direction == 'up':
            start_x = width // 2
            start_y = height * 0.8  # Near the bottom
            end_x = width // 2
            end_y = height * 0.2  # Near the top
        elif direction == 'up_short':
            start_x = width // 2
            start_y = height * 0.8  # Near the bottom
            end_x = width // 2
            end_y = height * 0.55  # Near the top
        elif direction == 'down_short':
            start_x = width // 2
            start_y = height * 0.2  # Near the top
            end_x = width // 2
            end_y = height * 0.55  # Near the bottom
        elif direction == 'down':
            start_x = width // 2
            start_y = height * 0.2  # Near the top
            end_x = width // 2
            end_y = height * 0.8  # Near the bottom
        elif direction == 'left':
            start_x = width * 0.8  # Near the right
            start_y = height // 2
            end_x = width * 0.2  # Near the left
            end_y = height // 2
        elif direction == 'right':
            start_x = width * 0.2  # Near the left
            start_y = height // 2
            end_x = width * 0.8  # Near the right
            end_y = height // 2
        else:
            raise ValueError("Invalid direction. Use 'up', 'down', 'left', or 'right'.")
        # Perform the swipe using Appium's driver
        self.driver.swipe(start_x, start_y, end_x, end_y, duration=500)
    

    def find_element(self, dynamic, x_path_name=None, var=None):
        driver = self.driver
        dynamic_check = dynamic
        if dynamic_check == False:
            try:
                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, self.x_paths[x_path_name])))
                return element
            except Exception as e:
                print(e)
                raise
        else:
            try:
                element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, var)))
                return element
            except Exception as e:
                print(e)
                raise

    def navigate_to_inbox(self):
        print("Navigating to Inbox...")
        inbox = self.find_element(False, 'inbox')
        inbox.click()
        time.sleep(2)
        return
    
    def find_and_open_chat(self, user_name):
        print(f"Searching for chat with user: {user_name}")
        var = f'//android.widget.TextView[@resource-id="com.zhiliaoapp.musically:id/tuo" and @text="{user_name}"]'
        while True:
            try:
                user = self.find_element(True, var=var)
                user.click()
                time.sleep(2)
                break
            except:
                self.swipe('up_short')
        return
    
    
    def scroll_chat_and_scrape(self, user_name):
        print(f"Starting the loop for: {user_name}")
        for i in range(self.counter):
            try:
                self.user_name.append(user_name)
                print(user_name)
                video_element = self.find_element(False, 'video_element')
                video_element.click()
                time.sleep(2)
                share_element = self.find_element(False, 'share_element')
                share_element.click()
                time.sleep(2)
                copy_link = self.find_element(False, 'copy_link')
                copy_link.click()
                time.sleep(2)
                link = self.driver.get_clipboard_text()
                self.video_link.append(link)
                self.timestamp.append(datetime.now())
                print("Copied Video Link:", link)
                self.driver.back()
                self.swipe('down_short')
                
                # Save progress after each successful scrape
                self.save_progress()
                
            except Exception as e:
                print(f"Error scraping video {i+1} for {user_name}: {e}")
                continue

    def save_data(self):
        """Save data to Excel and clear progress file"""
        print("Saving scraped data to Excel...")
        df = pd.DataFrame({
            'Account Name':self.user_name,
            'Video Link':self.video_link,
            'Timestamp':self.timestamp
        })
        df.to_excel(self.output_file, index=False)
        print(f"Data saved to {self.output_file}")
        # Clear progress file after successful save
        try:
            os.remove(self.progress_file)
        except:
            pass
    
    def run(self):
        try:
            self.navigate_to_inbox()
            for _, row in self.data.iterrows():
                user_name = row['username']
                try:
                    self.find_and_open_chat(user_name)
                    self.scroll_chat_and_scrape(user_name)
                    self.driver.back()
                    time.sleep(2)
                except Exception as e:
                    print(f"Error processing {user_name}: {e}")
                    continue
            self.save_data()
        except Exception as e:
            print(f"Fatal error: {e}")
        finally:
            self.driver.quit()
            # Save final data if any was collected
            if self.user_name:
                self.save_data()

if __name__ == "__main__":
    scraper = TikTokScraper(2, r"C:\Users\hp\OneDrive\Documents\Code Playground\Shivam Projects\input_tiktok.xlsx")
    scraper.run()