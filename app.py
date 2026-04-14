from flask import Flask, redirect
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# Optional: Small in-memory cache for titles (grows as people use it)
TITLE_CACHE = {}

@app.route('/')
def home():
    return """
    <h1>fixSCP</h1>
    <p style="font-family:Arial;">Simply replace <code>scp-wiki.wikidot.com</code> with <code>fixscp.onrender.com</code></p>
    <p>Example: <a href="/scp-173">/scp-173</a> or <a href="/SCP-682">/SCP-682</a></p>
    """

@app.route('/<path:path>')
def fix_scp(path):
    # Normalize path
    if path.startswith('http'):
        original_url = path
    else:
        # Clean common variations (scp-173, SCP173, 173, etc.)
        num = re.search(r'(\d{3,4})', path)
        if num:
            scp_num = f"scp-{num.group(1)}"
        else:
            scp_num = re.sub(r'[^a-z0-9-]', '', path.lower())
            if not scp_num.startswith('scp-'):
                scp_num = 'scp-' + scp_num
        original_url = f"https://scp-wiki.wikidot.com/{scp_num}"

    try:
        headers = {'User-Agent': 'fixSCP: SCP Discord Embed Fixer'}
        r = requests.get(original_url, headers=headers, timeout=12)
        
        if r.status_code != 200:
            return redirect(original_url)

        soup = BeautifulSoup(r.text, 'html.parser')

        # --- Title ---
        title_tag = soup.find('title')
        page_title = title_tag.get_text(strip=True) if title_tag else "SCP Foundation Entry"
        
        # Clean title if needed
        if " - SCP Foundation" in page_title:
            page_title = page_title.replace(" - SCP Foundation", "")

        # Cache it
        TITLE_CACHE[original_url] = page_title

        # --- Object Class ---
        obj_class = "Unknown"
        for strong in soup.find_all(['strong', 'b']):
            if any(x in strong.text for x in ["Object Class:", "Object Class :"]):
                sibling = strong.next_sibling
                if sibling:
                    text = sibling.strip() if isinstance(sibling, str) else sibling.get_text(strip=True)
                    obj_class = text.split('\n')[0].strip() or "Unknown"
                break

        # --- Main Image ---
        image_url = None
        for img in soup.find_all('img', src=True):
            src = img['src']
            if 'local--files' in src or 'scp-' in src.lower():
                if not src.startswith('http'):
                    src = 'https://scp-wiki.wikidot.com' + src if src.startswith('/') else src
                image_url = src
                break

        # --- Description ---
        description = "Anomalous object requiring special containment procedures."
        content = soup.find('div', id='page-content')
        if content:
            paragraphs = content.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 40 and not any(skip in text.lower() for skip in ["item #:", "object class:", "special containment"]):
                    description = (text[:380] + "...") if len(text) > 380 else text
                    break

        full_desc = f"Object Class: {obj_class}\n\n{description}"

        # === Final HTML with rich meta tags ===
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{page_title}</title>
            
            <meta property="og:title" content="{page_title}">
            <meta property="og:description" content="{full_desc.replace('"', '&quot;')}">
            <meta property="og:url" content="{original_url}">
            <meta property="og:type" content="article">
            <meta name="twitter:card" content="summary_large_image">
            {"<meta property='og:image' content='" + image_url + "'>" if image_url else ""}
            
            <meta name="theme-color" content="#aa0000">
        </head>
        <body style="font-family: system-ui, Arial; background:#0f0f0f; color:#eee; padding:30px; max-width:800px; margin:auto;">
            <h2>SCP Preview</h2>
            <h1>{page_title}</h1>
            <p><strong>Object Class:</strong> {obj_class}</p>
            <p>{description}</p>
            <hr>
            <p><a href="{original_url}" style="color:#44aaff; font-size:1.1em;">→ Read full entry on the SCP Wiki</a></p>
        </body>
        </html>
        """
        return html

    except Exception:
        return redirect(original_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
