from flask import Flask, request
import anthropic
import base64
import os

app = Flask(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

PROMPT = """
You are an expert in Discrete Structures mathematics.
Analyze this image of a problem.

If you CAN read it:
- Solve it step by step
- Give the final answer clearly
- Keep response under 100 words (it will be spoken aloud)

If you CANNOT read it (blurry, dark, cut off):
- Reply with ONLY: "Cannot read image, please retake"

Be concise. This will be read aloud through speakers.
"""

@app.route("/solve", methods=["POST"])
def solve():
    image_b64 = None
    
    # Try file upload first
    if "image" in request.files:
        image_bytes = request.files["image"].read()
        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    
    # Try base64 in form data
    elif "image" in request.form:
        image_b64 = request.form["image"]
    
    # Try raw body
    elif request.data:
        image_b64 = base64.standard_b64encode(request.data).decode("utf-8")
    
    if not image_b64:
        return "No image received", 400

    try:
        response = claude_client.messages.create(
            model="claude-opus-4-5",
            max_tokens=500,
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
                        {"type": "text", "text": PROMPT}
                    ],
                }
            ],
        )
        return response.content[0].text

    except Exception as e:
    import traceback
    traceback.print_exc()
    return f"Error: {str(e)}", 500