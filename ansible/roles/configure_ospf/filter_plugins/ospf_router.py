class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_ospf_router_config": aoscx_generate_ospf_router_config
        }

def aoscx_generate_ospf_router_config(all_vars):
    result = {
        "post": {},
        "put": {},
        "delete": {}
    }

    ansible_host = all_vars.get("ansible_host")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    router_ospf = all_vars.get("router_ospf", {})
    router_ospf_schema = all_vars.get("router_ospf_schema")
    router_ospf_instance_schema = router_ospf_schema.get("instance")
    router_ospf_post_attributes = all_vars.get("router_ospf_post_attributes")
    router_ospf_put_attributes = all_vars.get("router_ospf_put_attributes")
    get_ospf_routers = all_vars.get("get_ospf_routers")
    physical_interfaces = all_vars.get("physical_interfaces", {})
    vlan_interfaces = all_vars.get("vlan_interfaces", {})

    physical_ospf_interfaces = {
        interface: value
        for interface, value in physical_interfaces.items()
        if value.get("ip_ospf_process") != None 
        and value.get("ip_ospf_area") != None
        and value.get("routing")
    }

    vlan_ospf_interfaces = {
        interface: value
        for interface, value in vlan_interfaces.items()
        if value.get("ip_ospf_process") != None 
        and value.get("ip_ospf_area") != None
    }

    defaults = {
        key: value.get("default",) if value else None
        for key, value in router_ospf_instance_schema.items()
    }

    for router, value in router_ospf.items():
        value = value or {}

        ##########################  Repeat this for lag and VLAN interfaces  ##########################
        active_interfaces = {}

        for interface, config in physical_ospf_interfaces.items():
            if config.get("ip_ospf_process") == router:
                if not config.get("ip_ospf_passive", True):
                    active_interfaces[interface] = (
                        f"/rest/{restversion}/system/interfaces/{interface.replace('/', '%2F')}"
                    )

        for interface, config in vlan_ospf_interfaces.items():
            if config.get("ip_ospf_process") == router:
                if not config.get("ip_ospf_passive", True):
                    active_interfaces[interface] = (
                        f"/rest/{restversion}/system/interfaces/{interface.replace('/', '%2F')}"
                    )
        ################################################################################################

        config_attributes = {
            "active_interfaces": active_interfaces,
            "admin_router_id": value.get("router_id") or defaults.get("router_id") or "0.0.0.0",
            "auto_cost_ref_bw": value.get("reference_bandwidth") or defaults.get("reference_bandwidth") or 100000,
            "instance_tag": router,
            "passive_interface_default": value.get("passive_interface_default") or defaults.get("passive_interface_default") or False,
            "stub_router_adv": {
                "admin_set": False,
                "include_stub": False,
                "startup": value.get("max_metric_router_lsa_on_startup") or defaults.get("max_metric_router_lsa_on_startup") or 600
            }
        }

        vrf = value.get("vrf") or defaults.get("vrf")
        router_configured = get_ospf_routers.get(vrf, {}).get(str(router), {})

        if router_configured:
            compare = {
                key: router_configured[key]
                for key in router_ospf_put_attributes
                if key in router_configured
            }
            
        else:
            compare = None

        if not compare:
            post_body = {
                key: config_attributes[key]
                for key in router_ospf_post_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/ospf_routers"

            post = {
                "body": post_body,
                "url": url
            }

            result["post"][router] = post

        elif compare:
            put_body = {
                key: config_attributes[key]
                for key in router_ospf_put_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/ospf_routers/{router}"

            if compare != put_body:
                put = {
                    "body": put_body,
                    "url": url
                }

                result["put"][router] = put

    for vrf, routers in get_ospf_routers.items():
        for router in routers:
            desired = int(router) in router_ospf.keys()

            if not desired:
                result["delete"][router] = {
                    "url": f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/ospf_routers/{router}"
                }

    return result