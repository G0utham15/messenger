from datetime import datetime
import hashlib
from bson import ObjectId
from pymongo import MongoClient, DESCENDING

client = MongoClient(host="localhost", port=27017)

chat_db = client.get_database("auth") 
users_collection = chat_db.get_collection("user")
rooms_collection = chat_db.get_collection("rooms")
room_members_collection = chat_db.get_collection("room_members")
messages_collection = chat_db.get_collection("messages")
user_rooms= chat_db.get_collection("user_rooms")
group_transactions=chat_db.get_collection("groupTransactions")
transaction_message=chat_db.get_collection("transactionMessage")

def save_room(room_name, created_by, type='group'):
    room_id = rooms_collection.insert_one(
        {'name': room_name, 'created_by': created_by, 'created_at': datetime.now(), 'admin':[created_by], 'users':[created_by], 'type':type}).inserted_id
    add_room_member(room_id, room_name, created_by, created_by,  True, type)
    return room_id

def update_room(room_id, room_name):
    rooms_collection.update_one({'_id': ObjectId(room_id)}, {'$set': {'name': room_name}})
    room_members_collection.update_many({'_id.room_id': ObjectId(room_id)}, {'$set': {'room_name': room_name}})


def get_room(room_id):
    return rooms_collection.find_one({'_id': ObjectId(room_id)})


def add_room_member(room_id, room_name, username, added_by, is_room_admin=False, type='group'):
    room_members_collection.insert_one(
        {'_id': {'room_id': ObjectId(room_id), 'username': username}, 'room_name': room_name, 'added_by': added_by,
         'added_at': datetime.now(), 'is_room_admin': is_room_admin, 'type':type})
    


def add_room_members(room_id, room_name, usernames, added_by, type='group', official='False'):
    room_members_collection.insert_many(
        [{'_id': {'room_id': ObjectId(room_id), 'username': username}, 'room_name': room_name, 'added_by': added_by,
          'added_at': datetime.now(), 'is_room_admin': False, 'type':type, 'official':official} for username in usernames])
    for username in usernames:
        rooms_collection.update_one({'_id': ObjectId(room_id)}, {'$push': {'users': username}})

def remove_room_members(room_id, usernames):
    room_members_collection.delete_many(
        {'_id': {'$in': [{'room_id': ObjectId(room_id), 'username': username} for username in usernames]}})


def get_room_members(room_id):
    return list(room_members_collection.find({'_id.room_id': ObjectId(room_id)}))


def get_rooms_for_user(username):
    return list(room_members_collection.find({'_id.username': username}))


def is_room_member(room_id, username):
    return room_members_collection.count_documents({'_id': {'room_id': ObjectId(room_id), 'username': username}})


def is_room_admin(room_id, username):
    return room_members_collection.count_documents(
        {'_id': {'room_id': ObjectId(room_id), 'username': username}, 'is_room_admin': True})


def save_message(room_id, text, sender, type):
    if type=='chat':
        messages_collection.insert_one({'room_id': room_id, 'text': text, 'sender': sender, 'created_at': datetime.now()})
    else:
        group_transactions.insert_one({'room_id':room_id, 'sender': sender,'body': hashlib.md5(text.encode()).hexdigest(), 'created_at': datetime.now()})
        try:
            transaction_message.insert_one({'_id': hashlib.md5(text.encode()).hexdigest(), 'text': text})
        except:
            pass

#MESSAGE_FETCH_LIMIT = 50

def get_last_message(room_id, type):
    if get_messages(room_id, type).__len__!=0:
        return get_messages(room_id, type)[-1]
    else:
        return ""
        
def get_group_messages():
    return list(transaction_message.find({}))
    
def get_messages(room_id, type):
    #offset = page * MESSAGE_FETCH_LIMIT
    if type=='chat':
        messages = list(messages_collection.find({'room_id': room_id}).sort('_id', DESCENDING))
        for message in messages:
            message['date']=message['created_at'].strftime("%d-%m-%y")
            message['created_at'] = message['created_at'].strftime("%H:%M")
    else:
        messages = list(group_transactions.find({'room_id': room_id}).sort('_id', DESCENDING))
        if messages.__len__!=0:
            for message in messages:
                message['text']=list(transaction_message.find({'_id':message['body']}))[0]['text']
                message['date']=message['created_at'].strftime("%d-%m-%y")
                message['created_at'] = message['created_at'].strftime("%H:%M")
    """
    messages = list(
        messages_collection.find({'room_id': room_id}).sort('_id', DESCENDING).limit(MESSAGE_FETCH_LIMIT).skip(offset))
    """

    return messages[::-1]
