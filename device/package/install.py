import subprocess
import os

def load_and_run_image():
    """Load the new Docker image and restart the container."""
    # Extract the update package
    subprocess.run(['tar', '-xvf', 'update_package.tar'], check=True)

    # Load the Docker image from the tarball
    subprocess.run(['docker', 'load', '-i', 'myimage.tar'], check=True)

    # Stop and remove the old container, then start the new one
    subprocess.run(['docker', 'container', 'stop', 'iot-device'], check=True)
    subprocess.run(['docker', 'container', 'rm', 'iot-device'], check=True)
    subprocess.run(['docker', 'run', '--name', 'iot-device', '-d', 'myimage:latest'], check=True)

    print("Container updated successfully.")

if __name__ == '__main__':
    load_and_run_image()
