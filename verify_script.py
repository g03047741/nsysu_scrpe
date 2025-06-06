import pandas as pd
import os
import math

def verify_risk_data():
    """
    驗證主檔案A與各個獨立CSV檔案的風險資料是否一致。
    """
    # 1. 設定檔案路徑 (請根據您的實際情況修改)
    file_a_path = 'file_A.csv'
    individual_csvs_dir = 'individual_csvs/'

    # 2. 讀取主檔案 A
    try:
        df_a = pd.read_csv(file_a_path)
        # 確保關鍵欄位存在
        required_cols = ['uuid', '職務', '風險等級', '自動化風險分數']
        if not all(col in df_a.columns for col in required_cols):
            print(f"錯誤：主檔案 {file_a_path} 缺少必要的欄位。需要欄位：{required_cols}")
            return
    except FileNotFoundError:
        print(f"錯誤：找不到主檔案 {file_a_path}，請檢查路徑。")
        return
    
    print("開始進行資料比對...\n")
    mismatch_count = 0

    # 3. 遍歷主檔案 A 的每一行
    for index, row_a in df_a.iterrows():
        # 從主檔案A獲取比對基準
        uuid = row_a['uuid']
        job_title = row_a['職務']
        risk_level_a = row_a['風險等級']
        risk_score_a = row_a['自動化風險分數']

        # 4. 組合對應的 csv 檔名與路徑
        csv_filename = f"{uuid}_{job_title}.csv"
        csv_filepath = os.path.join(individual_csvs_dir, csv_filename)

        # 5. 讀取獨立 csv 檔案並驗證
        if not os.path.exists(csv_filepath):
            print(f"⚠️  警告：找不到檔案 -> {csv_filename}")
            continue

        try:
            # 讀取csv，並指定沒有標頭(header)，這樣第一行纔不會被當作欄位名稱
            df_individual = pd.read_csv(csv_filepath, header=None)
            
            if df_individual.empty:
                print(f"⚠️  警告：檔案為空 -> {csv_filename}")
                continue

            # 獲取最後一行資料
            last_row = df_individual.iloc[-1]

            # 根據範例 '總結,低風險,,,0.304' 解析資料
            # 索引 1 是風險等級, 索引 5 是分數
            risk_level_csv = last_row[1]
            risk_score_csv = float(last_row[5])

            # 6. 進行比對
            level_match = (risk_level_a == risk_level_csv)
            # 使用 math.isclose() 來比對浮點數，避免精度問題
            score_match = math.isclose(risk_score_a, risk_score_csv)

            if not level_match or not score_match:
                mismatch_count += 1
                print(f"❌ 資料不一致：{csv_filename}")
                if not level_match:
                    print(f"  - 風險等級不符：主檔案='{risk_level_a}', CSV檔='{risk_level_csv}'")
                if not score_match:
                    print(f"  - 風險分數不符：主檔案={risk_score_a}, CSV檔={risk_score_csv}")
                print("-" * 20)

        except Exception as e:
            print(f"處理檔案 {csv_filename} 時發生錯誤: {e}")

    print("\n比對完成！")
    if mismatch_count == 0:
        print("✅ 所有資料皆一致。")
    else:
        print(f"總共發現 {mismatch_count} 筆資料不一致。")

# 執行驗證函式
if __name__ == "__main__":
    verify_risk_data()