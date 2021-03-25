from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_security import login_required, current_user
from bson.json_util import dumps
from db import *
mod_blueprint = Blueprint('mods', __name__, template_folder='templates')

@mod_blueprint.route("/")
@login_required
def index():
    mod_messages=get_group_messages()
    return render_template('mod/index.html', mod_messages=mod_messages)

@mod_blueprint.route("/user")
@login_required
def users():
    return render_template('mod/users.html')

@mod_blueprint.route("/profile")
@login_required
def profile():
    return render_template('mod/profile.html')

@mod_blueprint.route("/create", methods=['GET', 'POST'])
@login_required
def create_channel():
    if request.method == 'POST':
        room_name = request.form.get('room_name')
        usernames = [i['username'] for i in list(users_collection.find({"roles":[]},{'username':1, '_id':0}))] 
        type_room="Channel"
        if len(room_name) and len(usernames):
            room_id = save_room(room_name, current_user.username, type_room, official=True)
            add_room_members(room_id, room_name, usernames, current_user.username, type_room)
            flash("channel created Successfully", "success")
            return redirect(url_for("mods.index"))
            #return redirect(url_for('mod.view_room', room_id=room_id))
        else:
            flash("Failed to create room", 'error')
