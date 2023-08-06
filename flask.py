from flask import Flask, request, jsonify
import time

app = Flask(__name__)

data = {}  # To store the data

@app.route('/', methods=['GET', 'POST'])
def handle_request():
    if request.method == 'POST':
        # Get data from the POST request
        data_json = request.get_json()
        lbin = data_json.get('lbin', '')

        # Store the data with timestamp
        data_set = {'lbin': lbin, 'last_updated': time.time()}
        data['data'] = data_set

    # Return the stored data as JSON
    return jsonify(data.get('data', {}))

if __name__ == '__main__':
    app.run()
