const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

socket.on('connect', function () {
    socket.emit('join_room', {
        username: "{{ username }}",
        room: "{{ room._id }}"
    });

    let message_input = document.getElementById('message_input');
    document.getElementById('message_input_form').onsubmit = function (e) {
        e.preventDefault();
        let message = message_input.value.trim();
        if (message.length) {
            socket.emit('send_message', {
                username: "{{ username }}",
                room: "{{ room._id }}",
                roomType:"{{ room.type }}",
                message: message
            })
        }
        message_input.value = '';
        message_input.focus();
    }
});

/*
    let page = 0;

document.getElementById("load_older_messages_btn").onclick = (e) => {
    page += 1;
    fetch("/rooms/{{ room._id }}/messages?page=" + page, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(response => {
        response.json().then(messages => {
            messages.reverse().forEach(message => prepend_message(message.text, message.sender, message.created_at));
        })
    })
};

function prepend_message(message, username, created_at) {
    const newNode = document.createElement('li');
    newNode.classList="list-group-item";
    newNode.innerHTML = `
    <div class="align-self-${data.username === "{{current_user.username}}" ? "end self" : "start"} p-1 my-1 mx-3 rounded bg-white shadow-sm message-item" style="float:${data.username === "{{current_user.username}}" ? "right" : "left"} ; width: fit-content;">
        <div class="options">
            <a href="#"><i class="fas fa-angle-down text-muted px-2"></i></a>
        </div>
        <div class="small font-weight-bold text-primary">
            ${data.username}
        </div>
        <div class="d-flex flex-row">
            <div class="body m-1 mr-2">${data.message}</div>
            <div class="time ml-auto small text-right flex-shrink-0 align-self-end text-muted" style="width:75px;">
                ${data.created_at}
            </div>
        </div>
    </div>
    `;
    const messages_div = document.getElementById('messages');
    messages_div.insertBefore(newNode, messages_div.firstChild);
} 
*/
window.onbeforeunload = function () {
    socket.emit('leave_room', {
        username: "{{ username }}",
        room: "{{ room._id }}"
    })
};

socket.on('receive_message', function (data) {
    const newNode = document.createElement('li');
    newNode.classList="list-group-item";
    if(data.username !=='{{current_user.username}}'){
        newNode.innerHTML = `
    <div class="align-self-${data.username === "{{current_user.username}}" ? "end self" : "start"} p-1 my-1 mx-3 rounded bg-white shadow-sm message-item" style="float:${data.username === "{{current_user.username}}" ? "right" : "left"} ; width: fit-content;">
        <div class="options">
            <a href="#"><i class="fas fa-angle-down text-muted px-2"></i></a>
        </div>
        <div class="small font-weight-bold text-primary">
            ${data.username}
        </div>
        <div class="d-flex flex-row">
            <div class="body m-1 mr-2">${data.message}</div>
            <div class="time ml-auto small text-right flex-shrink-0 align-self-end text-muted" style="width:75px;">
                ${data.created_at}
            </div>
        </div>
    </div>
    `;
    }
    else{
        newNode.innerHTML = `
    <div class="align-self-${data.username === "{{current_user.username}}" ? "end self" : "start"} p-1 my-1 mx-3 rounded bg-white shadow-sm message-item" style="float:${data.username === "{{current_user.username}}" ? "right" : "left"} ; width: fit-content;">
        <div class="options">
            <a href="#"><i class="fas fa-angle-down text-muted px-2"></i></a>
        </div>
        <div class="d-flex flex-row">
            <div class="body m-1 mr-2">${data.message}</div>
            <div class="time ml-auto small text-right flex-shrink-0 align-self-end text-muted" style="width:75px;">
                ${data.created_at}
            </div>
        </div>
    </div>
    `;
    }
    

    var node= document.getElementById('messages').appendChild(newNode);
    window.scrollTo(0,document.getElementById("messages").scrollHeight);
    //node.scrollIntoView();
});

socket.on('join_room_announcement', function (data) {
    if (data.username !== "{{ username }}") {
        const status=document.getElementById('status');
        status.innerHTML = `<h6>Online</h6>`;
    }
});

socket.on('leave_room_announcement', function (data) {
    const status=document.getElementById('status');
    status.innerHTML = `<h6>Last seen at: </h6>`;
});