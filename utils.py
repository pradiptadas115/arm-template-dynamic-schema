from datetime import datetime


def get_order_options(event):
    return {opt["id"]: opt["val"] for opt in event.get("options", [])}


def log(context, message, order_id=None):
    """Log a message to CMP agains an nFlex module and a SC order"""

    msg = {
        "message": message,
        "severity": "INFO",
        "service": "nflex.flexer",
        "timestamp": datetime.utcnow().strftime(
            '%Y-%m-%dT%H:%M:%S.%fZ'
        ),
    }

    payload = []
    if context.module_id:
        m = msg.copy()
        m["resource_id"] = "nflex-module-%s" % context.module_id
        payload.append(m)

    if order_id:
        m = msg.copy()
        m["resource_id"] = "sc-order-%s" % order_id
        payload.append(m)

    r = context.api.post("/logs", payload)
    if r.status_code != 200:
        print("Error sending logs to CMP: %s" % r.text)

    channel = "order-status-%s" % order_id
    websocket_payload = {
        "topic": "custom",
        "channel": channel,
        "data": {
            "message": message,
            "channel": channel,
            "data": payload
        },
    }
    r = context.api.post('/ws/message', websocket_payload)
    if r.status_code != 201:
        print("Error sending logs to websocket server: %s" % r.text)