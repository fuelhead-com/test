class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_vlan_interface_config": aoscx_generate_vlan_interface_config
        }

def aoscx_generate_vlan_interface_config(all_vars):

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
    vlan_interfaces = all_vars.get("vlan_interfaces", {}) or {}
    vlan_interface_schema = all_vars.get("vlan_interface_schema", {}).get("interface")
    post_attributes = all_vars.get("vlan_interface_post_attributes")
    put_attributes = all_vars.get("vlan_interface_put_attributes")
    get_vlan_interfaces = all_vars.get("get_vlan_interfaces", {})

    defaults = {
        key: value.get("default",) if value else None
        for key, value in vlan_interface_schema.items()
    }

    result["defaults"] = defaults

    for interface, value in vlan_interfaces.items():

        ospf_auth_keychain = None

        ip_ospf_keychain = value.get("ip_ospf_keychain", defaults.get("ip_ospf_keychain", None))

        if ip_ospf_keychain is not None:
            ospf_auth_keychain = {
                ip_ospf_keychain: f"/rest/{restversion}/system/keychains/{ip_ospf_keychain}"
            }

        ip_ospf_bfd = value.get("ip_ospf_bfd", defaults.get("ip_ospf_bfd", "default"))

        if ip_ospf_bfd == "default":
            ospf_bfd = ip_ospf_bfd
        elif ip_ospf_bfd:
            ospf_bfd = "enable"
        else:
            ospf_bfd = "disable"

        ospf_if_shutdown = value.get("ip_ospf_enabled", defaults.get("ip_ospf_enabled", True)) is not True

        ospf_network = value.get("ip_ospf_network", defaults.get("ip_ospf_network"))
        
        if ospf_network == "point-to-point":
            ospf_if_type = "ospf_iftype_pointopoint"
        elif ospf_network == "broadcast":
            ospf_if_type = "ospf_iftype_broadcast"
        else:
            ospf_if_type = None

        config_attributes = {
            "admin": "down" if value.get("enabled", defaults.get("enabled")) is False else "up",
            "name": interface,
            "description": value.get("description"),
            "ip_mtu": value.get("ip_mtu", defaults.get("ip_mtu")),
            "ip4_address": value.get("ipv4_address"),
            "ospf_auth_keychain": ospf_auth_keychain,
            "ospf_bfd": ospf_bfd,
            "ospf_if_shutdown": ospf_if_shutdown,
            "ospf_if_type": ospf_if_type,
            "type": "vlan"
        }

        result["config_attributes"][interface] = config_attributes

        interface_configured = interface in get_vlan_interfaces.keys()

        if interface_configured:
            interface_config = get_vlan_interfaces[interface]

            compare = {
                key: interface_config[key]
                for key in put_attributes
                if key in interface_config
            }

            result["compare"][interface] = compare

            put_body = {
                key: config_attributes[key]
                for key in put_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/interfaces/{interface}"

            if compare != put_body:
                put = {
                    "body": put_body,
                    "url": url
                }

                result["put"][interface] = put

        else:
            post_body = {
                key: config_attributes[key]
                for key in post_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/interfaces"

            post = {
                "body": post_body,
                "url": url
            }

            result["post"][interface] = post

    for interface in get_vlan_interfaces.keys():
        if interface not in vlan_interfaces.keys():

            result["delete"][interface] = {
                "url": f"https://{ansible_host}/rest/{restversion}/system/interfaces/{interface}"
            }

    return result