from PIL import Image, ImageFont, ImageDraw, ImageSequence
import requests
import random
import math
import web
import io
import re

# Route mapping: root redirects, aplle-ub handles direct URLs, default handles view/vixw klipy links
urls = (
    '/', 'RedirectToBonzi',
    '/aplle-ub/(.*)', 'AppleUbHandler',
    '(.+)', 'SexHack'
)

app = web.application(urls, globals())
web.config.debug = False
host = "127.0.0.1"
port = 8000

# Load default image into memory from file
try:
    with open("img/sex_default.png", "rb") as f:
        default_img = f.read()
except Exception:
    default_img = None

# User-Agent headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}


class RedirectToBonzi:
    def GET(self):
        raise web.seeother('https://bonziworld.kr')


class AppleUbHandler:
    def GET(self, target_path):
        """Handle /aplle-ub/ path for direct image and video URLs"""
        web.header('Cache-Control', 'public, max-age=86400')
        
        full_path = web.ctx.env.get('REQUEST_URI', '')
        if '/aplle-ub/' in full_path:
            target_url = full_path.split('/aplle-ub/', 1)[1]
        else:
            target_url = target_path

        if target_url and not target_url.startswith('http'):
            target_url = 'https://' + target_url

        if not target_url:
            print("AppleUbHandler: No target URL provided.")
            web.header('Content-type', 'image/png')
            return SexHack.default_response()

        print(f"Fetching media from URL: {target_url}")
        is_video = any(target_url.lower().split('?')[0].endswith(ext) for ext in ['.mp4', '.webm', '.mov', '.avi', '.m4v'])
        
        if is_video:
            web.header('Content-type', 'video/mp4')
            result = self.process_video(target_url)
        else:
            web.header('Content-type', 'image/gif')
            result = self.process_media(target_url)

        if result:
            return result
        
        print("AppleUbHandler: Processing failed, returning default.")
        web.header('Content-type', 'image/png')
        return SexHack.default_response()

    def process_media(self, url):
        """Process direct image/GIF URL with sine-wave flashing and ubscene.gif end"""
        try:
            r = requests.get(url, headers=headers, stream=True, timeout=10)
            r.raise_for_status()
            img_data = io.BytesIO(r.content)
            
            try:
                og_media = Image.open(img_data)
            except Exception as e:
                print(f"PIL failed to open image from URL {url}: {e}")
                return None

            frames = []
            width, height = 350, 185

            media_frames = []
            try:
                for frame in ImageSequence.Iterator(og_media):
                    media_frames.append(frame.convert("RGBA").resize((width, height)))
            except Exception:
                media_frames = [og_media.convert("RGBA").resize((width, height))]

            interrupt_idx = len(media_frames) // 2
            if interrupt_idx < 1:
                interrupt_idx = 1

            # Phase 1A: Play first half normally
            for idx in range(interrupt_idx):
                base_img = media_frames[idx]
                canvas = Image.new("RGBA", (width, height), (255, 255, 255, 255))
                canvas.paste(base_img, (0, 0), base_img)
                frames.append(canvas)

            # Phase 1B: Spin/interrupt final frame up to 90 degrees
            spin_steps = 10
            last_half_frame = media_frames[interrupt_idx - 1]
            for idx in range(spin_steps):
                angle = (idx / max(1, spin_steps - 1)) * (math.pi / 2)
                cos_a = max(0.02, math.cos(angle))
                sin_a = math.sin(angle)

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

            # Phase 2: Color flashing with random sine wave distortions per frame
            try:
                font = ImageFont.truetype("impact.ttf", 18)
            except IOError:
                font = ImageFont.load_default()

            message = "Fuck you,\nget Ub Ored,\nUB ORE UB PEAK!\n#UbOre #UbPeak"

            for i in range(100):
                bg_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255)
                text_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255)

                slide = Image.new("RGBA", (width, height), bg_color)
                draw = ImageDraw.Draw(slide)
                draw.multiline_text((width / 2, height / 2), message, fill=text_color, font=font, anchor="mm", align="center")
                
                # Apply random sine wave distortion effect across columns
                px = slide.load()
                amp = random.randint(2, 6)
                freq = random.uniform(0.05, 0.2)
                phase = i * 0.5
                
                temp_img = slide.copy()
                tpx = temp_img.load()
                for y in range(height):
                    shift = int(math.sin(y * freq + phase) * amp)
                    for x in range(width):
                        src_x = (x + shift) % width
                        px[x, y] = tpx[src_x, y]

                frames.append(slide)

            # Phase 3: End on img/ubscene.gif
            try:
                with open("img/ubscene.gif", "rb") as f:
                    ub_raw = f.read()
                ub_gif = Image.open(io.BytesIO(ub_raw))
                for frame in ImageSequence.Iterator(ub_gif):
                    frames.append(frame.convert("RGBA").resize((width, height)))
            except Exception as e:
                print(f"Could not load img/ubscene.gif: {e}")

            out = io.BytesIO()
            frames[0].save(
                out,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=40,
                optimize=True
            )
            return out.getvalue()
        except Exception as e:
            print(f"Error processing media URL {url}: {e}")
            return None

    def process_video(self, url):
        """Process direct video URL for aplle-ub, returning ubscene.mp4 bytes"""
        try:
            with open("img/ubscene.mp4", "rb") as f:
                ub_video = f.read()
            return ub_video
        except Exception as e:
            print(f"Could not load img/ubscene.mp4: {e}")
            try:
                r = requests.get(url, headers=headers, stream=True, timeout=10)
                r.raise_for_status()
                return r.content
            except Exception as ex:
                print(f"Failed to fallback download video: {ex}")
                return None


class SexHack:
    @staticmethod
    def default_response():
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
        try:
            parts = name.split('/')
            query = parts[-1] if len(parts) > 1 else name
            
            url = f"https://klipy.com/gif/{query}"
            r = requests.get(url, headers=headers, timeout=5)
            r.raise_for_status()
            
            img_url = None
            for pattern in [
                r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
                r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']'
            ]:
                match = re.search(pattern, r.text)
                if match:
                    img_url = match.group(1)
                    break
            
            if not img_url:
                print("Klipy image URL not found.")
                return None

            img_raw = requests.get(img_url, stream=True, headers=headers, timeout=5).raw
            og_gif = Image.open(img_raw)

            gif_frames = []
            try:
                for frame in ImageSequence.Iterator(og_gif):
                    gif_frames.append(frame.convert("RGBA").resize((350, 185)))
            except Exception:
                gif_frames = [og_gif.convert("RGBA").resize((350, 185))]

            width, height = 350, 185
            frames = []

            interrupt_idx = len(gif_frames) // 2
            if interrupt_idx < 1:
                interrupt_idx = 1

            for idx in range(interrupt_idx):
                base_img = gif_frames[idx]
                canvas = Image.new("RGBA", (width, height), (255, 255, 255, 255))
                canvas.paste(base_img, (0, 0), base_img)
                frames.append(canvas)

            spin_steps = 10
            last_half_frame = gif_frames[interrupt_idx - 1]
            for idx in range(spin_steps):
                angle = (idx / max(1, spin_steps - 1)) * (math.pi / 2)
                cos_a = max(0.02, math.cos(angle))
                sin_a = math.sin(angle)

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

            try:
                with open("img/ubscene.gif", "rb") as f:
                    ub_raw = f.read()
                ub_gif = Image.open(io.BytesIO(ub_raw))
                for frame in ImageSequence.Iterator(ub_gif):
                    frames.append(frame.convert("RGBA").resize((width, height)))
            except Exception:
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
            print(f"Error generating spinning GIF from Klipy: {e}")
            return None

    def handle_request(self, name):
        try:
            web.header('Cache-Control', 'public, max-age=86400')
            if re.search(r'^/?vi[ex]w/[A-Za-z0-9_-]*$', name):
                return self.generate_spinning_gif(name)
        except Exception as e:
            print(f"Handle request error: {e}")

    def GET(self, name):
        user_agent = web.ctx.env.get('HTTP_USER_AGENT', '')
        if 'Discordbot' in user_agent:
            web.header('Content-type', 'image/png')
            return self.default_response()

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
