from .screenshot import take_screenshot
from .agent_core import handle_action, create_response_with_retry
from .config import MODEL, DISPLAY_WIDTH, DISPLAY_HEIGHT, ITERATIONS

def extract_url(page):
    try:
        return page.url if page.url and page.url != "about:blank" else None
    except:
        return None

async def process_model_response(client, response, page, max_iterations=ITERATIONS):
    for iteration in range(max_iterations):
        if not getattr(response, 'output', None):
            print("No output from model.")
            break

        print(f"\n[Iteration {iteration+1}] Response ID: {getattr(response, 'id', 'unknown')}")

        for item in response.output:
            if getattr(item, "type", None) == "text":
                print(f"[テキスト応答]\n{item.text}")
            if getattr(item, "type", None) == "reasoning":
                print("[推論]")
                for s in getattr(item, "summary", []):
                    print(s if isinstance(s, str) else getattr(s, "text", ""))

        calls = [o for o in response.output if getattr(o, 'type', None) == 'computer_call']
        if not calls:
            break

        call = calls[0]
        await handle_action(page, call.action)

        img_b64 = await take_screenshot(page)

        next_input = [{
            "type": "computer_call_output",
            "call_id": call.call_id,
            "output": {"type": "input_image", "image_url": f"data:image/png;base64,{img_b64}"}
        }]

        cur_url = extract_url(page)
        if cur_url:
            next_input[0]["current_url"] = cur_url
            print(f"\tCurrent URL: {cur_url}")

        try:
            response = create_response_with_retry(
                client,
                model=MODEL,
                previous_response_id=response.id,
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
