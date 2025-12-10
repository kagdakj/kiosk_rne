import time
import json
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# -----------------------------
# Llama-3-8B-Web 모델 로드
# -----------------------------
print("Loading Llama-3-8B-Web model... (this may take a while)")
tokenizer = AutoTokenizer.from_pretrained("McGill-NLP/Llama-3-8B-Web")
model = AutoModelForCausalLM.from_pretrained(
    "McGill-NLP/Llama-3-8B-Web",
    torch_dtype='auto',
    device_map='auto'
)
agent = pipeline("text-generation", model=model, tokenizer=tokenizer)

# -----------------------------
# DOM 스냅샷 추출
# -----------------------------
def extract_actions(html, max_elements=30):
    soup = BeautifulSoup(html, "html.parser")
    elements = []
    for el in soup.find_all(["a","button","input","form"]):
        selector = None
        if el.get("id"):
            selector = f"#{el.get('id')}"
        elif el.get("name"):
            selector = f"[name=\"{el.get('name')}\"]"
        if selector:
            elements.append({
                "tag": el.name,
                "selector": selector,
                "text": el.get_text(strip=True),
                "attrs": dict(el.attrs)
            })
    return elements[:max_elements]

# -----------------------------
# 웹 자동화 에이전트
# -----------------------------
def autonomous_browser(goal, start_url="https://www.google.com"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(start_url)
        time.sleep(2)

        while True:
            html = page.content()
            actions = extract_actions(html)

            prompt = f"""
You are a web navigation agent.  
Goal: {goal}  
Current page URL: {page.url}  
Available interactive elements (tag, selector, text, attrs):  
{json.dumps(actions, indent=2)}

Reply with exactly ONE JSON action:
{{"action":"goto","url":"..."}}
{{"action":"click","selector":"..."}}
{{"action":"type","selector":"...","text":"..."}}
{{"action":"finish","summary":"..."}}
Do NOT add extra text.
"""
            out = agent(prompt, max_new_tokens=128, do_sample=False)[0]['generated_text']
            print("Model output:", out)

            try:
                action = json.loads(out)
            except json.JSONDecodeError:
                print("Invalid JSON. Stopping.")
                break

            act_type = action.get("action") or action.get("click") or action.get("type")

            if action.get("action") == "goto":
                print(f"Navigating to {action['url']}")
                page.goto(action["url"])
            elif action.get("action") == "click":
                try:
                    print(f"Clicking {action['selector']}")
                    page.click(action["selector"])
                except:
                    print(f"Failed to click {action['selector']}")
            elif action.get("action") == "type":
                try:
                    print(f"Typing into {action['selector']}: {action['text']}")
                    page.fill(action["selector"], action["text"])
                except:
                    print(f"Failed to type into {action['selector']}")
            elif action.get("action") == "finish":
                print("Task completed. Summary:")
                print(action.get("summary"))
                break
            else:
                print("Unknown action. Stopping.")
                break

            time.sleep(2)  # 페이지 로딩 안정화

        browser.close()

# -----------------------------
# 실행 예제
# -----------------------------
if __name__ == "__main__":
    autonomous_browser("search for 'rickroll' on YouTube and play the first video", "https://www.youtube.com")
