#!/usr/bin/python3

import json
import sys


def replace_uid_recursive(d, type_name, new_uid):
    if isinstance(d, list):
        for item in d:
            replace_uid_recursive(item, type_name, new_uid)
    elif isinstance(d, dict):
        if 'datasource' in d and d['datasource'].get('type') == type_name:
            d['datasource']['uid'] = new_uid
        for key in d:
            replace_uid_recursive(d[key], type_name, new_uid)


def update_dashboard_uid(zabbix_uid, elasticsearch_uid, pm_uid, path):
    # Update the all *.json for monitoring dashboard.
    for dashboard in ["monitor", "kubernetes"]:
        with open(f'{path}/{dashboard}.json', 'r', encoding='utf-8') as file:
            dashboard_json = json.load(file)
        dashboard_json['id'] = None
        if dashboard == "monitor":
            replace_uid_recursive(dashboard_json,
                    "alexanderzobnin-zabbix-datasource", zabbix_uid)
            replace_uid_recursive(dashboard_json, "elasticsearch",
                    elasticsearch_uid)
        else:
            replace_uid_recursive(dashboard_json, "elasticsearch",
                                  elasticsearch_uid)
        with open(f'{path}/{dashboard}-updated.json',
                'w', encoding='utf-8') as file:
            json.dump({"dashboard": dashboard_json, "folderId": 0,
                    "overwrite": True}, file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    args = sys.argv[1:]
    update_dashboard_uid(args[0], args[1], args[2], args[3])

