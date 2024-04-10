"""
from openai_service import call_gpt_with_image
from utils import encode_image

def main():
    img_path = "/Users/shridharathinarayanan/vibeify/test.png"
    img = encode_image(img_path)
    print(call_gpt_with_image(img))

if __name__ == "__main__":
    main()
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("routes:app", host="0.0.0.0", port=8000, reload=True)