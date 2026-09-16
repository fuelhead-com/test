class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_aaa_server_group_prios_config": aoscx_generate_aaa_server_group_prios_config
        }

def aoscx_generate_aaa_server_group_prios_config(all_vars):
    result = {
        "config_attributes": {},
        "post": {},
        "put": {},
        "delete": {}
    }

    ansible_host = all_vars.get("ansible_host")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    aaa_server_group_prios = all_vars.get("aaa_server_group_prios", {}) or {}
    aaa_server_group_prios_schema = all_vars.get("aaa_server_group_prios_schema", {}).get("type", {})
    put_attributes = all_vars.get("aaa_server_group_prios_put_attributes")
    get_aaa_server_group_prios = all_vars.get("get_aaa_server_group_prios")

    defaults = {
        key: value.get("default",) if value else None
        for key, value in aaa_server_group_prios_schema.items()
    }

    result["defaults"] = defaults

    for type, value in aaa_server_group_prios.items():
        value = value or {}

        accounting_group_prios = {
            str(key): f"/rest/{restversion}/system/aaa_server_groups/{value}"
            for key, value in value.get("accounting_group_prios", defaults.get("accounting_group_prios", {})).items()
        }

        authentication_group_prios = {
            str(key): f"/rest/{restversion}/system/aaa_server_groups/{value}"
            for key, value in value.get("authentication_group_prios", defaults.get("authentication_group_prios", {})).items()
        }

        authorization_group_prios = {
            str(key): f"/rest/{restversion}/system/aaa_server_groups/{value}"
            for key, value in value.get("authorization_group_prios", defaults.get("authorization_group_prios", {})).items()
        }

        radius_authorize_only_group_prios = {
            str(key): f"/rest/{restversion}/system/aaa_server_groups/{value}"
            for key, value in value.get("radius_authorize_only_group_prios", defaults.get("radius_authorize_only_group_prios", {})).items()
        }

        config_attributes = {
            "accounting_group_prios": accounting_group_prios,
            "authentication_group_prios": authentication_group_prios,
            "authorization_group_prios": authorization_group_prios,
            "radius_authorize_only_group_prios": radius_authorize_only_group_prios
        }

        result["config_attributes"][type] = config_attributes

        type_configured = type in get_aaa_server_group_prios.keys()

        if type_configured:
            type_config = get_aaa_server_group_prios[type]

            compare = {
                key: type_config[key]
                for key in put_attributes
                if key in type_config
            }

            put_body = {
                key: config_attributes[key]
                for key in put_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/v10.16/system/aaa_server_group_prios/{type}"

            if compare != put_body:
                put = {
                    "body": put_body,
                    "url": url
                }

                result["put"][type] = put

    return result