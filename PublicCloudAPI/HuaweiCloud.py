# coding: utf-8

from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkdns.v2.region.dns_region import DnsRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkdns.v2 import *

from huaweicloudsdkcore.auth.credentials import GlobalCredentials
from huaweicloudsdkcdn.v1.region.cdn_region import CdnRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkcdn.v1 import *

from log_printer import class_log_printer
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
    def list_public_zone(self):
        """
        # Show all zones and their ID under the account
        # Zone here is a public domain
        :return: List of public zones
        """
        client = DnsClient.new_builder() \
            .with_credentials(self.__credentials) \
            .with_region(DnsRegion.value_of(self.__region)) \
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

    @class_log_printer
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

    @class_log_printer
    def get_record_china_line_id(self, name):
        # 遍历中国大陆地区解析记录 ID
        result = []
        records = self.get_record_id_by_name(name)["recordsets"]
        for record in records:
            if record["line"] == "CN":
                result.append(record["id"])
        return result  # return a list of record ID

    @class_log_printer
    def get_record_abroad_line_id(self, name):
        # 遍历国外地区解析记录 ID
        result = []
        records = self.get_record_id_by_name(name)["recordsets"]
        for record in records:
            if record["line"] == "Abroad":
                result.append(record["id"])
        return result  # return a list of record ID

    @class_log_printer
    def get_record_default_line_id(self, name):
        # 遍历默认解析记录 ID
        result = []
        records = self.get_record_id_by_name(name)["recordsets"]
        for record in records:
            if record["line"] == "default_view":
                result.append(record["id"])
        return result  # return a list of record ID

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

    @class_log_printer
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
                    if this_record["line"] == line:
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
    def update_record_set_by_id(self, name: str, record_type: str, new_record_value: list, zone_id: str, recordset_id: str):
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
        record_id_list = self.get_record_sets_id_by_name(name, target_line, zone_id)
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
