from PIL import Image, ImageFont, ImageDraw, ImageSequence
import requests
import random
import math
import web
import io
import re
import os

# Route mapping: root redirects to bonziworld.kr, everything else goes to SexHack
urls = (
    '/', 'RedirectToBonzi',
    '(.+)', 'SexHack'
)

app = web.application(urls, globals())
web.config.debug = False
host = "127.0.0.1"
port = int(os.environ.get("PORT", 10000))

# Load default image into memory from file
try:
    with open("img/sex_default.png", "rb") as f:
        default_img = f.read()
except Exception:
    default_img = None

# User-Agent for Tenor requests
headers = {
    'User-Agent': 'A Discord Bot by an unknown person using github.com/rebane2001/txnor-server',
}


class RedirectToBonzi:
    def GET(self):
        raise web.seeother('https://bonziworld.kr')


class SexHack:
    @staticmethod
    def default_response():
        """Return default image from file if available, otherwise generate programmatically"""
        if default_img:
            return default_img
        img = Image.new("RGBA", (350, 185), (220, 220, 220, 255))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("impact.ttf", 28)
        except IOError:
            font = ImageFont.load_default()
        draw.text((350 / 2, 185 / 2), "DEFAULT", fill=(80, 80, 80), font=font, anchor="mm")
        
        out = io.BytesIO()
        img.save(out, "PNG")
        return out.getvalue()

    @staticmethod
    def generate_spinning_gif(name):
        """Play first half of Tenor GIF, spin/interrupt halfway, flash colors with text, and end on ubscene.gif"""
        try:
            parts = name.split('/')
            query = parts[-1] if len(parts) > 1 else name
            
            url = f"https://tenor.com/view/{query}"
            r = requests.get(url, headers=headers, timeout=5)
            
            img_url = None
            for pattern in [
                r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
                r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
                r'<meta class="dynamic" name="twitter:image" content="([^"]+)">'
            ]:
                match = re.search(pattern, r.text)
                if match:
                    img_url = match.group(1)
                    break
            
            if not img_url:
                print(f"Tenor image URL not found for query: {query}")
                return None

            img_url = img_url.replace("AAC/", "AAe/")
            img_raw = requests.get(img_url, stream=True, headers=headers, timeout=5).raw

            og_gif = Image.open(img_raw)

            # Extract frames from the animated Tenor GIF
            gif_frames = []
            try:
                for frame in ImageSequence.Iterator(og_gif):
                    gif_frames.append(frame.convert("RGBA").resize((350, 185)))
            except Exception:
                gif_frames = [og_gif.convert("RGBA").resize((350, 185))]

            width, height = 350, 185
            frames = []

            # Interrupt halfway through the GIF frames
            interrupt_idx = len(gif_frames) // 2
            if interrupt_idx < 1:
                interrupt_idx = 1

            # Phase 1A: Play the first half of the Tenor GIF normally
            for idx in range(interrupt_idx):
                base_img = gif_frames[idx]
                canvas = Image.new("RGBA", (width, height), (255, 255, 255, 255))
                canvas.paste(base_img, (0, 0), base_img)
                frames.append(canvas)

            # Phase 1B: Spin/interrupt the final frame of that first half up to 90 degrees
            spin_steps = 10
            last_half_frame = gif_frames[interrupt_idx - 1]
            for idx in range(spin_steps):
                angle = (idx / max(1, spin_steps - 1)) * (math.pi / 2)
                
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)
                if cos_a < 0.02:
                    cos_a = 0.02

                cx, cy = width / 2, height / 2
                hw = (width / 2) * cos_a
                v_skew = sin_a * 25

                quad = (
                    cx - hw, v_skew,
                    cx - hw, height - v_skew,
                    cx + hw, height + v_skew,
                    cx + hw, -v_skew
                )

                canvas = Image.new("RGBA", (width, height), (255, 255, 255, 255))
                transformed = last_half_frame.transform((width, height), Image.QUAD, quad, Image.BICUBIC)
                canvas.paste(transformed, (0, 0), transformed)
                frames.append(canvas)

            # Phase 2: Flash colors and text for 100 frames
            try:
                font = ImageFont.truetype("impact.ttf", 18)
            except IOError:
                font = ImageFont.load_default()

            message = "Fuck you,\nget Ub Ored,\nUB ORE UB PEAK!\n#UbOre #UbPeak"

            for _ in range(100):
                bg_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255)
                text_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255)

                flash_slide = Image.new("RGBA", (width, height), bg_color)
                draw = ImageDraw.Draw(flash_slide)
                draw.multiline_text((width / 2, height / 2), message, fill=text_color, font=font, anchor="mm", align="center")
                frames.append(flash_slide)

            # Phase 3: Switch to img/ubscene.gif and end there
            try:
                with open("img/ubscene.gif", "rb") as f:
                    ub_raw = f.read()
                ub_gif = Image.open(io.BytesIO(ub_raw))
                for frame in ImageSequence.Iterator(ub_gif):
                    frames.append(frame.convert("RGBA").resize((width, height)))
            except Exception as e:
                print(f"Could not load img/ubscene.gif: {e}")
                final_slide = Image.new("RGBA", (width, height), (255, 255, 255, 255))
                draw = ImageDraw.Draw(final_slide)
                draw.multiline_text((width / 2, height / 2), message, fill=(0, 0, 0), font=font, anchor="mm", align="center")
                frames.append(final_slide)

            out = io.BytesIO()
            frames[0].save(
                out,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=40,
                optimize=True
            )
            web.header('Content-type', 'image/gif')
            return out.getvalue()
        except Exception as e:
            print(f"Error generating spinning GIF: {e}")
            return None

    def handle_request(self, name):
        try:
            web.header('Cache-Control', 'public, max-age=86400')

            if re.search(r'^/?vi[ex]w/[A-Za-z0-9_-]*$', name):
                return self.generate_spinning_gif(name)

        except Exception as e:
            print(f"Handle request error: {e}")

    def GET(self, name):
        """Handle a request"""
        web.header('Content-type', 'image/png')
        filtered_name = re.sub(r'[^\.\/A-Za-z0-9_-]+', '', name)
        filtered_name = re.sub(r'^/?xn-../view', '/vixw', filtered_name)
        filtered_name = re.sub(r'^/?([A-Za-z-]*/)?vi', '/vi', filtered_name)
        
        response = self.handle_request(filtered_name)
        if response:
            return response
        return self.default_response()


if __name__ == "__main__":
    web.httpserver.runsimple(app.wsgifunc(), (host, port))
