import os
import requests
from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from PIL import Image, ImageOps
from io import BytesIO

app = Flask(__name__)

# Folders setup
HTMLS_FOLDER = os.path.join(os.path.dirname(__file__), 'htmls')
CACHE_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'generated')
os.makedirs(HTMLS_FOLDER, exist_ok=True)
os.makedirs(CACHE_FOLDER, exist_ok=True)

app.config['HTMLS_FOLDER'] = HTMLS_FOLDER

@app.route('/')
def index():
    return "Flask Discord Embed Server is Running!"

# --- Dynamic Image Generation Helpers ---
def process_image(img_url, effect_type):
    try:
        response = requests.get(img_url, timeout=5)
        img = Image.open(BytesIO(response.content)).convert("RGB")
    except Exception:
        # Fallback image if download fails
        img = Image.new("RGB", (300, 300), color=(73, 109, 137))

    if effect_type == 'e':
        # Mild/Standard Variant: Pixelation, Color Inversion, text "38"
        # Pixelate by scaling down and back up using NEAREST
        small = img.resize((img.width // 12, img.height // 12), resample=Image.Resampling.NEAREST)
        img = small.resize(img.size, resample=Image.Resampling.NEAREST)
        
        # Invert colors
        img = ImageOps.invert(img)
        
    elif effect_type == 'x':
        # Worse Variant: Extreme pixelation, heavy deep-fry effect, inverted, text "ON TOP BRO SAID S/E/X TOO"
        small = img.resize((img.width // 24, img.height // 24), resample=Image.Resampling.NEAREST)
        img = small.resize(img.size, resample=Image.Resampling.NEAREST)
        
        # Invert and posterize/enhance contrast
        img = ImageOps.invert(img)
        img = ImageOps.posterize(img, 2)

    # Save processed image to cache
    output_filename = f"processed_{effect_type}_{abs(hash(img_url))}.png"
    output_path = os.path.join(CACHE_FOLDER, output_filename)
    img.save(output_path, "PNG")
    
    return url_for('static', filename=f'generated/{output_filename}', _external=True)

# --- Wildcard Route Handler ---
# Handles any deep paths like /e/klipy.com/gifs/... or /x/htsrh/hstrh/... or ./e/3/ddddddd/...
@app.route('/<path:subpath>')
def catch_all(subpath):
    segments = subpath.strip('/').split('/')
    if not segments:
        return redirect(url_for('index'))
    
    mode = segments[0].lower() # Expecting 'e' or 'x' (or redirects anything else)
    
    if mode == 'e':
        text_overlay = "38"
        template_name = "template_e.html"
        # Extract remaining path as the target asset reference if present
        target_path = "/".join(segments[1:]) if len(segments) > 1 else "default"
        # Construct source image URL (e.g., from klipy or a placeholder)
        img_source = f"https://{target_path}" if "klipy.com" in target_path else "https://media.klipy.com/gifs/sailor-moon-love-15.gif"
        
        processed_image_url = process_image(img_source, 'e')
        
        return render_template(
            template_name, 
            image_url=processed_image_url, 
            overlay_text=text_overlay,
            redirect_url=url_for('discord_replace_via_msg', _external=True)
        )
        
    elif mode == 'x':
        text_overlay = "ON TOP BRO SAID S/E/X TOO"
        template_name = "template_x.html"
        target_path = "/".join(segments[1:]) if len(segments) > 1 else "default"
        img_source = f"https://{target_path}" if "klipy.com" in target_path else "https://media.klipy.com/gifs/sailor-moon-love-15.gif"
        
        processed_image_url = process_image(img_source, 'x')
        
        return render_template(
            template_name, 
            image_url=processed_image_url, 
            overlay_text=text_overlay,
            redirect_url=url_for('discord_replace_via_msg', _external=True)
        )
    else:
        # Fallback / General catch-all redirection to target endpoint
        return redirect(url_for('discord_replace_via_msg'))

@app.route('/discord_replace_via_msg')
def discord_replace_via_msg():
    return render_template('index.html', message="Redirected via Discord substitute mechanism handler.")

# Serve files inside the local 'htmls' folder if requested directly
@app.route('/htmls/<path:filename>')
def serve_html_folder(filename):
    return send_from_directory(app.config['HTMLS_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
