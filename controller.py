import socket
import threading
import curses
import sys
import time
import cv2 as cv
import pickle
import numpy


HOST = '206.21.94.178' # Address to connect to
PORT = 50008

connected = False
target_status = "UNKNOWN"
target_debug_level = 0

socket_connection = None

quit_called = False

log_text = [""]
input_text = ""

def recv(amount):
    global connected, socket_connection
    ret =socket_connection.recv(amount)
    if not ret:
        disconnect()
        log("connection lost")
    return ret

def recieve_data():
    global connected, socket_connection, target_status

    
    while connected:
        try:
            bytes_remaing = 0
            while recv(1) != b"\n": # Waits for start of packet
                pass
                
            header = recv(8) # Size of header info

            if not header.isdigit():
                log(f"Recieved invalid packet: {header}")
                continue
            else:
                bytes_remaing = int(str(header, 'ascii'))
            
            if bytes_remaing == 0:
                log("Recieved empty packet")
                continue

            log(f"Packet size: {bytes_remaing}")
            
            data = b""
            while bytes_remaing > 0:
                data += recv(bytes_remaing)
                
                bytes_remaing -= len(data)

            log(f"Data: {data}")
                
            split_data = data.split(b":", 1)
            if len(split_data) == 2:
                command, argument = split_data
            else:
                command = split_data[0]
                argument = None
            
            if command == b"STATUS":
                target_status = str(argument, "ascii")
            
            if command == b"MSG":
                log(f"msg: {str(argument, "ascii")}")

            if command == b"IMG":
                if argument == None:
                    log("Uhh we didn't get an image ig (This shouldn't happen)")
                    continue
                
                log(f"Got img size, {len(argument)}")
                cv.imshow("We just got an image, we just got an image", pickle.loads(argument))
                cv.waitKey()

                pass

            #log(str(data, "ascii"))
        except Exception as e: 
            log("Error while recieving data: {}".format(str(e)))
            disconnect()
            return

def send_text(text):
    global connected, socket_connection

    if not connected:
        return
    
    try:
        socket_connection.sendall(bytes(text, "ascii"))
    except Exception as e:
        log("Error while sending data: {}".format(str(e)))

def process_input(screen):
    global input_text
    while True:
        ch = screen.getch()

        if ch == curses.KEY_ENTER or ch == 10 or ch == 13:
            execute_command()
            input_text = ""
        
        if ch == 8:
            input_text = input_text[:-1]

        if ch <= 255 and ch >= 0: # Because getch dosn't always return in ascii range
            new_char = str(bytes([ch]), "ascii")

            if new_char.isprintable() or new_char == "." or new_char == " ":
                input_text += str(bytes([ch]), "ascii")

exec
def disconnect():
    global socket_connection, connected

    connected = False
    socket_connection.close()

def connect():
    global socket_connection, connected
    try:
        socket_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_connection.connect((HOST, PORT))
        connected = True

        recieve_thread = threading.Thread(target=recieve_data)
        recieve_thread.daemon = True
        recieve_thread.start()

        log("Connected!")
        
    except Exception as e:
        log("Could not connect to target: {}".format(str(e)))
        socket_connection.close()


def execute_command():
    global connected, input_text, socket_connection, quit_called

    split_text = input_text.rstrip().split(" ", 1)
    if len(split_text) == 1:
        command = split_text[0]
        argument = None
    else:
        command, argument = split_text

    

    if (command == "connect" or command == "cn"):
        if argument != None:
            log("connect does not require argument")

        log("Attempting connection")
        if not connected:
            connection_thread = threading.Thread(target=connect)
            connection_thread.daemon = True
            connection_thread.start()
        else:
            log("Already connected!")
    elif (command == "disconnect" or command == "dc"):
        if argument != None:
            log("disconnect does not require argument")
            
        log("Disconnecting")
        if connected:
            disconnect()
    elif (command == "quit" or command == "q"):
        if argument != None:
            log("quit does not require argument, quitting anyway")
        if connected:
            disconnect()
        quit_called = True
    elif (command == "honk" or command == "h"):
        if not connected:
            log("Must be connected to honk")
            return
        
        durration = "0.5"
        try:
            durration = float(argument)
        except:
            log("Could not parse argument, using 0.5s as durration")

        log("Sending honk signal")
        send_text("HONK:{}".format(durration))
    elif (command == "execute" or command == "ex"):
        if argument == None:
            log("Payload requires argument")
            return
        
        log("Sending execute signal")

        send_text("EXECUTE:{}".format(argument))
        # picobot_api.setLedColor(0, 255, 0, 0)
    elif (command == "payload" or command == "pl"):
        if argument == None:
            argument = "payload.py"
        
        try:
            file = open(argument)
            content = file.read()
        except Exception as e:
            log("Error: {}".format(str(e)))
            return

        log(f"Sending payload: {argument}")

        send_text("EXECUTE:{}".format(content))
        # picobot_api.setLedColor(0, 255, 0, 0)
    elif (command == "stop" or command == "s"):
        if argument != None:
            log("Stop takes no arguments")
        
        log("Sending stop signal")

        send_text("STOP:")
    elif (command == "playsound" or command == "play"):

        if argument == None:
            argument = ""

        log(f"Playing sound: {argument}")
            
        send_text(f"PLAYSOUND:{argument}")
    elif (command == "stopsound" or command == "ssnd"):
        log("Stopping sound")

        send_text("STOPSOUND:")
    elif command == "log":
        if argument == None:
            argument = "log.txt"

        log(f"Log saved to: {argument}")
        
        with open(argument, "w") as f:
            for line in log_text:
                f.write(line + "\n")
    else:
        log("Invalid Command!")

def log(message):
    message = message.replace("\n", "\\n")
    log_text.append(message)

stdscr = curses.initscr()
curses.cbreak()
curses.noecho()
curses.start_color()
curses.use_default_colors()
stdscr.keypad(True)

# Executing Paused Error Await DEBUG ON/OFF  (NOT) CONNECTED

curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_GREEN)  # GOOD
curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)    # BAD
curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)  # INFO
curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK) # FROM TARGET 

input_thread = threading.Thread(target=process_input, kwargs={"screen": stdscr})
input_thread.daemon = True
input_thread.start()



while not quit_called:

    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()

    # Prints log messages
    for i, s in enumerate(reversed(log_text)):
        y_pos = max_y - i - 3
        if y_pos < 0:
            break

        if len(s) >= max_x: # Messages that are too long cause curses to crash
                s = s[:max_x - 1]
        
        if s.startswith("msg:"):
            
            stdscr.addstr(y_pos, 0, s, curses.color_pair(4))
            continue
        stdscr.addstr(y_pos, 0, s)

    # Print status bar message
    label_pos = 0
    def add_label(text, color):
        global label_pos

        stdscr.addstr(max_y - 2, label_pos, text, color)
        label_pos += len(text) + 3 # Adds a spacer

    if connected:
        add_label(" CONNECTED ", curses.color_pair(1))
        add_label(f" STATUS: {target_status} ", curses.color_pair(3))
    else:
        add_label(" NOT CONNECTED ", curses.color_pair(2))
    
    

    #     stdscr.addstr(max_y - 2, 0, " CONNECTED ", curses.color_pair(1))
    # else:
    #     stdscr.addstr(max_y - 2, 0, " NOT CONNECTED ", curses.color_pair(2))

    stdscr.addstr(max_y - 1, 0, f"Command: {input_text}")

    stdscr.refresh()
    
sys.exit()



