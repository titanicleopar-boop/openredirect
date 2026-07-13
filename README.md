# 🛠️ LINUX INSTALLATION GUIDE FROM SCRATCH (INSTALLATION STEPS)

### 1. Update System & Install Dependencies
```bash
sudo apt update && sudo apt install python3 python3-pip python3-venv git -y
```

### 2. Install Required Python Packages
```bash
pip3 install curl-cffi uro
```

### 3. Set Executable Permissions
```bash
chmod +x openredirect.py
```

### 4. Run the Scanner
```bash
./openredirect.py
```
#### 5
```bash
https://www.kali.org/tools/getallurls
https://github.com/projectdiscovery/katana
https://github.com/tomnomnom/waybackurls
```
##### urltopkapsam.txt / wayback katana gau
---

###### Waf Speed
```bash
max_threads, request_delay = 20, 0.04  or 20 15 5 
```

####### Waf Speed
```bash
urllist.txt  add https://example.com 1x 10x *
```

######## 📺 PoC Video Demonstration

[![YouTube Video Kapağı](https://github.com/user-attachments/assets/45531d2a-fd89-49ee-a313-248864e41b44)](https://www.youtube.com/watch?v=aMGj7tm9E1E)

# 🚀 HIGHLIGHTED WEAPON FEATURES

### 1. JA4/TLS Fingerprint Impersonation (Anti-Bot Bypass)
Standard Python requests libraries are easily detected by cybersecurity firewalls (WAFs). This script utilizes `curl_cffi` to impersonate a real Google Chrome browser, tricking protection giants like Cloudflare, Akamai, and Imperva at the fingerprint (**TLS/JA4 Fingerprint**) level.

### 2. AI-Powered Anti-Captcha Room
Automatically detects verification barriers like reCAPTCHA that may appear during scanning. Thanks to **2Captcha API** integration, it solves obstacles automatically using AI without human intervention and continues scanning seamlessly.

### 3. 2-Stage Smart Prioritization
To save time, it first scans URLs containing keywords with the highest probability of causing an Open Redirect (`?next=`, `?url=`, `/logout/`) as **Step 1**. Then, it scans the entire remaining pool to ensure absolute success as **Step 2**.

### 4. Uro Smart URL De-duplication
Automatically reduces hundreds of unnecessary URLs with the same parameter (e.g., `sayfa.php?id=1`, `sayfa.php?id=2`) into a single template. This integration reduces crawling and fuzzing time by **10 times**.

### 5. Smart WAF Blocking Counter (Safe-Mode)
If the IP address receives 5 consecutive blocks from the target site (`403 Forbidden`, `429 Too Many Requests`), it automatically switches to safe mode and cools down to prevent the IP address from being completely banned (blacklisted).

### 6. Session Protection & Recovery (Resume/Checkpoint)
If the scan is interrupted, the power goes out, or you press `CTRL+C`, it writes the index number to a `checkpoint.json` file. When you restart the script, it doesn't start from zero; it continues exactly from the second it left off.

### 7. Centralized FTP Reporting Automation
Automatically uploads a stylish HTML report, generated when the scan is complete, to your specified remote or local FTP server for centralized logging.

### 8. Neon Cyber HTML Report
Produces a premium cybersecurity report powered by Bootstrap, supporting a dark mode theme, and cleanly displaying vulnerable links along with proof of concept (PoC) data.

### 9. 🧠 Akıllı Oturum Koruma ve sinsi Hafıza Sistemi (Kayıpsız Checkpoint)
Ziyaret Edilen URL Geçmişi: Tarayıcı artık sadece "kaçıncı sırada" olduğunu değil, taraması tamamen biten her URL'nin kendisini checkpoint.json dosyasına kazır.Mükerrer İstek Atlaması: Elektrik kesintisi veya bilgisayarın kapanması durumunda tarama baştan başlasa bile, liste sırası ne kadar değişirse değişsin, daha önce taranmış linkleri milisaniyeler içinde tespit eder ve tek bir payload bile göndermeden doğrudan pas geçer.Zafiyet Kurtarma: Çökme anına kadar bulduğun tüm zafiyetler JSON hafızasından otomatik olarak geri yüklenir; emeğin asla çöpe gitmez.

### 10. ⏱️ 15 Dakikada Bir Canlı Otomatik Raporlama ve FTP Yedekleme
Canlı Rapor Güncelleme: Tarama saatlerce sürse bile, scriptin bitmesini beklemeden her 15 dakikada bir o ana kadar bulunan tüm canlı zafiyetleri mevcut HTML raporuna anlık olarak yazar.

