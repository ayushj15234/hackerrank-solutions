import os
import sys
import time
import requests

# Read raw configurations from GitHub Secrets
USERNAME = os.environ.get("HR_USERNAME")
SESSION_TOKEN = os.environ.get("HR_COOKIE")

if not USERNAME or not SESSION_TOKEN:
    print("Error: HR_USERNAME or HR_COOKIE environment variables are missing.")
    sys.exit(1)

# Clean up variables to ensure no hidden characters break the code
USERNAME = USERNAME.strip().replace('"', '').replace("'", "")
SESSION_TOKEN = SESSION_TOKEN.strip().replace('"', '').replace("'", "")

# Mapping HackerRank language strings to file extensions
EXTENSION_MAP = {
    "python": "py", "python3": "py", "cpp": "cpp", "cpp14": "cpp",
    "java": "java", "java8": "java", "c": "c", "javascript": "js",
    "ruby": "rb", "swift": "swift", "go": "go", "sql": "sql"
}

# Create session with browser spoofing
session = requests.Session()
session.headers.update({
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "accept": "application/json"
})

# Explicitly assign only the session token to the cookie jar
session.cookies.set("_hr_session", SESSION_TOKEN, domain="www.hackerrank.com")

def fetch_submissions(username):
    all_submissions = []
    limit, offset, has_more = 20, 0, True
    print("Connecting securely to HackerRank profile data...")

    while has_more:
        # Strictly structured path formatting
        url = f"https://hackerrank.com{username}/submissions"
        params = {"offset": offset, "limit": limit}
        
        try:
            response = session.get(url, params=params, timeout=15)
        except Exception as e:
            print(f"Network request connection error: {e}")
            break
        
        if response.status_code != 200:
            print(f"Failed to fetch data at offset {offset}. Status code: {response.status_code}")
            break
            
        try:
            data = response.json()
        except Exception:
            print("Failed to parse response. Your session token might be invalid or expired.")
            break

        submissions = data.get("models", [])
        if not submissions:
            break
            
        all_submissions.extend(submissions)
        offset += limit
        has_more = data.get("page", 0) * limit < data.get("total", 0)
        time.sleep(1)
        
    return all_submissions

def save_submissions_as_files(submissions):
    print(f"Processing {len(submissions)} submissions...")
    saved_count = 0
    
    for sub in submissions:
        if sub.get("status") == "Accepted":
            challenge = sub.get("challenge", {})
            slug = challenge.get("slug")
            language = sub.get("language")
            code_content = sub.get("code")

            if not slug or not code_content:
                continue

            ext = EXTENSION_MAP.get(language, "txt")
            track = challenge.get("track", {}).get("slug", "general")
            folder_path = os.path.join(track, slug)
            os.makedirs(folder_path, exist_ok=True)

            file_name = f"solution.{ext}"
            full_path = os.path.join(folder_path, file_name)

            if not os.path.exists(full_path):
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(code_content)
                print(f"Added new solution: {full_path}")
                saved_count += 1
                
    print(f"Saved {saved_count} new solutions to your repository.")

if __name__ == "__main__":
    submissions = fetch_submissions(USERNAME)
    if submissions:
        save_submissions_as_files(submissions)
        print("Sync complete.")
    else:
        print("No submissions retrieved.")
        sys.exit(1)
