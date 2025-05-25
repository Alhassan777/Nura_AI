#!/usr/bin/env python3
"""
Simple test to check if Gemini API is working.
"""

import os
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()


def test_gemini_api():
    """Test basic Gemini API functionality."""
    print("🧪 Testing Gemini API...")
    print("-" * 30)

    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print(f"✅ GOOGLE_API_KEY loaded ({len(api_key)} characters)")
    else:
        print("❌ GOOGLE_API_KEY not found!")
        return

    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash")
        model = genai.GenerativeModel(model_name)
        print(f"✅ Gemini model initialized: {model_name}")

        # Simple test
        print("🔄 Testing simple prompt...")
        response = model.generate_content(
            "Hello, please respond with just the word 'success'"
        )
        print(f"✅ Response received: {repr(response.text)}")

        # JSON test
        print("🔄 Testing JSON prompt...")
        json_prompt = (
            'Please respond with valid JSON: {"test": "success", "number": 42}'
        )
        response = model.generate_content(json_prompt)
        print(f"✅ JSON response: {repr(response.text)}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_gemini_api()
