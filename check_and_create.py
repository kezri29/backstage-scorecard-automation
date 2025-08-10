import os
import requests
import sys

SONAR_HOST_URL = os.getenv("SONAR_HOST_URL", "https://sonarcloud.io")
SONAR_TOKEN = os.getenv("SONAR_TOKEN")
SONAR_PROJECT_KEY = os.getenv("SONAR_PROJECT_KEY")
SONAR_ORG = os.getenv("SONAR_ORGANIZATION")

if not SONAR_TOKEN or not SONAR_PROJECT_KEY or not SONAR_ORG:
    print("❌ Missing SONAR_TOKEN, SONAR_PROJECT_KEY, or SONAR_ORGANIZATION environment variables.")
    sys.exit(1)

def project_exists():
    """Check if SonarCloud project exists."""
    url = f"{SONAR_HOST_URL}/api/projects/search?projects={SONAR_PROJECT_KEY}"
    response = requests.get(url, auth=(SONAR_TOKEN, ""))
    if response.status_code != 200:
        print(f"❌ Failed to connect to SonarCloud API: {response.status_code} {response.text}")
        sys.exit(1)

    data = response.json()
    return len(data.get("components", [])) > 0

def create_project():
    """Create project in SonarCloud."""
    url = f"{SONAR_HOST_URL}/api/projects/create"
    payload = {
        "name": SONAR_PROJECT_KEY,
        "project": SONAR_PROJECT_KEY,
        "organization": SONAR_ORG
    }
    response = requests.post(url, data=payload, auth=(SONAR_TOKEN, ""))
    if response.status_code != 200:
        print(f"❌ Failed to create project: {response.status_code} {response.text}")
        sys.exit(1)
    print(f"✅ Project '{SONAR_PROJECT_KEY}' created successfully.")

if __name__ == "__main__":
    print(f"🔍 Checking if project '{SONAR_PROJECT_KEY}' exists on SonarCloud...")
    if project_exists():
        print("✅ Project already exists. Nothing to do.")
    else:
        print("🚀 Project not found. Creating project...")
        create_project()
        print("⏳ Waiting for Automatic Analysis to trigger on next push.")
