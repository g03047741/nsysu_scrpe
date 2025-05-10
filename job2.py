import pandas as pd
from sentence_transformers import SentenceTransformer, util

# 模型準備
model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2')

risk_similarity = pd.read_csv("risk_similarity.csv", encoding="utf-8-sig")
print()
# 2. 建立 onets list
onets = []

for index, row in risk_similarity.iterrows():
    soc_code = row["SOC_code"]
    title = row["職業名稱"]
    task = row["任務描述"]
    risk = row["自動化風險分數"]
    
    # 只要確保這些欄位都有值，才加入
    if pd.notnull(soc_code) and pd.notnull(title) and pd.notnull(task) and pd.notnull(risk):
        onets.append((soc_code, title, task, risk))

# 3. 確認結果
print(f"成功建立 {len(onets)} 筆資料到 onets")
print(onets[:3])  # 顯示前3筆看一下


# # 5. 從 onets 中提取任務敘述句
# tasks = [x[2] for x in onets]

# # 6. 轉換成語意向量（embedding）
# task_embeddings_en = model.encode(tasks, convert_to_tensor=True)



# 中文職缺摘要文字
job_desc = "負責鼎新 Tiptop (T100) ERP系統的維護工作，包括監控系統運作、解決系統錯誤、優化系統性能，以及設計、開發任務等。負責Oracle DB 數據庫的維護工作並能夠迅速處理數據庫相關的問題，確保數據庫的穩定運行和安全性。"

# 假設 onets 是已經建好的清單
# onets = [(SOC_code, title, task, risk_score), ...]

# 轉換中文描述向量
job_vec = model.encode(job_desc, convert_to_tensor=True)

# 提取 O*NET 任務敘述並轉向量
task_texts = [task for _, _, task, _ in onets]
task_embeddings = model.encode(task_texts, convert_to_tensor=True)

# 語意相似度計算
similarities = util.pytorch_cos_sim(job_vec, task_embeddings)
similarity_scores = similarities.squeeze().tolist()

# 整合結果
results = []
numerator = 0
denominator = 0

for i, (code, title, task, risk) in enumerate(onets):
    sim = similarity_scores[i]
    results.append({
        "O*NET職業代碼": code,
        "職業名稱": title,
        "任務摘要": task,
        "語意相似度": round(sim, 3),
        "自動化風險分數": risk
    })
    numerator += sim * risk
    denominator += sim

# 計算加權總風險值
weighted_risk = numerator / denominator if denominator != 0 else 0
weighted_risk = round(weighted_risk, 3)

# 判斷風險等級
if weighted_risk <= 0.33:
    risk_level = "低風險"
elif weighted_risk <= 0.66:
    risk_level = "中風險"
else:
    risk_level = "高風險"

# 加入總結行
results.append({
    "O*NET職業代碼": "總結",
    "職業名稱": risk_level,
    "任務摘要": "",
    "語意相似度": "",
    "自動化風險分數": weighted_risk
})

# 轉成 DataFrame 查看
df_results = pd.DataFrame(results)

print(f"加權總自動化風險值：{weighted_risk} ({risk_level})")
print(df_results)

df_results.to_csv('result.csv')
