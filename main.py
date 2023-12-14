#!./bin/python3 -W ignore

import base64
import os
import sys
from IPython import embed
from IPython.core import ultratb
from openai import OpenAI
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import config

import warnings

sys.excepthook = ultratb.FormattedTB(
    mode="Verbose", color_scheme="Linux", call_pdb=True
)

client = OpenAI()


def monitor_directory(path):
    """
    Monitors the specified directory for new files.
    When a new file is added, it triggers an on_created event.
    """
    event_handler = NewFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            directory_name = os.path.basename(os.path.dirname(event.src_path))
            send_image_to_openai(event.src_path, directory_name)


def send_image_to_openai(image_path, prompt):
    """
    Sends the image along with the prompt to OpenAI's multi-modal Vision API.
    :param image_path: Path to the image file.
    :param prompt: Text prompt extracted from the directory name.
    :return: Response from the API.
    """
    print(f"Sending request to OpenAI ...")
    try:
        image_type = image_path.split(".")[-1]
        with open(image_path, "rb") as image_file:
            binary_data = image_file.read()
            base64_encoded_data = base64.b64encode(binary_data)
            image_data = base64_encoded_data.decode("utf-8")

        request = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"you will be provided with a image. Please look into the image and answer the following question: {prompt}",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{image_type};base64,{image_data}",
                            "detail": "high",
                        },
                    },
                ],
            },
        ]
        # print(request)

        # Create the request to OpenAI's API
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=request,
            max_tokens=3000,
        )

        try:
            os.system("clear")
            print(response.choices[0].message.content)
            print(
                f"tokens: {response.usage.prompt_tokens}/{response.usage.completion_tokens}"
            )

            # Print the total token used and cost.
            # $0.01 per 1k for input token
            # $0.03 per 1k output token
            cost = (
                response.usage.completion_tokens * 0.00003
                + response.usage.prompt_tokens * 0.00001
            )
            print(f"${cost}")
        except:
            embed()

        print("\r\n" * 10)
    except Exception as e:
        print(f"Error sending image to OpenAI: {e}")
        return None


# Example usage
# response = send_image_to_openai('path/to/image.jpg', 'How do I fix this?')
# print(response)

if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=UserWarning)
    path = config.WATCH_DIRECTORY
    monitor_directory(path)
