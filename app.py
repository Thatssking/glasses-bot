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

@app.route("/")
def home():
    return "Bot is running!"

@app.route("/solve", methods=["POST"])
def solve():
    try:
        if not ANTHROPIC_API_KEY:
            return "Error: ANTHROPIC_API_KEY is missing", 500

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        image_bytes = None

        if "image" in request.files:
            print("Image received from request.files")
            image_bytes = request.files["image"].read()

        elif request.form.get("image"):
            print("Image received from request.form")
            form_value = request.form.get("image")

            try:
                image_bytes = base64.b64decode(form_value)
            except Exception:
                return "Error: image in form was not valid base64", 400

        elif request.data:
            print("Image received from raw request.data")
            image_bytes = request.data

        if not image_bytes:
            return "No image received", 400

        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
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