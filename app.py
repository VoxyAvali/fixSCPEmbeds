from flask import Flask, request, redirect, render_template_string
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# Simple homepage
HOME_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>FixSCP: (hopefully) better SCP Wiki Embeds</title>
    <meta property="og:title" content="FixSCP">
    <meta property="og:description" content="trying to make SCP wiki links better in Discord and such">
</head>
<body style="font-family:Arial; text-align:center; padding:50px;">
    <h1>FixSCP</h1>
    <p>Just replace <code>scp-wiki.wikidot.com</code> with <code>https://fixscp.onrender.com</code></p>
    <p>Example: <a href="/scp-173">fixscp.onrender.com/scp-173</a></p>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HOME_HTML)

@app.route('/<path:path>')
def fix_scp(path):
    # Redirect full URLs or handle SCP numbers
    if path.startswith('http'):
        url = path
    else:
        url = f"https://scp-wiki.wikidot.com/{path}"
    
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return "Could not fetch SCP page", 400
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Basic extraction
        title = soup.find('title').text.strip() if soup.find('title') else "SCP Entry"
        description = "SCP Foundation entry. Check the full page for details."
        
        # Try to get first paragraph
        content = soup.find('div', id='page-content')
        if content:
            p = content.find('p')
            if p:
                description = p.text.strip()[:400] + "..." if len(p.text) > 400 else p.text.strip()
        
        # Very basic HTML with good meta tags for Discord
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta property="og:title" content="{title}">
            <meta property="og:description" content="{description}">
            <meta property="og:url" content="{url}">
            <meta name="twitter:card" content="summary_large_image">
        </head>
        <body>
            <h1>Redirecting to original SCP...</h1>
            <p><a href="{url}">Open original page</a></p>
        </body>
        </html>
        """
        return html
    except:
        return redirect(f"https://scp-wiki.wikidot.com/{path}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
