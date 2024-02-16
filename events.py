from flask import request
from flask_socketio import emit
from flask_socketio import SocketIO 

socketio = SocketIO()
users = {}

@socketio.on("connect")
def handle_connect():
    print("Client connected!")