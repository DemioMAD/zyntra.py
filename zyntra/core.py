from __future__ import annotations
import asyncio
import time
import aiohttp
from urllib.parse import urljoin
import socketio
from dataclasses import dataclass, field
import shlex
from enum import Enum

_BASE_URL = "https://zyntra.gg"
_API_VER = "v1"

class Presence(Enum):
    offline = 0
    online = 1
    away = 2
    dnd = 3

class ZyntraRestClient:
    def __init__(self, base_url: str, token: str):
        """
        REST client for interacting with Zyntra APIs.
        """
        self.base_url = base_url
        self._token = token
        self.session = None
        self.headers = {
            "Authorization": self._token,
            "User-Agent": "ZyntraDotPy/1.0"
        }

    async def start(self):
        self.session = aiohttp.ClientSession(headers=self.headers)

    async def get(self, endpoint: str):
        url = urljoin(self.base_url, endpoint)
        try:
            async with self.session.get(url, headers=self.headers) as resp:
                data = await self._parse_response(resp)
                return data
        except Exception as ex:
            return {"status": -1, "message": str(ex)}

    async def post(self, endpoint: str, json = None):
        url = urljoin(self.base_url, endpoint)
        try:
            async with self.session.post(url, json=json, headers=self.headers) as resp:
                data = await self._parse_response(resp)
                return data
        except Exception as ex:
            return {"status": -1, "message": str(ex)}

    async def delete(self, endpoint: str):
        url = urljoin(self.base_url, endpoint)
        try:
            async with self.session.delete(url, headers=self.headers) as resp:
                data = await self._parse_response(resp)
                return data
        except Exception as ex:
            return {"status": -1, "message": str(ex)}
        
    async def patch(self, endpoint: str, data = None):
        url = urljoin(self.base_url, endpoint)
        try:
            async with self.session.patch(url, headers=self.headers, json=data) as resp:
                data = await self._parse_response(resp)
                return data
        except Exception as ex:
            return {"status": -1, "message": str(ex)}

    async def _parse_response(self, resp):
        content_type = resp.headers.get("Content-Type", "")
        if "application/json" in content_type:
            body = await resp.json()
        else:
            body = await resp.text()

        if 200 <= resp.status < 300:
            return {"status": resp.status, "message": body}
        else:
            return {"status": resp.status, "message": body}

    async def disconnect(self):
        if self.session and not self.session.closed:
            await self.session.close()

@dataclass
class Embed:
    title: str = ""
    description: str = ""
    color: str = "#ffffff"
    image_url: str = ""
    footer: str = ""
    thumbnail_img: str = ""
    author: str = ""
    url: str = ""

@dataclass
class Channel:
    id: int
    _bot: Client

    async def send(self, content: str = "", embed: Embed = None):
        if content == "" and not embed:
            print("Either content or embed must be provided!")
            return None
        return await self._bot.send_message(self, content, embed)

@dataclass
class User:
    username: str
    uid: int

    @property
    def mention(self):
        return f"<@{self.uid}>"

@dataclass
class Message:
    content: str
    id: int
    bucket_id: int
    sender: User
    in_cache: bool
    channel: Channel
    embed: Embed
    _bot: Client

    async def reply(self, content: str = "", embed: Embed = None):
        url = f"/api/{_API_VER}/channels/{self.channel.id}/messages"
        payload = { "content": content, "replyId": self.id }
        if embed:
            payload["embed"] = {
                "title": embed.title,
                "description": embed.description,
                "color": embed.color,
                "image": embed.image_url,
                "footer": embed.footer,
                "thumbnail": embed.thumbnail_img,
                "url": embed.url
            }

        if content == "" and not embed:
            print("Either content or embed must be provided!")
            return None

        response = await self._bot._client.post(url, payload)

        if 200 <= response.get("status", 0) < 300:
            msg = await self._bot.get_message(PartialMessage(
                response.get("message", {}).get("messageId", 0),
                self.channel
            ))
            return msg
        else:
            print(f"Failed to reply: {response}")
            return response
        
    async def edit(self, new_content: str):
        print(self.sender, self._bot.user)
        if self.sender == self._bot.user:
            url = f"/api/{_API_VER}/channels/{self.channel.id}/messages/{self.id}"
            response = await self._bot._client.patch(url, { "content": new_content })
            if 200 <= response.get("status", 0) < 300:
                if self.id in self._bot.fetched_messages:
                    del self._bot.fetched_messages[self.id]
            
                return await self._bot.get_message(PartialMessage(self.id, self.channel))
            else:
                print(f"Failed to edit message: {response}")
                return None
        else:
            print(f"You cannot edit messages made by humans! Only edit your own messages, this library is in beta after all.")
            return None
        
    async def delete(self):
        if self.sender == self._bot.user:
            url = f"/api/{_API_VER}/channels/{self.channel.id}/messages/{self.id}"
            response = await self._bot._client.delete(url)
            if 200 <= response.get("status", 0) < 300:
                if self.id in self._bot.fetched_messages:
                    del self._bot.fetched_messages[self.id]

                return True
            else:
                print(f"Failed to delete message: {response}")
                return False
        else:
            print(f"You cannot delete messages made by humans! Only delete your own messages, this library is in beta after all.")
            return False

@dataclass
class PartialMessage:
    id: int
    channel: Channel

class Interaction:
    def __init__(self, channel: Channel, user: User, bot: Client, og_msg: Message = None):
        self.channel = channel
        self.user = user
        self.client = bot
        self.__original_msg__ = og_msg

    async def send(self, content: str = "", embed: Embed = None):
        try: 
            if content == "" and not embed:
                print("Either content or embed must be provided!")
                return None
            return await self.channel.send(str(content), embed)
        except Exception as ex:
            print(str(ex))

    async def reply(self, content: str = "", embed: Embed = None):
        try:
            if content == "" and not embed:
                print("Either content or embed must be provided!")
                return None
            
            if self.__original_msg__:
                return await self.__original_msg__.reply(str(content), embed)
            else:
                return await self.channel.send(str(content), embed)
        except Exception as ex:
            print(str(ex))

@dataclass
class CommandData:
    name: str
    description: str = ""
    cooldown: int = 0
    user_cooldowns: dict = field(default_factory=dict)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, CommandData):
            return False
        return self.name == other.name

    @classmethod
    def from_name(self, name: str):
        return self(name)

class Client:
    def __init__(self, token: str, id: int, prefix: str = "!"):
        self.id = id
        self.socket = None
        self.running = False
        self.__on_ready__ = None
        self.__on_message__ = None
        self.prefix = prefix
        self._token = token
        self._client = ZyntraRestClient(_BASE_URL, self._token)
        self.commands = {}
        self.fetched_messages = {}
        self._user = None
        self.__on_sock_conn__ = None
        self.__on_command_cooldown__ = None
    
    async def __fetch_self_user__(self):
        if not self._user:         
            url = f"/api/{_API_VER}/users/@me"
            response = await self._client.get(url)
            if 200 <= response.get("status", 0) < 300:
                self._user = User(response.get("message", {}).get("username", ""), int(response.get("message", {}).get("id", 0)))
            else:
                print(f"Failed to get bot user: {response}")

    @property
    def user(self):
        return self._user
    
    def on_cooldown(self):
        def wrapper(func):
            if not asyncio.iscoroutinefunction(func):
                raise Exception("Callback is not async!")
            
            self.__on_command_cooldown__ = func
            return func
        return wrapper

    def on_message_create(self):
        def wrapper(func):
            if not asyncio.iscoroutinefunction(func):
                raise Exception("Callback is not async!")
            
            self.__on_message__ = func
            return func
        return wrapper
    
    def on_socket_connect(self):
        def wrapper(func):
            if not asyncio.iscoroutinefunction(func):
                raise Exception("Callback is not async!")
            
            self.__on_sock_conn__ = func
            return func
        return wrapper    

    def on_ready(self):
        def wrapper(func):
            if not asyncio.iscoroutinefunction(func):
                raise Exception("Callback is not async!")
            
            self.__on_ready__ = func
            return func
        return wrapper    

    def command(self, name: str, description: str, cooldown: int = 0):
        def wrapper(func):
            if not asyncio.iscoroutinefunction(func):
                raise Exception("Callback is not async!")
            command_dat = CommandData(name, description, cooldown, user_cooldowns={})
            self.commands[command_dat] = func
            return func
        return wrapper
    
    def __is_on_cooldown__(self, command_dat: CommandData, user_id: int):
        now = time.time()
        last_used = command_dat.user_cooldowns.get(user_id, 0)
        cooldown = command_dat.cooldown

        if cooldown == 0:
            return (False, 0)
        
        elapsed = now - last_used
        if elapsed < cooldown:
            return (True, cooldown - elapsed)
        
        command_dat.user_cooldowns[user_id] = now
        return (False, 0)
    
    async def auth_url(self, permissions_integer: int):
        return f"https://zyntra.gg/authorize/bot/{self.id}/?permissions={permissions_integer}"

    async def __start(self):
        await self._client.start()
        await self.__fetch_self_user__()

        try:
            self.running = True
            self.socket = socketio.AsyncClient()

            @self.socket.on("connect")
            async def connect():
                await self.socket.emit("join", { "token": self._token })
                if self.__on_sock_conn__:
                    await self.__on_sock_conn__()

            @self.socket.on("messageReceived")
            async def on_message(data):
                msg = await self.get_message(PartialMessage(data.get("messageId"), Channel(int(data.get("channel", 0)), self)))
                content = msg.content.strip()
                if content.startswith(self.prefix):
                    parts = shlex.split(content[len(self.prefix):])
                    if not parts:
                        return
                    command = parts[0]
                    args = parts[1:]
                    command_dat = next((cd for cd in self.commands if cd.name == command), None)
                    if command_dat in self.commands:
                        inter = Interaction(msg.channel, msg.sender, self, msg)
                        is_cooldown, remaining = self.__is_on_cooldown__(command_dat, msg.sender.uid)
                        if not is_cooldown:
                            await self.commands[command_dat](inter, args)
                        else:
                            if self.__on_command_cooldown__:
                                await self.__on_command_cooldown__(command_dat, msg.channel, remaining)
                if self.__on_message__:
                    await self.__on_message__(msg)

            await self.socket.connect(_BASE_URL, self._client.headers, transports=['websocket'], socketio_path="ws")
            await self.set_presence(Presence.online)
            if self.__on_ready__:
                await self.__on_ready__()

            asyncio.create_task(self.socket.wait())

            while self.running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            await self.stop()
        except Exception as ex:
            print(ex)

    def start(self):
        asyncio.run(self.__start())

    async def stop(self):
        if not self.running:
            return
        
        await self.set_presence(Presence.offline)
        self.running = False
        await self._client.disconnect()

    async def get_message(self, partial_msg: PartialMessage):
        if partial_msg.id in self.fetched_messages:
            return self.fetched_messages[partial_msg.id]

        url = f"/api/{_API_VER}/channels/{partial_msg.channel.id}/messages/{partial_msg.id}"
        response = await self._client.get(url)

        if 200 <= response.get("status", 0) < 300:
            user = User(
                response.get("message", {}).get("sender", {}).get("username", "Unknown"),
                int(response.get("message", {}).get("sender", {}).get("id", 0))
            )

            emb = Embed(
                response.get("message", {}).get("embed", {}).get("title", ""),
                response.get("message", {}).get("embed", {}).get("description", ""),
                response.get("message", {}).get("embed", {}).get("color", "#FF0000"),
                response.get("message", {}).get("embed", {}).get("image", ""),
                response.get("message", {}).get("embed", {}).get("footer", ""),
                response.get("message", {}).get("embed", {}).get("thumbnail", ""),
                response.get("message", {}).get("embed", {}).get("url", "")
            )

            msg = Message(
                response.get("message", {}).get("content", ""),
                partial_msg.id,
                response.get("message", {}).get("bucketId", 0),
                user,
                response.get("message", {}).get("inCache"),
                partial_msg.channel,
                embed=emb,
                _bot=self
            )
            self.fetched_messages[partial_msg.id] = msg
            return msg
        else:
            print(f"Failed to send message: {response}")
            return response
        
    async def set_presence(self, status: Presence):
        url = f"/api/{_API_VER}/updatePresence"
        response = await self._client.post(url, { "status": status.value })
        if 200 <= response.get("status", 0) < 300:
            return response
        else:
            print(f"Failed to set presence: {response}")
            return None

    async def send_message(self, channel: Channel, content: str = "", embed: Embed = None):
        url = f"/api/{_API_VER}/channels/{channel.id}/messages"
        payload = { "content": content }
        if embed:
            payload["embed"] = {
                "title": embed.title,
                "description": embed.description,
                "color": embed.color,
                "image": embed.image_url,
                "footer": embed.footer,
                "thumbnail": embed.thumbnail_img,
                "url": embed.url
            }

        if content == "" and not embed:
            print("Either content or embed must be provided!")
            return None

        response = await self._client.post(url, payload)

        if 200 <= response.get("status", 0) < 300:
            msg = await self.get_message(PartialMessage(
                response.get("message", {}).get("messageId", 0),
                channel
            ))
            return msg
        else:
            print(f"Failed to send message: {response}")
            return response