from flask import Flask, redirect
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

NICKNAMES = {}

def load_nicknames():
    try:
        with open('nicknameIndex.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if ' - ' in line:
                    key, value = line.split(' - ', 1)
                    NICKNAMES[key.strip().upper()] = value.strip()
        print(f"Loaded {len(NICKNAMES)} SCP nicknames")
    except FileNotFoundError:
        print("nicknameIndex.txt not found")
    except Exception as e:
        print(f"Error loading nicknames: {e}")

load_nicknames()

@app.route('/')
def home():
    return """
    <h1>🛠 FixSCP</h1>
    <p>Simply replace scp-wiki.wikidot.com with this website´s URL</p>
    <p>© 2026 VoxyAvali</p>
    """

@app.route('/<path:path>')
def fix_scp(path):
    if path.startswith('http'):
        original_url = path
    else:
        match = re.search(r'(\d{3,4})', path)
        scp_num = f"SCP-{match.group(1).zfill(3)}" if match else "SCP-???"
        original_url = f"https://scp-wiki.wikidot.com/scp-{match.group(1).zfill(3)}" if match else f"https://scp-wiki.wikidot.com/{path}"

    try:
        headers = {'User-Agent': 'FixSCP Discord Embedder'}
        r = requests.get(original_url, headers=headers, timeout=10)
        
        if r.status_code != 200:
            return redirect(original_url)

        soup = BeautifulSoup(r.text, 'html.parser')

        number = re.search(r'SCP-\d{3,4}', original_url.upper())
        number = number.group(0) if number else "SCP-???"

        nickname = NICKNAMES.get(number, "Unknown")
        if nickname == "Unknown":
            title_tag = soup.find('title')
            if title_tag:
                page_title = title_tag.get_text(strip=True).replace(" - SCP Foundation", "")
                if ' - ' in page_title:
                    nickname = page_title.split(' - ', 1)[1]

        obj_class = "Unknown"
        for tag in soup.find_all(['strong', 'b']):
            if "Object Class" in tag.text:
                sibling = tag.next_sibling
                if sibling:
                    text = sibling.strip() if isinstance(sibling, str) else sibling.get_text(strip=True)
                    obj_class = text.splitlines()[0].strip() or "Unknown"
                break

        image_url = None
        for img in soup.select('#page-content img'):
            src = img.get('src', '')
            if 'local--files' in src or re.search(r'scp-\d', src.lower()):
                if not src.startswith('http'):
                    src = 'https://scp-wiki.wdfiles.com' + (src if src.startswith('/') else '/' + src)
                image_url = src
                break

        full_desc = f"""#: {number}
• "{nickname}"
• Classification: {obj_class}"""

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{number} - {nickname}</title>
            
            <meta property="og:title" content="{number} - {nickname}">
            <meta property="og:description" content="{full_desc.replace('\n', ' | ')}">
            <meta property="og:url" content="{original_url}">
            <meta property="og:type" content="article">
            <meta name="twitter:card" content="summary_large_image">
            {"<meta property='og:image' content='" + image_url + "'>" if image_url else ""}
            <meta name="theme-color" content="#990000">

            <meta http-equiv="refresh" content="0; url={original_url}">
        </head>
        <body style="font-family:Arial; text-align:center; padding:60px; background:#0f0f0f; color:#ddd;">
            <h2>Redirecting to SCP Wiki...</h2>
            <p><strong>{number} - {nickname}</strong></p>
            <p>If nothing happens, <a href="{original_url}">click here</a>.</p>
        </body>
        </html>
        """
        return html

    except:
        return redirect(original_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
