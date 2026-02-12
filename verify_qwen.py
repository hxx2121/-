
import os
import sys
import django

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_main.settings')
django.setup()

from django_qa.utils.llm import LLMMessage, chat

def verify_qwen():
    print("--- Verifying Qwen (Tongyi Qianwen) Integration ---")
    
    # Check Environment Variable
    api_key = os.environ.get("QWEN_API_KEY")
    print(f"Checking QWEN_API_KEY: {'Found' if api_key else 'Missing (Please set in .env)'}")
    
    if not api_key:
        print("Skipping actual API call because API Key is missing.")
        return

    print("Attempting to create Qwen Client...")
    try:
        print("Sending test message...")
        response = chat([LLMMessage(role="user", content="Hello, write a python hello world function.")])
        
        print("\nResponse from Qwen:")
        print("-" * 20)
        print(response)
        print("-" * 20)
        print("\nSUCCESS: Qwen integration is working!")
        
    except Exception as e:
        print(f"\nERROR: Failed to call Qwen API. Reason: {e}")

if __name__ == "__main__":
    verify_qwen()
