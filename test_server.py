#!/usr/bin/env python3

from flask import Flask

app = Flask(__name__)

@app.route('/test')
def test():
    return "Test working!"

@app.route('/qr_scan')
def qr_scan():
    return "QR Scan working!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)
