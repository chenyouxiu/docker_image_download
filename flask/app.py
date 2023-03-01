import docker
from docker.utils.json_stream import json_stream
import io
import logging
from flask import Flask, request, send_file, render_template

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/download', methods=['POST'])
def download_image():
    # Get input parameters
    image_name_all = request.form.get('image_name', '')
    if "docker pull " in image_name_all:
      image_name_all = image_name_all.replace("docker pull ","")
    if ":" in str(image_name_all):
      image_name_all = image_name_all.split(":")
      image_name = image_name_all[0]
      tag = image_name_all[1]
    else:
      image_name = image_name_all
      tag = "latest"
    #image_name= image_name.replace("%2F","/")
    print(image_name)
    #logging.info(image_name,tag)

    # Connect to Docker engine
    client = docker.from_env()

    # Pull image from Docker Hub
    try:
        progress = client.api.pull(f'{image_name}:{tag}', stream=True)
        for line in progress:
            print(eval(line))
            status = eval(line)
            if 'status' in status and 'progressDetail' in status:
              progress_detail = status['progressDetail']
              if 'current' in progress_detail and 'total' in progress_detail:
                  progress_percent = progress_detail['current'] / progress_detail['total'] * 100
                  #speed = progress_detail['speed'] / 1024 / 1024  # Convert bytes/sec to MB/sec
                  logging.info(f"Pulling {image_name}:{tag} - {progress_percent:.2f}% - ")
    except docker.errors.APIError as e:
        logging.error(f"Failed to pull image {image_name}:{tag}: {e}")
        return "Failed to download the image. Please try again later."

    # Save image to a file-like object
    image_file = io.BytesIO()
    for chunk in client.images.get(f"{image_name}:{tag}").save():
        image_file.write(chunk)
    image_file.seek(0)

    # Return the image file as a download attachment
    attachment_filename = f'{image_name}_{tag}.tar'
    mimetype = 'application/tar'
    return send_file(
        image_file,
        as_attachment=True,
        attachment_filename=attachment_filename,
        mimetype=mimetype
    )

if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)

