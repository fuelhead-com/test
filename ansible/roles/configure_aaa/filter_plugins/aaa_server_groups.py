class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_aaa_server_groups_config": aoscx_generate_aaa_server_groups_config
        }

def aoscx_generate_aaa_server_groups_config(all_vars):
    result = {
        "config_attributes": {},
        "post": {},
        "put": {},
        "delete": {}
    }

    ansible_host = all_vars.get("ansible_host")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    aaa_server_groups = all_vars.get("aaa_server_groups", {}) or {}
    aaa_server_groups_schema = all_vars.get("aaa_server_groups", {})
    post_attributes = all_vars.get("aaa_server_groups_post_attributes")
    put_attributes = all_vars.get("aaa_server_groups_put_attributes")
    get_aaa_server_groups = all_vars.get("get_aaa_server_groups")

    defaults = {
        key: value.get("default",) if value else None
        for key, value in aaa_server_groups_schema.items()
    }

    result["defaults"] = defaults

    for group, value in aaa_server_groups.items():
        value = value or {}

        config_attributes = {
            "group_name": group,
            "group_type": value.get("group_type")
        }

        result["config_attributes"][group] = config_attributes

        group_configured = group in get_aaa_server_groups.keys()

        if group_configured:
            group_config = get_aaa_server_groups[group]

            compare = {
                key: group_config[key]
                for key in put_attributes
                if key in group_config
            }

        else:
            compare = None

        if not group_configured:
            post_body = {
                key: config_attributes[key]
                for key in post_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/aaa_server_groups"

            post = {
                "body": post_body,
                "url": url
            }

            result["post"][group] = post

        elif group_configured:
            put_body = {
                key: config_attributes[key]
                for key in put_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/aaa_server_groups/{group}"

            if compare != put_body:
                put = {
                    "body": put_body,
                    "url": url
                }

                result["put"][group] = put

    for group in get_aaa_server_groups.keys():
        if group not in aaa_server_groups.keys():

            result["delete"][group] = {
                "url": f"https://{ansible_host}/rest/{restversion}/system/aaa_server_groups/{group}"
            }

    return result