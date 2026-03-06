import httpx
import json
import uuid

API_URL = "http://localhost:8000/api/v1/machines/"

def test_machine_registration():
    print("Testing Machine Registration...")
    
    # 1. Register a new machine
    machine_data = {
        "name": f"Machine-{uuid.uuid4().hex[:6]}",
        "location": "Factory Floor A",
        "sensor_type": "Temperature, Pressure",
        "status": "active"
    }
    
    try:
        response = httpx.post(API_URL, json=machine_data)
        print(f"POST /machines status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            machine_id = data["id"]
            print(f"Successfully registered machine with ID: {machine_id}")
            
            # 2. Get the machine
            response = httpx.get(f"{API_URL}{machine_id}")
            print(f"GET /machines/{machine_id} status: {response.status_code}")
            if response.status_code == 200:
                print("Successfully retrieved machine details.")
                
            # 3. List all machines
            response = httpx.get(API_URL)
            print(f"GET /machines status: {response.status_code}")
            if response.status_code == 200:
                machines = response.json()
                print(f"Number of machines in database: {len(machines)}")
                
        else:
            print(f"Failed to register machine: {response.text}")
            
    except Exception as e:
        print(f"Error during verification: {e}")

if __name__ == "__main__":
    test_machine_registration()
