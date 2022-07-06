from PublicCloudAPI.HuaweiCloud import HuaweiCloudAccount
from PublicCloudAPI.QCloud import QCloudAccount
from PublicCloudAPI.GCore import GCoreAccount
from PaaSTask import PaaSTask

import time
import schedule
import json
from schedule import every, repeat

switch_to_off_peak_cdn_list = []
switch_to_regular_cdn_list = []
switch_to_free_cdn_list = []


@repeat(every().day.at('00:00'))
def switch_to_off_peak_cdn(task_list: list):
    # 默认假设只有华为云CDN
    for cdn_task in task_list:
        pass


@repeat(every().day.at('18:00'))
def switch_to_regular_cdn(task_list: list):
    for cdn_task in task_list:
        return True


@repeat(every(5).minutes)
def switch_to_free_cdn(task_list: list):
    for cdn_task in task_list:
        return True


if __name__ == '__main__':
    with open("config.json", "r") as f:
        config = json.load(f)
    for task in config["task"]:
        domain = task["domain"]
        enable_off_peak_switch = task["enable_off_peak_switch"]
        enable_traffic_package_switch = task["enable_traffic_package_switch"]
        traffic_package_floor_limit = task["traffic_package_floor_limit"]
        dns_provider = list(task["dns"].keys())[0]
        if dns_provider.lower() == "huaweicloud":
            dns_account = HuaweiCloudAccount(ak=task["dns"][dns_provider]["ak"], sk=task["dns"][dns_provider]["sk"])
        else:
            print("Unsupported DNS provider: " + dns_provider)
            break

        for cdn_provider in list(task["cdn"].keys()):
            if cdn_provider.lower() == "huaweicloud":
                cdn_account = HuaweiCloudAccount(ak=task["cdn"][cdn_provider]["ak"], sk=task["cdn"][cdn_provider]["sk"])
                this_task = PaaSTask(domain=domain, dns_account=dns_account,
                                     cdn_cname=task["cdn"][cdn_provider]["cname"],
                                     cdn_account=cdn_account, cdn_account_type=cdn_provider)
            elif cdn_provider.lower() == "qcloud":
                cdn_account = QCloudAccount(SecretId=task["cdn"][cdn_provider]["SecretId"],
                                            SecretKey=task["cdn"][cdn_provider]["SecretKey"])
                this_task = PaaSTask(domain=domain, dns_account=dns_account,
                                     cdn_cname=task["cdn"][cdn_provider]["cname"],
                                     cdn_account=cdn_account, cdn_account_type=cdn_provider)
            elif cdn_provider.lower() == "gcore":
                cdn_account = GCoreAccount(api_key=task["cdn"][cdn_provider]["api_key"])
                this_task = PaaSTask(domain=domain, dns_account=dns_account,
                                     cdn_cname=task["cdn"][cdn_provider]["cname"],
                                     cdn_account=cdn_account, cdn_account_type=cdn_provider)
            else:
                print("Unsupported DNS provider: " + dns_provider)
                if task["cdn"][cdn_provider]["cname"] != "":
                    this_task = PaaSTask(domain=domain, dns_account=dns_account,
                                         cdn_cname=task["cdn"][cdn_provider]["cname"])
                else:
                    break

            if enable_off_peak_switch:
                if task["cdn"][cdn_provider]["off_peak_type"] == "off-peak":
                    switch_to_off_peak_cdn_list.append(this_task)
                elif task["cdn"][cdn_provider]["off_peak_type"] == "regular":
                    switch_to_regular_cdn_list.append(this_task)
                elif task["cdn"][cdn_provider]["off_peak_type"] == "all-time":
                    print("All time CDN provider:: " + dns_provider)
                else:
                    print("Error reading off peak CDN config")
                    break

            if task["cdn"][cdn_provider]["priority"] == "fail-over":
                switch_to_free_cdn_list.append(this_task)

    while True:
        schedule.run_pending()
        time.sleep(1)
