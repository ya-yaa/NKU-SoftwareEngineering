# 并发访问测试脚本

import requests
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# 测试配置
TARGET_URL = "http://127.0.0.1:5000/"  # 要测试的目标页面
NUM_REQUESTS = 100                     # 总请求数
MAX_WORKERS = 20                       # 并发线程数

def send_request(i):
    try:
        start = time.time()
        resp = requests.get(TARGET_URL, timeout=10)
        end = time.time()
        return {
            "编号": i + 1,
            "状态码": resp.status_code,
            "响应时间（ms）": round((end - start) * 1000, 2),
            "是否成功": resp.status_code == 200
        }
    except Exception as e:
        return {
            "编号": i + 1,
            "状态码": "错误",
            "响应时间（ms）": None,
            "是否成功": False
        }

def run_concurrent_test():
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(send_request, i) for i in range(NUM_REQUESTS)]
        for future in as_completed(futures):
            results.append(future.result())
    return pd.DataFrame(results)

if __name__ == "__main__":
    df = run_concurrent_test()

    # 保存详细请求结果
    df.to_csv("并发访问测试_详细结果.csv", index=False, encoding="utf-8-sig")

    # 输出统计信息
    success_count = df["是否成功"].sum()
    fail_count = NUM_REQUESTS - success_count
    avg_time = df["响应时间（ms）"].dropna().mean()
    max_time = df["响应时间（ms）"].dropna().max()

    print("—— 并发访问测试结果汇总 ——")
    print(f"总请求数：{NUM_REQUESTS}")
    print(f"成功次数：{success_count}")
    print(f"失败次数：{fail_count}")
    print(f"平均响应时间：{avg_time:.2f} ms")
    print(f"最大响应时间：{max_time:.2f} ms")

    # 输出简表
    summary = pd.DataFrame([{
        "总请求数": NUM_REQUESTS,
        "成功数": success_count,
        "失败数": fail_count,
        "平均响应时间（ms）": round(avg_time, 2),
        "最大响应时间（ms）": round(max_time, 2)
    }])
    summary.to_csv("并发访问测试_汇总.csv", index=False, encoding="utf-8-sig")
