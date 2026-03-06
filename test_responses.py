import requests
import json
import uuid
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_success_response():
    print("\n--- Testing Success Response (List Machines) ---")
    try:
        response = requests.get(f"{BASE_URL}/machines/")
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

def test_validation_error():
    print("\n--- Testing Validation Error (Empty Ingest) ---")
    try:
        response = requests.post(f"{BASE_URL}/data/ingest", json={})
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

def test_not_found_error():
    print("\n--- Testing Not Found Error (Get Machine) ---")
    random_id = str(uuid.uuid4())
    try:
        response = requests.get(f"{BASE_URL}/machines/{random_id}")
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Give uvicorn a moment to reload if needed
    time.sleep(1)
    test_success_response()
    test_validation_error()
    test_not_found_error()
