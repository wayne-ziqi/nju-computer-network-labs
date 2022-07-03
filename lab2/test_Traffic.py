from Table_traffic import Table_traffic

if __name__ == '__main__':
    cache = Table_traffic()
    cache.add_entry('h1', 1)
    Iface = cache.get_interface('h4', 20)
    cache.add_entry('h2', 2)
    Iface = cache.get_interface('h2', 38)
    cache.add_entry('h3', 3)
    Iface = cache.get_interface('h3', 15)
    cache.add_entry('h4', 4)
    Iface = cache.get_interface('h5', 50)
    cache.add_entry('h5', 5)
    Iface = cache.get_interface('h1', 47)
    cache.add_entry('h6', 6)
    Iface = cache.get_interface('h1', 30)
    cache.add_entry('h4', 4)
    Iface = cache.get_interface('h5', 25)
    cache.add_entry('h2', 7)
    Iface = cache.get_interface('h4', 30)
    cache.add_entry('h4', 10)
    Iface = cache.get_interface('h1', 30)

