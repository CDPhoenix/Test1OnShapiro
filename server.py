import asyncio
import subprocess
from flask import Flask, jsonify, send_from_directory
from playwright.async_api import async_playwright

# ============================================================
# 1. Runtime 安装 Playwright 浏览器（Render 必须如此）
# ============================================================
subprocess.run(["python", "-m", "playwright", "install", "chromium"])

app = Flask(__name__, static_folder="static")

# ============================================================
# 全局状态
# ============================================================
playwright_instance = None
browser_instance = None
request_count = 0              # 计数 API 请求次数
RESTART_THRESHOLD = 10         # 每 10 次重启一次


# ============================================================
# 2. 用于初始化浏览器
# ============================================================
async def init_browser():
    global playwright_instance, browser_instance

    print("=== Initializing Playwright Browser ===")
    playwright_instance = await async_playwright().start()
    browser_instance = await playwright_instance.chromium.launch(headless=True)
    print("=== Browser Launched ===")


# ============================================================
# 3. 自动重启浏览器
# ============================================================
async def restart_browser():
    global playwright_instance, browser_instance, request_count

    print("=== Restarting Browser (hit threshold) ===")

    # 关闭旧浏览器
    if browser_instance:
        await browser_instance.close()

    # 停止旧 playwright
    if playwright_instance:
        await playwright_instance.stop()

    # 重置计数器
    request_count = 0

    # 启动新的浏览器
    await init_browser()


# ============================================================
# 4. 使用全局浏览器爬取一次网页
# ============================================================
async def fetch_data(eid="eid_206333"):
    global request_count

    # 检查是否需要重启浏览器
    request_count += 1
    if request_count >= RESTART_THRESHOLD:
        await restart_browser()

    # ----- 开始抓取 -----
    url = "https://umich.libcal.com/spaces?lid=2761&gid=5040"

    page = await browser_instance.new_page()

    await page.goto(url, timeout=0)
    await page.wait_for_timeout(2000)

    selector = f'td.fc-timeline-lane.fc-resource[data-resource-id="{eid}"]'
    td = await page.query_selector(selector)

    if not td:
        await page.close()
        return []

    events = await td.query_selector_all(".fc-timeline-event-harness a[title]")

    results = []
    for e in events:
        title = await e.get_attribute("title")
        if title:
            parts = title.split(" - ")
            time = " - ".join(parts[:-2])
            status = parts[-1]

            results.append({"eid": eid, "time": time, "status": status})

    await page.close()
    return results


# ============================================================
# 5. API
# ============================================================
@app.route("/api/get_data")
def get_data():
    data = asyncio.run(fetch_data())
    return jsonify(data)


# ============================================================
# 6. 主页
# ============================================================
@app.route("/")
def home():
    return send_from_directory("static", "index.html")


# ============================================================
# 7. Flask 启动前初始化浏览器
# ============================================================
if __name__ == "__main__":
    asyncio.run(init_browser())
    app.run(host="0.0.0.0", port=5000)