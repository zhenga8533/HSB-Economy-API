from flask import Flask, request, jsonify
import time

app = Flask(__name__)

data = {}  # To store the data

@app.route('/', methods=['GET', 'POST'])
def handle_request():
    if request.method == 'POST':
        # Get data from the POST request
        data_json = request.get_json()
        items = data_json.get('items', '')

        # Store the data with timestamp
        data['data'] = {'last_updated': time.time(), 'items': items}

    # Return the stored data as JSON
    return jsonify(data.get('data', {}))

if __name__ == '__main__':
    app.run()
