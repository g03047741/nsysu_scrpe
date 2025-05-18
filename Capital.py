from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import re
import time
import uuid
import pandas as pd
from random import randint
from utilities import *

def filter_unique_links_in_group(group):
    # 檢查該組內的公司連結是否都是唯一的
    # is_unique 對於只有一個元素的 Series 也會回傳 True，
    # 但因為我們是從 df_with_duplicated_names (公司名稱至少出現兩次) 來的，所以群組大小至少為2。
    return group['公司連結'].is_unique
    # 或者使用 nunique，更明確表達 "唯一連結的數量等於群組內的項目數量"
    # return group['公司連結'].nunique() == len(group)

def company_link_unmatch(df):
    duplicated_names_mask = df.duplicated(subset=['公司名稱'], keep=False)
    df_with_duplicated_names = df[duplicated_names_mask]

    if df_with_duplicated_names.empty:
        print("沒有任何公司名稱出現重複，因此無法找到公司重複但連結不重複的項目。")
    else:
        print("\n「公司名稱」有重複的列 (初步篩選):")
        print(df_with_duplicated_names)
        print("-" * 50)

        result_df = df_with_duplicated_names.groupby('公司名稱').filter(filter_unique_links_in_group)

        if not result_df.empty:
            print("\n公司名稱重複，但公司連結不重複的項目:")
            print(result_df.sort_values(by=['公司名稱', '公司連結']))

            return result_df
        else:
            print("\n在公司名稱重複的項目中，沒有找到公司連結不重複的情況。")
            print("這可能表示所有公司名稱重複的項目，其公司連結也恰好是重複的，")
            print("或者原始資料中沒有公司名稱重複的情況。")

def get_Company_from_jobList():
    company = pd.read_csv("company_info.csv", encoding=encoding_type)
    job_links = pd.read_csv("job_links_104.csv", encoding=encoding_type)
    company.rename(columns={'公司': '公司名稱'}, inplace=True)

    companies_to_check_mask = ~job_links['公司名稱'].isin(company['公司名稱'])
    new_companies_from_job_links_df = job_links[companies_to_check_mask]

    print("\n僅存在於 job_links DataFrame 中的公司資料 (初步篩選):")
    print(new_companies_from_job_links_df)

    # 處理是否有新的公司需要新增
    if not new_companies_from_job_links_df.empty:
        # 2. (可選但通常是好的做法) 如果 job_links 中對於同一個新公司有多筆記錄，
        #    我們可能只想新增一筆代表性的記錄。這裡保留第一次出現的。
        new_companies_from_job_links_df = new_companies_from_job_links_df.drop_duplicates(subset=['公司名稱'], keep='first')
        print("\n去除重複後，準備處理的新公司資料:")
        print(new_companies_from_job_links_df)
        
        data_formatted_to_add = new_companies_from_job_links_df.reindex(columns=company.columns)

        print("\n依照 company 欄位格式調整後，準備新增的資料:")
        print(data_formatted_to_add)

        # 4. 將格式化後的新的公司資料附加到 company DataFrame
        #    pd.concat 用於合併 DataFrames。
        #    ignore_index=True 會重新產生索引，避免索引重複。
        company_updated = pd.concat([company, data_formatted_to_add], ignore_index=True)
        
        print("\n更新後的 company DataFrame:")
        print(company_updated)
    else:
        print("\njob_links 中沒有新的公司需要新增到 company DataFrame。")
        company_updated = company.copy() # 若無新資料，則 company_updated 等於原始 company

    company_updated.to_csv("company_info_merge_jobLinks.csv", encoding=encoding_type, index=False)
    

def merger_jobList_companyList():
    company = pd.read_csv("company_info.csv", encoding=encoding_type)
    job_links = pd.read_csv("job_links_104.csv", encoding=encoding_type)
    company.rename(columns={'公司': '公司名稱'}, inplace=True)
    result = pd.merge(job_links, company, how='left', on='公司名稱')
    # print(result)
    df_with_uuid = result.assign(uuid=[str(uuid.uuid4()) for _ in range(len(result))])
    df_with_uuid = df_with_uuid[['uuid','公司名稱','公司連結','產業類別','資本額','員工人數','職缺連結','經歷','學歷','工作地點']]
    df_with_uuid.to_csv("result_3.csv", encoding=encoding_type, index=False)

def Capital_104():
   
    company = pd.read_csv("result_3.csv", encoding=encoding_type)
    Capital_nan = company[company[['資本額']].isnull().any(axis=1)]
    # print(Capital_nan)
    Capital_nan = Capital_nan[['uuid','公司名稱','公司連結']]
    # print(rows_with_nan)
    Capital_nan_search = Capital_nan.drop_duplicates()
    # print(Capital_nan_search.shape)
    # 開始呼叫爬蟲
    driver = scrape_drive()
    company.set_index('uuid', inplace=True)
    for i in Capital_nan_search.values.tolist():
        data_extracted = {}
        url = i[2]
        # print(f"Fetching page {i[1]}: {url}") 
        driver.get(url)
        time.sleep(3)
        data_extracted['uuid'] = i[0]
        industry_category_element = driver.find_element(By.XPATH, "//h3[text()='產業類別']/ancestor::div[contains(@class, 'intro-table__head')]/following-sibling::div[contains(@class, 'intro-table__data')][1]//a")
        data_extracted['產業類別'] = industry_category_element.text.strip()

        # 2. 取得資本額
        # 資本額的文字直接在 <p> 標籤內，但包含了連結文字，我們需要處理一下
        capital_element = driver.find_element(By.XPATH, "//h3[text()='資本額']/ancestor::div[contains(@class, 'intro-table__head')]/following-sibling::div[contains(@class, 'intro-table__data')][1]/p")
        full_capital_text = capital_element.text.strip()
        # "300億 經濟部商業司查詢" -> 取 "300億"
        data_extracted['資本額'] = full_capital_text.split(' ')[0]

        # 3. 取得員工人數
        # 員工人數的文字在 <p> 標籤內
        employee_count_element = driver.find_element(By.XPATH, "//h3[text()='員工人數']/ancestor::div[contains(@class, 'intro-table__head')]/following-sibling::div[contains(@class, 'intro-table__data')][1]/p")
        data_extracted['員工人數'] = employee_count_element.text.strip()

        # print("\n提取到的資料:")

        # print(data_extracted)
        uuid_to_update = data_extracted['uuid']
        data_to_set = {key: value for key, value in data_extracted.items() if key != 'uuid'}

        # 檢查 uuid 是否存在於索引中
        if uuid_to_update in company.index:
            # 逐一更新欄位
            for column, value in data_to_set.items():
                if column in company.columns: # 確保 DataFrame 中有這個欄位才更新
                    company.loc[uuid_to_update, column] = value
                else:
                    print(f"警告: 欄位 '{column}' 不存在於 DataFrame 中，無法更新。")
            print(f"\n成功更新 uuid 為 '{uuid_to_update}' 的資料。")
        else:
            print(f"\n錯誤: uuid '{uuid_to_update}' 在 DataFrame 索引中未找到，無法更新。")
        
        # print(company)
        # input()
        
    company.to_csv("result_4.csv", encoding=encoding_type, index=False)
    driver.quit()

def Capital_gov():
    try:
        # 開啟瀏覽器
        driver = scrape_drive

        url = f"https://findbiz.nat.gov.tw/fts/query/QueryBar/queryInit.do"
        driver.get(url)

        # --- 要輸入的資料 ---
        search_term = "邦尼"
        input_field_id = "qryCond"

        wait = WebDriverWait(driver, 10) # 等待最多10秒

        # 等待輸入框出現並且可見
        input_element = wait.until(EC.visibility_of_element_located((By.ID, input_field_id)))
        print(f"找到輸入框 (ID: {input_field_id})")
        input_element.clear()

        # 輸入資料
        input_element.send_keys(search_term)
        print(f"已在輸入框中輸入: '{search_term}'")

        search_button_id = "qryBtn"

        print(f"正在嘗試定位搜尋按鈕 (ID: {search_button_id})...")
        # 等待按鈕可被點擊
        search_button = wait.until(EC.element_to_be_clickable((By.ID, search_button_id)))
        print(f"找到搜尋按鈕 (ID: {search_button_id})")

        search_button.click()
        print("已點擊搜尋按鈕")

        # 等待一些時間讓搜尋結果載入 (可選，但通常有用)
        print("等待搜尋結果載入...")
        time.sleep(5) # 簡單等待，更好的方式是等待某個結果元素出現

        # 重新載入頁面
        print("正在重新載入頁面...")
        driver.refresh()
        print("頁面已重新載入")
        time.sleep(3)
        more_button = driver.find_element(By.CSS_SELECTOR, "span[class='moreLinkMouseOut']")

        more_button.click()
        
    except Exception as e:
        print(f"發生錯誤: {e}")
    
    finally:
        # 關閉瀏覽器 (可選，如果您想在結束後保持瀏覽器打開以進行檢查，可以註釋掉這行)
        # input("按 Enter 鍵關閉瀏覽器...") # 執行完畢後等待使用者按 Enter
        input()
        if 'driver' in locals() and driver is not None:
            driver.quit()
            print("瀏覽器已關閉")


if __name__ == "__main__":

    get_Company_from_jobList()
    # Capital_104()