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

# 模型準備
model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2')

risk_similarity = pd.read_csv("risk_similarity.csv", encoding="utf-8-sig")

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

risk_similarity_104 = pd.read_csv("result_7.csv", encoding="utf-8-sig")

Data104 = risk_similarity_104.values.tolist()

print(len(Data104))
for j in Data104[2500:3009]:
    print(j)
    print(j[0],j[1])
    # random_uuid = uuid.uuid4()

    # UUID 物件
    # print(f"UUID 物件: {random_uuid}")

    # 通常會將 UUID 轉換成字串來使用
    # uuid_string = str(random_uuid)
    # print(f"UUID 字串: {uuid_string}")
    # 中文職缺摘要文字
    job_cat_list = j[4].split("、")
    print(len(job_cat_list))
    # input()
    for job_cat in job_cat_list:
        job_cat = job_cat.replace("\n", "")
        job_desc = job_cat+" "+j[10]

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
        results_all =[]
        numerator = 0
        denominator = 0
        numerator_all = 0
        denominator_all = 0

        for i, (code, title, task, risk) in enumerate(onets):
            sim = similarity_scores[i]
            data = {
                "O*NET職業代碼": code,
                "職業名稱": title,
                "任務摘要": task,
                "語意相似度": round(sim, 3),
                "自動化風險分數": risk
            }
            if round(sim, 3) >= 0:
                results.append(data)
                numerator += sim * risk
                denominator += sim

            results_all.append(data)
            numerator_all += sim * risk
            denominator_all += sim

        # 計算加權總風險值
        weighted_risk = numerator / denominator if denominator != 0 else 0
        weighted_risk = round(weighted_risk, 3)
        weighted_risk_all = numerator_all / denominator_all if denominator_all != 0 else 0
        weighted_risk_all = round(weighted_risk_all, 3)
        # 判斷風險等級
        if weighted_risk <= 0.33:
            risk_level = "低風險"
        elif weighted_risk <= 0.66:
            risk_level = "中風險"
        else:
            risk_level = "高風險"

        # 判斷風險等級
        if weighted_risk_all <= 0.33:
            risk_level_all = "低風險"
        elif weighted_risk_all <= 0.66:
            risk_level_all = "中風險"
        else:
            risk_level_all = "高風險"

        # 加入總結行
        results.append({
            "O*NET職業代碼": "總結",
            "職業名稱": risk_level,
            "任務摘要": "",
            "語意相似度": "",
            "自動化風險分數": weighted_risk
        })
        results_all.append({
            "O*NET職業代碼": "總結",
            "職業名稱": risk_level_all,
            "任務摘要": "",
            "語意相似度": "",
            "自動化風險分數": weighted_risk_all
        })
       
        results_104.append({
            "ID":j[0],
            "公司": j[2],
            "職務": j[1],
            "類別": job_cat,
            "工作內容":j[10],
            "風險等級": risk_level,
            "自動化風險分數": weighted_risk,
            "風險等級_all": risk_level_all,
            "自動化風險分數_all": weighted_risk_all
        })

        # 轉成 DataFrame 查看
        df_results = pd.DataFrame(results)
        df_results_all = pd.DataFrame(results_all)
        df_results_104 = pd.DataFrame(results_104)

        print(f"加權總自動化風險值：{weighted_risk} ({risk_level})")
        print(df_results)

        df_results.to_csv('output/'+ j[0]+"_"+job_cat+'.csv')
        df_results_all.to_csv('output_all/'+ j[0]+"_"+job_cat+'.csv')
        
        try:
            with open(result_path, 'r') as f:
                # 檔案已存在，附加時不寫入表頭
                df_results_104.to_csv(result_path, mode='a', header=False, index=False)
        except FileNotFoundError:
            # 檔案不存在，第一次寫入，包含表頭
            df_results_104.to_csv(result_path, mode='w', header=True, index=False)
