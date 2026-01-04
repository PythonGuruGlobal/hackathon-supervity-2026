import requests
import json
import sys

def test_prediction():
    url = "http://127.0.0.1:8000/predict"
    
    # Test case 1: Common symptoms (Should rely on ML - High Confidence)
    payload_ml = {
        "symptoms": ["chills", "vomiting", "high_fever"] 
    }
    
    # Test case 2: Vague/Complex symptoms (Should trigger RAG - Low Confidence/Augmented)
    # Note: Whether it triggers RAG depends on model confidence, but let's test the endpoint mechanics
    payload_rag = {
        "symptoms": ["strange rash", "fatigue", "unexplained pain"]
    }

    print("--- Testing ML Path ---")
    try:
        response = requests.post(url, json=payload_ml)
        if response.status_code == 200:
            print("Status: 200 OK")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- Testing RAG/Complex Path ---")
    try:
        response = requests.post(url, json=payload_rag)
        if response.status_code == 200:
            print("Status: 200 OK")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_prediction()
