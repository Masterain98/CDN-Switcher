# coding: utf-8

from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkdns.v2.region.dns_region import DnsRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkdns.v2 import *

from huaweicloudsdkcore.auth.credentials import GlobalCredentials
from huaweicloudsdkcdn.v1.region.cdn_region import CdnRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkcdn.v1 import *

from huaweicloudsdkcore.auth.credentials import GlobalCredentials
from huaweicloudsdkbss.v2.region.bss_region import BssRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkbss.v2 import *

from log_printer import class_log_printer
import datetime
import json
import re


class HuaweiCloudAccount:
    def __init__(self, ak, sk, region="ap-southeast-1"):
        """
        :param ak: Access Key ID
        :param sk: Secret Access Key
        """
        self.__ak = ak
        self.__sk = sk
        self.__region = region

        self.__credentials = BasicCredentials(ak, sk)
        self.__global_credentials = GlobalCredentials(ak, sk)

    """
    DNS API Starts here
    """

    @class_log_printer
    def get_record_id_by_name(self, name):
        """
            # This is a generic function provided by HuaweiCloud
            :param zone_id: Zone ID
            :param name: Record name
            :return: Record ID
        """
        result_recordsets = []

        client = DnsClient.new_builder() \
            .with_credentials(self.__credentials) \
            .with_region(DnsRegion.value_of(self.__region)) \
            .build()

        try:
            request = ListRecordSetsWithLineRequest()
            request.name = name
            response = client.list_record_sets_with_line(request)
            response = json.loads(str(response))
            for record in response["recordsets"]:
                if record["name"] == name:
                    result_recordsets.append(record)
            return {
                "links": {
                    "self": "https://dns.myhuaweicloud.com/v2.1/recordsets?" + name
                },
                "recordsets": result_recordsets
            }

        except exceptions.ClientRequestException as e:
            print(e.status_code)
            print(e.request_id)
            print(e.error_code)
            print(e.error_msg)


    @class_log_printer
    def get_zone_id_by_name(self, name):
        """
        # Get zone ID by zone name
        :param name: Zone name
        :return: Zone ID
        """
        client = DnsClient.new_builder() \
            .with_credentials(self.__credentials) \
            .with_region(DnsRegion.value_of(self.__region)) \
            .build()

        try:
            request = ListRecordSetsWithLineRequest()
            request.name = name
            response = client.list_record_sets_with_line(request)
            response = json.loads(str(response))
            if response["metadata"]["total_count"] == 0:
                return None
            else:
                return response["recordsets"][0]["zone_id"]
        except exceptions.ClientRequestException as e:
            print(e.status_code)
            print(e.request_id)
            print(e.error_code)
            print(e.error_msg)
            return None

    def describe_cdn_provider(self, name):
        default_line_cdn_provider = []
        china_line_cdn_provider = []
        abroad_line_cdn_provider = []

        record_sets = self.get_record_id_by_name(name)["recordsets"]
        for record in record_sets:
            if record["type"] == "CNAME":
                for value in record["records"]:
                    if "aicdn.com" in value:
                        this_cdn_provider = "upyun"
                    elif "gcdn.co" in value:
                        this_cdn_provider = "gcore"
                    elif re.search(r"cdnhwc(\d)+.cn", value) is not None:
                        this_cdn_provider = "huaweicloud"
                    else:
                        this_cdn_provider = "Unknown:" + value

                    if record["line"] == "default_view":
                        default_line_cdn_provider.append(this_cdn_provider)
                    elif record["line"] == "CN":
                        china_line_cdn_provider.append(this_cdn_provider)
                    elif record["line"] == "Abroad":
                        abroad_line_cdn_provider.append(this_cdn_provider)
                    else:
                        print("Unknown line")

        print("Default line CDN provider: " + str(default_line_cdn_provider))
        print("China line CDN provider: " + str(china_line_cdn_provider))
        print("Abroad line CDN provider: " + str(abroad_line_cdn_provider))
        return {
            "default": default_line_cdn_provider,
            "CN": china_line_cdn_provider,
            "Abroad": abroad_line_cdn_provider
        }

    @class_log_printer
    def delete_records_set_by_id(self, recordset_id, zone_id):
        client = DnsClient.new_builder() \
            .with_credentials(self.__credentials) \
            .with_region(DnsRegion.value_of(self.__region)) \
            .build()

        try:
            request = DeleteRecordSetsRequest()
            request.zone_id = zone_id
            request.recordset_id = recordset_id
            response = client.delete_record_sets(request)
            return json.loads(str(response))
        except exceptions.ClientRequestException as e:
            print(e.status_code)
            print(e.request_id)
            print(e.error_code)
            print(e.error_msg)
            return None

    @class_log_printer
    def get_record_sets_id_by_name(self, name, line=None, zone_id=None):
        record_id_list = []
        if zone_id is None:
            zone_id = self.get_zone_id_by_name(name)
        client = DnsClient.new_builder() \
            .with_credentials(self.__credentials) \
            .with_region(DnsRegion.value_of(self.__region)) \
            .build()

        try:
            request = ShowRecordSetByZoneRequest()
            request.zone_id = zone_id
            request.name = name
            response = json.loads(str(client.show_record_set_by_zone(request)))["recordsets"]
            for this_record in response:
                if line is not None:
                    if this_record["line"].lower() == line.lower():
                        record_id_list.append(this_record["id"])
            return record_id_list
        except exceptions.ClientRequestException as e:
            print(e.status_code)
            print(e.request_id)
            print(e.error_code)
            print(e.error_msg)
            return None

    @class_log_printer
    def delete_records_set_by_name(self, name, zone_id=None):
        if zone_id is None:
            zone_id = self.get_zone_id_by_name(name)
        record_id_list = self.get_record_sets_id_by_name(name=name, zone_id=zone_id)
        for record_id in record_id_list:
            client = DnsClient.new_builder() \
                .with_credentials(self.__credentials) \
                .with_region(DnsRegion.value_of(self.__region)) \
                .build()

            try:
                request = DeleteRecordSetsRequest()
                request.zone_id = zone_id
                request.recordset_id = record_id
                response = client.delete_record_sets(request)
                return json.loads(str(response))
            except exceptions.ClientRequestException as e:
                print(e.status_code)
                print(e.request_id)
                print(e.error_code)
                print(e.error_msg)
                return None

    @class_log_printer
    def update_record_set_by_id(self, name: str, record_type: str, new_record_value: list, zone_id: str,
                                recordset_id: str):
        client = DnsClient.new_builder() \
            .with_credentials(self.__credentials) \
            .with_region(DnsRegion.value_of(self.__region)) \
            .build()

        try:
            request = UpdateRecordSetsRequest()
            request.zone_id = zone_id
            request.recordset_id = recordset_id
            listUpdateRecordSetsReqRecordsbody = new_record_value
            request.body = UpdateRecordSetsReq(
                records=listUpdateRecordSetsReqRecordsbody,
                type=record_type,
                name=name
            )
            response = client.update_record_sets(request)
            return json.loads(str(response))
        except exceptions.ClientRequestException as e:
            print(e.status_code)
            print(e.request_id)
            print(e.error_code)
            print(e.error_msg)
            return None

    @class_log_printer
    def update_record_set_by_name_line(self, name: str, target_line: str, new_record_value: list, record_type: str):
        result_list = []
        zone_id = self.get_zone_id_by_name(name)
        record_id_list = self.get_record_sets_id_by_name(name=name, line=target_line, zone_id=zone_id)
        if len(record_id_list) == 0:
            raise AttributeError("No record found")
        for record_id in record_id_list:
            result_list.append(
                self.update_record_set_by_id(name=name, record_type=record_type, new_record_value=new_record_value,
                                             zone_id=zone_id, recordset_id=record_id))
        if len(result_list) > 0:
            print("Successfully updated record '" + name + "' with line " + target_line)
        return result_list

    """
    CDN API Starts here
    """

    def cdn_client_generator(self):
        try:
            client = CdnClient.new_builder() \
                .with_credentials(self.__global_credentials) \
                .with_region(CdnRegion.value_of(self.__region)) \
                .build()
        except KeyError:
            try:
                client = CdnClient.new_builder() \
                    .with_credentials(self.__global_credentials) \
                    .with_region(CdnRegion.value_of("ap-southeast-1")) \
                    .build()
            except Exception:
                raise AttributeError("No credentials found")
        print("CDN API credentials generated successfully")
        return client

    @class_log_printer
    def get_cdn_quota(self):
        client = self.cdn_client_generator()

        try:
            request = ShowQuotaRequest()
            response = client.show_quota(request)
            return json.loads(str(response))
        except exceptions.ClientRequestException as e:
            print(e.status_code)
            print(e.request_id)
            print(e.error_code)
            print(e.error_msg)
            return None

    @class_log_printer
    def cdn_list_domains(self):
        client = self.cdn_client_generator()

        try:
            request = ListDomainsRequest()
            response = client.list_domains(request)
            return json.loads(str(response))
        except exceptions.ClientRequestException as e:
            print(e.status_code)
            print(e.request_id)
            print(e.error_code)
            print(e.error_msg)
            return None

    def get_cdn_domain_id_by_name(self, name: str):
        all_domains_list = self.cdn_list_domains()
        for domain in all_domains_list["domains"]:
            if domain["domain_name"] == name:
                return domain["id"]
        return None

    def disable_cdn_domain_by_id(self, domain_id: str):
        client = self.cdn_client_generator()
        try:
            request = DisableDomainRequest()
            request.domain_id = domain_id
            response = client.disable_domain(request)
            return json.loads(str(response))
        except exceptions.ClientRequestException as e:
            print(e.status_code)
            print(e.request_id)
            print(e.error_code)
            print(e.error_msg)
            return None

    def disable_cdn_domain_by_name(self, name: str):
        domain_id = self.get_cdn_domain_id_by_name(name)
        if domain_id is None:
            raise AttributeError("No domain found")
        return self.disable_cdn_domain_by_id(domain_id)

    def enable_cdn_domain_by_id(self, domain_id: str):
        client = self.cdn_client_generator()
        try:
            request = EnableDomainRequest()
            request.domain_id = domain_id
            response = client.enable_domain(request)
            return json.loads(str(response))
        except exceptions.ClientRequestException as e:
            print(e.status_code)
            print(e.request_id)
            print(e.error_code)
            print(e.error_msg)
            return None

    def enable_cdn_domain_by_name(self, name: str):
        domain_id = self.get_cdn_domain_id_by_name(name)
        if domain_id is None:
            raise AttributeError("No domain found")
        return self.enable_cdn_domain_by_id(domain_id)

    def get_all_free_resource(self):
        client = BssClient.new_builder() \
            .with_credentials(self.__global_credentials) \
            .with_region(BssRegion.value_of("cn-north-1")) \
            .build()

        try:
            request = ListFreeResourceInfosRequest()
            response = client.list_free_resource_infos(request)
            return json.loads(str(response))
        except exceptions.ClientRequestException as e:
            print(e.status_code)
            print(e.request_id)
            print(e.error_code)
            print(e.error_msg)
            return None

    def get_all_active_cdn_traffic_package(self):
        cdn_package_id_list = []

        all_free_resource_packages = self.get_all_free_resource()["free_resource_packages"]
        for package in all_free_resource_packages:
            if package["service_type_name"] == "内容分发网络" and package["status"] == 1:
                for item in package["free_resources"]:
                    cdn_package_id_list.append(item["free_resource_id"])
        return cdn_package_id_list

    def get_remaining_traffic(self):
        china_mainland_traffic_remaining = 0
        china_mainland_traffic_total = 0
        china_off_peak_traffic_remaining = 0
        china_off_peak_traffic_total = 0

        cdn_package_id_list = self.get_all_active_cdn_traffic_package()
        for package_id in cdn_package_id_list:
            client = BssClient.new_builder() \
                .with_credentials(self.__global_credentials) \
                .with_region(BssRegion.value_of("cn-north-1")) \
                .build()

            try:
                request = ListFreeResourceUsagesRequest()
                listListFreeResourceUsagesReqFreeResourceIdsbody = [
                    package_id
                ]
                request.body = ListFreeResourceUsagesReq(
                    free_resource_ids=listListFreeResourceUsagesReqFreeResourceIdsbody
                )
                response = json.loads(str(client.list_free_resource_usages(request)))["free_resources"][0]
                if "闲时" in response["free_resource_type_name"]:
                    china_off_peak_traffic_remaining += response["amount"]
                    china_off_peak_traffic_total += response["original_amount"]
                else:
                    china_mainland_traffic_remaining += response["amount"]
                    china_mainland_traffic_total += response["original_amount"]
            except exceptions.ClientRequestException as e:
                print(e.status_code)
                print(e.request_id)
                print(e.error_code)
                print(e.error_msg)
                return None
        return {
            "china_mainland_traffic_remaining": china_mainland_traffic_remaining,
            "china_mainland_traffic_total": china_mainland_traffic_total,
            "china_mainland_traffic_percent": round(
                china_mainland_traffic_remaining / china_mainland_traffic_total * 100, 2),
            "china_off_peak_traffic_remaining": china_off_peak_traffic_remaining,
            "china_off_peak_traffic_total": china_off_peak_traffic_total,
            "china_off_peak_traffic_percent": round(
                china_off_peak_traffic_remaining / china_off_peak_traffic_total * 100, 2)
        }

    def get_remaining_traffic_percentage(self):
        """
        获取剩余流量的百分比
        :return:
        """
        remaining_traffic = self.get_remaining_traffic()
        current_hour = datetime.datetime.now().hour
        if current_hour >= 18:
            return remaining_traffic["china_mainland_traffic_percent"]
        else:
            return remaining_traffic["china_off_peak_traffic_percent"]
