import os
import requests
from git import Repo

# 🚀 Change this to your local GitHub repo path
LOCAL_REPO_PATH = "/Users/psadithyan/Documents/PROJECT/waybackog/wayback"

# 🚀 GitHub URL of the text file
GITHUB_FILE_PATH = "ngrok-url.txt"

# 🚀 Function to get the latest NGROK URL
def get_ngrok_url():
    try:
        response = requests.get("http://127.0.0.1:4040/api/tunnels")
        response_json = response.json()
        return response_json["tunnels"][0]["public_url"]
    except Exception as e:
        print("Error getting NGROK URL:", e)
        return None

# 🚀 Function to update GitHub file
def update_github():
    repo = Repo(LOCAL_REPO_PATH)
    file_path = os.path.join(LOCAL_REPO_PATH, GITHUB_FILE_PATH)
    
    # Get new NGROK URL
    ngrok_url = get_ngrok_url()
    if not ngrok_url:
        print("❌ Failed to get NGROK URL!")
        return
    
    # Update the file content
    with open(file_path, "w") as f:
        f.write(ngrok_url)
    
    # Git Commit & Push
    repo.git.add(GITHUB_FILE_PATH)
    repo.index.commit(f"🔄 Auto-update NGROK URL: {ngrok_url}")
    origin = repo.remote(name="origin")
    origin.push()

    print("✅ NGROK URL updated successfully:", ngrok_url)

# 🚀 Run the update function
if __name__ == "__main__":
    update_github()
