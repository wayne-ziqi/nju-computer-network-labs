from typing import Dict


class DulNode(object):
    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        self.pre: DulNode = None
        self.nxt: DulNode = None


class DulList(object):
    def __init__(self):
        self._head = DulNode()
        self._tail = DulNode()
        self._head.nxt = self._tail
        self._tail.pre = self._head  # non-loop

    def remove(self, node: DulNode):
        if node.nxt != None:
            node.nxt.pre = node.pre
        node.pre.nxt = node.nxt

    def push_head(self, node: DulNode):
        node.nxt = self._head.nxt
        node.nxt.pre = node
        node.pre = self._head
        self._head.nxt = node

    def pop_tail(self):
        if self._head.nxt == self._tail:
            return None  # empty list
        else:
            self.remove(self._tail.pre)
            tail = self._tail.pre
            return tail

class Table_LRU(object):
    '''
    head is the recently used entry while tail is the  LRU entry
    '''

    def __init__(self, capacity=5):
        self._capacity = capacity
        self._hashTable = {}
        self._entries = DulList()

    def printCache(self):
        print("Cache");
        for key,val in self._hashTable.items():
            print(f"MAC: {key}, interface: {val.value}")

    def set_recent(self, key):
        node = self._hashTable[key]
        self._entries.remove(node)
        self._entries.push_head(node)

    def del_LRU(self):
        node = self._entries.pop_tail()
        if node != None:
            del self._hashTable[node.key]

    def add_entry(self, key, value):
        if key not in self._hashTable.keys():
            if len(self._hashTable) == self._capacity: #table is full
                self.del_LRU()
            node = DulNode(key, value)
            self._entries.push_head(node)
            self._hashTable[key] = node
        else:
            '''
                when an entry need updating , do not change the LRU state
            '''
            self._hashTable[key].value = value

    def get_interface(self, mac):
        if mac not in self._hashTable.keys():
            return None
        else:
            self.set_recent(mac)
            return self._hashTable[mac].value


