import requests

def get_today_fish_prices():
    url = "http://www.xinfadi.com.cn/getPriceData.html"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "http://www.xinfadi.com.cn/priceDetail.html",
        "Origin": "http://www.xinfadi.com.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
        "X-Requested-With": "XMLHttpRequest",
    }

    payload = {
        "limit": 50,
        "current": 1,
        "pubDateStartTime": "2025/05/30",  # 替换为你需要的日期或动态生成
        "pubDateEndTime": "",
        "prodPcatid": "1190",
        "prodCatid": "1209",
        "prodName": ""
    }

    try:
        response = requests.post(url, data=payload, headers=headers)
        data = response.json()
        cleaned = []

        for item in data.get("list", []):
            cleaned.append({
                "品名": item["prodName"],
                "最低价": item["lowPrice"],
                "平均价": item["avgPrice"],
                "最高价": item["highPrice"],
                "规格": item["specInfo"],
                "产地": item["place"],
                "单位": item["unitInfo"],
                "发布日期": item["pubDate"]
            })

        return cleaned

    except Exception as e:
        print("❌ 请求失败：", e)
        return []
