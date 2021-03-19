from flask import Blueprint, render_template, request, redirect, url_for
from flask_security import login_required, current_user
from flask import current_app as app
from flask_admin.base import MenuLink
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
