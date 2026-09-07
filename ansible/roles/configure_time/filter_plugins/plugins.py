class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_ntp_association_config": aoscx_generate_ntp_association_config
        }

def aoscx_generate_ntp_association_config(all_vars):

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
    ntp_associations = all_vars.get("time", {}).get("ntp", {}).get("servers") or {}
    ntp_association_schema = all_vars.get("time_schema", {}).get("ntp", {}).get("servers", {}).get("ntp_server")
    post_attributes = all_vars.get("ntp_association_post_attributes")
    put_attributes = all_vars.get("ntp_association_put_attributes")
    get_ntp_associations = all_vars.get("get_ntp_associations")
    default_vrf = all_vars.get("time_schema", {}).get("ntp", {}).get("vrf", {}).get("default")

    defaults = {
        key: value.get("default",) if value else None
        for key, value in ntp_association_schema.items()
    }
    defaults["vrf"] = default_vrf

    result["defaults"] = defaults

    for ntp_association, value in ntp_associations.items():
        value = value or {}
        vrf = all_vars.get("time", {}).get("ntp", {}).get("vrf", default_vrf)

        config_attributes = {
            "address": ntp_association,
            "association_attributes": {
                "burst_mode": value.get("burst_mode", defaults.get("burst_mode")),
                "maxpoll": value.get("maxpoll", defaults.get("maxpoll")),
                "minpoll": value.get("minpoll", defaults.get("minpoll")),
                "ntp_version": value.get("version", defaults.get("version")),
                "prefer": value.get("prefer", defaults.get("prefer")),
                "ref_clock_id": "--"
            },
            "key_id": None,
            "vrf": f"/rest/{restversion}/system/vrfs/{vrf}"
        }

        result["config_attributes"][ntp_association] = config_attributes

        configured_ntp_associations = get_ntp_associations.get(vrf, {})
        configured_ntp_associations_list = configured_ntp_associations.keys()
        ntp_association_configured = ntp_association in configured_ntp_associations_list

        if ntp_association_configured:
            ntp_association_config = configured_ntp_associations[ntp_association]

            compare = {
                key: ntp_association_config[key]
                for key in put_attributes
                if key in ntp_association_config
            }

            result["compare"][ntp_association] = compare

            put_body = {
                key: config_attributes[key]
                for key in put_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/ntp_associations/{ntp_association}"

            if compare != put_body:
                put = {
                    "body": put_body,
                    "url": url
                }

                result["put"][ntp_association] = put

        elif not ntp_association_configured:
            post_body = {
                key: config_attributes[key]
                for key in post_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/ntp_associations"

            post = {
                "body": post_body,
                "url": url
            }

            result["post"][ntp_association] = post

    for vrf, ntp_servers in get_ntp_associations.items():
        ntp_servers = ntp_servers or {}

        for ntp_server, value in ntp_servers.items():
            value = value or {}

            if ntp_server not in ntp_associations.keys():
                result["delete"][ntp_server] = {
                    "url": f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/ntp_associations/{ntp_server}",
                    "condition1": True
                }

            elif ntp_server in ntp_associations.keys():
                if vrf != defaults.get("vrf"):
                        
                    result["delete"][ntp_server] = {
                        "url": f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/ntp_associations/{ntp_server}",
                        "condition2": True,
                        "desired_vrf": ntp_associations[ntp_server].get("vrf"),
                        "configured_rf": vrf    
                    }
            

    return result