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
import re
import io

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

def format_change(file):
    format_ = 'utf-8-sig'
    df = pd.read_csv(file, encoding=format_)
    print(df)
    new_file = file.split('.')
    df.to_csv(new_file[0]+'_formatted.'+new_file[1],index=False, encoding=format_)


def convert_capital_to_numeric(capital_str):
    if pd.isna(capital_str): # 處理缺失值
        return None

    capital_str = str(capital_str) # 確保是字串格式
    

    if '億' in capital_str:
        num_str = capital_str.replace('資本額', '').replace('元', '') # 移除不必要的文字
        num = float(re.findall(r'\d+\.?\d*', num_str.split('億')[0])[-1]) # 取億前面的數字
        return num * 100000000
    elif '萬' in capital_str:
        num_str = capital_str.replace('資本額', '').replace('元', '') # 移除不必要的文字
        num = float(re.findall(r'\d+\.?\d*', num_str.split('萬')[0])[-1]) # 取萬前面的數字
        return num * 10000
    else:
        cleaned_str = capital_str.replace(',', '') 
        return float(cleaned_str)

def convert_capital():
    df = pd.read_csv('result_7.csv', encoding=encoding_type)
    # 套用轉換函數到 'capital' 欄位
    df['資本額'] = df['資本額'].apply(convert_capital_to_numeric)
    df['資本額'] = df['資本額'].fillna(0)

    print(df)
    df.to_csv('result_8.csv',index=False, encoding=encoding_type)


# 輔助函數：解析單個薪資數值字串 (例如 "3萬5千", "35000", "3.5萬")
def _parse_single_salary_value(value_str_orig):
    if pd.isna(value_str_orig):
        return 0.0
    # 清理字串：移除頭尾空格、逗號，並預先移除"元"（如果存在）
    value_str = str(value_str_orig).strip().replace(',', '').replace(' ', '')
    if value_str.endswith('元'):
        value_str = value_str[:-1]
    
    if not value_str: # 如果清理後為空字串
        return 0.0

    total_value = 0.0
    # 複製一份用於逐步消耗的字串，避免修改原始傳入的 value_str (雖然此處 value_str 已是副本)
    remaining_str = value_str 
    
    # 1. 處理 '萬' (ten thousand)
    # 使用 re.search 而非 re.match，因為 "萬" 不一定在字串開頭 (雖然常見)
    wan_match = re.search(r'(\d+\.?\d*)\s*萬', remaining_str)
    if wan_match:
        try:
            total_value += float(wan_match.group(1)) * 10000
            # 更新 remaining_str 為 "萬" 匹配部分之後的內容
            remaining_str = remaining_str[wan_match.end():]
        except ValueError:
            pass # 數字轉換失敗

    # 2. 處理 '千' (thousand) 在剩餘字串中的部分
    qian_match = re.search(r'(\d+\.?\d*)\s*千', remaining_str)
    if qian_match:
        try:
            total_value += float(qian_match.group(1)) * 1000
            remaining_str = remaining_str[qian_match.end():]
        except ValueError:
            pass

    # 3. 處理剩餘的純數字部分 (例如 "3萬500" 中的 "500")
    if remaining_str.strip(): # 如果處理完萬/千後還有剩餘非空字串
        # 確保剩餘部分是純數字才進行加總
        plain_match = re.fullmatch(r'(\d+\.?\d+)', remaining_str.strip())
        if plain_match:
            try:
                total_value += float(plain_match.group(1))
            except ValueError:
                pass
            
    # 4. 如果 total_value 仍為 0 (表示未找到萬/千單位，或剩餘部分非純數字)
    #    則嘗試將原始清理後的字串 (value_str) 直接視為純數字解析
    if total_value == 0:
        plain_match_orig = re.fullmatch(r'(\d+\.?\d+)', value_str) # 使用 fullmatch 確保整個字串是數字
        if plain_match_orig:
            try:
                total_value = float(plain_match_orig.group(1))
            except ValueError:
                return 0.0 # 原始字串也無法解析為純數字
        # else: 如果也不是純數字，total_value 保持 0.0
            
    return total_value

# 主要轉換函數：將工作待遇文字轉換為標準化月薪
def convert_salary_to_monthly(salary_text):
    if pd.isna(salary_text):
        return 0.0
    
    text = str(salary_text).strip() # 原始輸入的副本

    # 優先處理無法量化或特定描述的情況
    non_numeric_keywords = [
        "面議", "論件計酬", "按件計酬", "依公司規定", "公司規定", "依相關規定",
        "相關規定", "薪資另議", "待遇面議", "薪資面議", "面談", "電洽", "另議"
    ]
    for keyword in non_numeric_keywords:
        if keyword in text:
            return 0.0

    # 標準化文字：移除常見修飾詞、單位「元」、處理大小寫K為千元
    # 注意：空格移除應謹慎，避免影響 "3 萬" 這類寫法，但 _parse_single_salary_value 已處理
    text_processed = text.replace(' ', '') # 移除所有空格以簡化後續處理
    text_processed = text_processed.replace('以上', '').replace('以下', '').replace('起', '')
    text_processed = text_processed.replace('元', '')
    text_processed = text_processed.replace('Ｋ', 'K').replace('k', '000') # 將 K/k 替換為 '000'

    # 標準化範圍分隔符號，統一用 '-'
    text_processed = re.sub(r'[~至\-–到]', '-', text_processed)

    # 判斷薪資週期 (時薪/日薪/年薪/月薪)
    period_multiplier = 1.0 # 預設為月薪
    
    # 保留一份用於判斷週期的原始文本(或初步清理的文本)
    # 因為 "時薪", "月薪" 等關鍵字可能會被後續的數字提取邏輯中的 replace 影響
    text_for_period_check = text # 用未被過度處理的 text 進行週期判斷

    if "時薪" in text_for_period_check:
        period_multiplier = 8 * 30 # 每天8小時，每月30天
        text_processed = text_processed.replace("時薪", "")
    elif "日薪" in text_for_period_check or "日給" in text_for_period_check:
        period_multiplier = 30 # 每月30天
        text_processed = text_processed.replace("日薪", "").replace("日給", "")
    elif "年薪" in text_for_period_check:
        period_multiplier = 1/12.0
        text_processed = text_processed.replace("年薪", "")
    elif "月薪" in text_for_period_check:
        text_processed = text_processed.replace("月薪","")
    # 若無明確週期關鍵字，則預設為月薪 (period_multiplier = 1.0)

    # `text_processed` 此時應主要包含數字、萬/千單位、以及可能的範圍分隔符 '-'
    
    extracted_numbers = []
    # 按範圍分隔符 '-' 分割字串
    salary_parts = text_processed.split('-')
    
    if len(salary_parts) == 2: # 可能是一個薪資範圍 "數值1 - 數值2"
        val1_str, val2_str = salary_parts[0], salary_parts[1]
        num1 = _parse_single_salary_value(val1_str)
        num2 = _parse_single_salary_value(val2_str)
        
        if num1 > 0.0 and num2 > 0.0:
            extracted_numbers = [num1, num2]
        elif num1 > 0.0: # 若只有範圍的第一部分成功解析
            extracted_numbers = [num1]
        elif num2 > 0.0: # 若只有範圍的第二部分成功解析 (較少見)
            extracted_numbers = [num2]
        # 若兩者解析均失敗或為0，extracted_numbers 保持為空

    elif len(salary_parts) == 1: # 不是範圍，或 '-' 非預期分隔符，視為單個薪資數值
        single_val = _parse_single_salary_value(salary_parts[0])
        if single_val > 0.0:
            extracted_numbers = [single_val]
    
    # 若按 '-' 分割後仍無法提取到數字 (例如 salary_parts 包含多個元素但非有效薪資範圍)
    # 或者原始字串中並無有效的 '-' 作為分隔符
    # 嘗試將移除週期關鍵字後的整個 `text_processed` 作為單一值解析 (備用邏輯)
    if not extracted_numbers and len(salary_parts) > 1 : # 分割出多部分但未成功解析為範圍
        fallback_single_val = _parse_single_salary_value(text_processed.replace('-', '')) # 移除所有 '-' 再試
        if fallback_single_val > 0.0:
            extracted_numbers = [fallback_single_val]


    if not extracted_numbers: # 若最終未能提取到任何有效薪資數值
        return 0.0

    # 計算基礎薪資 (若是範圍則取平均值，否則取單值)
    base_salary = 0.0
    if len(extracted_numbers) == 1:
        base_salary = extracted_numbers[0]
    elif len(extracted_numbers) == 2:
        # 確保兩個數字都大於0才計算平均，避免一個為0影響結果 (雖然_parse_single_salary_value已處理0)
        if extracted_numbers[0] > 0 and extracted_numbers[1] > 0:
             base_salary = (extracted_numbers[0] + extracted_numbers[1]) / 2.0
        elif extracted_numbers[0] > 0: # 如果第二個數字無效，則只取第一個
            base_salary = extracted_numbers[0]
        elif extracted_numbers[1] > 0: # 如果第一個數字無效，則只取第二個
            base_salary = extracted_numbers[1]
        else: # 兩個數字都無效
            return 0.0
    
    if base_salary <= 0.0: # 若基礎薪資計算結果為0或負值
        return 0.0

    # 根據薪資週期計算標準化月薪
    calculated_monthly_salary = base_salary * period_multiplier
    
    return round(calculated_monthly_salary)

def salary_():
    # --- 主程式流程 ---
    # 1. 讀取 CSV 檔案
    file_path = 'result_10.csv' # 請確保檔案路徑正確
    try:
        # 嘗試使用 UTF-8 編碼讀取
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    except UnicodeDecodeError:
        try:
            # 若 UTF-8 失敗，嘗試使用 'big5' (台灣常用編碼)
            df = pd.read_csv(file_path, encoding='big5')
        except UnicodeDecodeError:
            try:
                # 若 'big5' 失敗，嘗試使用 'cp950' (另一台灣常用編碼)
                df = pd.read_csv(file_path, encoding='cp950')
            except Exception as e:
                print(f"讀取檔案 '{file_path}' 時發生錯誤，嘗試多種編碼失敗: {e}")
                df = pd.DataFrame() # 建立空的 DataFrame 以避免後續錯誤
        except FileNotFoundError:
            print(f"錯誤：找不到檔案 '{file_path}'。請確認檔案路徑是否正確。")
            df = pd.DataFrame()
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 '{file_path}'。請確認檔案路徑是否正確。")
        df = pd.DataFrame()


    if not df.empty and '工作待遇' in df.columns:
        # 2. 套用轉換函數到「工作待遇」欄位，並建立新欄位「月薪」
        df['月薪'] = df['工作待遇'].apply(convert_salary_to_monthly)

        # 3. 顯示結果 (例如前10筆以及包含「工作待遇」和新「月薪」的欄位)
        print("轉換結果預覽 (前20筆):")
        print(df[['工作待遇', '月薪']].head(20))

        #  يمكنك أيضًا حفظ DataFrame المحدث إلى ملف CSV جديد إذا لزم الأمر
        df.to_csv('result_11.csv', index=False, encoding='utf-8-sig')
        # print("\n已將包含月薪的結果儲存到 result_10_with_monthly_salary.csv")

    else:
        if df.empty:
            print("未能讀取 DataFrame，請檢查檔案路徑和內容。")
        else:
            print("錯誤：DataFrame 中找不到 '工作待遇' 欄位。")

def merge_data():
    df1 = pd.read_csv('result_8.csv', encoding=encoding_type)
    df2 = pd.read_csv('result_104_1_formatted_.csv', encoding=encoding_type)
    merged_df = pd.merge(df2, df1, on='uuid', how='left', suffixes=('', '_df1'))

    # 3. 處理同名欄位並填補缺失值
    # 找出在合併前 df1 和 df2 中共同存在的欄位 (除了 'uuid')
    common_columns_to_fill = []
    if '公司名稱' in df2.columns and '公司名稱_df1' in merged_df.columns:
        common_columns_to_fill.append('公司名稱')
    # 如果還有其他共同欄位，也用類似方式加入 common_columns_to_fill 列表

    for col in common_columns_to_fill:
        # 使用 df2 的欄位值，如果為 NaN，則用 df1 對應欄位 (col + '_df1') 的值填補
        merged_df[col] = merged_df[col].combine_first(merged_df[col + '_df1'])
        
        # 4. 移除多餘的輔助欄位
        merged_df = merged_df.drop(columns=[col + '_df1'])

    # 現在 merged_df 就是整合後的 DataFrame
    # 它包含了 df2 的所有資料，並由 df1 補充了 df2 所沒有的欄位，
    # 以及在共同欄位中 df2 為 NaN 而 df1 有值的情況。
    print("整合後的 DataFrame (前5筆):")
    print(merged_df.head())

    print("\n整合後的 DataFrame 欄位:")
    print(merged_df.columns)

    merged_df.to_csv('result_10.csv',index=False, encoding=encoding_type)

def location():
    print("工作地點")
    df = pd.read_csv('result_0604.csv', encoding=encoding_type)

    # 取得 'your_column_name' 欄位中每個字串的前 6 個字元
    df['地點'] = df['地點'].str[:6]

    # 列印更新後的 DataFrame
    print(df)
    df.to_csv('result_12.csv',index=False, encoding=encoding_type)
if __name__ == "__main__":
    # format_change('result_104_1.csv')
#    merge_data()
#    salary_()
    location()
