# 接口响应时间测试

import requests
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# 本地运行地址
BASE_URL = "http://127.0.0.1:5000"

# 批量接口测试清单（可按需添加）
endpoints = [
    {"path": "/register", "method": "GET", "desc": "用户注册页加载"},
    {"path": "/login", "method": "GET", "desc": "用户登录页加载"},
    {"path": "/fish_price_today", "method": "GET", "desc": "今日鱼价页面"},
    {"path": "/AI_center", "method": "GET", "desc": "智能中心首页"},
    {"path": "/alerts", "method": "GET", "desc": "养殖户预警数据接口"},
    {"path": "/fish_farms", "method": "GET", "desc": "渔场分页列表"},
    {"path": "/admin/export_fishes?format=csv", "method": "GET", "desc": "导出鱼类数据（CSV）"},
    {"path": "/admin/logs", "method": "GET", "desc": "操作日志页面（需登录）"},
    {"path": "/datas", "method": "GET", "desc": "养殖户数据中心（需登录）"},
]

# 测试函数
def test_endpoint(endpoint):
    full_url = BASE_URL + endpoint["path"]
    try:
        start = time.time()
        response = requests.get(full_url, timeout=5)
        end = time.time()
        return {
            "接口功能": endpoint["desc"],
            "状态码": response.status_code,
            "响应时间 (ms)": round((end - start) * 1000, 2),
            "是否成功": response.status_code == 200
        }
    except Exception as e:
        return {
            "接口功能": endpoint["desc"],
            "状态码": "连接失败",
            "响应时间 (ms)": None,
            "是否成功": False
        }

# 并发测试（可修改 max_workers 控制并发）
def run_tests():
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(test_endpoint, endpoints))
    return pd.DataFrame(results)

if __name__ == "__main__":
    df = run_tests()
    print(df.to_markdown(index=False))  # 控制台表格输出
    df.to_csv("接口响应测试结果.csv", index=False, encoding="utf-8-sig")  # 保存为CSV
