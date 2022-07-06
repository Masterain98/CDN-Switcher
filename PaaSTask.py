from PublicCloudAPI.HuaweiCloud import HuaweiCloudAccount


class PaaSTask:
    def __init__(self, domain: str, dns_account: HuaweiCloudAccount, cdn_cname: str, region: list,
                 cdn_account=None, cdn_account_type=None, traffic_package_floor_limit: float = 0):
        """
        :param domain: 此 CDN 域名
        :param dns_account: 默认为华为云DNS账号，不支持其它公有云
        :param cdn_cname: 此 CDN 的 CNAME 解析值
        :param region: 此 CDN 的地域
        :param cdn_account: 此 CDN 的账号 Object。如果不指定，则为None，用于主程序判定是否可以执行公有云API接口函数
        :param cdn_account_type: 此 CDN 所属的公有云平台。如果不指定，则为None，用于主程序判定是否可以执行公有云API接口函数
        :param traffic_package_floor_limit: 此 CDN 允许的最低流量包限制。如果不指定，则为 0 (当该值为负时即使流量包用完也可以继续使用该CDN)
        """

        self.domain = domain
        self.dns_account = dns_account
        self.cdn_cname = cdn_cname
        self.region = region
        self.traffic_package_floor_limit = traffic_package_floor_limit

        if cdn_account is not None and cdn_account_type is not None:
            self.cdn_account = cdn_account
            self.cdn_account_type = cdn_account_type
        elif cdn_account is not None and cdn_account_type is None:
            self.cdn_account = None
            self.cdn_account_type = None
        else:
            raise TypeError("cdn_account and cdn_account_type must be both None or both not None")

    def add_cdn_config(self, cdn_account, cdn_account_type: str):
        """
        添加 CDN 账号和其公有云平台类型
        :param cdn_account: 此 CDN 的账号 Object
        :param cdn_account_type: 此 CDN 所属的公有云平台
        :return:
        """
        self.cdn_account = cdn_account
        self.cdn_account_type = cdn_account_type
        return self
