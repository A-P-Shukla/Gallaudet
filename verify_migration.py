import requests
import time
import threading
import uvicorn
from application import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=5001)

def test_endpoints():
    base_url = "http://127.0.0.1:5001"
    
    # Wait for server to start
    time.sleep(5)
    
    print("Testing /predict...")
    try:
        response = requests.post(f"{base_url}/predict")
        print(f"Status: {response.status_code}, Response: {response.json()}")
        assert response.status_code == 200
    except Exception as e:
        print(f"Failed: {e}")

    print("Testing /space...")
    try:
        response = requests.post(f"{base_url}/space")
        print(f"Status: {response.status_code}, Response: {response.json()}")
        assert response.status_code == 200
    except Exception as e:
        print(f"Failed: {e}")

    print("Testing /backspace...")
    try:
        response = requests.post(f"{base_url}/backspace")
        print(f"Status: {response.status_code}, Response: {response.json()}")
        assert response.status_code == 200
    except Exception as e:
        print(f"Failed: {e}")

    print("Testing /clear...")
    try:
        response = requests.post(f"{base_url}/clear")
        print(f"Status: {response.status_code}, Response: {response.json()}")
        assert response.status_code == 200
    except Exception as e:
        print(f"Failed: {e}")

    print("Testing /video_feed...")
    try:
        response = requests.get(f"{base_url}/video_feed", stream=True)
        print(f"Status: {response.status_code}")
        assert response.status_code == 200
        # Read a bit of the stream to ensure it's working
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                print("Received video chunk")
                break
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    # Start server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    test_endpoints()
