import re
import base64
import json
import requests
from deploy import deployment
# from deploy import get_credentials
from utils import log
import time
from datetime import datetime
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource.subscriptions import SubscriptionClient
from azure.mgmt.resource import ResourceManagementClient
from collections import OrderedDict


def handle(event, context):
    order = get_order_options(event)
    context.log("Order_ Handle: {}".format(order))
    order_id = event["order_id"]
    template_name = order["template"]
    account_id = order["account_id"]
    resource_group = order["resource_id_%s" % account_id]
    # template_name = template_name + datetime.utcnow().strftime('%Y%m%dT%H%M%S%fZ')
    deployment_async_operation = deployment(event, context, template_name, resource_group)  # deployment
    update_order(context, order_id, "Deployed")
    log(context, deployment_async_operation, order_id)
    return "Processed, Status: {}".format(json.dumps(deployment_async_operation))

def schema(event, context):
    context.log("Event Handle: {}".format(event))
    step = event.get("step")
    if not step:
        return choose_account(event, context)
    if step in globals():
        return globals()[step](event, context)

def choose_account(event, context):
    questions = []
    resp = context.api.post(
        "/query",
        {
            "queries": [
                {
                    "key": "type",
                    "values": ["account"],
                },
                {
                    "key": "provider.id",
                    "values": ["azure"],
                }
            ]
        },
    )
    accounts = resp.json()["items"]
    questions.append(
        {
            "type": "select",
            "label": "Account ID",
            "id": "account_id",
            "options": [
                {"label": account["base"]["name"], "value": account["id"]}
                for account in accounts
            ],
            "fieldset": "Account details",
        }
    )

    # sub
    for account in accounts:
        subs = account["metadata"]["provider_specific_editable"]["subscriptions"]  # noqa
        questions.append(
            {
                "type": "select",
                "id": "subscription_id_%s" % account["id"],
                "label": "Account Subscription ID",
                "dependency": [
                    {
                        "id": "account_id",
                        "value": account["id"],
                    },
                ],
                "options": [
                    {"label": sub["id"], "value": sub["id"]}
                    for sub in subs
                ],
                "fieldset": "Account details",
            }
        )
    # resource group
    for account in accounts:
        rgs = account["metadata"]["provider_specific"]["resource_groups"]
        questions.append(
            {
                "type": "select",
                "id": "resource_id_%s" % account["id"],
                "label": "Resource Group",
                "dependency": [
                    {
                        "id": "account_id",
                        "value": account["id"],
                    },
                ],
                "options": [
                    {"label": rg, "value": rg}
                    for rg in rgs
                ],
                "fieldset": "Account details",
            }
        )
    return {
        "questions": questions,
        "previous_step": None,
        "current_step": "choose_account",
        "next_step": "template_parameter",
    }

def template_parameter(event, context):
    # template_name = "101-vm-simple-linux"   # hardcoded
    order = get_order_options(event)
    context.log("Order_schema: {}".format(order))
    # context.log("Event: {}".format(event))
    service_id = event.get("service_def_id")
    # template_name = context.config['template']
    resp = context.api.get("/storage/buckets/azure-templates/{}/azuredeploy.json".format(service_id))
    template = json.loads(resp.content,object_pairs_hook=OrderedDict)

    ######### Get location name ###############

    account_id = order["account_id"]
    subscription_id = order["subscription_id_%s" % account_id]
    credentials = event.get("credentials")
    context.log("creds {}".format(credentials))
    creds = ServicePrincipalCredentials(
        credentials["client_id"],
        credentials["client_secret"],
        tenant=credentials["tenant_id"],
    )
    resource_client = ResourceManagementClient(creds, str(subscription_id))
    resource_groups = resource_client.resource_groups.list()
    location = " "
    for r in resource_groups :
        if r.name == order["resource_id_%s" % account_id]:
            location = r.location
            break
    context.log(location, "debug")

    # location = "Central US"
    questions = []
    type_map = {
        "string": "text",
        "securestring": "password",
        "bool": "checkbox",
        "int": "number",
        "array": "textArea",
    }
    for k, v in template["parameters"].items():
        q = {
            "id": k,
            "label": " ".join(map(str.capitalize, camel_case_split(k))),
            "type": type_map.get(v["type"], "text"),
            "validation": [{"type": "required"},{"pattern":"([a-z]+)"}],
            "help": v["metadata"]["description"],
        }
        if "allowedValues" in v:
            if not v["type"] in ("bool", "int"):
                q["type"] = "select"
                q["options"] = [
                    {"value": av, "label": str(av)}
                    for av in v["allowedValues"]
                ]
        if "defaultValue" in v:
            q["value"] = v["defaultValue"]
            if v["type"] == "array":
                q["value"] = json.dumps(q["value"])

        if "location" in k:
            q["value"] = location
            if v["type"] == "array":
                q["value"] = json.dumps(q["value"])

        questions.append(q)
    return {
        "questions": questions,
        "previous_step": "choose_account",
        "current_step": "template_parameter",
        "next_step": None,
    }

def camel_case_split(identifier):
    matches = re.finditer(
        r'.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)',
        identifier
    )
    return [str(m.group(0)) for m in matches]

def update_order(context, order_id, status, option_label=None, option_value=None):
    if order_id == None:
        raise Exception("Service catalog Order ID missing")

    context.log("Updating status/options for the Order: [{}]".format(order_id))

    resp = context.api.get("/orders/{}".format(order_id))
    json_result = resp.json()
    options = json_result["options"]
    payload = {
        "status": status,
    }

    if option_label:
        options.append({
            "id": option_label,
            "key": option_label,
            "val": option_value,
        })
    payload["options"] = options

    resp = context.api.put("/orders/{}".format(order_id), payload)
    if resp.status_code != 200:
        context.log("Failed to update order: %s" % resp.text)

def get_order_options(event):
    return {opt["id"]: opt["val"] for opt in event.get("options", [])}