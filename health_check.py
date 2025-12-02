import requests
import subprocess
import sys

def check_docker():
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        print("Docker PS Output:")
        print(result.stdout)
        print(result.stderr)
        if result.returncode != 0:
            return False
        return True
    except Exception as e:
        print(f"Docker check failed: {e}")
        return False

def check_service(url, name):
    try:
        response = requests.get(url, timeout=2)
        print(f"{name}: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"{name}: Failed - {e}")
        return False

if __name__ == "__main__":
    with open("health_check_output.txt", "w") as f:
        f.write("Checking Docker...\n")
        if check_docker():
            f.write("\nChecking Services...\n")
            s1 = check_service("http://localhost:3001/panel", "Data Ingestion")
            s2 = check_service("http://localhost:3002/panel", "Monitoring")
            
            if s1 and s2:
                f.write("\nSUCCESS: All services are running.\n")
            else:
                f.write("\nFAILURE: Some services are down.\n")
        else:
            f.write("\nFAILURE: Docker is not running or accessible.\n")
