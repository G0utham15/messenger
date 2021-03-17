from app import create_app
from flask import redirect
from flask_socketio import SocketIO, join_room, leave_room
from db import *
import logging
app = create_app()
socketio = SocketIO(app)
@app.route("/")
def home():
    return redirect('/login')

@socketio.on('send_message')
def handle_send_message_event(data):
    data['created_at'] = datetime.now()
    data['date']=data['created_at'].strftime("%d-%m-%y")
    data['created_at'] = data['created_at'].strftime("%H:%M")
    save_message(data['room'], data['message'], data['username'], data['roomType'])
    socketio.emit('receive_message', data, room=data['room'])


@socketio.on('join_room')
def handle_join_room_event(data):
    join_room(data['room'])
    socketio.emit('join_room_announcement', data, room=data['room'])


@socketio.on('leave_room')
def handle_leave_room_event(data):
    leave_room(data['room'])
    socketio.emit('leave_room_announcement', data, room=data['room'])

if __name__=="__main__":
    socketio.run(app, debug=True)