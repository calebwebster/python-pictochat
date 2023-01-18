import selectors
import socket

sel = selectors.DefaultSelector()

def accept(sock):
    conn, addr = None, None
    try:
        conn, addr = sock.accept()  # Should be ready
    except BlockingIOError:
        pass
    if not conn:
        return
    print('accepted', conn, 'from', addr)
    conn.setblocking(False)
    print(f"Descriptor: {conn.fileno()}")
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn, mask):
    data = conn.recv(1000)  # Should be ready
    if data:
        print('echoing', repr(data), 'to', conn)
        conn.send(data)  # Hope it won't block
    else:
        print('closing', conn)
        sel.unregister(conn)
        conn.close()

sock = socket.socket()
sock.bind(('localhost', 1234))
sock.listen(100)
sock.setblocking(False)

while True:
    accept(sock)
    events = sel.select()
    for key, mask in events:
        callback = key.data
        callback(key.fileobj, mask)