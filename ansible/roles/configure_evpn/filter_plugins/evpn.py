class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_evpn_config": aoscx_generate_evpn_config
        }

def aoscx_generate_evpn_config(all_vars):
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
    evpn = all_vars.get("evpn", {}) or {}
    evpn_schema = all_vars.get("evpn_schema", {})
    post_attributes = all_vars.get("evpn_post_attributes")
    put_attributes = all_vars.get("evpn_put_attributes")
    get_evpn = all_vars.get("get_evpn")

    defaults = {
        key: value.get("default",) if value else None
        for key, value in evpn_schema.items()
    }

    config_attributes = {
        "arp_suppression_enable": evpn.get("arp_suppression_enable", defaults.get("arp_suppression_enable")),
        "mac_move_count": evpn.get("mac_move_count", defaults.get("mac_move_count")),
        "mac_move_timer": evpn.get("mac_move_timer", defaults.get("mac_move_timer")),
        "redistribute": {
            "local-mac": evpn.get("redistribute_local_mac", defaults.get("redistribute_local_mac")),
            "local-svi": evpn.get("redistribute_local_svi", defaults.get("redistribute_local_svi"))
        }
    }

    result["config_attributes"] = config_attributes

    evpn_configured = get_evpn != {}

    if evpn_configured:
        if evpn != {}:

            compare = {
                key: get_evpn[key]
                for key in put_attributes
                if key in get_evpn
            }

            result["compare"] = compare

            put_body = {
                key: config_attributes[key]
                for key in put_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/evpn"

            if compare != put_body:
                put = {
                    "body": put_body,
                    "url": url
                }

                result["put"] = put

        else:
            result["delete"] = {
                "url": f"https://{ansible_host}/rest/{restversion}/system/evpn"
            }

    else:
        if evpn != {}:
            post_body = {
                key: config_attributes[key]
                for key in post_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/evpn"

            post = {
                "body": post_body,
                "url": url
            }

            result["post"] = post

    return result
