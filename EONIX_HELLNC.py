import asyncio
import logging
import os
import random
import sys
import getpass
from itertools import count
from urllib.parse import unquote
from pyfiglet import figlet_format
from cfonts import render
from playwright.async_api import async_playwright

# --- Hellish Colors ---
COLORS = {
    'fred': '\033[38;5;196m',     # bright lava red
    'borange': '\033[38;5;208m',  # smoldering orange
    'cblack': '\033[38;5;232m',   # deep dark black/gray
    'hyellow': '\033[38;5;220m',  # glowing flame yellow
    'reset': '\033[0m',
    'bold': '\033[1m',
}

# --- Banner ---
def banner():
    os.system("cls" if os.name == "nt" else "clear")
    print(COLORS['fred'] + "☩☨" * 35 + COLORS['reset'])
    print(COLORS['borange'] + figlet_format("EONIX", font="bubble") + COLORS['reset'])
    print(COLORS['cblack'] + "The Rdp Killer : Eonix" + COLORS['reset'])
    print(COLORS['fred'] + "GOD OF HELL : EONIX| Version: 1" + COLORS['reset'])
    print(COLORS['hyellow'] + "Async Version⚰️" + COLORS['reset'])
    print(COLORS['fred'] + "☩☨" * 35 + COLORS['reset'])

# --- Authentication ---
print(COLORS['fred'] + "☩☨" * 35 + COLORS['reset'])
print(COLORS['borange'] + "†‡ SΞCURΞ ΛCCΞSS RΞQU1RΞD ‡†" + COLORS['reset'])
print(
    COLORS['cblack']
    + "☩☨ WΞLCΟMΞ ΤΟ ΤΗΞ HΞLLΙSH ΤΗRΟΝΞ: NΙTΙΝ ‡ RΙSHU ‡ MΑDΑRΑ ‡ SΡΙDΥ ☨☩"
    + COLORS['reset']
)
print(COLORS['hyellow'] + "🩸 Every step you take here is watched by unseen eyes… 🩸" + COLORS['reset'])
print(COLORS['fred'] + "☩☨" * 35 + COLORS['reset'])

password = getpass.getpass(
    f"{COLORS['borange']}🩸 Enter your secret key to continue:{COLORS['reset']} "
).strip()
if password != "pyscriptqueen":
    # FIXED: triple quotes to allow multiline text safely
    print(
        f"""{COLORS['fred']}O, F1LTHY SΩUL, WHΩ DΛRΞS DΞFY LΩRD EΩN1X ΛND ΞNTΞR HΞLL UNΛNNΩUNCΞD!
THΞ 1NFΞRNΛL FLΛMΞS CLΛ1M YΩU, BΩDY ΛND SP1R1T, FΩR ΞTΞRN1TY!{COLORS['reset']}"""
    )
    sys.exit(1)

# --- Welcome Screen ---
os.system("cls" if os.name == "nt" else "clear")
print(COLORS['fred'] + "☩☨" * 35 + COLORS['reset'])
print(COLORS['borange'] + figlet_format("WELCOME", font="slant") + COLORS['reset'])
print(
    COLORS['cblack']
    + "♡♡ Welcome to the script of "
    + COLORS['fred']
    + "Python Queen ANANYA ♡♡"
    + COLORS['reset']
)
print(COLORS['hyellow'] + "☩☨ CURSΞD ΛND CRΛFTΞD BY EΩN1X ☨☩" + COLORS['reset'])
print(COLORS['fred'] + "☩☨" * 35 + COLORS['reset'])

# --- Logging ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Name generation ---
ufo_bases = [
    "sᴀᴛᴀɴ", "ʀᴇᴀᴘᴇʀ", "ɢᴏᴅ ᴏғ ʜᴇʟʟ",
    "ᴅᴇᴍᴏɴ", "ᴅᴏᴏᴍ", "ғᴜʀʏ", "ɴᴀʀᴋ ᴋᴀ ᴅᴇᴠᴛᴀ"
]
emoji_suffixes = ["⚰️", "💀", "🔯", "☠️", "🪦"]
name_counter = count(1)
used_names = set()
success_count = 0
fail_count = 0
lock = asyncio.Lock()

# --- Inputs ---
banner()
session_id = input(
    f"{COLORS['borange']}☩☨ MΛSTΞR OF HΞLL, GRΛNT MΞ THΞ SΞSSIΩN ID ☨☩:{COLORS['reset']} "
).strip() or unquote("default_session_id")
dm_url = input(
    f"{COLORS['hyellow']}ΞNTΞR DΛMNΞD L1NK:{COLORS['reset']} "
).strip() or "https://www.instagram.com/direct/t/default/"
user_prefix = input(
    f"{COLORS['cblack']}†☩☨ MORTΛL, NAME THΛT NΛKΞD BLOODY ΛSS WHO SHALL SCREAM FOREVΞR †☨:{COLORS['reset']} "
).strip() or "Princess"

try:
    task_count = int(
        input(f"{COLORS['fred']}🩸HΞLL TΛSK CØUꋊT:{COLORS['reset']} ").strip()
    )
except ValueError:
    task_count = 5

def generate_name():
    """Generate a unique group name."""
    while True:
        base = random.choice(ufo_bases)
        emoji = random.choice(emoji_suffixes)
        suffix = next(name_counter)
        name = f"{user_prefix} {base} {emoji}_{suffix}"
        if name not in used_names:
            used_names.add(name)
            return name

async def rename_loop(context):
    """Main loop that keeps renaming the group."""
    global success_count, fail_count
    page = await context.new_page()
    try:
        await page.goto(dm_url, wait_until="domcontentloaded", timeout=120_000)
        gear = page.locator('svg[aria-label="Conversation information"]')
        await gear.wait_for(timeout=60_000)
        await gear.click()
    except Exception as e:
        logging.error(f"Page initialization failed: {e}")
        return

    change_btn = page.locator('div[aria-label="Change group name"][role="button"]')
    group_input = page.locator('input[aria-label="Group name"][name="change-group-name"]')
    save_btn = page.locator('div[role="button"]:has-text("Save")')

    while True:
        try:
            name = generate_name()
            await change_btn.click()
            await group_input.fill(name)

            if await save_btn.get_attribute("aria-disabled") == "true":
                async with lock:
                    fail_count += 1
                await asyncio.sleep(0.4)
                continue

            await save_btn.click()
            async with lock:
                success_count += 1

            await asyncio.sleep(1.0)
        except Exception as e:
            async with lock:
                fail_count += 1
            logging.warning(f"Rename attempt failed: {e}")
            await asyncio.sleep(1.0)

async def live_stats():
    """Show live statistics of progress."""
    while True:
        async with lock:
            print(
                f"{COLORS['borange']}‡☩ HΞLL PΛTH ☩‡: {dm_url}{COLORS['reset']}\n"
                f"{COLORS['cblack']}‡☩ BΩRNΞD SΩUL CΩUNTS ‡☩️: {task_count}{COLORS['reset']}\n"
                f"{COLORS['hyellow']}‡☩ ΛBYSSΛL T1TLΞ RΞVΞΛLΞD ☩‡: {len(used_names)}{COLORS['reset']}\n"
                f"{COLORS['fred']}‡☩ HΞLLW1N ☩‡: {success_count}{COLORS['reset']} | "
                f"{COLORS['borange']}‡☩ WΛSTΞD ☩‡: {fail_count}{COLORS['reset']}\n",
                flush=True
            )
        await asyncio.sleep(4)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            locale="en-US",
            extra_http_headers={"Referer": "https://www.instagram.com/"},
        )
        await context.add_cookies([{
            "name": "sessionid",
            "value": session_id,
            "domain": ".instagram.com",
            "path": "/",
            "httpOnly": True,
            "secure": True,
            "sameSite": "None"
        }])

        tasks = [asyncio.create_task(rename_loop(context)) for _ in range(task_count)]
        tasks.append(asyncio.create_task(live_stats()))

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logging.info("Tasks cancelled.")
        except KeyboardInterrupt:
            logging.info("Interrupted by user.")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

