from ansible.template import Templar
from urllib.parse import quote

class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_bgp_neighbor_config": aoscx_generate_bgp_neighbor_config
        }

def aoscx_generate_bgp_neighbor_config(all_vars):
    templar = Templar(loader=None, variables=all_vars)

    result = {
        "config_attributes": {},
        "compare": {},
        "defaults": {},
        "post": {},
        "put": {},
        "delete": {}
    }

    ansible_host = all_vars.get("ansible_host")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    router_bgp = all_vars.get("router_bgp", {}) or {}
    bgp_neighbor_schema = all_vars.get("bgp_neighbor_schema", {}).get("neighbor", {})
    bgp_neighbor_post_attributes = all_vars.get("bgp_neighbor_post_attributes")
    bgp_neighbor_put_attributes = all_vars.get("bgp_neighbor_put_attributes")
    bgp_neighbor_peer_group_post_attributes = all_vars.get("bgp_neighbor_peer_group_post_attributes")
    bgp_neighbor_peer_group_put_attributes = all_vars.get("bgp_neighbor_peer_group_put_attributes")
    get_bgp_neighbors = all_vars.get("get_bgp_neighbors")
    bgp_key = all_vars.get("bgp_key")

    defaults = {
        key: value.get("default",) if value else None
        for key, value in bgp_neighbor_schema.items()
    }

    timer_defaults = {
        key: value.get("default",) if value else None
        for key, value in bgp_neighbor_schema["timers"].items()
    }

    activate_defaults = {
        key: value.get("default",) if value else None
        for key, value in bgp_neighbor_schema["activate"].items()
    }

    route_reflector_client_defaults = {
        key: value.get("default",) if value else None
        for key, value in bgp_neighbor_schema["route_reflector_client"].items()
    }

    send_community_defaults = {
        key: value.get("default",) if value else None
        for key, value in bgp_neighbor_schema["send_community"].items()
    }

    defaults["timers"] = timer_defaults

    defaults["activate"] = activate_defaults

    defaults["route_reflector_client"] = route_reflector_client_defaults

    defaults["send_community"] = send_community_defaults

    result["defaults"] = defaults

    for rtr, value in router_bgp.items():
        value = value or {}
        neighbors = value.get("neighbors", {})
        vrf = value.get("vrf", defaults.get("vrf"))

        for neighbor, neighbor_config in neighbors.items():
            neighor_configured = neighbor in get_bgp_neighbors.get(vrf, {}).get(str(rtr), {}).keys()
            is_peer_group = neighbor_config.get("is_peer_group", defaults.get("is_peer_group", False))
            local_if_name = neighbor_config.get("local_interface", defaults.get("local_interface"))

            if local_if_name:
                local_if_name_url_encoded = quote(local_if_name, safe="")

                local_interface = {
                    local_if_name: f"/rest/{restversion}/system/interfaces/{local_if_name_url_encoded}"
                }
            else:
                local_interface = None


            if not is_peer_group:
                bgp_peer_group = {
                    neighbor_config.get('bgp_peer_group'): f"/rest/{restversion}/system/vrfs/default/bgp_routers/{rtr}/bgp_neighbors/{neighbor_config.get('bgp_peer_group')}" 
                }
            else:
                bgp_peer_group = None

            # Check if bgp password needs update
            password = templar.template(neighbor_config.get("password", defaults.get("password")))
            
            if neighbor_config.get("password"):
                if neighor_configured:
                    get_neighbor_config = get_bgp_neighbors[vrf][str(rtr)][neighbor]

                    if neighbor_config.get("replace_password"):
                        password = templar.template(neighbor_config.get("password", defaults.get("password")))
                    else:
                        if get_neighbor_config.get("password"):
                            password = get_neighbor_config.get("password")

            config_attributes = {
                "ip_or_ifname_or_group_name": neighbor,
                "activate": neighbor_config.get("activate", defaults.get("activate")),
                "bfd_enable": neighbor_config.get("bfd_enable", defaults.get("bfd_enable")),
                "bgp_peer_group": bgp_peer_group,
                "description": neighbor_config.get("description", defaults.get("description")),
                "is_peer_group": is_peer_group,
                "local_interface": local_interface,
                "password": password,
                "remote_as": neighbor_config.get("remote_as", defaults.get("remote_as")),
                "route_reflector_client": neighbor_config.get("route_reflector_client", defaults.get("route_reflector_client")),
                "send_community": neighbor_config.get("send_community", defaults.get("send_community")),
                "shutdown": not neighbor_config.get("enable", defaults.get("enable", False)),
                "timers": neighbor_config.get("timers", defaults.get("timers"))
            }

            result["config_attributes"][f"{neighbor}_{rtr}"] = config_attributes

            # neighor_configured = neighbor in get_bgp_neighbors.get(vrf, {}).get(str(rtr), {}).keys()

            if neighor_configured:
                neighbor_config = get_bgp_neighbors[vrf][str(rtr)][neighbor]

                # if not neighbor_config.get("replace_password"):
                #     password = neighbor_config.get("password")
                # else:
                #     password = templar.template(neighbor_config.get("password", defaults.get("password")))

                # config_attributes["password"] = password

                result["config_attributes"][f"{neighbor}_{rtr}"] = config_attributes

                if not is_peer_group:
                    compare = {
                        key: neighbor_config[key]
                        for key in bgp_neighbor_put_attributes
                        if key in neighbor_config
                    }

                    put_body = {
                        key: config_attributes[key]
                        for key in bgp_neighbor_put_attributes
                        if key in config_attributes
                    }

                else:
                    compare = {
                        key: neighbor_config[key]
                        for key in bgp_neighbor_peer_group_put_attributes
                        if key in neighbor_config
                    }

                    put_body = {
                        key: config_attributes[key]
                        for key in bgp_neighbor_peer_group_put_attributes
                        if key in config_attributes
                    }
                    
                result["compare"][f"{neighbor}_{rtr}"] = compare

                url = f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/bgp_routers/{rtr}/bgp_neighbors/{neighbor}"

                if compare != put_body:
                    put = {
                        "body": put_body,
                        "url": url
                    }

                    result["put"][f"{neighbor}_{rtr}"] = put

            else:
                if not is_peer_group:

                    post_body = {
                        key: config_attributes[key]
                        for key in bgp_neighbor_post_attributes
                        if key in config_attributes
                    }

                else:
                    post_body = {
                        key: config_attributes[key]
                        for key in bgp_neighbor_peer_group_post_attributes
                        if key in config_attributes
                    }

                url = f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/bgp_routers/{rtr}/bgp_neighbors"

                post = {
                    "body": post_body,
                    "url": url
                }

                result["post"][f"{neighbor}_{rtr}"] = post

    for vrf, routers in get_bgp_neighbors.items():
        routers = routers or {}

        for rtr, value in routers.items():
            value = value or {}

            for neighbor in value:
                if neighbor not in router_bgp.get(int(rtr), {}).get("neighbors", {}).keys():

                    result["delete"][f"{neighbor}_{rtr}"] = {
                        "url": f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/bgp_routers/{rtr}/bgp_neighbors/{neighbor}"
                    }

    return result