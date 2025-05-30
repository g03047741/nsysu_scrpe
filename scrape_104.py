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
from utilities import scrape_drive
# from config import *
# from sheets_ import upload_to_sheets


def job_list_page(page_count):
    driver = scrape_drive()
    filename = "job_links_104.csv" 
    link_list = []
    company_list = []
    company_name = []
    experience_list = []
    education_list = []
    location_list = []
    print("Starting link scraping...")
    try:
        for page in range(1, page_count+1): # Loop through pages 1 to 100
            url = f"https://www.104.com.tw/jobs/search/?jobcat=2007000000&jobsource=index_s&mode=l&page={page}"
            print(f"Fetching page {page}: {url}") 
            driver.get(url)
            # Consider using WebDriverWait instead of fixed sleep for better efficiency and reliability
            time.sleep(randint(7, 15))

            try:
                # Find all job link elements on the current page
                links = driver.find_elements(By.CSS_SELECTOR, "a[data-gtm-joblist='職缺-職缺名稱']")
                page_links_count = 0
                for i in links:
                    href = i.get_attribute("href")
                    if href: # Ensure the href attribute exists
                        link_list.append(href)
                        page_links_count += 1
                print(f"Found {page_links_count} links on page {page}.")

                company = driver.find_elements(By.CSS_SELECTOR, "a[data-gtm-joblist='職缺-公司名稱']")
                for i in company:
                    href = i.get_attribute("href")
                    # print(href)
                    company_list.append(href)
                    company_name.append(i.text)
                experience = driver.find_elements(By.CSS_SELECTOR, "div.list-small__experience")
                for i in experience:
                    # print(i.text)
                    experience_list.append(i.text)
                education = driver.find_elements(By.CSS_SELECTOR, "div.list-small__education")
                for i in education:
                    # print(i.text)
                    education_list.append(i.text)
                location = driver.find_elements(By.CSS_SELECTOR, "div.list-small__location")
                for i in location:
                    # print(i.text)
                    location_list.append(i.text)

            except Exception as e:
                print(f"Error finding links on page {page}: {e}")
    except Exception as e:
        print(f"An error occurred during scraping: {e}")
    finally:

        data = {
            "職缺連結":link_list,
            "公司名稱":company_name,
            "公司連結":company_list,
            "經歷":experience_list,
            "學歷":education_list,
            "工作地點":location_list
        }

        df = pd.DataFrame(data)
        df['uuid'] = df.apply(lambda row: uuid.uuid4(), axis=1)
        print(df)
        df.to_csv(filename,index=False)

    driver.quit()
    
    return df

def search_company_list(pages):
    driver = scrape_drive()
 
    company = []
    capital = []
    employee_count= []
    industry_type = []
    for page in range(1, pages+1):
        url = f"https://www.104.com.tw/company/search/?jobcat=2007000000&jobsource=n_my104_search&mode=s&page={page}"
        print(f"Fetching page {page}: {url}") 
        driver.get(url)
        # 初始化變數來儲存結果
        time.sleep(randint(7, 15)) 
        company_link_element = driver.find_elements(By.XPATH, "//div[contains(@class, 'company-name-link')]/a[contains(@class, 'company-name-link--pc')]")
        for i in company_link_element:
            company.append(i.text)

        try:
            # 定位包含所有資訊的父層 div 元素
            info_container = driver.find_elements(By.XPATH, "//div[contains(@class, 'company-list__infoTags')]")
            for i in info_container:
                
                # 找到該 div 下所有的 span 元素
                info_spans = i.find_elements(By.XPATH, './span')
                industry_type_temp = info_spans[1]
                industry_type.append(industry_type_temp.text.strip())
                capital_temp = info_spans[2]
                capital.append(capital_temp.text.strip())
                employee_count_temp = info_spans[3]
                employee_count.append(employee_count_temp.text.strip())
        
        except Exception as e:
            print("錯誤：無法定位到指定的 HTML 元素。請檢查 XPath 或頁面結構。")
            print(e)
            # 若找不到元素，可以選擇建立一個包含 "未找到" 的 DataFrame
            df = pd.DataFrame({
                '資本額': ["未找到"],
                '員工人數': ["未找到"],
                '產業類別': ["未找到"]
            })
        except Exception as e:
            print(f"發生了未預期的錯誤: {e}")
            # 若發生其他錯誤，可以選擇建立一個包含 "錯誤" 的 DataFrame
            df = pd.DataFrame({
                '資本額': ["錯誤"],
                '員工人數': ["錯誤"],
                '產業類別': ["錯誤"]
            })

        if not (len(company) == len(capital) and len(capital) == len(employee_count) and len(employee_count) == len(industry_type)):
            input() 
            
        data_dict = {
            '公司名稱':company,
            '資本額': capital,
            '員工人數': employee_count,
            '產業類別': industry_type
        }
        # --- 輸出 DataFrame ---
        print("--- 提取結果 (DataFrame) ---")
        df = pd.DataFrame(data_dict)
        print(df)
        
        filename = 'company_info.csv'
        file_exists_initially = os.path.exists(filename)

        write_header = not file_exists_initially
        df.to_csv(filename,
                index=False,            
                mode='a',             # 'a' = append (附加)
                    header=write_header,  # 根據是否為第一次寫入決定是否加表頭
                    encoding='utf-8-sig'  # 保持編碼一致性
                )
    driver.quit()

def job_info(link_list_df):
 
    df = link_list_df[link_list_df['status']!='Done']
    # link_list = df.values.tolist()
    csv_filename_append = 'output.csv'
    driver = scrape_drive()

    time.sleep(3)
    company_link = []
    for row in df.itertuples(index=True, name='PandasRow'):
        job_list = []
        company_list = []
        job_category = []
        needs_person = []
        salary_list = []
        skill = []
        job_description_list = []


        current_index = row.Index
        item_url = row.job_link
        education = [row.education]
        location = [row.location]
        experience = [row.experience]
        processed_result_status  = ''
        # print(current_index,item_url,current_status)

        driver.get(item_url)
        time.sleep(randint(3, 4))

        try:
            jobs = driver.find_element(By.CSS_SELECTOR, "div.job-header__title h1")
            
            # print(jobs.text)
            job_list.append(jobs.text)
    
            company = driver.find_element(By.CSS_SELECTOR, "a[data-gtm-head='公司名稱']")
            # print(company.get_attribute('title'))
            company_list.append(company.get_attribute('title'))
            company_link.append(company.get_attribute('href'))

            job_discript = driver.find_element(By.XPATH, "//div[contains(@class, 'job-address')]")
            salary = job_discript.get_attribute('salary')
            # print(salary)
            #薪資
            salary_list.append(salary)
            #需求人數
            needemp = job_discript.get_attribute('needemp')
            needs_person.append(needemp)

            job_category_elements = driver.find_element(By.XPATH, "//div[contains(@class, 'job-description-table')]")
            job_temp = job_category_elements.find_elements(By.XPATH, "//div[contains(@class, 'list-row')]")
            job_cat_temp = job_temp[0]
            job_cat = job_cat_temp.find_element(By.XPATH, "//div[contains(@class, 'list-row__data')]")
            job_category.append(job_cat.text)

            skill_table = driver.find_element(By.XPATH, "//div[contains(@class, 'job-requirement-table')]")
            skill_head = skill_table.find_elements(By.XPATH, ".//div[contains(@class, 'list-row__head')]")
            skill_data = skill_table.find_elements(By.XPATH, ".//div[contains(@class, 'list-row__data')]")

            for i in range(len(skill_head)):
                # print(skill_head[i].text)
                if skill_head[i].text == "工作技能":
                    skill.append(skill_data[i].text)

            job_description = driver.find_element(By.XPATH, "//p[contains(@class, 'job-description__content')]")
            job_description_list.append(job_description.text)
            
        except Exception as e:
            print(f"抓取 '職務類別' 時發生錯誤: {e}")
            processed_result_status = 'Error'

        if processed_result_status == '':
            processed_result_status = 'Done'

        df.loc[current_index, 'status'] = processed_result_status


        print(f"準備逐筆附加資料到 '{csv_filename_append}'...")
        
        data = {
            "職缺名稱":job_list,
            "公司":company_list,
            "需求人數":needs_person,
            "職位類別":job_category,
            "工作待遇":salary_list,
            "工作技能":skill,
            "學歷要求":education,
            "地點":location,
            "經歷要求":experience,
            "工作內容":job_description_list,
        }
        
        try:
            df_row = pd.DataFrame(data)

            file_exists_initially = os.path.exists(csv_filename_append)

            write_header = not file_exists_initially
        
            df_row.to_csv(
                csv_filename_append,
                mode='a',             # 'a' = append (附加)
                header=write_header,  # 根據是否為第一次寫入決定是否加表頭
                index=False,          # 通常附加時也不需要索引
                encoding='utf-8-sig'  # 保持編碼一致性
            )
         
            file_exists_initially = True # 更新狀態，表示檔案現在肯定存在了

        except Exception as e:
            print(e)
            print(data)

    csv_filename_basic = 'link_status.csv'
    #用來看哪邊沒有上傳到
    try:
        df.to_csv(csv_filename_basic)
        print(f"\n已將 DataFrame 寫入到 '{csv_filename_basic}' (包含索引和表頭)")
        # 你可以打開 basic_output.csv 看看，會發現多了第一欄的索引(0, 1, 2)
    except Exception as e:
        print(f"\n寫入檔案 '{csv_filename_basic}' 時發生錯誤: {e}")

    driver.quit()

def read_file_to_df(txt_filename):
    encoding_type = 'utf-8'
    try:
        df = pd.read_csv(txt_filename, encoding=encoding_type)
        print("檔案讀取成功！ DataFrame 內容：")
        print(df)

    except FileNotFoundError:
        print(f"錯誤：找不到檔案 '{txt_filename}'。")
        exit()
    except Exception as e:
        print(f"讀取檔案時發生錯誤: {e}")
        exit()
    # 提供一個新的欄位名稱列表
    new_headers = ['job_link','company','company_link','experience','education','location']

    # 直接賦值給 df.columns
    df.columns = new_headers
    # --- 新增 'status' 欄位 ---
    print("\n新增 'status' 欄位...")

    # 方法一：賦予所有行相同的值 (最常見)
    default_status = 'pending' # 你可以設定任何預設值
    df['status'] = default_status
    print(f"已新增 'status' 欄位，並將所有值設為 '{default_status}'。")
    print(df)
    return df

def Combine_dataframe():

    file_path1 = 'output.csv'
    file_path2 = 'company_info.csv'

    df1 = pd.read_csv(file_path1, encoding='utf-8')
    df2 = pd.read_csv(file_path2, encoding='utf-8')

    merged_left = pd.merge(df1, df2, on='公司', how='left')

    print("--- Left Join 結果 ---")
    print(merged_left)

    merged_left.to_csv('104.csv',index=False, encoding='utf-8-sig')

def get_element_text_by_label(driver, label_text):
    """
    Finds an element based on the text of its preceding label (h3)
    and returns the text content of the associated data element.

    Args:
        driver: The Selenium WebDriver instance.
        label_text: The exact text of the h3 label (e.g., '產業類別').

    Returns:
        The text content of the data element, or None if not found.
    """
    try:
        # XPath Explanation:
        # //h3[text()='{label_text}'] : Find the h3 element with the exact text.
        # /parent::div                 : Go up to its parent div (the 'head' div).
        # /following-sibling::div[contains(@class, 'intro-table__data')][1] : Find the first following sibling div that contains the 'intro-table__data' class.
        # /p                           : Go down to the p tag inside the data div (adjust if data is in another tag like 'a').
        #
        # For "產業類別", the data is inside p/a, so we adjust the path slightly
        # For "資本額", the main text is in 'p', but there's also an 'a'. Getting text from 'p' might include the link text.
        # For "員工人數", the data is directly in 'p'.

        base_xpath = f"//h3[text()='{label_text}']/parent::div/following-sibling::div[contains(@class, 'intro-table__data')][1]"

        if label_text == "產業類別":
            # Data is inside p > a tag
            data_element = driver.find_element(By.XPATH, f"{base_xpath}//a")
        elif label_text == "資本額":
             # Data is inside p tag, might include extra text from 'a' tag. Get text from 'p'.
             data_element = driver.find_element(By.XPATH, f"{base_xpath}/p")
        elif label_text == "員工人數":
             # Data is directly inside p tag
             data_element = driver.find_element(By.XPATH, f"{base_xpath}/p")
        else:
            # Default: try finding a 'p' tag, might need adjustment for other fields
            data_element = driver.find_element(By.XPATH, f"{base_xpath}/p")

        full_text = data_element.text

        # Specific cleaning for '資本額' if needed (remove the link text)
        if label_text == "資本額":
             # Find the link text within the paragraph, if it exists
             try:
                 link_element = data_element.find_element(By.XPATH, ".//a")
                 link_text = link_element.text
                 # Remove the link text and surrounding whitespace
                 return full_text.replace(link_text, '').strip()
             except NoSuchElementException:
                 # No link found, return the full text trimmed
                 return full_text.strip()
        else:
            return full_text.strip() # General trimming for other fields

    except NoSuchElementException:
        print(f"元素未找到: {label_text}")
        return None
    except Exception as e:
        print(f"獲取 '{label_text}' 時發生錯誤: {e}")
        return None

def fix_missing():
    file_path1 = '104.csv'
    file_path2 = 'job_links_104.csv'
    df = pd.read_csv(file_path1, encoding='utf-8')
    df1 = pd.read_csv(file_path2, encoding='utf-8')
    # df1.fillna('NA')
  
    rows_with_nan = df[df[['資本額']].isnull().any(axis=1)]
    # print(rows_with_nan)

    # find_data = rows_with_nan['公司'].values.tolist()
    # find_data = list(set(find_data))
    rows_with_nan = rows_with_nan[['公司']]
    # print(rows_with_nan)
    df_unique_all = rows_with_nan.drop_duplicates()
    # print(df_unique_all)
 

    df1 = df1[['公司連結','公司名稱']]
    # print(df1)
    df1_renamed = df1.rename(columns={
        '公司名稱': '公司'
    })
    df1_unique_all = df1_renamed.drop_duplicates(subset=['公司'], keep='first')
    # print(df1_unique_all)

    merged_df_inner = pd.merge(df_unique_all, df1_unique_all, on='公司', how='inner')
    print(merged_df_inner)

    merged_df_= merged_df_inner.values.tolist()

    driver = scrape_drive()
    scraped_data = []
    for i in merged_df_:
        print(i)
        url = i[1]
        driver.get(url)
        # 初始化變數來儲存結果
        time.sleep(randint(7, 15)) 
        industry_category = get_element_text_by_label(driver, "產業類別")
        capital = get_element_text_by_label(driver, "資本額")
        employee_count = get_element_text_by_label(driver, "員工人數")
        # --- Print the results ---
        print(f"產業類別: {industry_category}")
        print(f"資本額: {capital}")
        print(f"員工人數: {employee_count}")

        scraped_data.append({
            '公司':i[0],
            '產業類別':industry_category,
            '資本額':capital,
            '員工人數':employee_count
        })
    df_scraped = pd.DataFrame(scraped_data)
    df_scraped.to_csv('company_capital.csv',index=False,encoding='utf-8-sig')
    df_updated = pd.merge(df, df_scraped, on='公司', how='left')
    print(df_updated)
    df_updated.to_csv('104_update_company.csv',index=False,encoding='utf-8-sig')
 
    #先找104 的公司

    # for i in find_data:
    #     print(i)
        
    # print(df1)

if __name__ == "__main__":

    # job_list_page()

    # 記得檢查有幾頁
    # search_company_list(100)

    # time.sleep(3)
    # try:
    #     job_link = read_file_to_df('job_links_104.csv')
    # except:
    #     job_list_page()
    #     job_link = read_file_to_df('job_links_104.csv')

    # job_info(job_link)

    Combine_dataframe()

    fix_missing()
    