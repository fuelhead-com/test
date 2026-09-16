class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_macsec_policies_config": aoscx_generate_macsec_policies_config
        }

def aoscx_generate_macsec_policies_config(all_vars):
    result = {
        "config_attributes": {},
        "post": {},
        "put": {},
        "delete": {}
    }

    ansible_host = all_vars.get("ansible_host")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    macsec_policies = all_vars.get("macsec_policies", {}) or {}
    macsec_policies_schema = all_vars.get("macsec_policies_schema", {}).get("policy", {})
    post_attributes = all_vars.get("macsec_policies_post_attributes")
    put_attributes = all_vars.get("macsec_policies_put_attributes")
    get_macsec_policies = all_vars.get("get_macsec_policies")

    defaults = {
        key: value.get("default",) if value else None
        for key, value in macsec_policies_schema.items()
    }

    result["defaults"] = defaults

    for policy, value in macsec_policies.items():
        value = value or {}

        cipher_suites = {
            "gcm_aes_128_enabled": value.get("cipher_suite_gcm_aes_128_enabled", defaults.get("cipher_suite_gcm_aes_128_enabled", False)),
            "gcm_aes_256_enabled": value.get("cipher_suite_gcm_aes_256_enabled", defaults.get("cipher_suite_gcm_aes_256_enabled", False)),
            "gcm_aes_xpn_128_enabled": value.get("cipher_suite_gcm_aes_xpn_128_enabled", defaults.get("cipher_suite_gcm_aes_xpn_128_enabled", False)),
            "gcm_aes_xpn_256_enabled": value.get("cipher_suite_gcm_aes_xpn_256_enabled", defaults.get("cipher_suite_gcm_aes_xpn_256_enabled", False)),
        }

        replay_protect_disable = not value.get("replay_protect_enable", defaults.get("replay_protect_enable", False))

        replay_window = value.get("replay_window_size", defaults.get("replay_window_size", 0))

        config_attributes = {
            "name": policy,
            "cipher_suites": cipher_suites,
            "replay_protect_disable": replay_protect_disable,
            "replay_window": replay_window
        }

        result["config_attributes"][policy] = config_attributes

        policy_config = False

        policy_configured = policy in get_macsec_policies.keys()

        if policy_configured:
            policy_config = get_macsec_policies[policy]

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

            url = f"https://{ansible_host}/rest/{restversion}/system/macsec_policies"

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

            url = f"https://{ansible_host}/rest/{restversion}/system/macsec_policies/{policy}"

            if compare != put_body:
                put = {
                    "body": put_body,
                    "url": url
                }

                result["put"][policy] = put

    for policy in get_macsec_policies.keys():
        if policy not in macsec_policies.keys():

            result["delete"][policy] = {
                "url": f"https://{ansible_host}/rest/{restversion}/system/macsec_policies/{policy}"
            }

    return result