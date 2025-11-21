# -*- coding: utf-8 -*-
"""
Created on Thu Nov 20 21:02:27 2025

@author: Dapeng Wang
"""

import asyncio
import subprocess
from flask import Flask, jsonify, send_from_directory
from playwright.async_api import async_playwright

# Install Playwright browser in RUNTIME, not in build
subprocess.run(["python", "-m", "playwright", "install", "chromium"])

app = Flask(__name__, static_folder="static")

async def fetch_data(eid="eid_206333"):
    url = "https://umich.libcal.com/spaces?lid=2761&gid=5040"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(url, timeout=0)
        await page.wait_for_timeout(3000)

        selector = f'td.fc-timeline-lane.fc-resource[data-resource-id="{eid}"]'
        td = await page.query_selector(selector)

        if not td:
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

        await browser.close()
        return results


@app.route("/api/get_data")
def get_data():
    data = asyncio.run(fetch_data())
    return jsonify(data)


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)