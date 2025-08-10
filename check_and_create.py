import os
import requests
import sys

# --- Environment Variables ---
SONAR_HOST_URL = os.getenv("SONAR_HOST_URL", "https://sonarcloud.io")
SONAR_TOKEN = os.getenv("SONAR_TOKEN")
SONAR_PROJECT_KEY = os.getenv("SONAR_PROJECT_KEY")
SONAR_ORG = os.getenv("SONAR_ORG")
SONAR_PROJECT_NAME = os.getenv("SONAR_PROJECT_NAME")

if not all([SONAR_TOKEN, SONAR_PROJECT_KEY, SONAR_ORG, SONAR_PROJECT_NAME]):
    print("❌ Missing required environment variables.")
    sys.exit(1)

def sonar_api(method, endpoint, **kwargs):
    """Helper to call SonarCloud API."""
    url = f"{SONAR_HOST_URL}{endpoint}"
    resp = requests.request(method, url, auth=(SONAR_TOKEN, ""), **kwargs)
    if resp.status_code not in (200, 201, 204):
        print(f"❌ API call failed [{resp.status_code}]: {resp.text}")
        sys.exit(1)
    return resp

def project_exists():
    """Check if SonarCloud project already exists."""
    resp = sonar_api("GET", "/api/projects/search", params={
        "projects": SONAR_PROJECT_KEY,
        "organization": SONAR_ORG
    })
    return len(resp.json().get("components", [])) > 0

def create_project():
    """Create SonarCloud project."""
    payload = {
        "name": SONAR_PROJECT_NAME,
        "project": SONAR_PROJECT_KEY,
        "organization": SONAR_ORG
    }
    sonar_api("POST", "/api/projects/create", data=payload)
    print(f"✅ Project '{SONAR_PROJECT_KEY}' created successfully.")

def create_sonar_properties():
    """Create sonar-project.properties file."""
    properties_content = f"""sonar.projectKey={SONAR_PROJECT_KEY}
                            sonar.organization={SONAR_ORG}
                            
                            # This is the name and version displayed in the SonarCloud UI.
                            #sonar.projectName={SONAR_PROJECT_NAME}
                            #sonar.projectVersion=1.0
                            
                            # Path is relative to the sonar-project.properties file. Replace "\\" by "/" on Windows.
                            sonar.sources=src/
                            
                            # Encoding of the source code. Default is default system encoding
                            #sonar.sourceEncoding=UTF-8
                            """
    
    # Write to the repository root (go back from backstage-scorecard-automation to repo root)
    properties_path = "../sonar-project.properties"
    with open(properties_path, 'w') as f:
        f.write(properties_content)
    print(f"✅ Created sonar-project.properties file.")

if __name__ == "__main__":
    print(f"🔍 Checking if project '{SONAR_PROJECT_KEY}' exists...")
    
    if project_exists():
        print("✅ Project already exists.")
    else:
        print("🚀 Project not found. Creating project...")
        create_project()
    
    print("📝 Creating sonar-project.properties file...")
    create_sonar_properties()
    
    print("✅ Project created successfully.")
    print("ℹ️  Project will be linked to GitHub through CI-based analysis.")
    print("📋 Note: For automatic analysis features, import your GitHub org in SonarCloud manually.")

# import os
# import requests
# import sys

# # --- Environment Variables ---
# SONAR_HOST_URL = os.getenv("SONAR_HOST_URL", "https://sonarcloud.io")
# SONAR_TOKEN = os.getenv("SONAR_TOKEN")
# SONAR_PROJECT_KEY = os.getenv("SONAR_PROJECT_KEY")
# SONAR_ORG = os.getenv("SONAR_ORG")
# SONAR_PROJECT_NAME = os.getenv("SONAR_PROJECT_NAME")

# if not all([SONAR_TOKEN, SONAR_PROJECT_KEY, SONAR_ORG, SONAR_PROJECT_NAME]):
#     print("❌ Missing required environment variables.")
#     sys.exit(1)

# def sonar_api(method, endpoint, **kwargs):
#     """Helper to call SonarCloud API."""
#     url = f"{SONAR_HOST_URL}{endpoint}"
#     resp = requests.request(method, url, auth=(SONAR_TOKEN, ""), **kwargs)
#     if resp.status_code not in (200, 201, 204):
#         print(f"❌ API call failed [{resp.status_code}]: {resp.text}")
#         sys.exit(1)
#     return resp

# def project_exists():
#     """Check if SonarCloud project already exists."""
#     resp = sonar_api("GET", "/api/projects/search", params={
#         "projects": SONAR_PROJECT_KEY,
#         "organization": SONAR_ORG
#     })
#     return len(resp.json().get("components", [])) > 0

# def create_project():
#     """Create SonarCloud project."""
#     payload = {
#         "name": SONAR_PROJECT_NAME,
#         "project": SONAR_PROJECT_KEY,
#         "organization": SONAR_ORG
#     }
#     sonar_api("POST", "/api/projects/create", data=payload)
#     print(f"✅ Project '{SONAR_PROJECT_KEY}' created successfully.")

# def bind_to_github():
#     """Bind the project to GitHub repository."""
#     payload = {
#         "organization": SONAR_ORG,
#         "projectKey": SONAR_PROJECT_KEY,
#         "repository": SONAR_PROJECT_NAME,
#         "almSetting": "github"
#     }
#     try:
#         sonar_api("POST", "/api/alm_settings/set_github_binding", data=payload)
#         print(f"✅ Project bound to GitHub repository '{SONAR_PROJECT_NAME}'.")
#     except SystemExit:
#         print(f"⚠️  Could not bind to GitHub. This might require manual setup in SonarCloud.")

# if __name__ == "__main__":
#     print(f"🔍 Checking if project '{SONAR_PROJECT_KEY}' exists...")
    
#     if project_exists():
#         print("✅ Project already exists.")
#     else:
#         print("🚀 Project not found. Creating project...")
#         create_project()
#         print("🔗 Attempting to bind project to GitHub...")
#         bind_to_github()
    
#     print("✅ Project setup complete. Ready for analysis.")



# import os
# import requests
# import sys

# SONAR_HOST_URL = os.getenv("SONAR_HOST_URL", "https://sonarcloud.io")
# SONAR_TOKEN = os.getenv("SONAR_TOKEN")
# SONAR_PROJECT_KEY = os.getenv("SONAR_PROJECT_KEY")
# SONAR_ORG = os.getenv("SONAR_ORG")
# SONAR_PROJECT_NAME = os.getenv("SONAR_PROJECT_NAME")

# if not SONAR_TOKEN or not SONAR_PROJECT_KEY or not SONAR_ORG:
#     print("❌ Missing SONAR_TOKEN, SONAR_PROJECT_KEY, or SONAR_ORGANIZATION environment variables.")
#     sys.exit(1)

# def project_exists():
#     """Check if SonarCloud project exists."""
#     url = f"{SONAR_HOST_URL}/api/projects/search"
#     params = {
#         "projects": SONAR_PROJECT_KEY,
#         "organization": SONAR_ORG
#     }
#     response = requests.get(url, params=params, auth=(SONAR_TOKEN, ""))
    
#     if response.status_code != 200:
#         print(f"❌ Failed to connect to SonarCloud API: {response.status_code} {response.text}")
#         sys.exit(1)
    
#     data = response.json()
#     return len(data.get("components", [])) > 0

# def create_project():
#     """Create project in SonarCloud."""
#     url = f"{SONAR_HOST_URL}/api/projects/create"
#     payload = {
#         "name": SONAR_PROJECT_NAME,
#         "project": SONAR_PROJECT_KEY,
#         "organization": SONAR_ORG
#     }
#     response = requests.post(url, data=payload, auth=(SONAR_TOKEN, ""))
    
#     if response.status_code != 200:
#         print(f"❌ Failed to create project: {response.status_code} {response.text}")
#         sys.exit(1)
    
#     print(f"✅ Project '{SONAR_PROJECT_KEY}' created successfully.")

# if __name__ == "__main__":
#     print(f"🔍 Checking if project '{SONAR_PROJECT_KEY}' exists on SonarCloud...")
    
#     if project_exists():
#         print("✅ Project already exists. Nothing to do.")
#     else:
#         print("🚀 Project not found. Creating project...")
#         create_project()
#         print("⏳ Waiting for Automatic Analysis to trigger on next push.")
