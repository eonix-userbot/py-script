import asyncio
import random
import sys
import os
import json
import logging
from itertools import count
from urllib.parse import unquote
from typing import List
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# ---------- CONFIG ----------
# You can set these via environment variables or edit here.
SESSION_ID = os.getenv("SESSION_ID", "").strip()   # put your IG sessionid here or export env
DM_URL = os.getenv("DM_URL", "").strip()           # e.g. "https://www.instagram.com/direct/t/23868009596216607/"
PASSWORD = os.getenv("SCRIPT_PASSWORD", "").strip()  # must match one of allowed passwords
USER_PREFIX = os.getenv("USER_PREFIX", "TEAM")     # optional
TASKS = int(os.getenv("TASKS", "4"))               # number of concurrent workers
BASE_DELAY = float(os.getenv("BASE_DELAY", "2.0")) # recommended >= 1.0 for safety
JITTER = float(os.getenv("JITTER", "0.5"))         # randomness added/subtracted to delays
HEADLESS = os.getenv("HEADLESS", "true").lower() in ("1", "true", "yes")
OUTPUT_STATS = os.getenv("OUTPUT_STATS", "true").lower() in ("1", "true", "yes")
DATA_SAVE_FILE = os.getenv("DATA_FILE", "ig_renamer_state.json")
# Allowed script passwords (from the two original authors)
ALLOWED_PASSWORDS = {"pyscriptqueen", "eonixpapa"}
# ----------------------------

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("ig_renamer")

# Merge the base name pools from both original scripts (cleaned/simplified)
UFO_BASES = [
    "Rose", "Lily", "Daisy", "Orchid", "Cherry", "Star", "Nova",
    "⭞ ᴛᴍᴋᴄ ￫⋰🥰⋱", "⭞ ᴛᴍᴋᴄ ￫⋰😍⋱", "⭞ ᴛᴍᴋᴄ ￫⋰😘⋱", "⭞ ᴛᴍᴋᴄ ￫⋰🤑⋱",
    "⭞ ᴛᴍᴋᴄ ￫⋰😡⋱", "⭞ ᴛᴍᴋᴄ ￫⋰😋⋱", "⭞ ᴛᴍᴋᴄ ￫⋰🥺⋱", "⭞ ᴛᴍᴋᴄ ￫⋰😏⋱",
    "TMR", "HATER", "REXX", "RAVAN", "SENA", "SPIDY", "TMKL", "TMKC"
]
EMOJI_SUFFIXES = ["🌸", "💜", "✨", "💕", "🦋", "❤", "🧡", "💛", "💚", "💙"]
name_counter = count(1)
used_names = set()

# Stats
stats = {"success": 0, "fail": 0, "attempts": 0}

# Helper: save state minimally
def save_state():
    try:
        with open(DATA_SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump({"used_names": list(used_names), "stats": stats}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.debug("Could not save state: %s", e)

def generate_name(prefix: str = USER_PREFIX) -> str:
    """Create a unique name combining prefix, base, emoji and incremental suffix."""
    for _ in range(1000):
        base = random.choice(UFO_BASES)
        emoji = random.choice(EMOJI_SUFFIXES)
        suffix = next(name_counter)
        name = f"{prefix} {base} {emoji}_{suffix}"
        if name not in used_names:
            used_names.add(name)
            return name
    # fallback if exhausted
    return f"{prefix} {random.randint(1000,9999)}"

async def worker_task(context, worker_id: int):
    """Each worker opens a page, navigates to the DM, and repeatedly attempts renames."""
    page = await context.new_page()
    try:
        await page.goto(DM_URL, wait_until="domcontentloaded", timeout=120_000)
        # Wait for Conversation info/gear icon - try a few selectors
        # We wrap in a try so that single page error won't kill others
        selectors = [
            'svg[aria-label*="Conversation"]',
            'svg[aria-label*="Conversation information"]',
            'svg[aria-label*="Info"]',
            'svg[aria-label*="Details"]',
        ]
        found = False
        for sel in selectors:
            try:
                gear = page.locator(sel)
                await gear.wait_for(timeout=15_000)
                await gear.click()
                found = True
                break
            except PlaywrightTimeoutError:
                continue
        if not found:
            logger.warning(f"[W{worker_id}] Could not find group info button; page may be different.")
            # proceed anyway: try to find change name btn
        # locate the change name input/buttons (several fallbacks)
        change_btn = page.locator('div[aria-label="Change group name"][role="button"]')
        group_input = page.locator('input[aria-label="Group name"], input[name="change-group-name"], input[type="text"]')
        save_btn = page.locator('div[role="button"]:has-text("Save")')
    except Exception as e:
        logger.error(f"[W{worker_id}] Page init failed: {e}")
        await page.close()
        return

    # Main loop: generate name -> click change -> fill -> save -> sleep (with jitter)
    while True:
        attempt_name = generate_name()
        stats["attempts"] += 1
        try:
            # try click change button if visible
            try:
                await change_btn.click(timeout=3000)
            except Exception:
                # maybe already in edit or selector different - continue
                pass

            # focus and fill
            try:
                await group_input.click(click_count=3, timeout=3000)
                await group_input.fill(attempt_name, timeout=3000)
            except Exception:
                # fallback: use keyboard to type (slower)
                try:
                    await group_input.focus()
                    await page.keyboard.press("Control+A")
                    await page.keyboard.type(attempt_name)
                except Exception:
                    logger.debug(f"[W{worker_id}] Couldn't fill input directly; skipping this attempt.")
                    raise

            # check save button disabled attribute if present
            try:
                disabled = await save_btn.get_attribute("aria-disabled")
                if disabled == "true":
                    # nothing to save or name invalid; count as fail
                    stats["fail"] += 1
                    logger.debug(f"[W{worker_id}] Save button disabled for '{attempt_name}'.")
                else:
                    await save_btn.click(timeout=3000)
                    stats["success"] += 1
                    logger.info(f"[W{worker_id}] Renamed -> {attempt_name}  (S:{stats['success']}, F:{stats['fail']})")
            except Exception:
                # final fallback: press Enter
                try:
                    await page.keyboard.press("Enter")
                    stats["success"] += 1
                    logger.info(f"[W{worker_id}] Renamed (enter) -> {attempt_name}")
                except Exception as e:
                    stats["fail"] += 1
                    logger.debug(f"[W{worker_id}] Save fallback failed: {e}")
        except Exception as e:
            stats["fail"] += 1
            logger.debug(f"[W{worker_id}] Attempt error: {e}")

        # save state periodically
        if stats["attempts"] % 20 == 0:
            save_state()

        # Delay with jitter
        delay = max(0.0, BASE_DELAY + random.uniform(-JITTER, JITTER))
        await asyncio.sleep(delay)

async def show_stats_periodically():
    while True:
        if OUTPUT_STATS:
            logger.info(f"Stats: attempts={stats['attempts']} success={stats['success']} fail={stats['fail']} used_names={len(used_names)}")
        await asyncio.sleep(5.0)

async def main():
    # Basic checks
    if not PASSWORD:
        print("Please set SCRIPT_PASSWORD env or edit the top of the file with PASSWORD.")
        return
    if PASSWORD not in ALLOWED_PASSWORDS:
        print("Access denied: invalid script password.")
        print("Allowed: pyscriptqueen or eonixpapa")
        return
    if not SESSION_ID:
        print("Please set SESSION_ID (Instagram session cookie). Exiting.")
        return
    if not DM_URL:
        print("Please set DM_URL (Instagram direct thread URL). Exiting.")
        return

    # Start Playwright
    logger.info("Starting Playwright (headless=%s) ...", HEADLESS)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(locale="en-US", extra_http_headers={"Referer": "https://www.instagram.com/"})
        # add the sessionid cookie
        await context.add_cookies([{
            "name": "sessionid",
            "value": SESSION_ID,
            "domain": ".instagram.com",
            "path": "/",
            "httpOnly": True,
            "secure": True,
            "sameSite": "None"
        }])
        # create workers
        workers = [asyncio.create_task(worker_task(context, i)) for i in range(1, TASKS + 1)]
        workers.append(asyncio.create_task(show_stats_periodically()))
        try:
            await asyncio.gather(*workers)
        except asyncio.CancelledError:
            logger.info("Cancelled, shutting down.")
        except KeyboardInterrupt:
            logger.info("Interrupted by user.")
        finally:
            await browser.close()
            save_state()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        logger.exception("Fatal error: %s", exc)
