import asyncio
from core import (
    client,
    create_response_with_retry,
    handle_action,
    process_model_response,
    take_screenshot
)
from core.config import DISPLAY_WIDTH, DISPLAY_HEIGHT, MODEL
from playwright.async_api import async_playwright

async def main():
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
            if task.lower() in ('exit', 'quit'):
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
