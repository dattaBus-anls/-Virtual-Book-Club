# Quick test for Ollama with longer timeout
# Save as quick_ollama_test.py

import requests
import time

def test_ollama_connection():
    print("Testing Ollama connection with longer timeout...")
    
    try:
        # Test with longer timeout
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "tinyllama",
                "prompt": "Hello",
                "stream": False
            },
            timeout=30  # Longer timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Ollama is working!")
            print(f"Response: {result.get('response', 'No response')[:100]}...")
            return True
        else:
            print(f"❌ Ollama returned status: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Ollama is still timing out (even with 30s timeout)")
        print("Try restarting Ollama service")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama")
        print("Make sure 'ollama serve' is running")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_ollama_connection()