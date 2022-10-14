import datetime
import socket
import select
import locale
import sys


def packet_generator(request_type):
    """Generates the client packet to send to server."""
    
    client_packet = bytearray(6)
    client_packet[0] = 0x49
    client_packet[1] = 0x7E
    client_packet[2] = 0x00
    client_packet[3] = 0x01
    client_packet[4] = 0x00
    if request_type == "date":
        client_packet[5] = 0x01
    else:
        client_packet[5] = 0x02
    return client_packet


def client_checkin(response_packet):
    """Performs checks on the packet recived from the server to see if conditions are met."""
    
    if len(response_packet) < 13:
        print("Error. Packet too short. Must be at least 13 bytes.")
        sys.exit()
    elif (response_packet[0]<<8 | response_packet[1] !=  0x497E):
        print("Error. Not so magic number. Magic number is 0x497E.")
        sys.exit()
    elif (response_packet[2] | response_packet[3] !=  0x0002):
        print("Error. Unrecongised packet type. Expected 0x0002.")
        sys.exit()
    elif (response_packet[4] | response_packet[5] != 0x0001) and (response_packet[4] | response_packet[5] != 0x0002) and (response_packet[4] | response_packet[5] != 0x0003):
        print("Error. Unrecongised language code. Expected 0x0001 or 0x0002 or 0x0003.")
        sys.exit()
    elif (response_packet[6] | response_packet[7]  >= 2100 ):
        print("Error. Year not below 2100.")
        sys.exit()
    elif response_packet[8] < 0 and response_packet[8] > 13:
        print("Error. Month must be 1 - 12.")
        sys.exit()
    elif response_packet[9] < 0 and response_packet[9] > 32:
        print("Error. Day must be 1 - 31.")
        sys.exit()
    elif response_packet[10] < 0 and response_packet[10] > 24:
        print("Error. Hour must be 0 - 23.")
        sys.exit()
    elif response_packet[11] < 0 and response_packet[11] > 60:
        print("Error. Minute must be 0 - 59") 
        sys.exit()
    elif len(response_packet) - response_packet[12] != 13:
        print("Error. Fixed header must equal 13 bytes.") 
        sys.exit()
    else:
        print("Magic No: {} \nPacket Type: {} \nLanguage Code: {} \nYear: {} \nMonth: {} \nDay: {} \nHour: {} \nMinute: {} \nPacket Length: {} \nText: {}".format(response_packet[0]<<8 | response_packet[1], response_packet[2] | response_packet[3], response_packet[4] | response_packet[5],response_packet[6] | response_packet[7],response_packet[8],response_packet[9],response_packet[10],response_packet[11],response_packet[12], response_packet[13:].decode()))
      

def client_setup():
    """ Takes three parameters on the command line. """
    
    request_type = input("Would you like to see date or time: ")
    if request_type != 'date' and request_type != 'time':
        print("Invalid input please choose 'date' or 'time'.")
        sys.exit()
    ip_address = input("Please input IP address or host name: ")
    try:
        verify = socket.getaddrinfo(ip_address, None)
    except:
        print("Invalid IP address or host name.")
        sys.exit()      
    portnum = int(input("Enter port number in range 1024 to 64000: "))
    if portnum < 1024 and portnum > 64000:
        print("Number entered was not in range 1024 to 64000.")
        sys.exit()
    
    return request_type, ip_address, portnum


def client():
    """ Sends client packet to server and recieves server packet from server. """
    
    request_type, ip_address, portnum = client_setup()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    send_to_server = packet_generator(request_type)
    client_socket.sendto(send_to_server, (ip_address , portnum))
    
    try:
        select.select([client_socket], [], [], 1.0) 
    except:
        print("Error. Packet did not arrive within one second.")
    response_packet, addr = client_socket.recvfrom(1024)
    client_checkin(response_packet)

client()