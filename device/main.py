import subprocess
import sys
import time
import requests
import json


def load_config():
    with open("config.json", "r") as config_file:
        return json.load(config_file)


def send_telemetry(telemetry_data, auth_token, thingsboard_url):
    headers = {
        "Content-Type": "application/json",
    }
    telemetry_url = f"{thingsboard_url}/api/v1/{auth_token}/telemetry"

    try:
        response = requests.post(telemetry_url, headers=headers, json=telemetry_data)
        print(f"{response.status_code}")
        print(f"Telemetry sent successfully: {response.text}")
    except requests.RequestException as e:
        print(f"Error sending telemetry data to ThingsBoard: {e}")


def capture_video(camera_name, duration=2, output_file="output.mp4"):
    if not camera_name:
        return

    command = [
        "ffmpeg",
        "-y",
        "-r",
        "15",
        "-f",
        "vfwcap",
        "-i",
        camera_name,
        "-t",
        str(duration),
        "-s",
        "1280x720",
        output_file,
    ]

    try:
        subprocess.run(command, check=True)
        print(f"Video saved as {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print("An error occurred during video capture:", e)
        return False


def send_video_to_api(video_file, url, device_id, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}", "Device-ID": device_id}
    files = {"video": open(video_file, "rb")}
    try:
        response = requests.post(url + "/upload", headers=headers, files=files)
        print(f"Response from server: {response.text}")
        if response.status_code == 200:
            telemetry_data = response.json()
            return telemetry_data
        else:
            return {"status": 0, "message": "Server error"}
    except Exception as e:
        print(f"An error occurred when sending the video: {e}")
        return {"status": 0, "message": "Device error"}


if __name__ == "__main__":
    config = load_config()
    interval = config.get("interval", 60)  # Default to 300 seconds if not set
    camera_name = config["camera_name"]
    api_url = config["api_url"]
    thingsboard_url = config["thingsboard_url"]
    device_id = config["device_id"]
    auth_token = config["auth_token"]

    while True:
        output_file = f"output.mp4"
        if capture_video(camera_name, output_file=output_file):
            telemetry_data = send_video_to_api(
                output_file, api_url, device_id, auth_token
            )
            send_telemetry(telemetry_data, auth_token, thingsboard_url)
        time.sleep(interval)
