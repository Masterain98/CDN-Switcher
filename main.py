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


#@repeat(every().day.at('00:00'))
@repeat(every(1).minutes)
def switch_to_off_peak_cdn():
    task_list = switch_to_off_peak_cdn_list.copy()
    print("=" * 20 + "\nStart switching to off-peak CDN")
    # 默认假设只有华为云 CDN，或无指定平台的 CDN （仅设置了 cname 值的 CDN）
    # 遍历 switch_to_off_peak_cdn_list 中所有的 PaaSTask 对象
    for current_task in task_list:
        allow_switch = False

        # 针对 华为 CDN 进行切换
        if current_task.cdn_account_type == "huaweicloud":
            # 华为云/ Huawei Cloud
            # 检查 CDN 帐号流量包剩余量是否足高于最低限制
            remaining_traffic = current_task.cdn_account.get_remaining_traffic()
            print("Current traffic package status: " + str(remaining_traffic))
            # 如果高于限制，则切换
            if remaining_traffic["china_off_peak_traffic_percent"] > current_task.traffic_package_floor_limit:
                allow_switch = True
            else:
                pass
        # 当没有指定的 CDN 服务商时，不做任何检测，直接更新 cname 解析值
        else:
            allow_switch = True

        if allow_switch:
            # 在 PaaSTask 对象和 Config.json 中 region 是一个列表，因此需要遍历
            # update_record_set_by_name_line 中 region 要求是一个字符串
            for region in current_task.region:
                current_task.dns_account.update_record_set_by_name_line(name=current_task.domain,
                                                                        target_line=region,
                                                                        record_type="CNAME",
                                                                        new_record_value=[current_task.cdn_cname])
            print("Switch to off peak CDN: " + current_task.domain + "\nTarget CDN cname: " + current_task.cdn_cname)
    print("Task Ended Successfully" + "\n" + "=" * 20)


#@repeat(every().day.at('18:00'))
#@repeat(every(1).minutes)
def switch_to_regular_cdn():
    task_list = switch_to_regular_cdn_list.copy()
    print("=" * 20 + "\nStart switching to regular CDN")
    for current_task in task_list:
        allow_switch = False
        remaining_traffic = current_task.cdn_account.get_remaining_traffic_percentage()
        if remaining_traffic > current_task.traffic_package_floor_limit:
            print("高于限制，切换")
            allow_switch = True
        else:
            print("剩余流量：" + str(remaining_traffic) +
                  " | 低于限制：" + str(current_task.traffic_package_floor_limit) + " | 不切换")
        if current_task.cdn_account_type == "huaweicloud":
            print("切换至华为云 CDN")
            # 华为云/ Huawei Cloud
        elif current_task.cdn_account_type == "qcloud":
            print("切换至腾讯云 CDN")
            # 腾讯云/ Qcloud/ Tencent Cloud
        elif current_task.cdn_account_type == "gcore":
            print("切换至 G-Core CDN")
            # G-Core CDN
        else:
            # Others
            print("未知 CDN 服务商，根据规则默认允许切换")
            allow_switch = True

        if allow_switch:
            print("Switch to regular CDN: " + current_task.domain + "\nTarget CDN cname: " + current_task.cdn_cname)
            # 在 PaaSTask 对象和 Config.json 中 region 是一个列表，因此需要遍历
            # update_record_set_by_name_line 中 region 要求是一个字符串
            for region in current_task.region:
                print("目标域名: " + current_task.domain + "\n目标解析记录: " + current_task.cdn_cname + "\n目标区域: " + region)
                current_task.dns_account.update_record_set_by_name_line(name=current_task.domain,
                                                                        target_line=region,
                                                                        record_type="CNAME",
                                                                        new_record_value=[current_task.cdn_cname])
    print("Task Ended Successfully" + "\n" + "=" * 20)


@repeat(every(90).minutes)
def switch_to_free_cdn():
    """
    切换到免费 CDN
    相比闲时CDN切换，switch_to_free_cdn 有一个更复杂的逻辑
    其参数中的列表包含的并不是目标 CDN 而是 fail-over CDN
    该方法会检查目标域名当前的 CDN 服务商，并获得其剩余流量包量
    当流量低于阈值时，则切换到 fail-over CDN
    :param task_list: 一个包含 PaaSTask 对象的列表
    该列表结构为 [ fail-over CDN 的 PaaSTask 对象, [Activate CDN 帐号对象, CDN 服务商名(str)], [Activate CDN 帐号对象, CDN 服务商名(str)]]
    :return:
    """
    task_list = switch_to_free_cdn_list.copy()
    print("=" * 20 + "\nStart timely traffic check")
    for current_task in task_list:
        current_PaaSTask = current_task[0]
        # 每一个 current_task 代表一个 CDN 域名
        current_cdn_status = current_PaaSTask.dns_account.describe_cdn_provider(name=current_PaaSTask.domain)
        # current_cdn_status 的结构为         {
        #             "default": default_line_cdn_provider,
        #             "CN": china_line_cdn_provider,
        #             "Abroad": abroad_line_cdn_provider
        #         }

        for i in range(len(current_task)):
            # i == 0 位置为 fail-over CDN 帐号对象
            if i > 0:
                this_cdn_type = current_task[i][1]
                if this_cdn_type in current_cdn_status["default"]:
                    # 如果该 CDN 帐号是默认 CDN 帐号，则不需要检查流量包剩余量
                    current_remaining_traffic_percent = current_task[i][0].get_remaining_traffic()
                    if current_remaining_traffic_percent < current_task[i][2]:
                        print("CDN Traffic Package is low, switch to fail-over CDN: " + current_PaaSTask.domain)
                        current_PaaSTask.dns_account.update_record_set_by_name_line(name=current_PaaSTask.domain,
                                                                                target_line="default-view",
                                                                                record_type="CNAME",
                                                                                new_record_value=[current_PaaSTask.cdn_cname])
                    else:
                        print(
                            "CDN Traffic Package is high, keep using default CDN at Default Line: " + current_PaaSTask.domain)
                        pass
                elif this_cdn_type in current_cdn_status["CN"]:
                    current_remaining_traffic_percent = current_task[i][0].get_remaining_traffic()
                    if current_remaining_traffic_percent < current_task[i][2]:
                        print("CDN Traffic Package is low, switch to fail-over CDN: " + current_PaaSTask.domain)
                        current_PaaSTask.dns_account.update_record_set_by_name_line(name=current_PaaSTask.domain,
                                                                                target_line="CN",
                                                                                record_type="CNAME",
                                                                                new_record_value=[current_PaaSTask.cdn_cname])
                    else:
                        print("CDN Traffic Package is high, keep using default CDN at CN Line: " + current_PaaSTask.domain)
                        pass
                elif this_cdn_type in current_cdn_status["Abroad"]:
                    current_remaining_traffic_percent = current_task[i][0].get_remaining_traffic()
                    if current_remaining_traffic_percent < current_task[i][2]:
                        print("CDN Traffic Package is low, switch to fail-over CDN: " + current_PaaSTask.domain)
                        current_PaaSTask.dns_account.update_record_set_by_name_line(name=current_PaaSTask.domain,
                                                                                target_line="Abroad",
                                                                                record_type="CNAME",
                                                                                new_record_value=[current_PaaSTask.cdn_cname])
                    else:
                        print(
                            "CDN Traffic Package is high, keep using default CDN at Aboard Line: " + current_PaaSTask.domain)
                        pass
            else:
                pass
    print("Task Ended Successfully" + "\n" + "=" * 20)


if __name__ == '__main__':
    with open("config.json", "r") as f:
        config = json.load(f)
    for task in config["task"]:
        domain = task["domain"]
        print("=" * 20 + "\nStart checking domain config: " + domain)
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
                print("\nGenerating Huawei Cloud CDN account")
                cdn_account = HuaweiCloudAccount(ak=task["cdn"][cdn_provider]["ak"], sk=task["cdn"][cdn_provider]["sk"])
                this_task = PaaSTask(domain=domain, dns_account=dns_account,
                                     cdn_cname=task["cdn"][cdn_provider]["cname"], cdn_account=cdn_account,
                                     cdn_account_type=cdn_provider, region=task["cdn"][cdn_provider]["region"],
                                     traffic_package_floor_limit=traffic_package_floor_limit)
            elif cdn_provider.lower() == "qcloud":
                print("\nGenerating QCloud CDN account")
                cdn_account = QCloudAccount(SecretId=task["cdn"][cdn_provider]["SecretId"],
                                            SecretKey=task["cdn"][cdn_provider]["SecretKey"])
                this_task = PaaSTask(domain=domain, dns_account=dns_account,
                                     cdn_cname=task["cdn"][cdn_provider]["cname"], cdn_account=cdn_account,
                                     cdn_account_type=cdn_provider, region=task["cdn"][cdn_provider]["region"],
                                     traffic_package_floor_limit=traffic_package_floor_limit)
            elif cdn_provider.lower() == "gcore":
                print("\nGenerating GCore CDN account")
                cdn_account = GCoreAccount(api_key=task["cdn"][cdn_provider]["api_key"])
                this_task = PaaSTask(domain=domain, dns_account=dns_account,
                                     cdn_cname=task["cdn"][cdn_provider]["cname"], cdn_account=cdn_account,
                                     cdn_account_type=cdn_provider, region=task["cdn"][cdn_provider]["region"],
                                     traffic_package_floor_limit=traffic_package_floor_limit)
            else:
                print("\nUnsupported DNS provider: " + cdn_provider)
                if task["cdn"][cdn_provider]["cname"] != "":
                    this_task = PaaSTask(domain=domain, dns_account=dns_account, region=task["cdn"][cdn_provider]["region"],
                                         cdn_cname=task["cdn"][cdn_provider]["cname"])
                else:
                    break

            if enable_off_peak_switch:
                if task["cdn"][cdn_provider]["off_peak_type"] == "off-peak":
                    switch_to_off_peak_cdn_list.append(this_task)
                    print("Find off-peak CDN: " + cdn_provider)
                elif task["cdn"][cdn_provider]["off_peak_type"] == "regular":
                    switch_to_regular_cdn_list.append(this_task)
                    print("Find regular CDN: " + cdn_provider)
                elif task["cdn"][cdn_provider]["off_peak_type"] == "all-time":
                    print("All time CDN provider: " + cdn_provider)
                else:
                    print("Error reading off peak CDN config")
                    break

            if task["cdn"][cdn_provider]["priority"] == "fail-over":
                fail_over_task_list = [this_task]
                for this_cdn in list(task["cdn"].keys()):
                    if task["cdn"][this_cdn]["priority"] == "active":
                        # 只有 CDN 服务商提供了查询流量的接口也可以加入以下的条件
                        if cdn_provider.lower() == "huaweicloud":
                            this_active_cdn_account = HuaweiCloudAccount(ak=task["cdn"][cdn_provider]["ak"],
                                                                         sk=task["cdn"][cdn_provider]["sk"])
                            fail_over_task_list.append(
                                [this_active_cdn_account, "huaweicloud", traffic_package_floor_limit])
                        elif cdn_provider.lower() == "qcloud":
                            this_active_cdn_account = QCloudAccount(SecretId=task["cdn"][cdn_provider]["SecretId"],
                                                                    SecretKey=task["cdn"][cdn_provider]["SecretKey"])
                            fail_over_task_list.append([this_active_cdn_account, "qcloud", traffic_package_floor_limit])
                        elif cdn_provider.lower() == "gcore":
                            this_active_cdn_account = GCoreAccount(api_key=task["cdn"][cdn_provider]["api_key"])
                            fail_over_task_list.append([this_active_cdn_account, "gcore", traffic_package_floor_limit])
                        else:
                            pass
                switch_to_free_cdn_list.append(fail_over_task_list)
    print("\nRead config file successfully" + "\n" + "=" * 20)

    while True:
        schedule.run_pending()
        time.sleep(1)
