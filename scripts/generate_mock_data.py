import asyncio
import httpx
import random
import uuid
import logging
from datetime import datetime, timezone, timedelta

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
NUM_MACHINES = 10
DATA_POINTS_PER_MACHINE = 100
BATCH_SIZE = 50

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Predefined machine configurations to ensure stability
MOCK_MACHINES = [
    {"name": f"Machine-{i+1:02d}", "location": f"Zone-{random.randint(1, 5)}", "sensor_type": "industrial-sensor"}
    for i in range(NUM_MACHINES)
]

def generate_sensor_data(machine_id: str, timestamp: datetime) -> dict:
    """Generate a single mock sensor data point."""
    return {
        "machine_id": machine_id,
        "timestamp": timestamp.isoformat(),
        "metrics": {
            "temperature": round(random.uniform(20.0, 90.0), 2),
            "pressure": round(random.uniform(1.0, 15.0), 2),
            "speed": round(random.uniform(500.0, 3000.0), 2)
        }
    }

async def ensure_machine_exists(client: httpx.AsyncClient, machine_cfg: dict) -> str:
    """Check if a machine exists by name; register if not. Returns the machine ID."""
    try:
        # List all machines to find by name
        response = await client.get(f"{API_BASE_URL}/machines/")
        response.raise_for_status()
        machines = response.json()
        
        for m in machines:
            if m["name"] == machine_cfg["name"]:
                logger.info(f"Machine '{machine_cfg['name']}' already registered with ID: {m['id']}")
                return m["id"]
        
        # If not found, register it
        logger.info(f"Registering new machine: {machine_cfg['name']}")
        register_response = await client.post(f"{API_BASE_URL}/machines/", json=machine_cfg)
        register_response.raise_for_status()
        new_machine = register_response.json()
        logger.info(f"Successfully registered machine '{machine_cfg['name']}' with ID: {new_machine['id']}")
        return new_machine["id"]
        
    except Exception as e:
        logger.error(f"Error ensuring machine exists: {str(e)}")
        raise e

async def send_batch(client: httpx.AsyncClient, batch: list) -> bool:
    """Send a batch of sensor data to the API."""
    payload = {
        "gateway_id": f"mock-gateway-{random.randint(1, 5)}",
        "payloads": batch
    }
    
    try:
        response = await client.post(f"{API_BASE_URL}/data/ingest", json=payload)
        response.raise_for_status()
        logger.info(f"Successfully sent batch of {len(batch)} records. Status: {response.status_code}")
        return True
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False

async def main():
    logger.info(f"Starting mock data generation script.")
    
    async with httpx.AsyncClient() as client:
        # Step 1: Ensure all machines are registered and get their IDs
        logger.info("Step 1: Synchronizing machine metadata with PostgreSQL...")
        machine_ids = []
        for cfg in MOCK_MACHINES:
            m_id = await ensure_machine_exists(client, cfg)
            machine_ids.append(m_id)
            
        logger.info(f"Step 2: Generating and sending sensor data...")
        logger.info(f"Targeting {DATA_POINTS_PER_MACHINE} points per machine. Total: {len(machine_ids) * DATA_POINTS_PER_MACHINE} records.")
        
        # Generate base time and go back in time so we have historical data
        base_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        all_payloads = []
        
        for machine_id in machine_ids:
            # Generate data points chronologically for each machine
            for i in range(DATA_POINTS_PER_MACHINE):
                # Space data points by 5 minutes
                point_time = base_time + timedelta(minutes=5 * i)
                all_payloads.append(generate_sensor_data(machine_id, point_time))
                
        # Shuffle payloads to simulate real-world arrival out-of-order within batches
        random.shuffle(all_payloads)
        
        # Group into batches and send
        batches = [all_payloads[i:i + BATCH_SIZE] for i in range(0, len(all_payloads), BATCH_SIZE)]
        
        tasks = [send_batch(client, batch) for batch in batches]
        
        # Use asyncio.gather to send batches concurrently
        results = await asyncio.gather(*tasks)
        
        success_count = sum(1 for r in results if r)
        logger.info(f"Completed! Successfully sent {success_count} out of {len(batches)} batches.")

    # Print out machine IDs so user can test retrieval
    print("\n--- Mock Generation Complete ---")
    print("Use one of these Machine IDs to test the GET retrieval endpoint:")
    for m in machine_ids[:3]:
        print(f" - {m}")
    print("\nExample Retrieval Query Parameters:")
    print(f"start_time: {base_time.isoformat()}")
    print(f"end_time: {(base_time + timedelta(hours=24)).isoformat()}")
    
if __name__ == "__main__":
    asyncio.run(main())
