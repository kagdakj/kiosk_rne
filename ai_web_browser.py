import json
import time
import ollama
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


# ------------------------------------------
# 1) Chrome 브라우저 초기화
# ------------------------------------------
def init_browser():
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)
    return driver


# ------------------------------------------
# 2) LLM 프롬프트 템플릿
# ------------------------------------------
LLM_SYSTEM_PROMPT = """
You are a browser automation controller.
Output ONLY JSON with this exact format:

{
    "action": "click | type | goto | scroll | wait",
    "selector": "CSS selector (if needed)",
    "value": "value to type or URL",
    "wait": seconds_to_wait
}

NO explanations, NO additional text.
"""


# ------------------------------------------
# 3) LLM에게 명령어 전달 → JSON 행동 계획 받기
# ------------------------------------------
def ask_llm(user_command):
    response = ollama.chat(
        model="llama3.1",
        messages=[
            {"role": "system", "content": LLM_SYSTEM_PROMPT},
            {"role": "user", "content": user_command}
        ]
    )
    text = response['message']['content']

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print("❌ JSON 파싱 오류: LLM 출력 = ", text)
        return None


# ------------------------------------------
# 4) JSON 행동 계획 실행 → Selenium 제어
# ------------------------------------------
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


# ------------------------------------------
# 5) 메인 루프
# ------------------------------------------
def main():
    driver = init_browser()

    print("\n=== 🔥 LLM Chrome Controller 시작 ===\n")
    print("예: 구글에서 '강아지 사진' 검색해줘\n")

    while True:
        user_cmd = input("\n➡ 명령 입력: ")

        if user_cmd.lower() in ["exit", "quit"]:
            print("종료합니다.")
            break

        plan = ask_llm(user_cmd)

        if plan:
            print("\n📌 LLM 행동 계획:", plan)
            execute_action(driver, plan)


if __name__ == "__main__":
    main()
