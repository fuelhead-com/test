from ansible.template import Templar

class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_sflow_config": aoscx_generate_sflow_config
        }

def aoscx_generate_sflow_config(all_vars):
    templar = Templar(loader=None, variables=all_vars)

    result = {
        "config_attributes": {},
        "post": {},
        "put": {},
        "delete": {}
    }

    ansible_host = all_vars.get("ansible_host")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    sflow = all_vars.get("sflow", {}) or {}
    sflow_schema = all_vars.get("sflow_schema", {}).get("sflow_name", {})
    post_attributes = all_vars.get("sflow_post_attributes")
    put_attributes = all_vars.get("sflow_put_attributes")
    get_sflow = all_vars.get("get_sflow")

    defaults = {
        key: value.get("default",) if value else None
        for key, value in sflow_schema.items()
    }

    result["defaults"] = defaults

    for flow, value in sflow.items():
        value = value or {}

        flow_configured = flow in get_sflow.keys()

        agent_address = templar.template(value.get("agent_address"))
        enabled = value.get("enabled", defaults.get("enabled", False)) is not False
        header = value.get("header", defaults.get("header", 128))
        max_datagram = value.get("max_datagram", defaults.get("max_datagram", 1400))
        name = flow
        polling = value.get("polling", defaults.get("polling", 20))
        reachability_check = value.get("reachability_check", defaults.get("reachability_check", True)) is not False
        sampling = value.get("sampling", defaults.get("sampling", 4096))

        config_attributes = {
            "agent_address": agent_address,
            "enabled": enabled,
            "header": header,
            "max_datagram": max_datagram,
            "name": name,
            "polling": polling,
            "reachability_check": reachability_check,
            "sampling": sampling
        }

        result["config_attributes"][flow] = config_attributes

        flow_config = None
        
        if flow_configured:
            flow_config = get_sflow[flow]

            compare = {
                key: flow_config[key]
                for key in put_attributes
                if key in flow_config
            }

        else:
            compare = None

        if not flow_config:
            post_body = {
                key: config_attributes[key]
                for key in post_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/sflows"

            post = {
                "body": post_body,
                "url": url
            }

            result["post"][flow] = post

        elif flow_configured:
            put_body = {
                key: config_attributes[key]
                for key in put_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/sflows/{flow}"

            if compare != put_body:
                put = {
                    "body": put_body,
                    "url": url
                }

                result["put"][flow] = put

    for flow in get_sflow.keys():
        if flow not in sflow.keys():

            result["delete"][flow] = {
                "url": f"https://{ansible_host}/rest/{restversion}/system/sflows/{flow}"
            }

    return result