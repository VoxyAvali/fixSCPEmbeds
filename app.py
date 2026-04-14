from flask import Flask, redirect, request
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>FixSCP</h1>
    <p>Simply replace <code>scp-wiki.wikidot.com</code> with this site's URL</p>
    <p>Example: <a href="/scp-173">/scp-173</a></p>
    """

@app.route('/<path:path>')
def fix_scp(path):
    if path.startswith('http'):
        original_url = path
    else:
        match = re.search(r'(\d{3,4})', path)
        if match:
            scp_num = f"scp-{match.group(1).zfill(3)}"
        else:
            scp_num = re.sub(r'[^a-z0-9-]', '', path.lower())
            if not scp_num.startswith('scp-'):
                scp_num = 'scp-' + scp_num.lstrip('scp')
        original_url = f"https://scp-wiki.wikidot.com/{scp_num}"

    try:
        headers = {'User-Agent': 'FixSCP (Discord Embed Fixer)'}
        r = requests.get(original_url, headers=headers, timeout=10)
        
        if r.status_code != 200:
            return redirect(original_url)

        soup = BeautifulSoup(r.text, 'html.parser')

        title_tag = soup.find('title')
        page_title = title_tag.get_text(strip=True) if title_tag else "SCP Foundation"
        if " - SCP Foundation" in page_title:
            page_title = page_title.replace(" - SCP Foundation", "")

        obj_class = "Unknown"
        for strong in soup.find_all(['strong', 'b']):
            if "Object Class" in strong.text:
                sibling = strong.next_sibling
                if sibling:
                    text = sibling.strip() if isinstance(sibling, str) else sibling.get_text(strip=True)
                    obj_class = text.splitlines()[0].strip() or "Unknown"
                break

        image_url = None
        for img in soup.select('#page-content img'):
            src = img.get('src', '')
            if 'local--files' in src:
                if not src.startswith('http'):
                    src = 'https://scp-wiki.wdfiles.com' + src if src.startswith('/') else src
                image_url = src
                break

        if not image_url:
            for img in soup.find_all('img', src=True):
                src = img['src']
                if 'scp-' in src.lower() and ('png' in src or 'jpg' in src or 'jpeg' in src or 'gif' in src):
                    if not src.startswith('http'):
                        src = 'https://scp-wiki.wdfiles.com' + src if src.startswith('/') else src
                    image_url = src
                    break
   
        description = "Anomalous object requiring special containment."
        content = soup.find('div', id='page-content')
        if content:
            for p in content.find_all('p'):
                text = p.get_text(strip=True)
                if len(text) > 50 and not any(x in text.lower() for x in ["item #", "object class", "special containment"]):
                    description = (text[:350] + "...") if len(text) > 350 else text
                    break

        full_desc = f"Object Class: {obj_class}\n\n{description}"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{page_title}</title>
            
            <!-- Discord / Open Graph Meta Tags -->
            <meta property="og:title" content="{page_title}">
            <meta property="og:description" content="{full_desc.replace('"', '&quot;')}">
            <meta property="og:url" content="{original_url}">
            <meta property="og:type" content="article">
            <meta name="twitter:card" content="summary_large_image">
            {"<meta property='og:image' content='" + image_url + "'>" if image_url else ""}
            <meta name="theme-color" content="#990000">

            <!-- Instant Redirect -->
            <meta http-equiv="refresh" content="0; url={original_url}">
        </head>
        <body style="font-family:Arial; text-align:center; padding:50px; background:#111; color:#ddd;">
            <h2>Redirecting to SCP Wiki...</h2>
            <p>{page_title}</p>
            <p>If you are not redirected automatically, <a href="{original_url}" style="color:#44aaff;">click here</a>.</p>
        </body>
        </html>
        """
        return html

    except:
        return redirect(original_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
