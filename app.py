from flask import Flask, redirect
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>🛠 FixSCP</h1>
    <p>Replace scp-wiki.wikidot.com with this URL</p>
    """

@app.route('/<path:path>')
def fix_scp(path):
    if path.startswith('http'):
        original_url = path
    else:
        match = re.search(r'(\d{3,4})', path)
        scp_num = f"scp-{match.group(1).zfill(3)}" if match else re.sub(r'[^a-z0-9-]', '', path.lower())
        if not scp_num.startswith('scp-'):
            scp_num = 'scp-' + scp_num.lstrip('scp')
        original_url = f"https://scp-wiki.wikidot.com/{scp_num}"

    try:
        headers = {'User-Agent': 'FixSCP Discord Embedder'}
        r = requests.get(original_url, headers=headers, timeout=10)
        if r.status_code != 200:
            return redirect(original_url)

        soup = BeautifulSoup(r.text, 'html.parser')

        # Title & Nickname
        page_title = soup.find('title').get_text(strip=True) if soup.find('title') else "SCP Entry"
        page_title = page_title.replace(" - SCP Foundation", "").strip()

        number_match = re.search(r'(SCP-\d{3,4})', page_title)
        number = number_match.group(1) if number_match else "SCP-???"
        nickname = page_title.replace(number, "").strip(" -") or "Unknown"

        # Object Class
        obj_class = "Unknown"
        for tag in soup.find_all(['strong', 'b']):
            if "Object Class" in tag.text:
                sibling = tag.next_sibling
                if sibling:
                    obj_class = sibling.strip() if isinstance(sibling, str) else sibling.get_text(strip=True)
                    obj_class = obj_class.splitlines()[0].strip() or "Unknown"
                break

        # Image (strongest detection)
        image_url = None
        for img in soup.select('#page-content img'):
            src = img.get('src', '')
            if 'local--files' in src or re.search(r'scp-\d', src.lower()):
                if not src.startswith('http'):
                    src = 'https://scp-wiki.wdfiles.com' + src if src.startswith('/') else src
                image_url = src
                break

        # Clean single-line description for Discord
        full_desc = f"• The number: {number}\n• The nickname: {nickname}\n• The classification: {obj_class}"

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
            <meta property="og:site_name" content="FixSCP">
            <meta name="twitter:card" content="summary_large_image">
            {"<meta property='og:image' content='" + image_url + "'>" if image_url else ""}
            <meta name="theme-color" content="#990000">

            <!-- Instant redirect -->
            <meta http-equiv="refresh" content="0; url={original_url}">
        </head>
        <body style="font-family:Arial; text-align:center; padding:60px; background:#0f0f0f; color:#ddd;">
            <h2>🔄 Redirecting to the SCP Wiki...</h2>
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
