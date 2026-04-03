from flask import Flask, request
import anthropic
import base64
import os
import traceback

app = Flask(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

PROMPT = """
You are an expert in Discrete Structures mathematics.
Analyze this image of a problem.

If you CAN read it:
- Solve it step by step
- Give the final answer clearly
- Keep the response under 100 words
- Be concise because the answer will be spoken aloud

If you CANNOT read it:
- Reply with ONLY: Cannot read image, please retake
"""

def detect_media_type(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return "image/jpeg"

@app.route("/")
def home():
    return "Bot is running!"

@app.route("/solve", methods=["POST"])
def solve():
    try:
        if not ANTHROPIC_API_KEY:
            return "Error: ANTHROPIC_API_KEY is missing", 500

        if "image" not in request.files:
            return "Error: no uploaded file found in field 'image'", 400

        uploaded_file = request.files["image"]
        image_bytes = uploaded_file.read()

        if not image_bytes:
            return "Error: uploaded image file is empty", 400

        media_type = detect_media_type(image_bytes)
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

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