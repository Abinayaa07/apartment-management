from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def _notice_groups(notice):
    if notice.audience == "staff":
        return ["live_notices_staff", "live_notices_admin"]
    if notice.audience == "security":
        return ["live_notices_security", "live_notices_admin"]
    return [
        "live_notices_all",
        "live_notices_resident",
        "live_notices_staff",
        "live_notices_security",
        "live_notices_admin",
    ]


def broadcast_notice_created(notice):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    created_by = notice.created_by.username if notice.created_by else "System"
    payload = {
        "type": "notice_created",
        "title": notice.title,
        "message": notice.message,
        "created_by": created_by,
        "created_at": notice.created_at.strftime("%d %b %Y, %I:%M %p"),
        "audience": notice.get_audience_display(),
    }
    for group_name in _notice_groups(notice):
        async_to_sync(channel_layer.group_send)(group_name, payload)
