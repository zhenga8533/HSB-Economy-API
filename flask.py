from flask import Flask, request, jsonify
import time

app = Flask(__name__)

auction = {}
bazaar = {}


@app.route('/auction', methods=['GET', 'POST'])
def handle_auction():
    if request.method == 'POST':
        # Get data from the POST request
        data_json = request.get_json()
        items = data_json.get('items', '')

        # Store the data with timestamp
        auction['data'] = {'last_updated': time.time(), 'items': items}

    # Return the stored data as JSON
    return jsonify(auction.get('data', {}))


@app.route('/bazaar', methods=['GET', 'POST'])
def handle_bazaar():
    if request.method == 'POST':
        # Get data from the POST request
        data_json = request.get_json()
        items = data_json.get('items', '')

        # Store the data with timestamp
        bazaar['data'] = {'last_updated': time.time(), 'items': items}

    # Return the stored data as JSON
    return jsonify(bazaar.get('data', {}))


if __name__ == '__main__':
    app.run()
