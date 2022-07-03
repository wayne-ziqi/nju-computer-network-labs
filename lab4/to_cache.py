import time

class ToCache(object):
    def __init__(self, TTL=10.0, capacity=10):
        self._dic = {}
        self._ttl = TTL
        self._capacity = capacity
        # _dic = { ip : [MAC, interface, time stamp, TTL]}

    def __len__(self):
        return len(self._dic)

    def get_value(self, key):
        if key in self._dic.keys():
            return self._dic[key][0]
        else:
            return None

    def add_entry(self, key, value, ttl=100.0):
        if len(self._dic) < self._capacity:
            self._dic[key] = [value, time.time(), ttl]

    def printCache(self):
        print("Cache")
        for key, val in self._dic.items():
            print(f"IP: {key}   MAC: {val[0]}   stamp: {val[1]}")

    def update(self):
        curTime = time.time()
        for k in list(self._dic.keys()):
            if curTime - self._dic[k][1] >= self._dic[k][2]:
                self._dic.pop(k)
