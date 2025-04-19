import socket
import threading
import picobot_api
import cv2 as cv
import requests
import time
import multiprocessing
import waveplayer

def send_text(text):
    global connection, connected
    
    if not connected:
        return
    
    try:
        connection.sendall(bytes(text, "ascii"))
    except Exception as e:
        print("Error sending text: {}".format(str(e)))

def send_updates():
    global connected, status
    while connected:
        send_text("STATUS:{}".format(status))
        time.sleep(1)
        

        

HOST = ''
PORT = 50008

connection = None

execution_running = False
execution_process = None
execution_errored = False

music_playing = False
music_process = None
status = "UNKNOWN"

connected = False

picobot_api.init()

def exec_code(code):
    global execution_errored, execution_running
    
    try:
        exec(code)
    except Exception as e:
        print(f"Error in execution: {str(e)}")
        execution_errored = True
    print("Execution Finished")
    execution_running = False

while True:
    status = "AWAIT CONNECTION"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    print("IP:", requests.get("https://checkip.amazonaws.com").text.strip())
    print("Port:", PORT)
    print("Awaiting connection...")
    sock.listen(1)

    connection, addr = sock.accept()
    print("Connected by", addr)
    
    sock.close()
    connected = True
    
    status_update_thread = threading.Thread(target=send_updates)
    status_update_thread.daemon = True
    status_update_thread.start()
    
    while connected:
        print(execution_running, execution_errored)
        if execution_running:
            print(execution_process.exitcode, execution_process.is_alive())
            status = "EXECUTING"
        elif execution_errored:
            status = "ERROR"
        else:
            status = "IDLE"
            
        print("Awaiting message...")
        try:
            data = connection.recv(4096)
            
            if not data:
                connected = False
                break
        except Exception as e:
            print("Connection Error: {}".format(str(e)))
            connected = False
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
                
            picobot_api.playTone(440,durration)
            connection.sendall(b"MSG:Honked")
        if command == "EXECUTE":
            print("Executing Function")
            
            execution_running = True
            execution_errored = False
            
            if execution_process != None:
                print("Terminating old process")
                execution_process.terminate()
            
            
            execution_process = multiprocessing.Process(target=exec_code, kwargs={"code": argument})
            execution_process.daemon = True
            execution_process.start()
            print("Executing with pid: {}".format(execution_process.pid))

        if command == "STOP":
            if execution_process == None:
                print("No process to stop")
                continue
            
            print("Stopping Execution")
            
            execution_process.terminate()
        if command == "PLAYSOUND":
            if argument == None:
                argument = "pm.wav"
                
            print(f"playing file: {argument}")
            
            music_process = multiprocessing.Process(target=waveplayer.play, kwargs={"filename": argument})
            music_process.daemon = True
            music_process.start()
            print("Playing with pid: {}".format(music_process.pid))
        if command == "STOPSOUND":
            if music_process == None:
                print("No process to stop")
                continue
            
            print("Stopping Music")
            
            music_process.terminate()
        
    # Connection Quit
    connected = False
    if execution_process != None:
        execution_process.terminate()
    execution_running = False
    execution_errored = False
    
    if music_process != None:
        music_process.terminate()
    music_playing = False
        
    status_update_thread.join()
    print("Closing Connection")
    connection.close()
