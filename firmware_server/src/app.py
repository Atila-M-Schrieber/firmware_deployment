from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/firmware')
def hello():
	return "Hello World!"

@app.route('/firmware/status', methods=['POST'])
def status():
    if request.is_json:
        print("JSON data received")
        data = request.get_json()
    else:
        print("Form data received")
        data = request.form.to_dict()

    print(data)

    no_update = {
        "update": False
    }
    return jsonify(no_update)

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8000)
