import requests as rq
from datetime import datetime

URL = 'https://volcaronitee.pythonanywhere.com'


# Function to send data via POST request
def send_data(data):
    response = rq.post(URL, json=data)
    return response.json()


if __name__ == "__main__":
    data_to_send = {'input': 'Hello World!'}  # Replace with your desired data
    response_json = send_data(data_to_send)

    rq_input = response_json.get('input', '')
    updated = datetime.fromtimestamp(response_json.get('last_updated', 0))
    cc = response_json.get('cc', 0)

    print(f'Input is: {rq_input}')
    print(f'Last Updated: {updated}')
    print(f'Character count: {cc}')
