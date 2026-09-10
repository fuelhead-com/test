class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_loopback_interface_config": aoscx_generate_loopback_interface_config
        }

def aoscx_generate_loopback_interface_config(all_vars):

    result = {
        "config_attributes": {},
        "compare": {},
        "post": {},
        "put": {},
        "delete": {}
    }

    ansible_host = all_vars.get("ansible_host")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    loopback_interfaces = all_vars.get("loopback_interfaces", {}) or {}
    loopback_interfaces_schema = all_vars.get("loopback_interfaces_schema", {}).get("interface")
    post_attributes = all_vars.get("loopback_interfaces_post_attributes")
    put_attributes = all_vars.get("loopback_interfaces_put_attributes")
    get_loopback_int = all_vars.get("get_loopback_int", {})

    defaults = {
        key: value.get("default",) if value else None
        for key, value in loopback_interfaces_schema.items()
    }

    result["defaults"] = defaults

    for interface, value in loopback_interfaces.items():
        config_attributes = {
            "name": interface,
            "description": value.get("description"),
            "ip4_address": value.get("ipv4_address"),
            "ospf_if_shutdown": value.get("ip_ospf_enabled", defaults.get("ip_ospf_enabled", True)) is not True,
            "type": "loopback"
        }

        result["config_attributes"][interface] = config_attributes

        interface_configured = interface in get_loopback_int.keys()

        if interface_configured:
            interface_config = get_loopback_int[interface]

            compare = {
                key: interface_config[key]
                for key in put_attributes
                if key in interface_config
            }

            result["compare"][interface] = compare

            put_body = {
                key: config_attributes[key]
                for key in put_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/interfaces/{interface}"

            if compare != put_body:
                put = {
                    "body": put_body,
                    "url": url
                }

                result["put"][interface] = put

        else:
            post_body = {
                key: config_attributes[key]
                for key in post_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/interfaces"

            post = {
                "body": post_body,
                "url": url
            }

            result["post"][interface] = post

    for interface in get_loopback_int.keys():
        if interface not in loopback_interfaces.keys():

            result["delete"][interface] = {
                "url": f"https://{ansible_host}/rest/{restversion}/system/interfaces/{interface}"
            }
            
    return result