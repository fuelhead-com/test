import yaml

class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_vxlan_vni_config": aoscx_generate_vxlan_vni_config
        }

def aoscx_generate_vxlan_vni_config(all_vars):
    result = {
        "config_attributes": {},
        "compare": {},
        "post": {},
        "put": {},
        "delete": {},
        "vni_config": {}
    }

    ansible_host = all_vars.get("ansible_host")
    inventory_hostname = all_vars.get("inventory_hostname")
    group_names = all_vars.get("group_names")
    group_names.append("all")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    post_attributes = all_vars.get("vxlan_vni_post_attributes")
    put_attributes = all_vars.get("vxlan_vni_put_attributes")
    get_vxlan_vni = all_vars.get("get_vxlan_vni", {}) or {}
    overlay_vlan_files = all_vars.get("overlay_vlan_files")
    vni_offset = all_vars.get("vni_offset")

    all_overlay_vlans = {}

    for file in overlay_vlan_files:
        with open(file, "r", encoding="utf-8") as f:
            vlan = yaml.safe_load(f)

        all_overlay_vlans[vlan["id"]] = vlan

    switch_overlay_vlans = {}

    for vlan, value in all_overlay_vlans.items():
        if value.get("scope", {}).get("type") == "explicit":
            if inventory_hostname in value.get("scope", {}).get("targets"):
                switch_overlay_vlans[vlan] = value

        elif value.get("scope", {}).get("type") == "group":
            targets = value.get("scope", {}).get("targets", [])

            if any(x in group_names for x in targets):
                switch_overlay_vlans[vlan] = value

    result["switch_overlay_vlans"] = switch_overlay_vlans

    for vlan, value in switch_overlay_vlans.items():
        vxlan_id = vni_offset + vlan
        key_name = f"vxlan_vni,{vxlan_id}"

        config_attributes = {
            "id": vxlan_id,
            "interface": {
                "vxlan1": f"/rest/{restversion}/system/interfaces/vxlan1"
            },
            "routing": False,
            "type": "vxlan_vni",
            "vlan": {
                str(vlan): f"/rest/{restversion}/system/vlans/{vlan}"
            }
        }

        result["config_attributes"][key_name] = config_attributes


        vni_configured = key_name in get_vxlan_vni.keys()

        if vni_configured:
            vni_config = get_vxlan_vni[key_name]

            result["vni_config"][key_name] = vni_config

            compare = {
                key: vni_config[key]
                for key in put_attributes
                if key in vni_config
            }

            result["compare"][key_name] = compare

            put_body = {
                key: config_attributes[key]
                for key in put_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/virtual_network_ids/vxlan_vni,{vxlan_id}"

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

            url = f"https://{ansible_host}/rest/{restversion}/system/virtual_network_ids"

            post = {
                "body": post_body,
                "url": url
            }

            result["post"][key_name] = post

    for vni, value in get_vxlan_vni.items():
        vlan_id = value["id"] - vni_offset

        if vlan_id not in switch_overlay_vlans.keys():
            result["delete"][vni] = {
                "url": f"https://{ansible_host}/rest/{restversion}/system/virtual_network_ids/{vni}"
            }

    return result