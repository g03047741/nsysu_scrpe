import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch # <--- 新增導入

# 1. 設定運算裝置 (GPU/MPS/CPU)
if torch.cuda.is_available():
    device = torch.device("cuda")
    print("使用 GPU (CUDA) 進行運算")
elif torch.backends.mps.is_available(): # 適用於 Apple Silicon (M1/M2/M3)
    device = torch.device("mps")
    print("使用 Apple Silicon GPU (MPS) 進行運算")
else:
    device = torch.device("cpu")
    print("使用 CPU 進行運算")

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

risk_similarity_104 = pd.read_csv("104.csv", encoding="utf-8-sig")

Data104 = risk_similarity_104.values.tolist()


for j in Data104:

    print(j[0],j[1])
    # 中文職缺摘要文字
    job_desc = j[9]

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
    results_104 = []
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

    results_104.append({
        "公司": j[1],
        "職務": j[0],
        "工作內容":j[9],
        "風險等級": risk_level,
        "自動化風險分數": weighted_risk
    })

    # 轉成 DataFrame 查看
    df_results = pd.DataFrame(results)
    df_results_104 = pd.DataFrame(results_104)

    print(f"加權總自動化風險值：{weighted_risk} ({risk_level})")
    print(df_results)

    df_results.to_csv('output/'+j[1]+'_'+j[0]+'.csv')
 
    csv_file_path = 'result_104.csv'
    try:
        with open(csv_file_path, 'r') as f:
            # 檔案已存在，附加時不寫入表頭
            df_results_104.to_csv(csv_file_path, mode='a', header=False, index=False)
    except FileNotFoundError:
        # 檔案不存在，第一次寫入，包含表頭
        df_results_104.to_csv(csv_file_path, mode='w', header=True, index=False)
