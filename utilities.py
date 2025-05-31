from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
import os
import re
import time
import uuid
import pandas as pd
from random import randint

encoding_type = 'utf-8-sig'

def scrape_drive():
    # 自動下載ChromeDriver
    service = ChromeService(executable_path=ChromeDriverManager().install())

    # 關閉通知提醒
    # chrome_options = webdriver.ChromeOptions()
    # # chrome_options.add_argument(r"user-data-dir=C:\Users\USER\AppData\Local\Google\Chrome\User Data")
    
    chrome_options = Options()
    chrome_options.add_argument("--user-data-dir=C:\\temp\\chrome-user-data") #使用temp資料夾，或是其他你指定的資料夾
    chrome_options.add_argument("--disable-extensions") #停用擴充功能
    # chrome_options.add_argument(f"user-data-dir={user_data_dir}")
    # chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

    prefs = {"profile.default_content_setting_values.notifications" : 2}
    chrome_options.add_experimental_option("prefs",prefs)

    # 開啟瀏覽器
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    time.sleep(randint( 7, 15))

    try:
        driver.maximize_window()
    except:
        pass
    
    time.sleep(1)

    return driver
