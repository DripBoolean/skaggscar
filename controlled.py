import socket
import threading
import picobot_api
import cv2 as cv
import requests
import time
import multiprocessing
import waveplayer
import sys
import subprocess
import os
import pickle

HOST = ''
PORT = 50008

connection = None
connected = False
status = ""

music_process = None

execution_process = None
execution_pipe = None
execution_running = False
execution_errored = False

def send_text(text):
    global connection, connected
    
    if not connected:
        return
    
    try:
        connection.sendall(bytes(f"\n{len(text):08d}{text}", "ascii"))
    except Exception as e:
        print("Error sending text: {}".format(str(e)))

def send_raw(data):
    global connection, connected
    
    if not connected:
        return
    
    try:
        connection.sendall(b"\n" + bytes(format(len(data), "08d") + data, 'ascii'))
        # bytes_remaining = len(data)
        # while bytes_remaining > 0:
        #     sent_bytes = min(bytes_remaining, 1024)
        #     connection.sendall(data[0:sent_bytes])
        #     data = data[sent_bytes:]
        #     bytes_remaining -= sent_bytes
    except Exception as e:
        print("Error sending bytes: {}".format(str(e)))

        
def msg(text):
    send_text(f"MSG:{text}")

def img(image):
    data = pickle.dumps(image)
    msg(len(data))
    send_raw(b"IMG:" + data)

def stop_wheels():
    picobot_api.setMotorPower1(0)
    picobot_api.setMotorPower2(0)
    
def set_all_lights(r, g, b):
        for i in range(8):
            picobot_api.setLedColor(i, r, g, b)
            
def update_status():
    global connected, status, execution_pipe, execution_running, execution_errored
    
    i = 0
    while True:
        if connected:
            if execution_pipe != None:
                if execution_pipe.poll():
                    try:
                        ret = execution_pipe.recv()
                        
                        if ret == "Finished":
                            execution_running = False
                        if ret == "Error":
                            execution_errored = True
                        stop_wheels()
                    except:
                        pass
            
            if execution_running:
                status = "EXECUTING"
                set_all_lights(0, 255, 0)
            elif execution_errored:
                status = "ERROR"
                set_all_lights(255, 0, 0)
            else:
                status = "IDLE"
                set_all_lights(0, 0, 255)
                
            
            send_text("STATUS:{}".format(status))
        else:
            status = "AWAITING CONNECTION"
            if i % 2 == 0:
                set_all_lights(0, 0, 255)
            else:
                set_all_lights(0, 0, 0)
        time.sleep(0.5)
        i += 1
        

def exec_code(code, pipe):
    try:
        exec(code)
    except Exception as e:
        msg(f"Error in execution: {e}")
        print(f"Error in execution: {e}")
        pipe.send("Error")
    
    stop_wheels()
    print("Execution Finished")
    pipe.send("Finished")
    
def quick_exit():
    drop_connection()
    
    sys.exit()
    
def stop_execution():
    global execution_running, execution_errored, execution_process, execution_pipe
    
    print("Stopping Execution")
    if execution_process != None:
        execution_process.terminate()
        
    execution_running = False
    execution_errored = False
    
    execution_process = None
    execution_pipe = None
    
    stop_wheels()

def await_interupt():
    while True:
        byte = None
        try:
            byte = picobot_api.readButtons()
        except:
            pass
        if byte:
            if byte & 1:
                stop_execution()
                print("Stopping execution from button press")
            # if byte & 2:
            #     os.system("git pull")
            #     with open(__file__) as fself:
            #         byte_code = compile(fself.read(), __file__, "exec")
            #         new_process = multiprocessing.Process(target=exec, args=[byte_code])
            #         new_process.start()
            #     quick_exit()
            if byte & 4:
                stop_music()
                print("Stopping music from button press")
            if byte & 16:
                print("Stopping program from button press")
                quick_exit()
        time.sleep(0.1)
    
def start_execution(code):
    global execution_running, execution_errored, execution_process, execution_pipe
    print("Executing Function")
            
    execution_running = True
    execution_errored = False
    
    if execution_process != None:
        print("Terminating old process")
        execution_process.terminate()
    
    execution_pipe, sent_pipe = multiprocessing.Pipe()
    execution_process = multiprocessing.Process(target=exec_code, kwargs={"code": code, "pipe": sent_pipe})
    execution_process.daemon = True
    execution_process.start()
    print("Executing with pid: {}".format(execution_process.pid))

def play_music(filename):
    global music_process
    
    print(f"playing file: {filename}")
    
    music_process = multiprocessing.Process(target=waveplayer.play, kwargs={"filename": filename})
    music_process.daemon = True
    music_process.start()
    print("Playing with pid: {}".format(music_process.pid))


def stop_music():
    global music_process
    
    print("Stopping Music")
    
    if music_process == None:
        print("No music to stop")
        return
    
    music_process.terminate()

def drop_connection():
    global connected, connection
    
    if connected:
        print("Closing Connection")
        connection.close()
        connected = False
    
    stop_execution()
    stop_music()
    
def honk(durration):
    picobot_api.playTone(440,durration)
    connection.sendall(b"MSG:Honked")

def handle_recieved_data():
    global connected, connection
    
    while True:
        while not connected:
            establish_connection()
            
        while connected:
            print("Awaiting message...")
            try:
                data = connection.recv(4096)
                
                if not data:
                    print("Recieved disconnect message, dropping connection")
                    drop_connection()
                    break
            except Exception as e:
                print("Connection Error: {}".format(str(e)))
                drop_connection()
                break
            
            data_str = str(data, 'ascii')
            print("Recieved:", data_str)
            split_data = data_str.split(":", 1)
            if len(split_data) == 1:
                print("Recieved invalid command")
                continue
            
            command, argument = split_data

            if command == "HONK":
                durration = 0.0
                try:
                    durration = float(argument)
                except:
                    print("Recieced invalid honk argument")
                    
                honk(durration)
            if command == "EXECUTE":
                start_execution(argument)
            if command == "STOP":
                stop_execution()
            if command == "PLAYSOUND":
                if argument == None:
                    argument = "pm.wav"
                    
                play_music(argument)
            if command == "STOPSOUND":
                stop_music()

def establish_connection():
    global connected, connection
    try:
        print("IP:", requests.get("https://checkip.amazonaws.com").text.strip())
    except:
        pass
    
    print("Port:", PORT)
    print("Awaiting connection...")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, PORT))
        
        sock.listen(1)
        connection, addr = sock.accept()
        print("Connected by", addr)
        
        sock.close()
        connected = True
    except Exception as e:
        print(f"Error while establishing connection {e}")
        

if not picobot_api.init():
    print("Failed to init, exiting")
    sys.exit()

print("Starting threads")

status_update_thread = threading.Thread(target=update_status)
status_update_thread.daemon = True
status_update_thread.start()

handle_recieved_thread = threading.Thread(target=handle_recieved_data)
handle_recieved_thread.daemon = True
handle_recieved_thread.start()

print("Init complete")

await_interupt()
    
    
    
    
    
