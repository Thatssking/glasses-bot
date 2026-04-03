from flask import Flask, request
import anthropic
import base64
import os
import traceback

app = Flask(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

PROMPT = """
You are a highly capable problem-solving AI (like ChatGPT).

Look at the image and identify ALL problems (math, discrete structures, word problems, diagrams, etc).

Rules:
- Focus ONLY on actual problems/questions
- Ignore UI elements, backgrounds, or irrelevant text
- Do NOT describe the image

For EACH problem:
1. Understand it
2. Solve it correctly
3. Give a VERY SHORT answer

Output style:
- If it's simple math → just give the answer
- If it's multiple choice → say the correct letter + answer
- If it's conceptual (discrete math, logic, sets, graphs, etc) → give a SHORT final answer (no long explanation)

Format:
1: answer
2: answer
3: answer

Keep everything concise and natural for speech.
Do NOT explain unless absolutely necessary.
"""

def detect_media_type(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return "image/jpeg"

def decode_base64_loose(data: str) -> bytes:
    data = data.strip()
    if data.startswith("data:"):
        data = data.split(",", 1)[1]
    data = data.replace("\n", "").replace("\r", "").replace(" ", "")
    missing_padding = len(data) % 4
    if missing_padding:
        data += "=" * (4 - missing_padding)
    return base64.b64decode(data)

@app.route("/")
def home():
    return "Bot is running!"

@app.route("/solve", methods=["POST"])
def solve():
    try:
        if not ANTHROPIC_API_KEY:
            return "Error: ANTHROPIC_API_KEY is missing", 500

        image_bytes = None

        if "image" in request.files:
            print("Image received from request.files")
            image_bytes = request.files["image"].read()

        elif request.form.get("image"):
            print("Image received from request.form")
            form_value = request.form.get("image")

            try:
                image_bytes = decode_base64_loose(form_value)
                print("Decoded request.form as base64")
            except Exception:
                print("request.form was not base64, using raw text bytes")
                image_bytes = form_value.encode("utf-8")

        elif request.data:
            print("Image received from raw request.data")
            image_bytes = request.data

        if not image_bytes:
            return "Error: no image received", 400

        media_type = detect_media_type(image_bytes)
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        print(f"Detected media type: {media_type}")
        print("Calling Anthropic")

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": PROMPT,
                        },
                    ],
                }
            ],
        )

        if not response.content:
            return "Error: empty response from Anthropic", 500

        return response.content[0].text

    except Exception as e:
        traceback.print_exc()
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)