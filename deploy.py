import json
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode

AZURE_STORAGE_BUCKET_PATH = "/storage/buckets/azure-templates"

def deployment(event, context, deployment_name = "vk-test", resource_group = "NTTCMPTest"):
    order = get_order_options(event)
    account_id = order["account_id"]
    subscription_id = order["subscription_id_%s" % account_id]
    credentials = event.get("credentials")
    creds = ServicePrincipalCredentials(
        credentials["client_id"],
        credentials["client_secret"],
        tenant=credentials["tenant_id"],
    )
    resource_client = ResourceManagementClient(creds, str(subscription_id))
    # template_name = order["template"]
    service_id = event.get("service_def_id")

    resp = context.api.get("{}/{}/azuredeploy.json".format(AZURE_STORAGE_BUCKET_PATH, service_id))  # edited this with servic id
    template = json.loads(resp.content)

    parameters = {}
    for p in template["parameters"]:
        parameters[p] = {"value": order[p]}

    deployment_properties = {
        'mode': DeploymentMode.incremental,
        'template': template,
        'parameters': parameters
    }

    deployment_async_operation = resource_client.deployments.create_or_update(
        resource_group,
        deployment_name,
        deployment_properties
    )
    deployment_async_operation.wait()

    return deployment_async_operation.status()


def get_order_options(event):
    return {opt["id"]: opt["val"] for opt in event.get("options", [])}

# subscription = 1eaf224f-c75c-4995-b709-5001d6010ae5
'''
def get_credentials(event):
    """ Get account credentials. """
    credentials = event.get("credentials", {})
    context.log("Creds : ".format(credentials))
    # credentials = {}
    try:
        credentials["client_id"] # = "b017f6ed-c57f-4df7-859d-0820243d3e19"
        credentials["client_secret"] # = "YRRGMdPQcvS5Cfrsdy8LiW75bKpXoG+T79s9+bgVkrI="
        credentials["tenant_id"] # = "72342e4e-a16e-4ccb-899d-435959fd1f89"
    except KeyError as err:
        raise Exception(
            " account credentials %s not specified" % err
        )

    return credentials
'''