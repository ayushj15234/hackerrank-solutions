import os
import sys
import time
import requests

# Read credentials from GitHub Actions environment variables
EMAIL = os.environ.get("HR_EMAIL")
PASSWORD = os.environ.get("HR_PASSWORD")

if not EMAIL or not PASSWORD:
    print("Error: HR_EMAIL or HR_PASSWORD environment variables are missing.")
    sys.exit(1)

# Mapping HackerRank language strings to file extensions
EXTENSION_MAP = {
    "python": "py", "python3": "py", "cpp": "cpp", "cpp14": "cpp",
    "java": "java", "java8": "java", "c": "c", "javascript": "js",
    "ruby": "rb", "swift": "swift", "go": "go", "sql": "sql"
}

session = requests.Session()
session.headers.update({
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "accept": "application/json",
})

def login_to_hackerrank():
    print("Attempting to log in to HackerRank...")
    login_page_url = "https://hackerrank.com"
    session.get(login_page_url)
    csrf_token = session.cookies.get("X-CSRF-Token")

    auth_url = "https://hackerrank.com"
    login_data = {"login": EMAIL, "password": PASSWORD, "remember_me": False, "fallback": True}

    if csrf_token:
        session.headers.update({"X-CSRF-Token": csrf_token})

    response = session.post(auth_url, json=login_data)
    if response.status_code == 200 and response.json().get("status"):
        print("Login successful!")
        return response.json().get("user", {}).get("username")
    else:
        print(f"Login failed: {response.status_code}")
        sys.exit(1)

def fetch_submissions(username):
    all_submissions = []
    limit, offset, has_more = 20, 0, True
    print(f"Fetching submissions for {username}...")

    while has_more:
        url = f"https://hackerrank.com{username}/submissions?offset={offset}&limit={limit}"
        response = session.get(url)
        if response.status_code != 200:
            break
        data = response.json()
        submissions = data.get("models", [])
        if not submissions:
            break
        all_submissions.extend(submissions)
        offset += limit
        has_more = data.get("page", 0) * limit < data.get("total", 0)
        time.sleep(1)
    return all_submissions

def save_submissions_as_files(submissions):
    print("Saving solved problems to disk...")
    for sub in submissions:
        if sub.get("status") == "Accepted":
            # Extract challenge details
            challenge = sub.get("challenge", {})
            slug = challenge.get("slug")
            language = sub.get("language")
            code_content = sub.get("code")

            if not slug or not code_content:
                continue

            # Determine the file extension
            ext = EXTENSION_MAP.get(language, "txt")
            
            # Create a target directory path (e.g., algorithms/two-strings)
            track = challenge.get("track", {}).get("slug", "general")
            folder_path = os.path.join(track, slug)
            os.makedirs(folder_path, exist_ok=True)

            # Define exact file path (e.g., algorithms/two-strings/solution.py)
            file_name = f"solution.{ext}"
            full_path = os.path.join(folder_path, file_name)

            # Write code to file if it does not already exist
            if not os.path.exists(full_path):
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(code_content)
                print(f"Added new solution: {full_path}")

if __name__ == "__main__":
    username = login_to_hackerrank()
    submissions = fetch_submissions(username)
    save_submissions_as_files(submissions)
    print("Sync complete.")
