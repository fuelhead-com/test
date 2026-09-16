from ansible.template import Templar

class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_mka_policies_config": aoscx_generate_mka_policies_config
        }

def aoscx_generate_mka_policies_config(all_vars):
    templar = Templar(loader=None, variables=all_vars)

    result = {
        "config_attributes": {},
        "post": {},
        "put": {},
        "delete": {}
    }

    ansible_host = all_vars.get("ansible_host")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    mka_policies = all_vars.get("mka_policies", {}) or {}
    mka_policies_schema = all_vars.get("mka_policies_schema", {}).get("policy", {})
    post_attributes = all_vars.get("mka_policies_post_attributes")
    put_attributes = all_vars.get("mka_policies_put_attributes")
    get_mka_policies = all_vars.get("get_mka_policies")

    defaults = {
        key: value.get("default",) if value else None
        for key, value in mka_policies_schema.items()
    }

    result["defaults"] = defaults

    for policy, value in mka_policies.items():
        value = value or {}

        policy_configured = policy in get_mka_policies.keys()

        cak = templar.template(value.get("cak", None))

        if policy_configured and not value.get("update_cak", False):
            cak = get_mka_policies.get(policy, {}).get("cak", templar.template(value.get("cak", None)))

        ckn = templar.template(value.get("ckn", None))

        key_server_priority = value.get("key_server_priority", defaults.get("key_server_priority", 0))
        
        mode = value.get("mode", defaults.get("mode", None))


        config_attributes = {
            "name": policy,
            "cak": cak,
            "ckn": ckn,
            "key_server_priority": key_server_priority,
            "mode": mode
        }

        result["config_attributes"][policy] = config_attributes

        policy_config = False

        if policy_configured:
            policy_config = get_mka_policies[policy]

            compare = {
                key: policy_config[key]
                for key in put_attributes
                if key in policy_config
            }

        else:
            compare = None

        if not policy_config:
            post_body = {
                key: config_attributes[key]
                for key in post_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/mka_policies"

            post = {
                "body": post_body,
                "url": url
            }

            result["post"][policy] = post

        elif policy_configured:
            put_body = {
                key: config_attributes[key]
                for key in put_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/mka_policies/{policy}"

            if compare != put_body:
                put = {
                    "body": put_body,
                    "url": url
                }

                result["put"][policy] = put

    for policy in get_mka_policies.keys():
        if policy not in mka_policies.keys():

            result["delete"][policy] = {
                "url": f"https://{ansible_host}/rest/{restversion}/system/mka_policies/{policy}"
            }

    return result