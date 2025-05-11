from scrape_104 import *
from Capital import *

# 1. 公司清單，先去網站將資訊類別的公司filter打勾，爬之前先看有幾個頁面，接著查看總頁數，填入此function
search_company_list(100)
# 2. 職缺清單，先去網站將資訊類別的公司filter打勾，爬之前先看有幾個頁面，接著查看總頁數，填入此function
job_list_page(150)
# 3. 合併上面兩個的結果
merger_jobList_companyList()