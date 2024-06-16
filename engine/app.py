from flask import Flask, request, jsonify
import cv2
import boto3
import datetime
import os
import numpy as np
import cv2
import numpy as np
import os

app = Flask(__name__)

# Configure your S3 bucket and ThingsBoard details from environment variables
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
S3_BUCKET = os.getenv("S3_BUCKET")
THINGSBOARD_URL = os.getenv("THINGSBOARD_URL")
PORT = int(os.getenv("PORT"))
s3_client = boto3.client(
    "s3",
    endpoint_url="https://storage.yandexcloud.net",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)

# def authenticate_device(device_id, token):
#     headers = {'X-Authorization': f'Bearer {token}'}
#     response = requests.get(f'{THINGSBOARD_URL}/api/device/{device_id}', headers=headers)
#     return response.status_code == 200




def setup_network():
    configPath = os.path.join(
        "config_files", "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
    )
    weightsPath = os.path.join("config_files", "frozen_inference_graph.pb")
    classNames = []
    classFile = os.path.realpath(
        os.path.join(os.path.dirname(__file__), "config_files", "coco.names")
    )

    with open(classFile, "rt") as f:
        classNames = f.read().rstrip("\n").split("\n")

    net = cv2.dnn_DetectionModel(weightsPath, configPath)
    net.setInputSize(320, 320)
    net.setInputScale(1.0 / 127.5)
    net.setInputMean((127.5, 127.5, 127.5))
    net.setInputSwapRB(True)
    print("network load done")
    return net, classNames


net, classNames = setup_network()


def process_and_save_video(video_path, output_path):
    cap = cv2.VideoCapture(video_path)
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    size = (frame_width, frame_height)

    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    temp_output_path = output_path.replace(".mp4", ".avi")  # Temp file as AVI

    out = cv2.VideoWriter(temp_output_path, fourcc, 20, size)
    detection_stats = {}

    first_frame = True
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        classIds, confs, bbox = net.detect(frame, confThreshold=0.45)
        bbox = list(bbox)
        confs = list(np.array(confs).reshape(1, -1)[0])
        confs = list(map(float, confs))

        indices = cv2.dnn.NMSBoxes(bbox, confs, 0.45, 0.5)
        for i in indices:
            box = bbox[i]
            x, y, w, h = box
            class_name = classNames[classIds[i] - 1]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            cv2.putText(
                frame,
                class_name,
                (x + 10, y + 30),
                cv2.FONT_HERSHEY_COMPLEX,
                1,
                (0, 255, 0),
                2,
            )

            if first_frame:
                # Update detection stats
                if class_name in detection_stats:
                    detection_stats[class_name] += 1
                else:
                    detection_stats[class_name] = 1

        first_frame = False
        out.write(frame)

    cap.release()
    out.release()
    convert_video_to_mp4(temp_output_path, output_path)

    return detection_stats


def convert_video_to_mp4(input_path, output_path):
    import subprocess

    command = f"ffmpeg -y -i {input_path} -vcodec libx264 {output_path}"
    subprocess.run(command, shell=True)


@app.route("/upload", methods=["POST"])
def upload_video():
    device_id = request.headers.get("Device-ID")
    video_file = request.files["video"]

    # Save temporary input video
    input_video_path = "temp_input.mp4"
    video_file.save(input_video_path)

    # Define output video path
    output_video_path = "processed_output.mp4"

    # Process video and save with bounding boxes
    detection_stats = process_and_save_video(input_video_path, output_video_path)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d/%H:%M:%S")
    video_path = f"device-videos/{device_id}/{timestamp}.mp4"
    with open(output_video_path, "rb") as data:
        s3_client.upload_fileobj(data, S3_BUCKET, video_path)

    presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": video_path},
        ExpiresIn=3600,
    )

    res = {
        "status": 1,
        "message": "Video processed and uploaded successfully.",
        "video_path": video_path,
        "video_url": presigned_url,
    }
    res.update(detection_stats)
    return jsonify(res)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT)
