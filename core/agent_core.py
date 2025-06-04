import time
import json
import asyncio
from openai import APIError, APIConnectionError
from .config import DISPLAY_WIDTH, DISPLAY_HEIGHT

KEY_MAPPING = {
    "/": "Slash", "\\": "Backslash", "alt": "Alt", "arrowdown": "ArrowDown",
    "arrowleft": "ArrowLeft", "arrowright": "ArrowRight", "arrowup": "ArrowUp",
    "backspace": "Backspace", "ctrl": "Control", "delete": "Delete",
    "enter": "Enter", "esc": "Escape", "shift": "Shift", "space": " ",
    "tab": "Tab", "win": "Meta", "cmd": "Meta", "super": "Meta", "option": "Alt"
}

def validate_coordinates(x, y):
    return max(0, min(x, DISPLAY_WIDTH)), max(0, min(y, DISPLAY_HEIGHT))

def create_response_with_retry(client, **kwargs):
    last_resp = None
    for attempt in range(5):
        try:
            return client.responses.create(**kwargs)
        except (APIError, APIConnectionError) as e:
            code = getattr(e, "http_status", None)
            if code and (code == 499 or 500 <= code < 600):
                wait = 2 ** attempt
                print(f"⚠️ サーバーエラー {code}、{wait}s 後に再試行 ({attempt+1}/5)")
                time.sleep(wait)
                continue
            else:
                dump = last_resp.model_dump() if last_resp else {}
                with open("error_response_dump.json", "w", encoding="utf-8") as f:
                    json.dump(dump, f, ensure_ascii=False, indent=2)
                raise
    raise RuntimeError("Responses API のリトライが上限に達しました。")

async def handle_action(page, action):
    action_type = action.type
    if action_type == "click":
        selector = getattr(action, "selector", None)
        if selector:
            print(f"\tCSSクリック: {selector}")
            await page.wait_for_selector(selector, timeout=5000)
            await page.click(selector)
            return
        x, y = validate_coordinates(action.x, action.y)
        button = getattr(action, "button", "left")
        print(f"\tクリック: ({x},{y}) ボタン={button}")
        await page.mouse.click(x, y, button=button)
    elif action_type == "type":
        text = getattr(action, "text", "")
        print(f"\t文字入力: {text}")
        await page.keyboard.type(text, delay=50)
    elif action_type == "keypress":
        raw_keys = getattr(action, "keys", [])
        mapped_keys = [KEY_MAPPING.get(k.lower(), k.title()) for k in raw_keys]
        if len(mapped_keys) > 1:
            for key in mapped_keys:
                await page.keyboard.down(key)
            await asyncio.sleep(0.1)
            for key in reversed(mapped_keys):
                await page.keyboard.up(key)
        else:
            await page.keyboard.press(mapped_keys[0])
    elif action_type == "screenshot":
        print("\tスクリーンショットアクション検出")
    else:
        print(f"\t未対応アクション: {action_type}")
