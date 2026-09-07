class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_vrf_config": aoscx_generate_vrf_config
        }

def aoscx_generate_vrf_config(all_vars):
    result = {
        "config_attributes": {},
        "post": {},
        "put": {},
        "delete": {}
    }

    ansible_host = all_vars.get("ansible_host")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    vrfs = all_vars.get("vrf", {}) or {}
    vrf_schema = all_vars.get("vrf_schema", {}).get("vrf", {})
    post_attributes = all_vars.get("vrf_post_attributes")
    put_attributes = all_vars.get("vrf_put_attributes")
    get_vrfs = all_vars.get("get_vrfs")

    defaults = {
        key: value.get("default",) if value else None
        for key, value in vrf_schema.items()
    }

    result["defaults"] = defaults

    for vrf, value in vrfs.items():
        value = value or {}

        config_attributes = {
            "name": vrf,
            "https_server": {
                "enable": value.get("https_server_enable", defaults.get("https_server_enable"))
            },
            "ssh_enable": value.get("ssh_server_enable", defaults.get("ssh_server_enable")),
            "telnet_server_enable": value.get("telnet_server_enable", defaults.get("telnet_server_enable"))
        }

        result["config_attributes"][vrf] = config_attributes

        vrf_configured = vrf in get_vrfs.keys()

        if vrf_configured:
            vrf_config = get_vrfs[vrf]

            compare = {
                key: vrf_config[key]
                for key in put_attributes
                if key in vrf_config
            }

        else:
            compare = None

        if not vrf_configured:
            post_body = {
                key: config_attributes[key]
                for key in post_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/vrfs"

            post = {
                "body": post_body,
                "url": url
            }

            result["post"][vrf] = post

        elif vrf_configured:
            put_body = {
                key: config_attributes[key]
                for key in put_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}"

            if compare != put_body:
                put = {
                    "body": put_body,
                    "url": url
                }

                result["put"][vrf] = put

    for vrf in get_vrfs.keys():
        if vrf not in vrfs.keys() and get_vrfs[vrf]["type"] == "user":

            result["delete"][vrf] = {
                "url": f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}"
            }

    return result