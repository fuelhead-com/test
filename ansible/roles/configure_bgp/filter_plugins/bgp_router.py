from ansible.template import Templar

class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_bgp_router_config": aoscx_generate_bgp_router_config
        }

def aoscx_generate_bgp_router_config(all_vars):
    templar = Templar(loader=None, variables=all_vars)

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
    router_bgp = all_vars.get("router_bgp", {}) or {}
    router_bgp_schema = all_vars.get("router_bgp_schema", {}).get("asn", {})
    post_attributes = all_vars.get("bgp_router_post_attributes")
    put_attributes = all_vars.get("bgp_router_put_attributes")
    get_bgp_routers = all_vars.get("get_bgp_routers")

    defaults = {
        key: value.get("default",) if value else None
        for key, value in router_bgp_schema.items()
    }

    timer_defaults = {
        key: value.get("default",) if value else None
        for key, value in router_bgp_schema["timers"].items()
    }

    defaults["timers"] = timer_defaults

    result["defaults"] = defaults

    for rtr, value in router_bgp.items():
        value = value or {}
        vrf = value.get("vrf", defaults.get("vrf"))

        # Get router_id from global variables and strip of cidr
        router_id = templar.template(value.get("router_id", defaults.get("router_id")))
        router_id = router_id.split("/", 1)[0] if router_id else None

        config_attributes = {
            "always_compare_med": value.get("always_compare_med", defaults.get("always_compare_med")),
            "asn": rtr,
            "bestpath_as_path_multipath_relax": value.get("bestpath_as_path_multipath_relax", defaults.get("bestpath_as_path_multipath_relax")),
            "deterministic_med": value.get("deterministic_med", defaults.get("deterministic_med")),
            "protocol_disable": not value.get("enable", defaults.get("enable", False)),
            "log_neighbor_changes": value.get("log_neighbor_changes", defaults.get("log_neighbor_changes")),
            "maximum_paths": {
                "all-afs": value.get("maximum_paths", defaults.get("maximum_paths"))
            },
            "router_id": router_id,
            "timers": {
                "connect-retry": value.get("timers", {}).get("connect-retry", defaults.get("timers", {}).get("connect-retry")),
                "holdtime": value.get("timers", {}).get("holdtime", defaults.get("timers", {}).get("holdtime")),
                "keepalive": value.get("timers", {}).get("keepalive", defaults.get("timers", {}).get("keepalive"))
            },
            "vrf": vrf
        }

        result["config_attributes"][rtr] = config_attributes

        bgp_router_configured = str(rtr) in get_bgp_routers.get(vrf, {}).keys()

        if bgp_router_configured:
            rtr_config = get_bgp_routers[vrf][str(rtr)]

            compare = {
                key: rtr_config[key]
                for key in put_attributes
                if key in rtr_config
            }

            result["compare"][rtr] = compare

            put_body = {
                key: config_attributes[key]
                for key in put_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/bgp_routers/{rtr}"

            if compare != put_body:
                put = {
                    "body": put_body,
                    "url": url
                }

                result["put"][rtr] = put

        else:
            post_body = {
                key: config_attributes[key]
                for key in post_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/bgp_routers"

            post = {
                "body": post_body,
                "url": url
            }

            result["post"][rtr] = post

    for vrf, bgp_routers in get_bgp_routers.items():
        bgp_routers = bgp_routers or {}

        for rtr in bgp_routers:
            if int(rtr) not in router_bgp.keys():

                result["delete"][rtr] = {
                    "url": f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/bgp_routers/{rtr}"
                }

    return result