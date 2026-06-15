import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

def analyze_news(news):
    prompt = f"""
    Create an Instagram post:
    Title: {news['title']}
    Description: {news.get('description','')}

    Return:
    - Short catchy headline
    - 2 line caption
    - 5 hashtags
    """

    response = model.generate_content(prompt)
    return response.text
