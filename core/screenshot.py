import time
import base64
from playwright.async_api import Page
from .config import SCREENSHOT_ROOT

async def take_screenshot(page: Page, subdir: str = "", prefix: str = "shot"):
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
