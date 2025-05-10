import pandas as pd

data_path = 'data/'
# 1. 讀取三份資料
occupation_data = pd.read_excel(data_path+"Occupation Data.xlsx")
task_statements = pd.read_excel(data_path+"Task Statements.xlsx")
automation_data = pd.read_csv(data_path+"automation_data_by_state.csv", encoding='cp1252')
print(automation_data['Probability'])

# 2. 標準化欄位名稱（防止對不起來）
occupation_data.rename(columns={"O*NET-SOC Code": "SOC_code"}, inplace=True)
task_statements.rename(columns={"O*NET-SOC Code": "SOC_code"}, inplace=True)
automation_data.rename(columns={"SOC": "SOC_code"}, inplace=True)

# 3. 確保 SOC_code 格式一致（去空白、標準化）
occupation_data["SOC_code"] = occupation_data["SOC_code"].str.split('.').str[0]
task_statements["SOC_code"] = task_statements["SOC_code"].str.split('.').str[0]
automation_data["SOC_code"] = automation_data["SOC_code"].str.strip()

# 4. 合併資料
# 4-1. 任務表 + 職業說明表
merged = task_statements.merge(occupation_data, on="SOC_code", how="left")

# 4-2. 再加上自動化風險分數
final = merged.merge(automation_data, on="SOC_code", how="inner")
print(final.columns)
print(final['Probability'])
# 5. 清理並保留必要欄位（可依需要調整）
# 假設你的欄位是 'Task Description', 'Title', 'Occupation Description', 'probability'
final = final.rename(columns={
    "Title_x": "職業名稱",
    "Task": "任務描述",
    "Description": "職業說明",
    "Probability": "自動化風險分數"
})

print(final['自動化風險分數'])

# 6. 選取要匯出的欄位
risk_similarity = final[["SOC_code", "職業名稱", "職業說明", "任務描述", "自動化風險分數"]]

# 7. 匯出成 CSV
risk_similarity.to_csv("risk_similarity.csv", index=False, encoding="utf-8-sig")

print("匯出完成，產生 risk_similarity.csv！")
