from ansible.template import Templar

class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_alias_config": aoscx_generate_alias_config
        }

def aoscx_generate_alias_config(all_vars):
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
    cli_alias = all_vars.get("alias", {}) or {}
    alias_schema = all_vars.get("alias_schema", {}).get("alias", {})
    post_attributes = all_vars.get("alias_post_attributes")
    put_attributes = all_vars.get("alias_put_attributes")
    get_alias = all_vars.get("get_alias")

    defaults = {
        key: value.get("default",) if value else None
        for key, value in alias_schema.items()
    }

    result["defaults"] = defaults

    for alias, value in cli_alias.items():
        value = value or {}

        config_attributes = {
            "alias_definition": templar.template(value.get("cmd")),
            "alias_name": alias
        }

        result["config_attributes"][alias] = config_attributes

        alias_configured = alias in get_alias.keys()

        if alias_configured:
            alias_config = get_alias[alias]

            compare = {
                key: alias_config[key]
                for key in put_attributes
                if key in alias_config
            }

            result["compare"][alias] = compare

            put_body = {
                key: config_attributes[key]
                for key in put_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/cli_aliases/{alias}"

            if compare != put_body:
                put = {
                    "body": put_body,
                    "url": url
                }

                result["put"][alias] = put

        else:
            post_body = {
                key: config_attributes[key]
                for key in post_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/cli_aliases"

            post = {
                "body": post_body,
                "url": url
            }

            result["post"][alias] = post

    for alias in get_alias.keys():
        if alias not in cli_alias.keys():

            result["delete"][alias] = {
                "url": f"https://{ansible_host}/rest/{restversion}/system/cli_aliases/{alias}"
            }


    return result