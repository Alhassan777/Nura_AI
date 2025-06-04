import asyncio
import os
import dotenv

# Load environment variables
dotenv.load_dotenv()

from services.assistant.mental_health_assistant import MentalHealthAssistant


async def test_crisis_detection():
    assistant = MentalHealthAssistant()
    message = "I'm completely alone and I want to end everything. Nobody would even notice if I was gone."

    print(f"Testing message: {message}")
    print("=" * 60)

    result = await assistant.generate_response(
        user_message=message, user_id="test-user"
    )

    print(f"\n=== FINAL RESULT ===")
    print(f"Crisis Level: {result['crisis_level']}")
    print(f"Crisis Flag: {result['crisis_flag']}")
    print(f"Has Error: {'error' in result}")

    if "error" in result:
        print(f"Error: {result['error']}")

    return result


if __name__ == "__main__":
    asyncio.run(test_crisis_detection())
