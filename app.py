from flask import Flask, request, redirect
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>🛠 FixSCP</h1>
    <p>Replace <code>scp-wiki.wikidot.com</code> with <code>fixscp.onrender.com</code></p>
    <p>Example: <a href="/scp-173">/scp-173</a></p>
    """

@app.route('/<path:path>')
def fix_scp(path):
    # Clean the path
    if path.startswith('http'):
        original_url = path
    else:
        # Handle both scp-173 and scp/173
        clean_path = re.sub(r'^/?(scp-?|item-?)', 'scp-', path.lower())
        original_url = f"https://scp-wiki.wikidot.com/{clean_path}"

    try:
        headers = {'User-Agent': 'FixSCP-Bot[](https://github.com/yourname/fixscp)'}
        r = requests.get(original_url, headers=headers, timeout=15)
        
        if r.status_code != 200:
            return redirect(original_url)

        soup = BeautifulSoup(r.text, 'html.parser')

        # === Extract data ===
        title_tag = soup.find('title')
        page_title = title_tag.get_text(strip=True) if title_tag else "SCP Foundation"

        # Object Class
        obj_class = "Unknown"
        for strong in soup.find_all('strong'):
            if "Object Class:" in strong.text or "Object Class :" in strong.text:
                obj_class = strong.next_sibling.get_text(strip=True) if strong.next_sibling else "Unknown"
                break

        # Main image (most SCPs have one)
        image = None
        img_tag = soup.find('img', src=re.compile(r'local--files'))
        if img_tag and 'src' in img_tag.attrs:
            image = "https://scp-wiki.wikidot.com" + img_tag['src']

        # Short description (first real paragraph)
        description = "Anomalous object requiring special containment."
        content = soup.find('div', id='page-content')
        if content:
            paragraphs = content.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 30 and not text.startswith("Item #:"):
                    description = text[:380] + "..." if len(text) > 380 else text
                    break

        full_description = f"Object Class: {obj_class}\n\n{description}"

        # === Rich HTML with perfect meta tags for Discord ===
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{page_title}</title>
            
            <!-- Open Graph / Discord -->
            <meta property="og:title" content="{page_title}">
            <meta property="og:description" content="{full_description.replace('"', '&quot;')}">
            <meta property="og:url" content="{original_url}">
            <meta property="og:type" content="article">
            <meta name="twitter:card" content="summary_large_image">
            
            <!-- Image -->
            {"<meta property='og:image' content='" + image + "'>" if image else ""}
            
            <!-- Nice color based on class -->
            <meta name="theme-color" content="#ff4444">
        </head>
        <body style="font-family:Arial; padding:20px; background:#111; color:#ddd;">
            <h2>🔗 FixSCP Preview</h2>
            <p><strong>{page_title}</strong></p>
            <p><strong>Object Class:</strong> {obj_class}</p>
            <p>{description}</p>
            <hr>
            <p><a href="{original_url}" style="color:#00bbff;">→ View full entry on SCP Wiki</a></p>
        </body>
        </html>
        """
        return html

    except Exception as e:
        return redirect(original_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
