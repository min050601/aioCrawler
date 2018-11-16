import socket
import multiprocessing
_dnscache={}
def _setDNSCache():
    """
    Makes a cached version of socket._getaddrinfo to avoid subsequent DNS requests.
    """

    def _getaddrinfo(*args, **kwargs):
        global _dnscache
        if args in _dnscache:
            print(str(args)+" in cache")
            return _dnscache[args]

        else:
            print(str(args)+" not in cache")
            _dnscache[args] = socket._getaddrinfo(*args, **kwargs)
            return _dnscache[args]

    if not hasattr(socket, '_getaddrinfo'):
        socket._getaddrinfo = socket.getaddrinfo
        socket.getaddrinfo = _getaddrinfo
a=multiprocessing.Array('i',[0,0])
print(a)




