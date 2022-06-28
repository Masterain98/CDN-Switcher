from datetime import datetime, timezone, timedelta
import requests
import json


class GCoreAccount:
    def __init__(self, api_key):
        self.__api_key = api_key
        self.__default_headers = {
            "Authorization": "APIKey " + self.__api_key
        }


    def get_cdn_service_details(self):
        host = "https://api.gcorelabs.com/cdn/clients/me"
        response = requests.get(host, headers=self.__default_headers)
        return json.loads(response.text)

    def get_all_cdn_resources(self):
        host = "https://api.gcorelabs.com/cdn/resources"
        response = requests.get(host, headers=self.__default_headers)
        return json.loads(response.text)

    def get_cdn_id_by_domain(self, domain):
        all_resources = self.get_all_cdn_resources()
        for resource in all_resources:
            if resource["cname"] == domain:
                return resource["id"]
        return None

    def get_cdn_30_days_traffic(self, resource_id=None):
        host = "https://api.gcorelabs.com/cdn/statistics/aggregate/stats"
        utc_time_now = datetime.now(timezone.utc)
        start_time = (utc_time_now - timedelta(days=30)).strftime("%Y-%m-%dT%H:00:00")
        end_time = utc_time_now.strftime("%Y-%m-%dT%H:00:00")
        if resource_id is None:
            response = requests.get(host, headers=self.__default_headers,
                                    params={"service": "CDN",
                                            "from": start_time,
                                            "to": end_time,
                                            "metrics": "sent_bytes",
                                            "group_by": "resource"})
        else:
            response = requests.get(host, headers=self.__default_headers,
                                    params={"service": "CDN",
                                            "from": start_time,
                                            "to": end_time,
                                            "metrics": "sent_bytes",
                                            "group_by": "resource",
                                            "resource": resource_id})
        return json.loads(response.text)

    def get_cdn_30_day_traffic_by_domain(self, domain):
        target_id = self.get_cdn_id_by_domain(domain)
        result = self.get_cdn_30_days_traffic(resource_id=target_id)
        return result

    def get_remaining_traffic(self):
        TOTAL_TRAFFIC = 1099511627776
        total_traffic_bytes = 0
        result = self.get_cdn_30_days_traffic()["resource"]
        for resource_id in result.keys():
            total_traffic_bytes += result[resource_id]["metrics"]["sent_bytes"]
        return TOTAL_TRAFFIC-total_traffic_bytes

    def get_remaining_traffic_percentage(self):
        return round(self.get_remaining_traffic()/1099511627776, 4)
