class Table_traffic(object):
    def __init__(self, capacity=5):
        self._capacity = capacity
        self._hashTable = {}
        self._minK = None

    def printTable(self):
        print("Cache")
        for key, val in self._hashTable.items():
            print(f"MAC: {key}, interface: {val[0]}, traffic: {val[1]}")
    def add_entry(self, mac, interface):
        if mac not in self._hashTable.keys():
            if len(self._hashTable) == self._capacity:
                self._hashTable.pop(self._minK)
            self._hashTable[mac] = [interface, 0]
            self._minK = mac
        else:
            '''
                keep the origin traffic
            '''
            self._hashTable[mac][0] = interface
        # improve the speed of access to the min
        # the new entry is always the least traffic volume entry


    def get_interface(self, mac, volume):
        if mac not in self._hashTable.keys():
            return None
        else:
            self._hashTable[mac][1] += volume
            if mac == self._minK:
                for i in self._hashTable.keys():
                    if self._hashTable[i][1] < self._hashTable[self._minK][1]:
                        self._minK = i
            return self._hashTable[mac][0]
