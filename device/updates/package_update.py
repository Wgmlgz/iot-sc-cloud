import subprocess
import os

if __name__ == '__main__':
    subprocess.run(['docker', 'build', '-t', 'device-engine:latest', '.'], cwd='../device', check=True)
    subprocess.run(['docker', 'save', '-o', '../package/device-engine.tar', 'device-engine:latest'], check=True)
    subprocess.run(['tar', '-cvf', 'update_package.tar', '../package'], check=True)
    os.remove('device-engine.tar')
