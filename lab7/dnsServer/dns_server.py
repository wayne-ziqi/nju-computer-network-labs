'''DNS Server for Content Delivery Network (CDN)
'''
import random
import sys
from socketserver import UDPServer, BaseRequestHandler
from utils.dns_utils import DNS_Request, DNS_Rcode
from utils.ip_utils import IP_Utils
from datetime import datetime
# from geopy.distance import geodesic
import math

import re
from collections import namedtuple

__all__ = ["DNSServer", "DNSHandler"]


class DNSEntry(object):
    def __init__(self, mode: str, nameType: str, domain_name: str, transList: list):
        self.mode = mode
        self.nameType = nameType
        self.domain_name = domain_name
        self.transList = transList

    def match(self, targetDomain: str):
        bare_target = targetDomain.strip('.')
        bare_domain = self.domain_name.strip('.')
        if bare_target == bare_domain:
            return True
        else:
            if bare_target.endswith(bare_domain):
                if self.mode == 'ANY':
                    return True
        return False


class DNSServer(UDPServer):
    def __init__(self, server_address, dns_file, RequestHandlerClass, bind_and_activate=True):
        super().__init__(server_address, RequestHandlerClass, bind_and_activate=True)
        self._dns_table = []
        self.parse_dns_file(dns_file)

    def parse_dns_file(self, dns_file):
        # ---------------------------------------------------
        # TODO: your codes here. Parse the dns_table.txt file
        # and load the data into self._dns_table.
        # --------------------------------------------------
        with open(dns_file, 'r', encoding='utf-8') as fp:
            for line in fp:
                tokens = [elem for elem in line.split()]
                tmp_dname = tokens[0]
                DName = None
                dName_token = re.match(r'^\*\.[a-zA-Z\d.]+', tmp_dname)
                mode = 'ANY'
                if dName_token is not None:
                    mode = 'ANY'
                    DName = dName_token.group().strip('*.')
                else:
                    mode = 'UNI'
                    doc_token = re.match(r'^[a-zA-Z\d.]+', tmp_dname)
                    if doc_token is None:
                        raise 'Error domain name'
                    else:
                        DName = doc_token.group()
                nameType = tokens[1]
                nameList = []
                for i in range(2, len(tokens)):
                    nameList.append(tokens[i])
                self._dns_table.append(DNSEntry(mode, nameType, DName, nameList))

    @property
    def table(self):
        return self._dns_table


class DNSHandler(BaseRequestHandler):
    """
    This class receives clients' udp packet with socket handler and request data. 
    ----------------------------------------------------------------------------
    There are several objects you need to mention:
    - udp_data : the payload of udp protocol.
    - socket: connection handler to send or receive message with the client.
    - client_ip: the client's ip (ip source address).
    - client_port: the client's udp port (udp source port).
    - DNS_Request: a dns protocol tool class.
    We have written the skeleton of the dns server, all you need to do is to select
    the best response ip based on user's information (i.e., location).

    NOTE: This module is a very simple version of dns server, called global load ba
          lance dns server. We suppose that this server knows all the ip addresses of 
          cache servers for any given domain_name (or cname).
    """

    def __init__(self, request, client_address, server: DNSServer):
        self.table = server.table
        super().__init__(request, client_address, server)

    def calc_distance(self, pointA, pointB):
        ''' TODO: calculate distance between two points '''
        # (float, float)
        # return geodesic(pointA, pointB).km
        # Haversine method
        lat1, long1, lat2, long2 = map(math.radians, [pointA[0], pointA[1], pointB[0], pointB[1]])
        a = math.sin((lat1 - lat2) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * (math.sin((long1 - long2) / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return 6371 * c  # km

    def get_best_ip(self, srcIP: str, ipList: list):
        bestIP = None
        loc_src = IP_Utils.getIpLocation(srcIP)
        if loc_src is None:
            return ipList[random.randint(0, len(ipList) - 1)]
        bestDst = 0
        for ip in ipList:
            loc_dst = IP_Utils.getIpLocation(ip)
            if loc_dst is not None:
                curDst = self.calc_distance(loc_src, loc_dst)
                if bestIP is None or bestDst > curDst:
                    bestIP = ip
                    bestDst = curDst
        return bestIP if bestIP is not None else ipList[random.randint(0, len(ipList) - 1)]

    def get_response(self, request_domain_name):
        response_type, response_val = (None, None)
        # ------------------------------------------------
        # TODO: your codes here.
        # Determine an IP to response according to the client's IP address.
        #       set "response_ip" to "the best IP address".
        client_ip, _ = self.client_address
        idx = len(self.table)
        for i in range(len(self.table)):
            if self.table[i].match(request_domain_name):
                idx = i
                break
        if idx != len(self.table):
            response_type = self.table[idx].nameType
            if response_type == 'CNAME':
                response_val = self.table[idx].transList[0]
            elif response_type == 'A':
                response_val = self.get_best_ip(client_ip, self.table[idx].transList)
            else:
                raise "type error"

        # -------------------------------------------------
        return response_type, response_val

    def handle(self):
        """
        This function is called once there is a dns request.
        """
        ## init udp data and socket.
        udp_data, socket = self.request

        ## read client-side ip address and udp port.
        client_ip, client_port = self.client_address

        ## check dns format.
        valid = DNS_Request.check_valid_format(udp_data)
        if valid:
            ## decode request into dns object and read domain_name property.
            dns_request = DNS_Request(udp_data)
            request_domain_name = str(dns_request.domain_name)
            self.log_info(f"Receving DNS request from '{client_ip}' asking for "
                          f"'{request_domain_name}'")

            # get caching server address
            response = self.get_response(request_domain_name)

            # response to client with response_ip
            if None not in response:
                dns_response = dns_request.generate_response(response)
            else:
                dns_response = DNS_Request.generate_error_response(
                    error_code=DNS_Rcode.NXDomain)
        else:
            self.log_error(f"Receiving invalid dns request from "
                           f"'{client_ip}:{client_port}'")
            dns_response = DNS_Request.generate_error_response(
                error_code=DNS_Rcode.FormErr)

        socket.sendto(dns_response.raw_data, self.client_address)

    def log_info(self, msg):
        self._logMsg("Info", msg)

    def log_error(self, msg):
        self._logMsg("Error", msg)

    def log_warning(self, msg):
        self._logMsg("Warning", msg)

    def _logMsg(self, info, msg):
        ''' Log an arbitrary message.
        Used by log_info, log_warning, log_error.
        '''
        info = f"[{info}]"
        now = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
        sys.stdout.write(f"{now}| {info} {msg}\n")
