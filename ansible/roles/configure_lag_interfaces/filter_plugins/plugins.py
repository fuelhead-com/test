class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_lag_interface_config": aoscx_generate_lag_interface_config
        }

def aoscx_generate_lag_interface_config(all_vars):

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
    lag_interfaces = all_vars.get("lag_interfaces", {}) or {}
    lag_interfaces_schema = all_vars.get("lag_interfaces_schema", {}).get("interface")
    post_attributes = all_vars.get("lag_interfaces_post_attributes")
    put_attributes = all_vars.get("lag_interfaces_put_attributes")
    get_lag_interfaces = all_vars.get("get_lag_interfaces", {})

    defaults = {
        key: value.get("default",) if value else None
        for key, value in lag_interfaces_schema.items()
    }

    result["defaults"] = defaults


    for interface, value in lag_interfaces.items():
        routing = value.get("routing", defaults.get("routing")) is not False

        ip4_address = None

        description = value.get("description", defaults.get("description", None))

        interfaces = value.get("interfaces", defaults.get("interfaces", None))

        ip_mtu = value.get("ip_mtu", defaults.get("ip_mtu", 1500))

        lacp_mode = value.get("lacp_mode", defaults.get("lacp_mode", "active"))

        multi_chassis = value.get("multi_chassis", defaults.get("multi_chassis", False))

        lacp = "active"

        vlan_mode = None

        vlan_tag_body = None

        vlan_trunks = {}

        vrf = None

        stp_config = {
            "admin_edge_port_enable": False,
            "bpdu_filter_enable": False,
            "bpdu_guard_enable": False,
            "bpdus_rx_disable": False,
            "bpdus_tx_disable": False,
            "link_type": "auto",
            "loop_guard_enable": False,
            "port_priority": 128,
            "protocol_migration_disable": False,
            "restricted_port_role_disable": False,
            "restricted_port_tcn_disable": False,
            "root_guard_enable": False,
            "rpvst_filter_enable": False,
            "rpvst_guard_enable": False
        }

        admin = "up" if value.get("enabled", defaults.get("enabled", False)) else "down"

        if not multi_chassis:
            lacp = lacp_mode

        if interfaces is not None:
            interfaces = {
                key: f"/rest/{restversion}/system/interfaces/{key.replace('/', '%2F')}"
                for key in value.get("interfaces", [])
            }

        lacp_time = "fast" if value.get("lacp_rate", defaults.get("lacp_rate", "slow")) == "fast" else "slow"
        mclag_enabled = value.get("multi_chassis", defaults.get("multi_chassis", False)) == True

        other_config = {
            "lacp-time": lacp_time,
            "mclag_enabled": mclag_enabled
        }

        qos_config = {
            **({"cos_override": cos} if (cos := value.get("qos_cos", defaults.get("qos_cos"))) is not None else {}),
            **({"dscp_override": dscp} if (dscp := value.get("qos_dscp", defaults.get("qos_dscp"))) is not None else {}),
            "qos_trust": value.get("qos_trust", defaults.get("qos_trust")),
        }



        if routing:
            ip4_address = value.get("ipv4_address", defaults.get("ipv4_address", None))

        else:
            stp_config = {
                "admin_edge_port_enable": value.get("stp_port_type", defaults.get("stp_port_type")) == "admin-edge",
                "bpdu_filter_enable": value.get("stp_bpdu_filter", defaults.get("stp_bpdu_filter")) or False,
                "bpdu_guard_enable": value.get("stp_bpdu_guard", defaults.get("stp_bpdu_guard")) or False,
                "bpdus_rx_disable": False,
                "bpdus_tx_disable": False,
                "link_type": "auto",
                "loop_guard_enable": value.get("stp_loop_guard", defaults.get("stp_loop_guard")) or False,
                "port_priority": 128,
                "protocol_migration_disable": False,
                "restricted_port_role_disable": False,
                "restricted_port_tcn_disable": False,
                "root_guard_enable": value.get("stp_root_guard", defaults.get("stp_root_guard")) or False,
                "rpvst_filter_enable": False,
                "rpvst_guard_enable": False
            }

            if value.get("switchport_mode", defaults.get("switchport_mode")) == "access":
                vlan_mode = "access"
            else:
                vlan_mode = (
                    "native-tagged" 
                    if value.get("trunk_native_tagged", defaults.get("trunk_native_tagged")) 
                    else "native-untagged"
                )

            vlan_tag = (
                value.get("access_vlan", defaults.get("access_vlan"))
                if value.get("switchport_mode", defaults.get("switchport_mode")) == "access"
                else value.get("trunk_native_vlan", defaults.get("trunk_native_vlan"))
            )

            vlan_tag_body = {
                str(vlan_tag): f"/rest/{restversion}/system/vlans/{vlan_tag}"
            }

            trunk_allowed_vlan = value.get("trunk_allowed_vlan", defaults.get("trunk_allowed_vlan"))
            trunk_allowed_vlan_is_list = isinstance(trunk_allowed_vlan, list) and all(type(x) is int for x in trunk_allowed_vlan)

            if vlan_mode  != "access" and trunk_allowed_vlan_is_list:
                vlan_trunks = {
                    str(key): f"/rest/{restversion}/system/vlans/{key}"
                    for key in value.get("trunk_allowed_vlan", defaults.get("trunk_allowed_vlan"))
                }
        
        config_attributes = {
            "description": description,
            "admin": admin,
            "interfaces": interfaces,
            "ip4_address": ip4_address,
            "ip_mtu": ip_mtu,
            "lacp": lacp,
            "name": interface,
            "other_config": other_config,
            "qos_config": qos_config,
            "routing": routing,
            "stp_config": stp_config,
            "type": "lag",
            "vlan_mode": vlan_mode,
            "vlan_tag": vlan_tag_body,
            "vlan_trunks": vlan_trunks,
            "vrf": vrf
        }

        result["config_attributes"][interface] = config_attributes

        interface_configured = interface in get_lag_interfaces.keys()

        if interface_configured:
            interface_config = get_lag_interfaces[interface]

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

    for interface in get_lag_interfaces.keys():
        if interface not in lag_interfaces.keys():

            result["delete"][interface] = {
                "url": f"https://{ansible_host}/rest/{restversion}/system/interfaces/{interface}"
            }

    return result