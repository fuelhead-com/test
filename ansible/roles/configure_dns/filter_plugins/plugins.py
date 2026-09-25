class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_dns_config": aoscx_generate_dns_config
        }

def aoscx_generate_dns_config(all_vars):

    result = {
        "config_attributes": {},
        "compare": {},
        "patch": {},
    }

    ansible_host = all_vars.get("ansible_host")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    dns = all_vars.get("dns", {}) or {}
    dns_schema = all_vars.get("dns_schema", {}).get("vrf", {})
    patch_attributes = all_vars.get("dns_patch_attributes")
    get_dns_config = all_vars.get("get_dns_config", {})

    defaults = {
        key: value.get("default",) if value else None
        for key, value in dns_schema.items()
    }

    result["defaults"] = defaults

    for vrf, value in dns.items():

        dns_domain_name = value.get("dns_domain_name", defaults.get("dns_domain_name", None))

        servers = value.get("dns_name_servers", defaults.get("dns_name_servers", {}))

        dns_name_servers = {
            str(index): server
            for index, server in enumerate(servers)
        }
            
        config_attributes = {
            "dns_domain_name": dns_domain_name,
            "dns_name_servers": dns_name_servers
        }

        result["config_attributes"][vrf] = config_attributes


        dns_config = get_dns_config[vrf]

        compare = {
            key: dns_config[key]
            for key in patch_attributes
            if key in dns_config
        }

        result["compare"][vrf] = compare

        patch_body = {
            key: config_attributes[key]
            for key in patch_attributes
            if key in config_attributes
        }

        url = f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}"

        if compare != patch_body:
            patch = {
                "body": patch_body,
                "url": url
            }

            result["patch"][vrf] = patch

    for vrf, value in get_dns_config.items():
        if vrf not in dns.keys():
            zero_dns = {
                "dns_domain_name": None,
                "dns_name_servers": {}
            }

            if value != zero_dns:
                result["patch"][vrf] = {
                    "body": {
                        "dns_domain_name": None,
                        "dns_name_servers": None
                    },
                    "url": f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}"
                }

    return result