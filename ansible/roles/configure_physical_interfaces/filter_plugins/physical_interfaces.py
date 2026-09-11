class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_physical_interface_config": aoscx_generate_physical_interface_config
        }

def aoscx_generate_physical_interface_config(all_vars):

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
    physical_interfaces = all_vars.get("physical_interfaces", {}) or {}
    physical_interfaces_schema = all_vars.get("physical_interfaces_schema", {}).get("interface")
    put_attributes = all_vars.get("physical_interfaces_put_attributes")
    get_physical_interfaces = all_vars.get("get_physical_interfaces", {})

    # List of interfacse that are members of lag interfaces
    interfaces_in_lags = [
        interface
        for obj in lag_interfaces.values()
        for interface in obj.get("interfaces", [])
    ]

    result["interfaces_in_lags"] = interfaces_in_lags

    defaults = {
        key: value.get("default",) if value else None
        for key, value in physical_interfaces_schema.items()
    }

    result["defaults"] = defaults

    for interface, value in physical_interfaces.items():

        routing = value.get("routing", defaults.get("routing")) is not False

        description = value.get("description", defaults.get("description"))

        mtu = value.get("mtu", defaults.get("mtu") or 1500)

        ip_mtu = 1500

        ip4_address = None

        ospf_auth_keychain = None

        ospf_bfd = "default"

        ospf_if_shutdown = False

        ospf_if_type = None

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
        
        qos_config = {
            **({"cos_override": cos} if (cos := value.get("qos_cos", defaults.get("qos_cos"))) is not None else {}),
            **({"dscp_override": dscp} if (dscp := value.get("qos_dscp", defaults.get("qos_dscp"))) is not None else {}),
            **({"qos_trust": qos_trust} if (qos_trust := value.get("qos_trust", defaults.get("qos_trust"))) is not None else {})
        }

        admin = "up" if value.get("enabled", defaults.get("enabled", False)) else "down"
        
        user_config = {
            "admin": admin,
            "error_control": "auto",
            "interpacket_gap": "default",
            "leader_follower": "preferred-leader",
            "link_clock_tolerance": "wide",
            "link_state_snmp_if_mib_trap": True,
            "link_state_snmp_trap": True,
            **({"mtu": mtu} if (mtu := mtu) is not None else {}),
            "pause_override": False,
            "split_count": "4"
        }

        vlan_mode = None

        vlan_tag_body = None

        vlan_trunks = {}

        vrf = None

        if routing:
            vlan_tag = None

            ip4_address = value.get("ipv4_address", defaults.get("ipv4_address") or None)

            ip_mtu = value.get("ip_mtu", defaults.get("ip_mtu") or 1500)

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


            vrf_name = value.get("vrf", defaults.get("vrf")) or "default"

            if vrf_name != "default":
                vrf = {
                    vrf_name: f"/rest/{restversion}/system/vrfs/{vrf_name}"
                }

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


        # COnfiguration attributes for physical interfaces that are not members of lags
        if interface not in interfaces_in_lags:
            config_attributes = {
                "admin": admin,
                "description": description,
                "ip4_address": ip4_address,
                "ip_mtu": ip_mtu,
                "name": interface,
                "ospf_auth_keychain": ospf_auth_keychain,
                "ospf_bfd": ospf_bfd,
                "ospf_if_shutdown": ospf_if_shutdown,
                "ospf_if_type": ospf_if_type,
                "qos_config": qos_config,
                "routing": routing,
                "stp_config": stp_config,
                "type": "system",
                "user_config": user_config,
                "vlan_mode": vlan_mode,
                "vlan_tag": vlan_tag_body,
                "vlan_trunks": vlan_trunks,
                "vrf": vrf
            }

        else:
            # Configuration attributes för lag mmember interfaces
            config_attributes = {
                "description": description,
                "user_config": user_config
            }

        result["config_attributes"][interface] = config_attributes

        interface_configured = interface in get_physical_interfaces.keys()

        if interface_configured:
            interface_config = get_physical_interfaces[interface]

            compare = {
                key: interface_config[key]
                for key in put_attributes
                if key in config_attributes
            }

            result["compare"][interface] = compare

            put_body = {
                key: config_attributes[key]
                for key in put_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/interfaces/{interface.replace('/', '%2F')}"

            if compare != put_body:
                put = {
                    "body": put_body,
                    "url": url
                }

                result["put"][interface] = put

    return result