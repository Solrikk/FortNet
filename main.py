from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.responses import HTMLResponse
from datetime import datetime, timezone, timedelta
import uuid

app = FastAPI()

connected_users = {}
messages = []


def generate_user_code():
  return str(uuid.uuid4())


class UserInfo(BaseModel):
  username: str


class MessageInfo(BaseModel):
  username: str
  text: str


@app.get("/", response_class=HTMLResponse)
def read_root():
  return """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>SolrikkVPN</title>
    <style>
        body { 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            flex-direction: column;
            background-color: #f0f0f0;
            font-family: Arial, sans-serif;
        }
        #container {
            text-align: center;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            background-color: #ffffff;
            border-radius: 10px;
        }
        button {
            margin: 5px;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            background-color: #007bff;
            color: #ffffff;
        }
        input[type="text"] {
            padding: 10px;
            margin-top: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            width: 300px;
        }
        .online {
            color: green;
        }
        .offline {
            color: red;
        }
    </style>
</head>
<body>
    <div id="container">
        <h1>Подключение к VPN</h1>
        <button onclick="connectToVpn()">Подключиться</button>
        <button onclick="disconnectFromVpn()">Отключиться</button>
        <h2 id="moscowTime">Московское время: </h2>
        <h2>Подключенные пользователи:</h2>
        <ul id="usersList">
        </ul>
        <h2>Чат:</h2>
        <div id="chat">
        </div>
        <input type="text" id="chatMessage" placeholder="Введите сообщение" />
        <button onclick="sendMessage()">Отправить</button>
    </div>
    <script>
        async function connectToVpn() {
            const response = await fetch("/connect-to-vpn", {
                method: "POST",
                body: JSON.stringify({username: prompt("Введите ваше имя")}),
                headers: {"Content-Type": "application/json"}
            });
            const data = await response.json();
            alert(data.message);
            updateUsersList();
        }
        async function disconnectFromVpn() {
            const username = prompt("Введите ваше имя для отключения");
            const response = await fetch("/disconnect-from-vpn", {
                method: "POST",
                body: JSON.stringify({username}),
                headers: {"Content-Type": "application/json"}
            });
            const data = await response.json();
            alert(data.message);
            updateUsersList();
        }
        async function updateMoscowTime() {
            const moscowTime = new Date(new Date().getTime() + 3 * 3600 * 1000).toUTCString().replace(/ GMT$/, '');
            document.getElementById("moscowTime").innerHTML = "Московское время: " + moscowTime;
        }
        async function updateUsersList() {
            const response = await fetch("/connected-users");
            const data = await response.json();
            const usersList = document.getElementById("usersList");
            usersList.innerHTML = data.users.map(user => `<li class="${user.status}">${user.username} - ${user.status}</li>`).join('');
        }
        async function updateChat() {
            const response = await fetch("/chat");
            const data = await response.json();
            const chat = document.getElementById("chat");
            chat.innerHTML = data.messages.map(msg => `<p>${msg.username}: ${msg.text}</p>`).join('');
        }
        async function sendMessage() {
            const messageInput = document.getElementById("chatMessage");
            await fetch("/send-message", {
                method: "POST",
                body: JSON.stringify({username: "userName", text: messageInput.value}),
                headers: {"Content-Type": "application/json"}
            });
            messageInput.value = "";
            updateChat();
        }
        setInterval(() => {
            updateUsersList();
            updateChat();
            updateMoscowTime();
        }, 1000);
        window.onload = function() {
            updateUsersList();
            updateChat();
            updateMoscowTime();
        };
    </script>
</body>
</html>
    """


@app.post("/connect-to-vpn")
def connect_to_vpn(user_info: UserInfo):
  if user_info.username in connected_users:
    raise HTTPException(status_code=400, detail="User already connected")
  user_code = generate_user_code()
  connected_users[user_info.username] = {
      "username": user_info.username,
      "connectedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      "code": user_code,
      "status": "online"
  }
  return {
      "message": f"{user_info.username} подключен к VPN.",
      "code": user_code
  }


@app.get("/connected-users")
def get_connected_users():
  return {
      "users": [
          user for user in connected_users.values()
          if user['status'] == 'online'
      ]
  }


@app.post("/disconnect-from-vpn")
def disconnect_from_vpn(user_info: UserInfo):
  if user_info.username not in connected_users:
    raise HTTPException(status_code=404, detail="User not found")
  connected_users[user_info.username]['status'] = 'offline'
  return {"message": f"{user_info.username} теперь офлайн."}


@app.get("/chat")
def get_chat():
  return {"messages": messages}


@app.post("/send-message")
def send_message(message: MessageInfo):
  messages.append({"username": message.username, "text": message.text})
  return {"message": "Message sent successfully."}
