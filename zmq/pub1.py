import zmq

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind('tcp://127.0.0.1:2000')

while True:
    message = input("Enter your message: ")
    socket.send_string(message)

