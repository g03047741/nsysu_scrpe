import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch # <--- 新增導入
import os
import uuid

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

result_path = 'result_104.csv'

# 檢查檔案是否存在
if os.path.exists(result_path):
    print(f"檔案 '{result_path}' 存在。準備刪除...")
    try:
        # 如果檔案存在，則刪除檔案
        os.remove(result_path)
        print(f"檔案 '{result_path}' 已成功刪除。")
    except OSError as e:
        # 如果刪除過程中發生錯誤 (例如，權限不足)
        print(f"刪除檔案 '{result_path}' 時發生錯誤: {e}")
else:
    print(f"檔案 '{result_path}' 不存在。")


low_level = 0.33
medium_level = 0.66

# 模型準備
model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2')



# 2. 建立 onets list
risk_similarity = pd.read_csv("risk_similarity.csv", encoding="utf-8-sig")
risk_similarity.dropna()
risk_similarity = risk_similarity.rename(columns={"SOC_code": "soc_code", "職業名稱": "title", "任務描述": "task", "自動化風險分數": "risk"})
risk_similarity = risk_similarity.drop_duplicates(subset=['task'], keep='first')
risk_similarity = risk_similarity[["soc_code", "title", "task", "risk"]]
onets = tuple(risk_similarity.values.tolist())

# 3. 確認結果
print(f"成功建立 {len(onets)} 筆資料到 onets")
print(onets[:3])  # 顯示前3筆看一下

# # 5. 從 onets 中提取任務敘述句
# tasks = [x[2] for x in onets]

# # 6. 轉換成語意向量（embedding）
# task_embeddings_en = model.encode(tasks, convert_to_tensor=True)

risk_similarity_104 = pd.read_csv("104.csv", encoding="utf-8-sig")
risk_similarity_104 = risk_similarity_104.drop_duplicates(subset=['職缺名稱', '公司', '工作內容'], keep='first')
data_104 = risk_similarity_104.values.tolist()


for row in data_104:

    random_uuid = uuid.uuid4()

    # 通常會將 UUID 轉換成字串來使用
    uuid_string = str(random_uuid)
    # print(f"UUID 字串: {uuid_string}")
    # 中文職缺摘要文字
    job_desc = row[9]
    # print(row[9])

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
        if round(sim, 3) > 0:
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
    if weighted_risk <= low_level:
        risk_level = "低風險"
    elif weighted_risk <= medium_level:
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
        "ID":uuid_string,
        "公司": row[1],
        "職缺名稱": row[0],
        "工作內容": row[9],
        "風險等級": risk_level,
        "自動化風險分數": weighted_risk
    })

    # 轉成 DataFrame 查看
    df_results = pd.DataFrame(results)
    df_results_104 = pd.DataFrame(results_104)

    print(f"加權總自動化風險值：{weighted_risk} ({risk_level})")
    print(df_results)
    df_results.to_csv('output/'+ uuid_string +'.csv', index=False, encoding='utf-8-sig')
 
    
    try:
        with open(result_path, 'r') as f:
            # 檔案已存在，附加時不寫入表頭
            df_results_104.to_csv(result_path, mode='a', header=False, index=False, encoding='utf-8-sig')
    except FileNotFoundError:
        # 檔案不存在，第一次寫入，包含表頭
        df_results_104.to_csv(result_path, mode='w', header=True, index=False, encoding='utf-8-sig')
