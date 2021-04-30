from datetime import datetime
from flask import Blueprint, render_template, flash, send_file
from flask import redirect, request, render_template, url_for
from flask_security import login_required, current_user
from bson.json_util import dumps
import secrets
from bson import ObjectId
from flask_socketio import SocketIO
from db import *
public_blueprint = Blueprint('public', __name__, template_folder='templates', url_prefix="/user")
socketio = SocketIO()

requestUser=chat_db.get_collection("requests")
friends=chat_db.get_collection("friends")

@public_blueprint.route('/')
@login_required
def home_page():
    rooms = get_rooms_for_user(current_user.username)
    friend=friends.find_one({'_id':current_user.username})
    room_title=sidebarGen()

    return render_template('public/home_page.html',rooms=rooms, friend=friend, room_title=room_title)

def sidebarGen():
    rooms = get_rooms_for_user(current_user.username)
    room_title={}
    for i in rooms:
        room_id=i["_id"]["room_id"]
        if i['type']!='chat':
            room = get_room(room_id)
            messages = get_messages(room_id, i['type'])
            room_title[room_id]=[i["room_name"], dumps(messages)]
        else:
            room = get_room(room_id)
            if room and is_room_member(room_id, current_user.username):
                room_members = get_room_members(room_id)
                messages = get_messages(room_id, i['type'])
                roomMembers=[i["_id"]["username"] for i in room_members if i["_id"]["username"]!=current_user.username]
            room_title[room_id]=[roomMembers[0], dumps(messages)]
    return room_title

@public_blueprint.before_request

@public_blueprint.route('/search', methods=['POST'])
@login_required
def search_user():
    if request.method=='POST':
        user=request.form.get('username')
        users=list(users_collection.find({'username':user}))
        return render_template('public/search.html', users=users)

@public_blueprint.route('/request/<username>', methods=['GET','POST'])
@login_required
def request_user(username):
    requestUser.insert_one(
        {'from': current_user.username, 'from_name':current_user.name,'to':username, 'created_at': datetime.now()})
    flash("Request Sent", 'success')
    return redirect("/")

@public_blueprint.route('/requests', methods=['GET','POST'])
@login_required
def requests(**kwargs):
    
    Request=[requestUser.find_one({'to':current_user.username})]
    return render_template('public/request.html', users=Request)

@public_blueprint.route('/accept/<username>', methods=['GET', 'POST'])
@login_required
def accept(username):
    room_name="#"
    requestUser.find_one_and_delete({'from': username,'to':current_user.username})
    room_id = save_room(room_name, current_user.username, 'chat')
    add_room_member(room_id, room_name, username, current_user.username,True, 'chat')
    addFriend(username, current_user.username)
    return redirect("/")

def addFriend(user1, user2):
    if friends.find_one({'_id':user1}):
        friends.update_one({'_id':user1}, {'$push':{'friends':user2}})
    else:
        friends.insert_one({'_id':user1, 'friends':[user2]})
    if friends.find_one({'_id':user2}):
        friends.update_one({'_id':user2}, {'$push':{'friends':user1}})
    else:
        friends.insert_one({'_id':user2, 'friends':[user1]})


@public_blueprint.route('/leave/<room_id>', methods=['GET','POST'])
@login_required
def leave_room(room_id):
    if room_members_collection.find_one({'_id.room_id': ObjectId(room_id), '_id.username':current_user.username})['is_room_admin']:
        room_members_collection.delete_one({'_id.room_id': ObjectId(room_id), '_id.username':current_user.username})
        rooms_collection.delete_one({'_id':ObjectId(room_id)})
    return redirect("/")


@public_blueprint.route('/create-room', methods=['POST'])
@login_required
def create_room():
    if request.method == 'POST':
        room_name = request.form.get('room_name')
        banned=['<img src="/static/icons/patch-check-fill.svg">']
        for i in banned:
            if i in room_name:
                flash('You cannot Add that to symbol in the room title')
                return redirect(url_for('public.home_page'))
        usernames = request.form.getlist('friends')
        type_room=request.form.get('type')
        if len(room_name) and len(usernames):
            room_id = save_room(room_name, current_user.username, type_room)
            if current_user.username in usernames:
                usernames.remove(current_user.username)
            add_room_members(room_id, room_name, usernames, current_user.username, type_room)
            return redirect(url_for('public.view_room', room_id=room_id))
        else:
            flash("Failed to create room", 'error')
    #return render_template('chat/create_room.html', message=message)


@public_blueprint.route('/rooms/<room_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    room = get_room(room_id)
    if room and is_room_admin(room_id, current_user.username):
        existing_room_members = [member['_id']['username'] for member in get_room_members(room_id)]
        room_members_str = ",".join(existing_room_members)
        message = ''
        if request.method == 'POST':
            room_name = request.form.get('room_name')
            room['name'] = room_name
            update_room(room_id, room_name)

            new_members = [username.strip() for username in request.form.get('members').split(',')]
            members_to_add = list(set(new_members) - set(existing_room_members))
            members_to_remove = list(set(existing_room_members) - set(new_members))
            if len(members_to_add):
                add_room_members(room_id, room_name, members_to_add, current_user.username)
            if len(members_to_remove):
                remove_room_members(room_id, members_to_remove)
            message = 'Room edited successfully'
            room_members_str = ",".join(new_members)
            room_title=sidebarGen()
        return render_template('chat/edit_room.html', room=room, room_members_str=room_members_str, message=message, room_title=room_title)
    else:
        return "Room not found", 404

@public_blueprint.route('/rooms/<room_id>/')
@login_required
def view_room(room_id):
    room = get_room(room_id)
    friend=friends.find_one({'_id':current_user.username})
    rooms = get_rooms_for_user(current_user.username)
    if room and is_room_member(room_id, current_user.username):
        room_members = get_room_members(room_id)
        type=room['type']
        messages = get_messages(room_id, type)
        room_title=sidebarGen()
        roomMembers=[i["_id"]["username"] for i in room_members if i["_id"]["username"]!=current_user.username]
        return render_template('public/view_room.html',rooms=rooms, username=current_user.username, room=room, room_members=room_members,
                               messages=messages, roomMembers=roomMembers, friend=friend, room_title=room_title)
    else:
        return "Room not found", 404


@public_blueprint.route('/rooms/<room_id>/messages/')
@login_required
def get_older_messages(room_id):
    room = get_room(room_id)
    if room and is_room_member(room_id, current_user.username):
        messages = get_messages(room_id)
        return dumps(messages)
    else:
        return "Room not found", 404

@public_blueprint.route('/userSummery')
@login_required
def userSummery():
    createFolder("summery")
    messages=[]
    rooms = get_rooms_for_user(current_user.username)
    for i in rooms:
        room_id=i['_id']['room_id']
        messages.append(list(messages_collection.find({'room_id': room_id}).sort('_id', DESCENDING))[::-1])
    return str(messages)
    #with open("summery/userSummery.txt","a+") as file:
    #    file.write(messages)
    #return send_file(os.path.realpath("D:\\Projects\\messenger\\summery\\userSummery.txt"), as_attachment=True)

@public_blueprint.route('/roomSummery/<room_id>')
@login_required
def roomSummery(room_id):
    room = get_room(room_id)
    if room and is_room_member(room_id, current_user.username):
        summery(room_id, "summery/roomSummery.txt")
        return send_file(os.path.realpath("D:\\Projects\\messenger\\summery\\roomSummery.txt"), as_attachment=True)

def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)

def summery(room_id, filename):
    room = get_room(room_id)
    if room and is_room_member(room_id, current_user.username):
        createFolder("summery")
        messages = get_messages(room_id)
        messages.append({
            'username':current_user.username,
            'generated_at':datetime.now()
        })
        with open(filename,"a+") as file:
            file.write(dumps(messages))

@public_blueprint.before_request
def keyGen():
    users=list(chat_db.user.find({}, {"username":1, "_id":True}))
    for i in users:
        if chat_db.keys.find_one({"username":i['username']}):
            continue
        else:
            chat_db.keys.insert_one({"_id":i["_id"], "username":i['username'], "key":secrets.token_hex(16)})