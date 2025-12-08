import json
import time
import ollama
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ----------------------------------------
# 1) Chrome 브라우저 초기화
# ----------------------------------------
def init_browser():
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver


# ----------------------------------------
# 2) LLM System Prompt
# ----------------------------------------
LLM_SYSTEM_PROMPT = """
You are a browser automation agent.
You will receive:
1. User command
2. The structured DOM of the page (as JSON)
Your task:
- Generate JSON ONLY (no extra text)
- If the page is dynamic (SPA) and the element cannot be found, generate JS code instead
Output format:
{
    "action": "goto | click | type | scroll | wait | js",
    "selector": "CSS selector if needed",
    "value": "value or URL or JS code",
    "wait": 1
}
If the action cannot be performed, return:
{
    "action": "wait",
    "selector": "",
    "value": "",
    "wait": 1
}
"""


# ----------------------------------------
# 3) DOM을 JSON으로 추출
# ----------------------------------------
def get_dom_json(driver):
    dom_json = driver.execute_script("""
    function domToJson(el) {
        let obj = {
            tag: el.tagName,
            id: el.id || null,
            class: el.className || null,
            text: el.innerText || null,
            children: []
        };
        for (let child of el.children) {
            obj.children.push(domToJson(child));
        }
        return obj;
    }
    return domToJson(document.body);
    """)
    return dom_json


# ----------------------------------------
# 4) LLM에게 명령 전달
# ----------------------------------------
def ask_llm(user_cmd, dom_json):
    content = f"""
User Command: {user_cmd}

Page DOM (JSON):
{json.dumps(dom_json)}
"""
    response = ollama.chat(
        model="llama3.1",
        messages=[
            {"role": "system", "content": LLM_SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ]
    )

    raw = response['message']['content']
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("❌ JSON parsing failed. Falling back to JS execution if available.\nRaw output:\n", raw)
        return {"action": "js", "value": raw, "wait": 1}


# ----------------------------------------
# 5) 액션 실행
# ----------------------------------------
def execute_action(driver, action_json):
    action = action_json.get("action")
    selector = action_json.get("selector")
    value = action_json.get("value")
    wait = action_json.get("wait", 1)

    try:
        if action == "goto":
            driver.get(value)
            time.sleep(wait)

        elif action == "click":
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            element.click()
            time.sleep(wait)

        elif action == "type":
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            element.clear()
            element.send_keys(value)
            time.sleep(wait)

        elif action == "scroll":
            driver.execute_script(f"window.scrollBy(0, {value});")
            time.sleep(wait)

        elif action == "wait":
            time.sleep(wait)

        elif action == "js":
            driver.execute_script(value)
            time.sleep(wait)

        else:
            print("⚠ Unknown action:", action)

    except Exception as e:
        print("❌ Execution error:", e)


# ----------------------------------------
# 6) 메인 루프
# ----------------------------------------
def main():
    driver = init_browser()
    print("\n🔥 DOM-based SPA-compatible LLM Chrome Controller 시작\n")

    while True:
        cmd = input("\n➡ 명령 입력 (exit 종료): ")
        if cmd.lower() in ["exit", "quit"]:
            break

        # DOM 구조 추출
        dom_json = get_dom_json(driver)

        # LLM에게 명령 전달
        action = ask_llm(cmd, dom_json)

        if action:
            print("📌 LLM Action:", action)
            execute_action(driver, action)


if __name__ == "__main__":
    main()
