import json
import time
import ollama
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


# -----------------------------------------------------
# 1) Chrome 초기화
# -----------------------------------------------------
def init_browser():
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)
    return driver


# -----------------------------------------------------
# 2) LLM System Prompt
# -----------------------------------------------------
LLM_SYSTEM_PROMPT = """
You are a browser automation controller.

You will receive:
1. User command
2. The full HTML source of the current page

Your task:
- Analyze the HTML
- Decide the correct CSS selector
- Output ONLY a JSON action with this format:

{
    "action": "click | type | goto | scroll | wait",
    "selector": "CSS selector (if needed)",
    "value": "",
    "wait": 1
}

NEVER output text other than JSON.
If the command cannot be done, output:
{
    "action": "wait",
    "selector": "",
    "value": "",
    "wait": 1
}
"""


# -----------------------------------------------------
# 3) LLM에게 (명령어 + 페이지 소스) 전달 → JSON action 생성
# -----------------------------------------------------
def ask_llm(user_cmd, html_source):
    content = f"""
User Command: {user_cmd}

HTML Source of Current Page:
----------------------------
{html_source}
----------------------------
"""

    response = ollama.chat(
        model="llama3.1",
        messages=[
            {"role": "system", "content": LLM_SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ]
    )

    raw = response["message"]["content"]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("❌ JSON 파싱 실패:", raw)
        return None


# -----------------------------------------------------
# 4) LLM action JSON 실행
# -----------------------------------------------------
def execute_action(driver, action_json):
    action = action_json.get("action")
    selector = action_json.get("selector")
    value = action_json.get("value")
    wait = action_json.get("wait", 1)

    try:
        if action == "goto":
            driver.get(value)

        elif action == "click":
            element = driver.find_element(By.CSS_SELECTOR, selector)
            element.click()

        elif action == "type":
            element = driver.find_element(By.CSS_SELECTOR, selector)
            element.send_keys(value)

        elif action == "scroll":
            driver.execute_script(f"window.scrollBy(0, {value});")

        elif action == "wait":
            time.sleep(value)

        time.sleep(wait)

    except Exception as e:
        print("❌ 실행 오류:", e)


# -----------------------------------------------------
# 5) 메인 실행 루프
# -----------------------------------------------------
def main():
    driver = init_browser()
    print("\n🔥 LLM + HTML 분석 기반 Chrome Controller 시작\n")

    while True:
        cmd = input("\n➡ 명령 입력 (exit 종료): ")

        if cmd.lower() == "exit":
            break

        html = driver.page_source  # ← ✨ HTML 전체를 LLM에게 보내줌

        action = ask_llm(cmd, html)

        if action:
            print("📌 LLM Action:", action)
            execute_action(driver, action)


if __name__ == "__main__":
    main()
