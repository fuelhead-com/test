from ansible.template import Templar

class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_vxlan_interface_config": aoscx_generate_vxlan_interface_config
        }

def aoscx_generate_vxlan_interface_config(all_vars):
    templar = Templar(loader=None, variables=all_vars)

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
    vxlan_interface = all_vars.get("vxlan_interface", {}).get("vxlan1", {}) or {}
    vxlan_interface_schema = all_vars.get("vxlan_interface_schema", {}).get("vxlan1")
    post_attributes = all_vars.get("vxlan_interface_post_attributes")
    put_attributes = all_vars.get("vxlan_interface_put_attributes")
    get_vxlan_interface = all_vars.get("get_vxlan_interface", {})

    defaults = {
        key: value.get("default",) if value else None
        for key, value in vxlan_interface_schema.items()
    }

    result["defaults"] = defaults

    config_attributes = {
        "admin": "down" if vxlan_interface.get("enabled", defaults.get("enabled")) is False else "up",
        "description": vxlan_interface.get("description"),
        "name": "vxlan1",
        "options": {
            "local_ip": templar.template(vxlan_interface.get("source_ip")),
            "vxlan_dest_udp_port": "4789"
        },
        "type": "vxlan"
     }

    result["config_attributes"] = config_attributes

    vxlan_interface_configured = "vxlan1" in get_vxlan_interface.keys()

    result["vxlan_interface_configured"] = vxlan_interface_configured

    if vxlan_interface_configured:
        vxlan_interface_config = get_vxlan_interface["vxlan1"]
        if vxlan_interface != {}:

            compare = {
                key: vxlan_interface_config[key]
                for key in put_attributes
                if key in vxlan_interface_config
            }

            result["compare"] = compare

            put_body = {
                key: config_attributes[key]
                for key in put_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/interfaces/vxlan1"

            if compare != put_body:
                put = {
                    "body": put_body,
                    "url": url
                }

                result["put"] = put

        else:
            result["delete"] = {
                "url": f"https://{ansible_host}/rest/{restversion}/system/interfaces/vxlan1"
            }

    else:
        if vxlan_interface != {}:
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

            result["post"] = post

    return result