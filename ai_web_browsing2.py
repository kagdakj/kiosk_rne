import ollama
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json

# -----------------------------
# Ollama helper
# -----------------------------
system_prompt = """
You are a fully autonomous web browsing agent.
You receive a structured list of actionable elements on the page.
You must respond with ONE action in JSON:

{"action": "goto", "url": "https://example.com"}
{"action": "click", "selector": "CSS_SELECTOR"}
{"action": "type", "selector": "CSS_SELECTOR", "text": "TEXT"}
{"action": "finish", "summary": "SUMMARY_TEXT"}

Do NOT include explanations or any text outside JSON.
If you cannot perform an action, respond with finish and summarize the page instead.
"""

def ask_ollama(prompt):
    resp = ollama.chat(
        model="llama3.1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    return resp['message']['content']

# -----------------------------
# Extract interactive elements
# -----------------------------
def extract_actions(html, max_elements=20):
    soup = BeautifulSoup(html, "html.parser")
    inputs = [{"selector": f"#{i.get('id')}", "placeholder": i.get("placeholder", "")}
              for i in soup.find_all("input") if i.get("id")]
    buttons = [{"selector": f"#{b.get('id')}", "text": b.get_text(strip=True)}
               for b in soup.find_all("button") if b.get("id")]
    links = [{"selector": f"#{a.get('id')}", "text": a.get_text(strip=True)}
             for a in soup.find_all("a") if a.get("id")]
    return {
        "inputs": inputs[:max_elements],
        "buttons": buttons[:max_elements],
        "links": links[:max_elements]
    }

# -----------------------------
# Autonomous browsing agent
# -----------------------------
def autonomous_browser(goal, start_url="https://www.youtube.com"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(start_url)

        while True:
            html = page.content()
            dom_snapshot = extract_actions(html)

            prompt = f"""
Goal: {goal}
Current actionable elements on the page:
{json.dumps(dom_snapshot, indent=2)}

Decide ONE action to achieve the goal. Respond ONLY in JSON.
"""
            command = ask_ollama(prompt)
            print("Ollama Command:", command)

            try:
                action = json.loads(command)
            except json.JSONDecodeError:
                print("Invalid JSON. Stopping.")
                break

            if action["action"] == "goto":
                page.goto(action["url"])

            elif action["action"] == "click":
                try:
                    page.click(action["selector"])
                except:
                    print(f"Failed to click {action['selector']}")

            elif action["action"] == "type":
                try:
                    page.fill(action["selector"], action["text"])
                except:
                    print(f"Failed to type into {action['selector']}")

            elif action["action"] == "finish":
                print("Task Completed. Summary:\n", action["summary"])
                break

            else:
                print("Unknown action. Stopping.")
                break

        browser.close()

# -----------------------------
# Run the agent
# -----------------------------
autonomous_browser("search for 'rickroll' on YouTube and play the video")
