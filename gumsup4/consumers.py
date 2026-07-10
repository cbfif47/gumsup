
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.template.loader import render_to_string

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope["url_route"]["kwargs"]["group_id"]
        self.room = f"group_{self.group_id}"
        await self.channel_layer.group_add(self.room, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room, self.channel_name)

    async def receive(self, text_data):
        # htmx ws-send will send JSON of form fields by default
        try:
            data = json.loads(text_data or "{}")
        except json.JSONDecodeError:
            data = {}

        # TODO: apply your game logic here (play card, update models, etc.)
        card = {"rank": data.get("rank"), "suit": data.get("suit"), "player": data.get("player_name")}

        # Render a partial and broadcast it to everyone in the group
        html = render_to_string("partials/card_played.html", {"card": card})
        await self.channel_layer.group_send(self.room, {"type": "send.html", "html": html})

    async def send_html(self, event):
        # Channels maps "type": "send.html" -> method named "send_html"
        await self.send(text_data=event["html"])
