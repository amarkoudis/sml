from flask import Flask, request, session

app = Flask(__name__)
app.secret_key = 'test'

@app.route('/test', methods=['GET', 'POST'])
def test():
    print("Test route hit")
    if request.method == 'POST':
        print("POST data:", request.form)
    return "OK"

if __name__ == '__main__':
    app.run(port=8080)