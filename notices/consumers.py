from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NoticeNotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close()
            return

        self.group_names = ["live_notices_all", f"live_notices_{user.role}"]
        for group_name in self.group_names:
            await self.channel_layer.group_add(group_name, self.channel_name)
        await self.accept()
        await self.send_json(
            {
                "type": "connection_ready",
                "message": "Live notice notifications connected.",
            }
        )

    async def disconnect(self, close_code):
        for group_name in getattr(self, "group_names", []):
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def notice_created(self, event):
        await self.send_json(
            {
                "type": "notice_created",
                "title": event["title"],
                "message": event["message"],
                "created_by": event["created_by"],
                "created_at": event["created_at"],
                "audience": event["audience"],
            }
        )
