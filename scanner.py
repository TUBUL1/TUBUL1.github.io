import sys
import re
import asyncio
import json
import time
import random
import os
from datetime import datetime

# --- PHASE 0: ENVIRONMENT SETUP & DEPENDENCIES ---
# בדיקת ספריות חיוניות וטעינת הגדרות מסוף
try:
    import cloudscraper
    from bs4 import BeautifulSoup
    from playwright.async_api import async_playwright
except ImportError as e:
    print(f"[!] PHASE 0 ERROR: MISSING LIBRARIES: {e}")
    sys.exit(1)

def setup_terminal():
    """מכין את הטרמינל לתצוגה מקצועית של Phases."""
    if sys.platform == 'win32':
        try: sys.stdout.reconfigure(encoding='utf-8')
        except: pass
    border = "█" * 115
    print(f"\033[94m{border}\033[0m")
    print(f"\033[94m█ {'SIMPCITY ULTIMATE AUDITOR V3.3 - PHASE-MODULAR EDITION':^111} █\033[0m")
    print(f"\033[94m█ {'SYSTEM STATUS: READY | ARCHITECTURE: FULL-STRETCH | SHORTCUTS: DISABLED':^111} █\033[0m")
    print(f"\033[94m{border}\033[0m\n")

# נתוני גישה קבועים
GLOBAL_COOKIES = [
    {'name': 'ogaddgmetaprof_csrf', 'value': 'OhQ__ZiHgmgSlfey', 'domain': 'simpcity.cr', 'path': '/'},
    {'name': 'ogaddgmetaprof_session', 'value': 'tiNlDM7Fvoye-rl9MTiw_ZbJfYuVrjZd', 'domain': 'simpcity.cr', 'path': '/'},
    {'name': 'ogaddgmetaprof_user', 'value': '8477776%2Cu76fYs2peE6E_lMf5YcpocIrmMBIfCB8iuPMwnnb', 'domain': 'simpcity.cr', 'path': '/'}
]

class UltimateAuditor:
    def __init__(self):
        # אתחול מנועי הסריקה
        self.scraper = cloudscraper.create_scraper()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://simpcity.cr/'
        }
        self.req_cookies = {c['name']: c['value'] for c in GLOBAL_COOKIES}
        
        # מאגרי מידע למניעת כפילויות (De-duplication Stores)
        self.discovered_threads = []
        self.seen_thread_ids = set()      # PHASE 1 & 2
        self.seen_download_links = set()  # PHASE 3
        
        self.final_audit_results = []
        self.total_scanned_gb = 0.0
        
        # רשימת הגנה על שמות (White-list)
        self.protected_names = ["maisi", "aisha", "bailey", "daisy", "stacy", "sophieraiin", "raiin", "kaia", "maia"]

    def log(self, phase, action, message, status="INFO"):
        """מדפיס לוג מפורט הכולל את ה-Phase הנוכחי."""
        colors = {
            "INFO": "\033[94m[INFO]\033[0m",
            "SUCCESS": "\033[92m[SUCCESS]\033[0m", 
            "WARNING": "\033[93m[WARNING]\033[0m", 
            "ERROR": "\033[91m[ERROR]\033[0m", 
            "AI": "\033[95m[AI-FILTER]\033[0m", 
            "DUPLICATE": "\033[90m[DUPLICATE]\033[0m"
        }
        timestamp = datetime.now().strftime("%H:%M:%S")
        phase_str = f"PHASE-{phase}"
        print(f"[{timestamp}] [{phase_str:<7}] {colors.get(status, '[•]')} {action:<20} | {message}")

    # --- PHASE 2.1: URL NORMALIZATION ---
    def normalize_url(self, raw_url):
        """מנרמל URL כדי למנוע כפילויות של אותה הודעה במיקומים שונים."""
        match = re.search(r'(threads/[^/]+\.\d+)', raw_url)
        if match:
            return "https://simpcity.cr/" + match.group(1) + "/"
        return raw_url

    # --- PHASE 1.2: AI CONTENT VALIDATION ---
    def validate_content_authenticity(self, title):
        """בודק זיופי AI ללא פשרות וללא קיצורי דרך."""
        t_lower = title.lower().strip()
        is_protected = any(p in t_lower for p in self.protected_names)

        hard_filters = [
            r'fake\s*ai', r'ai\s*gen', r'ai\s*model', 
            r'deepfake', r'generated', r'stable\s*diffusion'
        ]

        for pattern in hard_filters:
            if re.search(pattern, t_lower):
                return False, f"Matched Forbidden AI Pattern: {pattern}"

        if not is_protected:
            if re.search(r'\bai\b', t_lower) or t_lower.endswith(' ai'):
                return False, "Standalone AI tag detected"

        return True, "Authentic"

    # --- PHASE 1: SEARCH & DISCOVERY ---
    def execute_deep_search(self, creator_name):
        """מנוע החיפוש והגילוי הראשוני."""
        self.log(1, "START", f"Deep search initiated for: {creator_name}")
        search_terms = creator_name.lower().replace('_', ' ').replace('.', ' ').split()
        
        search_url = "https://simpcity.cr/search/search"
        payload = {'keywords': creator_name, 'order': 'date'}

        try:
            res = self.scraper.post(search_url, data=payload, cookies=self.req_cookies, headers=self.headers, allow_redirects=True)
            current_url = res.url
            if "search/" not in current_url:
                current_url = f"https://simpcity.cr/search/1/?q={creator_name.replace(' ', '+')}&o=date"

            page_num = 1
            while current_url:
                self.log(1, "SEARCH-PAGINATION", f"Scanning Results Page {page_num}...")
                page_data = self.scraper.get(current_url, cookies=self.req_cookies, headers=self.headers)
                if page_data.status_code != 200: break
                
                soup = BeautifulSoup(page_data.text, 'html.parser')
                threads = soup.find_all('div', class_='contentRow-main')
                
                for t in threads:
                    title_node = t.find('h3', class_='contentRow-title')
                    if not title_node or not title_node.find('a'): continue
                    
                    full_title = title_node.get_text(strip=True)
                    raw_link = title_node.find('a').get('href')
                    
                    # --- PHASE 2: FILTERING & DE-DUPLICATION ---
                    clean_url = self.normalize_url(raw_link)
                    
                    if clean_url in self.seen_thread_ids:
                        self.log(2, "DUPLICATE-SKIP", f"Ignoring redundant URL: {full_title[:30]}...", "DUPLICATE")
                        continue

                    is_ok, reason = self.validate_content_authenticity(full_title)
                    if not is_ok:
                        self.log(2, "AI-FILTER", f"Discarded: {full_title[:30]} ({reason})", "AI")
                        continue

                    if not all(word in full_title.lower().replace('_', ' ').replace('.', ' ') for word in search_terms):
                        continue

                    if any(x in full_title.lower() for x in ["identify", "request", "discussion"]) and "megathread" not in full_title.lower():
                        self.log(2, "NOISE-SKIP", f"Skipping chat: {full_title[:30]}...", "WARNING")
                        continue

                    self.log(1, "MATCH-FOUND", f"Unique Entry: {full_title[:50]}", "SUCCESS")
                    self.discovered_threads.append({"title": full_title, "url": clean_url})
                    self.seen_thread_ids.add(clean_url)

                next_pg = soup.find('a', class_='pageNav-jump--next')
                if next_pg:
                    current_url = "https://simpcity.cr" + next_pg.get('href')
                    page_num += 1
                    time.sleep(random.uniform(2.5, 4.0))
                else:
                    current_url = None

            return len(self.discovered_threads) > 0
        except Exception as e:
            self.log(1, "ERROR", f"Search Phase Failed: {e}", "ERROR")
            return False

    # --- PHASE 3.2: HOST INSPECTION ---
    async def inspect_link(self, page, url):
        """מבצע אימות פיזי לכל לינק הורדה שנמצא."""
        try:
            await page.set_extra_http_headers({"User-Agent": self.headers['User-Agent']})
            resp = await page.goto(url, wait_until="networkidle", timeout=35000)
            if not resp or resp.status == 404: return 0.0, "❌ OFFLINE (404)"

            content = await page.content()
            
            if "gofile.io" in url:
                if "does not exist" in content: return 0.0, "❌ OFFLINE"
                try:
                    await page.wait_for_selector("#filemanager_itemslist, .bi-file-earmark", timeout=12000)
                    spans = await page.eval_on_selector_all("span", "els => els.map(e => e.innerText)")
                    gb = 0.0
                    for s in spans:
                        m = re.search(r'(\d+\.?\d*)\s*(GB|MB)', s, re.I)
                        if m:
                            v = float(m.group(1))
                            gb += v if 'GB' in m.group(2).upper() else v / 1024
                    return gb, "✅ ACTIVE"
                except: return 0.0, "✅ ACTIVE (SIZE N/A)"
            
            elif "pixeldrain.com" in url:
                if "not found" in content.lower(): return 0.0, "❌ OFFLINE"
                m = re.search(r'(\d+\.?\d*)\s*(GB|MB|GiB)', content, re.I)
                if m:
                    v = float(m.group(1))
                    u = m.group(2).upper()
                    return (v if 'G' in u else v / 1024), "✅ ACTIVE"
                return 0.0, "✅ ACTIVE"

            return 0.0, "✅ ACTIVE"
        except Exception:
            return 0.0, "⚠️ TIMEOUT/ERROR"

    # --- PHASE 3: CONTENT EXTRACTION & AUDIT ---
    async def process_all_threads(self):
        """סריקה עמוקה של דפי הדיונים וחילוץ נתונים."""
        self.log(3, "AUDIT-START", f"Processing {len(self.discovered_threads)} unique thread sources...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            await context.add_cookies(GLOBAL_COOKIES)
            
            for idx, thread in enumerate(self.discovered_threads, 1):
                self.log(3, "THREAD-OPEN", f"Source {idx}/{len(self.discovered_threads)}: {thread['title'][:45]}")
                tp = await context.new_page()
                try:
                    await tp.goto(thread['url'], wait_until="domcontentloaded", timeout=45000)
                    
                    # חילוץ דפדוף פנימי
                    pages = 1
                    nav = await tp.query_selector_all("ul.pageNav-main li")
                    if nav:
                        try: pages = int(await nav[-1].inner_text())
                        except: pages = 1

                    for p_idx in range(1, pages + 1):
                        if p_idx > 1:
                            await tp.goto(f"{thread['url']}page-{p_idx}", wait_until="domcontentloaded")
                        
                        self.log(3, "PAGE-SCAN", f"   Extracting links from Page {p_idx}/{pages}...")
                        src = await tp.content()
                        
                        # חילוץ לינקים בעזרת RegEx
                        raw_links = re.findall(r'https?://(?:gofile\.io/d/|pixeldrain\.com/[ul]/|bunkr|saint2)[a-zA-Z0-9./]+', src)
                        unique_links_in_page = set(raw_links)
                        
                        for l in unique_links_in_page:
                            # מניעת כפילות לינקים להורדה
                            if l in self.seen_download_links:
                                continue
                            
                            self.log(3, "INSPECTING", f"      Targeting: {l}")
                            ip = await context.new_page()
                            size, status = await self.inspect_link(ip, l)
                            
                            self.final_audit_results.append({
                                "thread": thread['title'][:30], "url": l, "status": status, "size": size
                            })
                            self.total_scanned_gb += size
                            self.seen_download_links.add(l)
                            await ip.close()
                            await asyncio.sleep(1.5)

                except Exception as e:
                    self.log(3, "THREAD-ERROR", f"Failed: {e}", "ERROR")
                finally:
                    await tp.close()

            await browser.close()
            self.final_report()

    # --- PHASE 4: REPORT GENERATION ---
    def final_report(self):
        """הפקת סיכום נתונים סופי."""
        print("\n" + "═"*135)
        print(f"║ {'PHASE 4: FINAL AUDIT SUMMARY':^131} ║")
        print("═"*135)
        for i in self.final_audit_results:
            sz_txt = f"{i['size']:.2f} GB" if i['size'] >= 1 else f"{i['size']*1024:.0f} MB"
            print(f"[{i['status']}] | {sz_txt:<10} | {i['thread']:<40} | {i['url']}")
        print("═"*135)
        print(f"✅ SYSTEM COMPLETED | TOTAL UNIQUE DATA: {self.total_scanned_gb:.2f} GB\n")

# --- MAIN EXECUTION GATE ---
async def run_audit():
    setup_terminal()
    app = UltimateAuditor()
    name = input("[?] ENTER CREATOR NAME TO START: ").strip()
    
    # PHASE 1 & 2
    if name and app.execute_deep_search(name):
        # PHASE 3 & 4
        await app.process_all_threads()
    else:
        print("[!] No results found. System shutting down.")

if __name__ == "__main__":
    asyncio.run(run_audit())