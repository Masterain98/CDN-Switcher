# coding: utf-8

from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkdns.v2.region.dns_region import DnsRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkdns.v2 import *

import json
import re


class HuaweiCloudAccount():
    def __init__(self, ak, sk, region="ap-southeast-1"):
        """
        :param ak: Access Key ID
        :param sk: Secret Access Key
        """
        self.__ak = ak
        self.__sk = sk
        self.__region = region

        self.__credentials = BasicCredentials(ak, sk)

    def list_public_zone(self):
        """
        # Show all zones and their ID under the account
        # Zone here is a public domain
        :return: List of public zones
        """
        client = DnsClient.new_builder() \
            .with_credentials(self.__credentials) \
            .with_region(DnsRegion.value_of("cn-east-2")) \
            .build()

        try:
            zone_list = []
            request = ListPublicZonesRequest()
            response = json.loads(str(client.list_public_zones(request)))["zones"]
            for zone in response:
                zone_list.append({"zone": zone["name"], "id": zone["id"]})
            return zone_list
        except exceptions.ClientRequestException as e:
            print(e.status_code)
            print(e.request_id)
            print(e.error_code)
            print(e.error_msg)
            return None

    def get_record_id_by_name(self, name):
        """
        # This is a generic function provided by HuaweiCloud
        :param zone_id: Zone ID
        :param name: Record name
        :return: Record ID
        """

        client = DnsClient.new_builder() \
            .with_credentials(self.__credentials) \
            .with_region(DnsRegion.value_of(self.__region)) \
            .build()

        try:
            request = ListRecordSetsWithLineRequest()
            request.name = name
            response = client.list_record_sets_with_line(request)
            return json.loads(str(response))
        except exceptions.ClientRequestException as e:
            print(e.status_code)
            print(e.request_id)
            print(e.error_code)
            print(e.error_msg)

    def get_record_china_line_id(self, name):
        # 遍历中国大陆地区解析记录 ID
        result = []
        records = self.get_record_id_by_name(name)["recordsets"]
        for record in records:
            if record["line"] == "CN":
                result.append(record["id"])
        return result  # return a list of record ID

    def get_record_abroad_line_id(self, name):
        # 遍历国外地区解析记录 ID
        result = []
        records = self.get_record_id_by_name(name)["recordsets"]
        for record in records:
            if record["line"] == "Abroad":
                result.append(record["id"])
        return result  # return a list of record ID

    def get_record_default_line_id(self, name):
        # 遍历默认解析记录 ID
        result = []
        records = self.get_record_id_by_name(name)["recordsets"]
        for record in records:
            if record["line"] == "default_view":
                result.append(record["id"])
        return result  # return a list of record ID

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
            request = ListPublicZonesRequest()
            response = json.loads(str(client.list_public_zones(request)))["zones"]
            for zone in response:
                if zone["name"] == name:
                    return zone["id"]
        except exceptions.ClientRequestException as e:
            print(e.status_code)
            print(e.request_id)
            print(e.error_code)
            print(e.error_msg)
            return None
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

    def describe_cdn_provider(self, name):
        default_line_cdn_provider = []
        china_line_cdn_provider = []
        abroad_line_cdn_provider = []

        record_sets = self.get_record_id_by_name(name)["recordsets"]
        for record in record_sets:
            if record["type"] == "CNAME":
                for value in record["records"]:
                    if "aicdn.com" in value:
                        this_cdn_provider = "UPYUN"
                    elif "qiniu.com" in value:
                        this_cdn_provider = "Qiniu"
                    elif "gcdn.co" in value:
                        this_cdn_provider = "G-Core"
                    elif re.match(r"cdnhwc(\d)+.cn", value) is not None:
                        this_cdn_provider = "Huawei Cloud"
                    else:
                        this_cdn_provider = "Unknown"

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

    def create_record_set_with_line(self, name: str, record_type: str, records: list, line: str, ttl: int = 300,
                                    zone_id: str = None):
        ALLOWED_TYPES = ["A", "AAAA", "CNAME", "TXT", "MX", "NS", "SRV", "CAA"]
        ALLOWED_LINES = ["default_view", "CN", "Abroad", "Dianxin", "Liantong", "Yidong", "Jiaoyuwang",
                         "Tietong", "Pengboshi"]
        if zone_id is None:
            try:
                root_domain = re.search(r"(\w|\d)+(\.{1})(\w)+(\.)?$", name).group(0)
            except AttributeError:
                print("Please input a valid domain name")
                return None
            zone_id = self.get_zone_id_by_name(root_domain)
        if record_type not in ALLOWED_TYPES:
            print("Please input a valid record type")
            return None
        if line not in ALLOWED_LINES:
            print("Please input a valid line")
            return None

        client = DnsClient.new_builder() \
            .with_credentials(self.__credentials) \
            .with_region(DnsRegion.value_of(self.__region)) \
            .build()

        try:
            request = CreateRecordSetWithLineRequest()
            request.zone_id = zone_id
            listCreateRecordSetWithLineReqRecordsbody = records
            request.body = CreateRecordSetWithLineReq(
                line=line,
                records=listCreateRecordSetWithLineReqRecordsbody,
                type=record_type,
                name=name
            )
            response = client.create_record_set_with_line(request)
            return json.loads(str(response))
        except exceptions.ClientRequestException as e:
            print(e.status_code)
            print(e.request_id)
            print(e.error_code)
            print(e.error_msg)
            return None