import yaml

class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_vlan_config": aoscx_generate_vlan_config
        }

def aoscx_generate_vlan_config(all_vars):
    result = {
        "config_attributes": {},
        "compare": {},
        "post": {},
        "put": {},
        "delete": {}
    }

    ansible_host = all_vars.get("ansible_host")
    inventory_hostname = all_vars.get("inventory_hostname")
    group_names = all_vars.get("group_names")
    group_names.append("all")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    vlan_schema = all_vars.get("vlan_schema", {}).get("id", {})
    post_attributes = all_vars.get("vlan_post_attributes")
    put_attributes = all_vars.get("vlan_put_attributes")
    get_vlans = all_vars.get("get_vlans")
    local_vlan_files = all_vars.get("local_vlan_files")
    overlay_vlan_files = all_vars.get("overlay_vlan_files")

    all_local_vlans = {}
    all_overlay_vlans = {}

    for file in local_vlan_files:
        with open(file, "r", encoding="utf-8") as f:
            vlan = yaml.safe_load(f)

        all_local_vlans[vlan["id"]] = vlan


    for file in overlay_vlan_files:
        with open(file, "r", encoding="utf-8") as f:
            vlan = yaml.safe_load(f)

        all_overlay_vlans[vlan["id"]] = vlan


    switch_local_vlans = {}

    for vlan, value in all_local_vlans.items():
        if value.get("scope", {}).get("type") == "explicit":
            if inventory_hostname in value.get("scope", {}).get("targets"):
                switch_local_vlans[vlan] = value

        elif value.get("scope", {}).get("type") == "group":
            targets = value.get("scope", {}).get("targets", [])

            if any(x in group_names for x in targets):
                switch_local_vlans[vlan] = value


    switch_overlay_vlans = {}

    for vlan, value in all_overlay_vlans.items():
        if value.get("scope", {}).get("type") == "explicit":
            if inventory_hostname in value.get("scope", {}).get("targets"):
                switch_overlay_vlans[vlan] = value

        elif value.get("scope", {}).get("type") == "group":
            targets = value.get("scope", {}).get("targets", [])

            if any(x in group_names for x in targets):
                switch_overlay_vlans[vlan] = value

    # switch_all_vlans dict includes all local and overlay VLANs required on the specific switch
    switch_all_vlans = switch_local_vlans | switch_overlay_vlans

    result["switch_all_vlans"] = switch_all_vlans

    defaults = {
        key: value.get("default",) if value else None
        for key, value in vlan_schema.items()
    }

    for vlan, value in switch_all_vlans.items():
        value = value or {}

        config_attributes = {
            "id": vlan,
            "description": value.get("description"),
            "mgmd_enable": {
                "igmp": value.get("ip_igmp_snooping_enable", defaults.get("ip_igmp_snooping_enable"))
            },
            "name": value.get("name", f"VLAN {vlan}")
        }

        result["config_attributes"][vlan] = config_attributes

        vlan_configured = str(vlan) in get_vlans.keys()

        if vlan_configured:
            vlan_config = get_vlans[str(vlan)]

            compare = {
                key: vlan_config[key]
                for key in put_attributes
                if key in vlan_config
            }

            result["compare"][vlan] = compare

            put_body = {
                key: config_attributes[key]
                for key in put_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/vlans/{vlan}"

            if compare != put_body:
                put = {
                    "body": put_body,
                    "url": url
                }

                result["put"][vlan] = put

        else:
            post_body = {
                key: config_attributes[key]
                for key in post_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/vlans"

            post = {
                "body": post_body,
                "url": url
            }

            result["post"][vlan] = post

    for vlan, value in get_vlans.items():
        ignore_types = [
            "default",
            "internal"
        ]

        if int(vlan) not in switch_all_vlans.keys():
            if value.get("type") not in ignore_types:

                result["delete"][vlan] = {
                    "url": f"https://{ansible_host}/rest/{restversion}/system/vlans/{vlan}"
                }

    return result