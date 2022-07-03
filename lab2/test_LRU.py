from Table_LRU import Table_LRU
def check(res, expect):
    if res != expect:
        print("ERROR: the expected result is {0}, but got {1} instead".format(expect, res))
    else:
        print("Pass!")

if __name__ == '__main__':
    cache = Table_LRU()
    cache.add_entry('h1', 1)
    Iface = cache.get_interface('h4')
    check(Iface, None)
    cache.add_entry('h2', 2)
    Iface = cache.get_interface('h1')
    check(Iface,1)
    cache.add_entry('h3', 3)
    Iface = cache.get_interface('h1')
    check(Iface, 1)
    cache.add_entry('h4', 4)
    Iface = cache.get_interface('h1')
    check(Iface,1)
    cache.add_entry('h5', 5)
    Iface = cache.get_interface('h1')
    check(Iface, 1)
    cache.add_entry('h6', 6)
    Iface = cache.get_interface('h7')
    check(Iface, None)
    cache.add_entry('h4', 4)
    Iface = cache.get_interface('h5')
    check(Iface, 5)

