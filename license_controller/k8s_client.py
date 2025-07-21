
from kubernetes import client, config
import json, base64

def init():
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()
    return client.CoreV1Api()

def b64d(b): return base64.b64decode(b).decode()
def b64e(s): return base64.b64encode(s.encode()).decode()

def get_secret(api, name, ns):
    return api.read_namespaced_secret(name, ns)

def patch_secret(api, name, ns, data):
    api.patch_namespaced_secret(name, ns, {'data': data})

def extract_license(secret):
    import json
    return json.loads(b64d(secret.data["license.json"]))
