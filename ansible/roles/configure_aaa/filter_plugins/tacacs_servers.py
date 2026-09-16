class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_tacacs_servers_config": aoscx_generate_tacacs_servers_config
        }

def aoscx_generate_tacacs_servers_config(all_vars):

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
    tacacs_servers = all_vars.get("tacacs_servers", {}) or {}
    tacacs_servers_schema = all_vars.get("tacacs_servers_schema", {}).get("server", {})
    post_attributes = all_vars.get("tacacs_servers_post_attributes")
    put_attributes = all_vars.get("tacacs_servers_put_attributes")
    get_tacacs_servers = all_vars.get("get_tacacs_servers", {})

    defaults = {
        key: value.get("default",) if value else None
        for key, value in tacacs_servers_schema.items()
    }

    result["defaults"] = defaults

    for vrf, servers in tacacs_servers.items():
        for srv, value in servers.items():
            address = srv
            tcp_port = value.get("tcp_port", defaults.get("tcp_port", 49))
            server = f"{srv},{tcp_port}"
            key_name = f"{vrf},{srv},{tcp_port}"

            auth_type = value.get("auth_type", defaults.get("auth_type", None))

            default_group_priority = value.get("default_group_priority", defaults.get("default_group_priority", 1))

            group = {}
            if value.get("group", False):
                group = {
                    key: f"/rest/{restversion}/system/aaa_server_groups/{key}"
                    for key in value.get("group")
                }

            passkey = value.get("passkey", defaults.get("passkey", None))

            timeout = value.get("timeout", defaults.get("timeout", 1))

            vrf_value = {
                vrf: f"/rest/{restversion}/system/vrfs/{vrf}"
            }
            
            config_attributes = {
                "address": address,
                "auth_type": auth_type,
                "default_group_priority": default_group_priority,
                "group": group,
                "passkey": passkey,
                "tcp_port": tcp_port,
                "timeout": timeout,
                "vrf": vrf_value
            }

            result["config_attributes"][key_name] = config_attributes

            server_configured = server in get_tacacs_servers.get(vrf, {}).keys()

            if server_configured:
                server_config = get_tacacs_servers[vrf][server]

                compare = {
                    key: server_config[key]
                    for key in put_attributes
                    if key in server_config
                }

                result["compare"][key_name] = compare

                put_body = {
                    key: config_attributes[key]
                    for key in put_attributes
                    if key in config_attributes
                }

                url = f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/tacacs_servers/{server}"

                if compare != put_body:
                    put = {
                        "body": put_body,
                        "url": url
                    }

                    result["put"][key_name] = put

            else:
                post_body = {
                    key: config_attributes[key]
                    for key in post_attributes
                    if key in config_attributes
                }

                url = f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/tacacs_servers"

                post = {
                    "body": post_body,
                    "url": url
                }

                result["post"][key_name] = post

    for vrf, servers in get_tacacs_servers.items():
        for srv, value in servers.items():
            server = f"{value['address']},{value['tcp_port']}"
            key_name = f"{vrf},{value['address']},{value['tcp_port']}"

            if value["address"] not in tacacs_servers.get(vrf, {}).keys():

                result["delete"][key_name] = {
                    "url": f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/tacacs_servers/{server}"
                }

    return result