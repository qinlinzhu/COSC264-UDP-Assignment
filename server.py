import datetime
import socket
import select
import locale
import sys


texts = {1 : ["Today's date is {} {}, {}", "The current time is {}:{}"], 2 : ["Ko te ra o tenei ra ko {} {}, {}","Ko te wa o tenei wa {}:{}"], 3 : ['Heute ist der {} {}, {}', "Die Uhrzeit ist {}:{}" ]}


maori = {'months' :["Kohitatea", "Hui-tanguru", "Poutu-te-rangi", "Paenga-whawh", "Haratua", "Pipiri", "Hongongoi", "Here-turi-koka", "Mahuru", "Whiringa-a-nuku", "Whiringa-a-rangi", "Hakihea"]}


def server_checkin(client_packet):
    """Performs checks on the packet recived from the client to see if conditions are met."""
    
    if len(client_packet) != 6:
        print("Error. Packet must 6 bytes.")
        sys.exit()
    elif (client_packet[0]<<8 | client_packet[1]!=  0x497E):
        print("Error. Not so magic number. Magic number is 0x497E.")
        sys.exit()
    elif (client_packet[2] | client_packet[3] !=  0x0001):
        print("Error. Unrecongised packet type. Expected 0x0001.")
        sys.exit()
    elif (client_packet[4] | client_packet[5] != 0x0001) and (client_packet[4] | client_packet[5] != 0x0002):
        print("Error. Unrecongised particular type. Expected 0x0001 or 0x0002.")
        sys.exit()
    else:
        return (client_packet[4] | client_packet[5])
    
    
def trilingual_timedate_machine(request_type, lang_port, PORTS):
    """Determines the language to be used for the textual representation and creates text for server packet."""
    
    time = datetime.datetime.now()
    if request_type == 0x0001 and lang_port == PORTS[0]:
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
        text = texts[1][0].format(time.strftime('%B'), time.day, time.year)
        language = "English"
        the_packet = packet_generator(language, text, time)
        return the_packet
    elif request_type == 0x0001 and lang_port == PORTS[1]:
        month = maori['months'][time.month-1]
        text = texts[2][0].format(month, time.day, time.year)   
        language = "Maori"
        the_packet = packet_generator(language, text, time)
        return the_packet        
    elif request_type == 0x0001 and lang_port == PORTS[2]:
        locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
        text = texts[3][0].format(time.strftime('%B'), time.day, time.year)
        language = "German"
        the_packet = packet_generator(language, text, time)
        return the_packet        
    elif request_type == 0x0002 and lang_port == PORTS[0]:
        text = texts[1][1].format(time.hour, time.minute)
        language = "English"
        the_packet = packet_generator(language, text, time)
        return the_packet        
    elif request_type == 0x0002 and lang_port == PORTS[1]:
        text = texts[2][1].format(time.hour, time.minute)
        language = "Maori"
        the_packet = packet_generator(language, text, time)
        return the_packet        
    elif request_type == 0x0002 and lang_port == PORTS[2]:
        text = texts[3][1].format(time.hour, time.minute)
        language = "German"
        the_packet = packet_generator(language, text, time)
        return the_packet        
    return language, text, time
    
    
def packet_generator(language, text, time):
    """Generates the server packet to send to client."""
    
    response_packet = bytearray(13) 
    response_packet[0] = 0x49
    response_packet[1] = 0x7E
    response_packet[2] = 0x00
    response_packet[3] = 0x02
    response_packet[4] = 0x00
    if language == "English":
        response_packet[5] = 0x01
    elif language == "Maori":
        response_packet[5] = 0x02
    elif language == "German":
        response_packet[5] = 0x03
    text_bytes = text.encode("utf-8")
    response_packet[6] = time.year >> 8
    response_packet[7] = time.year & 0b11111111
    response_packet[8] = time.month
    response_packet[9] = time.day
    response_packet[10] = time.hour
    response_packet[11] = time.minute
    response_packet[12] = len(text_bytes)
    response_packet += text_bytes
    return response_packet
    
    
def server_setup():
    """ Takes three ports on the command line. """
    
    PORTS = []
    for i in range(3):
        portnum = int(input('Enter port numbers:'))
        if (portnum >= 1024 and portnum <= 64000):
            if portnum in PORTS:
                print('Port {} already exists, no duplicate ports'.format(portnum))
                sys.exit()
            else:
                PORTS.append(portnum)  
        else:
            print("Duplicate port entered. Cannot have duplicate ports.")
            sys.exit()
    return PORTS


def server():
    """ Sends server packet to client and recieves client packet from client. Opens three UDP / datagram sockets and to bind these three sockets to the three given port numbers. """
    
    PORTS = server_setup()
    try: 
        eng_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        trm_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ger_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        eng_socket.bind(('',PORTS[0]))
        trm_socket.bind(('',PORTS[1]))
        ger_socket.bind(('',PORTS[2]))
    except:
        print("Error. Failed to bind ports.")
        sys.exit()
    
    while True:
        server_sockets = select.select([eng_socket, trm_socket, ger_socket],[],[])
        try:
            for packet in server_sockets[0]:
                data, addr = packet.recvfrom(1024)
                request_type = server_checkin(data)
                packed_package = trilingual_timedate_machine(request_type, packet.getsockname()[1], PORTS)
                packet.sendto(packed_package, addr)
        except:
            print("Error. Failed to send package.")
            sys.exit()

server()