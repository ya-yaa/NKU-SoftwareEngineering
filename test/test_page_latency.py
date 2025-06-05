# 页面加载时间测试

import requests
import time
import pandas as pd

# 页面路径与描述
pages = [
    {"desc": "首页", "url": "http://127.0.0.1:5000/"},
    {"desc": "用户注册页", "url": "http://127.0.0.1:5000/register"},
    {"desc": "用户登录页", "url": "http://127.0.0.1:5000/login"},
    {"desc": "智能中心", "url": "http://127.0.0.1:5000/AI_center"},
    {"desc": "鱼价展示页", "url": "http://127.0.0.1:5000/fish_price_today"},
    {"desc": "渔场信息页", "url": "http://127.0.0.1:5000/fish_farms"},
]

# 页面测试函数
def test_page(page):
    try:
        start = time.time()
        resp = requests.get(page["url"], timeout=10)
        end = time.time()
        return {
            "页面": page["desc"],
            "状态码": resp.status_code,
            "加载时间（ms）": round((end - start) * 1000, 2),
            "是否成功": resp.status_code == 200
        }
    except Exception as e:
        return {
            "页面": page["desc"],
            "状态码": "连接失败",
            "加载时间（ms）": None,
            "是否成功": False
        }

# 执行测试
results = [test_page(page) for page in pages]
df = pd.DataFrame(results)

# 输出结果
print(df.to_markdown(index=False))
df.to_csv("页面加载时间测试.csv", index=False, encoding="utf-8-sig")
