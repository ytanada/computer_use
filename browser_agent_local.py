import os
import time
import asyncio
import base64
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI, APIError, APIConnectionError
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from playwright.async_api import async_playwright, TimeoutError

# --- Load environment variables ---
load_dotenv()

API_KEY         = os.getenv("API_KEY")
AZURE_ENDPOINT  = os.getenv("AZURE_ENDPOINT")
API_VERSION     = os.getenv("API_VERSION")
MODEL           = os.getenv("MODEL")
DISPLAY_WIDTH   = int(os.getenv("DISPLAY_WIDTH", 1920))
DISPLAY_HEIGHT  = int(os.getenv("DISPLAY_HEIGHT", 1200))
ITERATIONS      = int(os.getenv("ITERATIONS", 9))
SCREENSHOT_ROOT = Path(__file__).parent / os.getenv("SCREENSHOT_DIR", "screenshots")

KEY_MAPPING = {
    "/": "Slash", "\\": "Backslash", "alt": "Alt", "arrowdown": "ArrowDown",
    "arrowleft": "ArrowLeft", "arrowright": "ArrowRight", "arrowup": "ArrowUp",
    "backspace": "Backspace", "ctrl": "Control", "delete": "Delete",
    "enter": "Enter", "esc": "Escape", "shift": "Shift", "space": " ",
    "tab": "Tab", "win": "Meta", "cmd": "Meta", "super": "Meta", "option": "Alt"
}

def validate_coordinates(x, y):
    return max(0, min(x, DISPLAY_WIDTH)), max(0, min(y, DISPLAY_HEIGHT))

# --- 追加：リトライ＆デバッグ用ラッパー -----------------------------------
def create_response_with_retry(client, **kwargs):
    last_resp = None
    for attempt in range(5):
        try:
            resp = client.responses.create(**kwargs)
            return resp
        except (APIError, APIConnectionError) as e:
            code = getattr(e, "http_status", None)
            # 499 や 5xx はリトライ
            if code and (499 == code or 500 <= code < 600):
                wait = 2 ** attempt
                print(f"⚠️ サーバーエラー {code}、{wait}s 後に再試行します ({attempt+1}/5)")
                time.sleep(wait)
                continue
            # その他はログダンプして再送せずにエラーを上げる
            else:
                dump = {}
                if last_resp:
                    dump = last_resp.model_dump()
                with open("error_response_dump.json", "w", encoding="utf-8") as f:
                    json.dump(dump, f, ensure_ascii=False, indent=2)
                print("❌ デバッグ用ダンプを error_response_dump.json に保存しました")
                raise
    raise RuntimeError("Responses API のリトライが上限に達しました。")

# --- 以下は既存コードに少し手を加えたもの --------------------------------

async def handle_action(page, action):
    action_type = action.type
    if action_type == "click":
        selector = getattr(action, "selector", None)
        if selector:
            print(f"\tCSSクリック: {selector}")
            await page.wait_for_selector(selector, timeout=5000)
            await page.click(selector)
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=5000)
            except TimeoutError:
                pass
            return
        x, y = validate_coordinates(action.x, action.y)
        button = getattr(action, "button", "left")
        print(f"\tクリック: ({x},{y}) ボタン={button}")
        if button == "back":
            await page.go_back()
        else:
            await page.mouse.click(x, y, button=button)
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=3000)
            except TimeoutError:
                pass
    elif action_type == "type":
        text = getattr(action, 'text', '')
        print(f"\t文字入力: {text}")
        await page.keyboard.type(text, delay=50)
    elif action_type == "keypress":
        raw_keys = getattr(action, "keys", [])
        print(f"\tAction: keypress {raw_keys}")
        lower_keys = [k.lower() for k in raw_keys]
        mapped_keys = [KEY_MAPPING.get(k, k.title()) for k in lower_keys]
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

async def take_screenshot(page, subdir: str = "", prefix: str = "shot"):
    data = await page.screenshot(full_page=False)
    target_dir = SCREENSHOT_ROOT / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{ts}.png"
    path = target_dir / filename
    with open(path, "wb") as f:
        f.write(data)
    print(f"Saved screenshot to: {path}")
    return base64.b64encode(data).decode()

async def process_model_response(client, response, page, max_iterations=ITERATIONS):
    for iteration in range(max_iterations):
        if not hasattr(response, 'output') or not response.output:
            print("No output from model.")
            break

        response_id = getattr(response, 'id', 'unknown')
        print(f"\nIteration {iteration+1} - Response ID: {response_id}\n")

        # モデル応答全体ダンプ（デバッグ用）
        print("=== API レスポンス 全体 ===")
        print(json.dumps(response.model_dump(), indent=2, ensure_ascii=False))
        print("===========================\n")

        # テキスト＆推論を表示
        for item in response.output:
            if getattr(item, "type", None) == "text":
                print(f"[モデルのテキスト応答]\n{item.text}\n")
            if getattr(item, "type", None) == "reasoning" and item.summary:
                print("=== Model Reasoning ===")
                for s in item.summary:
                    print(s if isinstance(s, str) else getattr(s, "text", ""))
                print("=====================\n")

        calls = [o for o in response.output if getattr(o, 'type', None) == 'computer_call']
        if not calls:
            break

        call = calls[0]
        call_id = call.call_id
        action  = call.action

        print(f">>> 実行アクション: {action.type}, call_id={call_id}")
        await handle_action(page, action)

        img_b64 = await take_screenshot(page)
        print("\tNew screenshot taken")

        next_input = [{
            "type": "computer_call_output",
            "call_id": call_id,
            "output": {"type": "input_image", "image_url": f"data:image/png;base64,{img_b64}"}
        }]
        # 現在URLも渡す
        try:
            cur = page.url
            if cur and cur != "about:blank":
                next_input[0]["current_url"] = cur
                print(f"\tCurrent URL: {cur}")
        except:
            pass

        # 次ステップ呼び出しもリトライラッパーで
        try:
            response = create_response_with_retry(
                client,
                model=MODEL,
                previous_response_id=response_id,
                tools=[{
                    "type": "computer_use_preview",
                    "display_width": DISPLAY_WIDTH,
                    "display_height": DISPLAY_HEIGHT,
                    "environment": "browser"
                }],
                input=next_input,
                truncation="auto"
            )
        except Exception as e:
            print(f"❌ 次ステップ API 呼び出しに失敗: {e}")
            break

    if iteration >= max_iterations-1:
        print("Reached maximum number of iterations. Stopping.")

async def main():
    client = AzureOpenAI(
        api_key=API_KEY,
        azure_endpoint=AZURE_ENDPOINT,
        api_version=API_VERSION
    )

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="/home/ubuntu/work/.chrome-profile",
            headless=False,
            executable_path="/usr/bin/google-chrome",
            args=[
                f"--window-size={DISPLAY_WIDTH},{DISPLAY_HEIGHT}",
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-setuid-sandbox",
                "--ignore-certificate-errors",
                "--disable-features=IsolateOrigins,site-per-process"
            ],
            viewport={"width": DISPLAY_WIDTH, "height": DISPLAY_HEIGHT},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto('https://www.bing.com/?cc=jp', wait_until='domcontentloaded')

        while True:
            task = input("Enter a task (or 'exit'): ")
            if task.lower() in ('exit','quit'):
                break

            img0 = await take_screenshot(page)
            try:
                response = create_response_with_retry(
                    client,
                    model=MODEL,
                    tools=[{
                        'type': 'computer_use_preview',
                        'display_width': DISPLAY_WIDTH,
                        'display_height': DISPLAY_HEIGHT,
                        'environment': 'browser'
                    }],
                    instructions=(
                        "あなたはブラウザを操作する AI です\n"
                        "1) 検索ボックスを CSS セレクタ `input[name=\"q\"]` で選択し、\n"
                        f"   「{task}」を入力後、Enter を押してください。\n"
                        "2) 検索結果リストの最初のリンク要素を\n"
                        "   CSS セレクタ `li.b_algo h2 a` でクリックしてください。\n"
                        "3) リンク先ページに遷移したらスクリーンショットを撮影し、"
                        "最後にそのページのタイトルを報告してください。"
                    ),
                    input=[{
                        'role': 'user',
                        'content': [
                            {'type': 'input_text',  'text': task},
                            {'type': 'input_image', 'image_url': f"data:image/png;base64,{img0}"}
                        ]
                    }],
                    truncation='auto'
                )
            except Exception as e:
                print(f"❌ 初回 API 呼び出しに失敗: {e}")
                break

            await process_model_response(client, response, page)

        await context.close()

if __name__ == '__main__':
    asyncio.run(main())
