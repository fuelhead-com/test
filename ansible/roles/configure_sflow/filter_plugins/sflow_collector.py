class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_sflow_collector_collector_config": aoscx_generate_sflow_collector_config
        }

def aoscx_generate_sflow_collector_config(all_vars):

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
    sflow_collector_schema = all_vars.get("sflow_collector_schema", {}).get("collector_ip", {})
    post_attributes = all_vars.get("sflow_collector_post_attributes")
    get_sflow_collectors = all_vars.get("get_sflow_collectors")

    defaults = {
        key: value.get("default",) if value else None
        for key, value in sflow_collector_schema.items()
    }

    result["defaults"] = defaults

    desired_collectors = {}

    for flow, value in sflow.items():

        desired_collectors[flow] = []

        for collector, collector_value in value.get("sflow_collector", {}).items():

            ip_address = collector

            udp_port = collector_value.get("udp_port", defaults.get("udp_port", 6343))

            vrf_name = collector_value.get("vrf", "default")

            vrf = {
                vrf_name: f"/rest/{restversion}/system/vrfs/{vrf_name}"
            }

            collector_name = f"{vrf_name},{collector},{udp_port}"

            desired_collectors[flow].append(collector_name)

            config_attributes = {
                "ip_address": ip_address,
                "udp_port": udp_port,
                "vrf": vrf
            }

            result["config_attributes"][collector_name] = config_attributes

            collector_configured = collector_name in get_sflow_collectors.get(flow, {}).keys()

            if not collector_configured:
                post_body = {
                    key: config_attributes[key]
                    for key in post_attributes
                    if key in config_attributes
                }

                url = f"https://{ansible_host}/rest/{restversion}/system/sflows/{flow}/collectors"

                post = {
                    "body": post_body,
                    "url": url
                }

                result["post"][collector_name] = post

    for flow, value in get_sflow_collectors.items():
        for collector, collector_value in value.items():

            if collector not in desired_collectors[flow]:

                result["delete"][collector] = {
                    "url": f"https://{ansible_host}/rest/{restversion}/system/sflows/{flow}/collectors/{collector}"
                }

    return result