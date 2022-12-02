import socket
import sys
import Service_client
import threading
import Buffer
import GUII

HEADER_LENGTH = 10
HOST = sys.argv[1] # Server's IP
DEVICE_HOST = sys.argv[2]
PORT = 13000

class Client:
    def __init__(self):
        self.socket = None
        self.listen_socket = None
        # Buffer contain cmd received from another user
        self.buff_dict = {}
        # Message list contain message with another user
        self.message_list_dict = {}
        self.lock = threading.Lock()
        self.target = None
        self.listen_flag = True

    def Connect(self):
        #This method will connect client socket to server socket 
        
        # Init socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to server's socket
        self.socket.connect((HOST, PORT))
        # Data of msg received from server
        res = self.Receive_message()['data']

        # Nếu msg nhận đc là 'done' -> close connection to server
        if res == 'done':
            self.close_response()
            return False

        return True

    def Listen(self):
        # Init listen socket
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind host and port cho listen socket
        self.listen_socket.bind(("", 0))

        self.setPort()
        self.listen_thread = threading.Thread(target=self.listen_run, args=())
        self.listen_thread.start()

    def setPort(self):
        print('setPort')  # Print console
        self.Send_message('setPort')  # Send 'setPort' to server
        # Set host and port
        host = self.ip
        port = self.listen_socket.getsockname()[1]

        self.Send_message(host)  # Send host ip to server
        # Encode port
        port = f"{port:<{HEADER_LENGTH}}".encode('utf-8')
        # Send port to server
        self.socket.send(port)
        
    def requestPort(self, username):
        self.Send_message('requestPort')
        self.Send_message(username)
        response = self.Receive_message()['data']
        if response == 'Successed':
            host = self.Receive_message()['data']
            port = self.socket.recv(HEADER_LENGTH)
            port = int(port.decode('utf-8').strip())
            return (host, port)
        else:
            return None

    def Receive_message(self):
        # This method is used to receive message from server

        # Establish connection to server, init a 3-way handshake
        message_header = self.socket.recv(HEADER_LENGTH)

        # Nếu msg_header nhận đc bằng 0
        if not len(message_header):
            self.close()
            return {'header': None,'data': None}

        # Convert header to int value
        message_length = int(message_header.decode('utf-8').strip())

        # Return an object of message header and message data
        return {
            'header': message_header, 
            'data': self.socket.recv(message_length).decode('utf-8')
        }

    def Send_message(self, message):
        #This method is used to send message to server
        #Arg: message: a string object

        # Encode message
        message = message.encode('utf-8')
        # Create header, encode header
        message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')

        # Msg gồm 2 phần: từ header lấy đc độ dài của message, sau đó recv msg
        self.socket.send(message_header + message)

    def Register(self, username, password):
        #Register services
        
        self.Send_message("Register")
        self.Send_message(username)
        self.Send_message(password)

        message_recv = self.Receive_message()
        if message_recv['data'] == "Successed":
            self.username = username
            return True
        else:
            return False

    def Login(self, username, password):
        # Login 

        self.Send_message("Login")
        self.Send_message(username)
        self.Send_message(password)

        message_recv = self.Receive_message()
        if message_recv['data'] == "Successed":
            self.username = username
            return True
        else:
            return False

    def showFriend(self):
        self.Send_message("showFriend")
        response = self.Receive_message()['data']
        if response == "Successed":
            length = self.socket.recv(HEADER_LENGTH)
            length = int(length.decode('utf-8').strip())
            friendDict = {}
            for _ in range(length):
                username = self.Receive_message()['data']
                status = self.Receive_message()['data']
                friendDict[username] = status
            return friendDict

        else:
            return None

    def showFriendRequest(self):
        self.Send_message("showFriendRequest")
        response = self.Receive_message()['data']
        if response == "Successed":
            length = self.socket.recv(HEADER_LENGTH)
            length = int(length.decode('utf-8').strip())
            requestList = []
            for _ in range(length):
                username = self.Receive_message()['data']
                #status = self.Receive_message()['data']
                requestList.append(username)
            return requestList

        else:
            return None
            
    def acceptFriendRequest(self, username2):
        self.Send_message("acceptFriendRequest")
        self.Send_message(username2)
        response = self.Receive_message()['data']
        if response == "Successed":
            return True
        else:
            return False
        
    def rejectFriendRequest(self, username2):
        self.Send_message("rejectFriendRequest")
        self.Send_message(username2)
        response = self.Receive_message()['data']
        if response == "Successed":
            return True
        else:
            return False

    def addFriend(self, username2):
        self.Send_message("addFriend")
        self.Send_message(username2)
        response = self.Receive_message()['data']
        if response == "Successed":
            return True
        else:
            return False

    def shutdown(self):
        self.Send_message("shutdown")

    def close(self):
        self.Send_message('done')
        # Đóng socket connect server
        self.socket.close()
        for username in self.buff_dict:
            self.buff_dict[username].assign('done', '') # (??)

        host = self.ip
        self.listen_flag = False
        if self.listen_socket is not None:
            # getsocketname[1] -> port, [0] -> ip
            port = self.listen_socket.getsockname()[1]
            # Init 1 socket mới
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Init connect
            s.connect((host, port))
            # Đóng socket
            s.close()

    def close_response(self):
        # Close connect to server
        self.socket.close()

    def listen_run(self):
        # Open listen_socket to listen
        self.listen_socket.listen()
        # Loop when <listen_flag> is <true>
        while self.listen_flag:
            print('accept1')  # Print console
            # conn: socket, addr: (host, port)
            (conn, addr) = self.listen_socket.accept()
            if self.listen_flag:
                buff = Buffer.Buffer(self.lock)  # Init buffer
                
                message_list = GUII.Message_list(self.chatui.Message_box_frame)
                service = Service_client.Service_client(conn, buff, message_list, self.username, ip = self.ip)
                # Add buffer of chat with this peer
                self.buff_dict[service.peer] = service.buffer
                # Check if this peer is already in message_list before
                if service.peer in self.message_list_dict:
                    service.message_list = self.message_list_dict[service.peer]
                else:
                    # If not create message_list of this peer
                    self.message_list_dict[service.peer] = service.message_list
                self.chatui.update()
                service.start()
            
        print('closed')

    def startChatTo(self, username):
        # Get address of that user
        addr = self.requestPort(username)
        if addr is None:
            return False
        # Init a new socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        buff = Buffer.Buffer(self.lock)
        # Check if this username already have chat history in message_list
        if username in self.message_list_dict:
            service = Service_client.Service_client(s, buff, self.message_list_dict[username], self.username, peer = username, ip = self.ip)
            self.buff_dict[username] = service.buffer 
        else:
            # If no create a new chatbox
            message_list = GUII.Message_list(self.chatui.Message_box_frame)
            service = Service_client.Service_client(s, buff, message_list, self.username, peer = username, ip = self.ip)
            self.buff_dict[username] = service.buffer
            self.message_list_dict[username] = service.message_list
        print(addr)
        service.connectTo(addr)
        service.start()
        self.chatui.update()
        return True

    def chatTo(self, message):
        if self.target is None:
            return
        username = self.target
        if username in self.buff_dict and self.buff_dict[username].status == True:
            self.buff_dict[username].assign('SendSMS', message)
            print('yet')
        else:
            check = self.startChatTo(username)
            if check:
                self.buff_dict[username].assign('SendSMS', message)
            else:
                self.chatui.update()

    def sendFileTo(self, filename):
        username = self.target
        if username in self.buff_dict and self.buff_dict[username].status == True:
            self.buff_dict[username].assign('SendFile', filename)
        else:
            check = self.startChatTo(username)
            if check:
                self.buff_dict[username].assign('SendFile', filename)
            else:
                print("Not friend")

    def run(self):
        self.loginui = GUII.LoginWindow(self, ('Helvetica', 13))
        self.loginui.run()
        
        self.chatui = GUII.ChatWindow(self, ('Helvetica', 13))
        self.chatui.run()

    def configIP(self, ip):
        self.ip = ip