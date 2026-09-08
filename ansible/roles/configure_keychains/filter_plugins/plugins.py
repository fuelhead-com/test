from ansible.errors import AnsibleFilterError


def validate_int(value, default, minimum, maximum):
    try:
        value = int(value)
        if minimum <= value <= maximum:
            return value
    except (TypeError, ValueError):
        pass

    return default


class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_keychain_config": aoscx_generate_keychain_config
        }

def aoscx_generate_keychain_config(desired_keychains, configured_keychains, all_vars):

    # ansible_host = all_vars.get("ansible_host")
    # aoscx_api_version = all_vars.get("aoscx_api_version")
    # restversion = f"v{aoscx_api_version}"

    # required_keychain_names = {item["name"] for item in desired_keychains}

    # result = {}

    # for item in desired_keychains:

    #     name = item.get("name")

    #     # compare = configured_keychains[name]

    #     send_post = False if name in configured_keychains.keys() else True

    #     post_body = {
    #         "name": name,
    #     }

    #     put_body = {}
        
    #     send_put = False

    #     result[name] = {
    #         "post": {
    #             "body": post_body,
    #             "url": f"https://{ansible_host}/rest/{restversion}/system/keychains",
    #             "send_post": send_post
    #           },
    #           "put": {
    #             "body": put_body,
    #             "url": f"https://{ansible_host}/rest/{restversion}/system/keychains/{name}",
    #             "send_put": send_put
    #           },
    #           "delete": {
    #             "url": f"https://{ansible_host}/rest/{restversion}/system/keychains/{name}",
    #             "send_delete": False
    #           }
    #         }

    #     # if compare:
    #     #     result[name]["compare"] = {name: compare}


    # for item in configured_keychains.keys():
    #     if item not in required_keychain_names:
    #         result[item] = {
    #             "post": {
    #                 "body": {},
    #                 "url": f"https://{ansible_host}/rest/{restversion}/system/keychains",
    #                 "send_post": False
    #             },
    #                 "put": {
    #                     "body": {},
    #                     "url": f"https://{ansible_host}/rest/{restversion}/system/keychains/{name}",
    #                     "send_put": False
    #                 },
    #             "delete": {
    #                 "send_delete": True,
    #                 "url": f"https://{ansible_host}/rest/{restversion}/system/keychains/{name}"
    #             }
    #         }
    
    return result
