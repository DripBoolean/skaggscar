# Example program illustrating:
#    + reading camera images and accessing individual pixel values.
#    + calling picobot_api functions

import pygame
import pygame.camera
import picobot_api
import time
import random

pygame.init()
pygame.camera.init()

pb_init=picobot_api.init()
if pb_init==False:
    print("Warning: picobot_api initialization failed! All picobot_api features disabled!")
    
#camera setup
CAM_SIZE=(320,240) #also supports (640,480),(800,600),(1024,768),(1920,1080),(3280,2464) 
CAM_FORMAT="RGB"  #also supports YUV and HSV 
CAM_DEVICE="/dev/video0"

cam = pygame.camera.Camera(CAM_DEVICE,CAM_SIZE,CAM_FORMAT)
cam.start()
cam.set_controls(True, True, 50) #flip window on both axes, set brightness to 50

#create display window
WINDOW_SIZE=(1024,768)
ds=pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption("PicoBot Example")
#load a font
font24=pygame.font.SysFont("Courier",14)

encoder1=0
encoder2=0
button_byte=0
while True:
    pygame.event.pump()
    keys=pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        break

    if pb_init==True:

        if keys[pygame.K_f]: #forward for 0.5 seconds
            picobot_api.setMotorPower1(100)
            picobot_api.setMotorPower2(100)
            time.sleep(0.5)
            picobot_api.setMotorPower1(0)
            picobot_api.setMotorPower2(0)
            
        if keys[pygame.K_b]: #back for 0.5 seconds
            picobot_api.setMotorPower1(-100)
            picobot_api.setMotorPower2(-100)
            time.sleep(0.5)
            picobot_api.setMotorPower1(0)
            picobot_api.setMotorPower2(0)
        
        if keys[pygame.K_t]: # beep a tone for 0.1 seconds
            picobot_api.playTone(440,0.1)
        
        if keys[pygame.K_e]: # read encoder values
            encoder1=picobot_api.readEncoder1()
            encoder2=picobot_api.readEncoder2()
        
        if keys[pygame.K_r]: # reset encoder values
            picobot_api.resetEncoder1()
            picobot_api.resetEncoder2()
            encoder1=0
            encoder2=0
        
        if keys[pygame.K_l]: # random LED colors
            for i in range(8):
                r=random.randint(0,64)
                g=random.randint(0,64)
                b=random.randint(0,64)
                picobot_api.setLedColor(i,r,g,b)    
        
        if keys[pygame.K_i]: # read input button byte
            button_byte=picobot_api.readButtons()
        
    
    ds.fill((0,0,0))
    image = cam.get_image() #read camera in as a surface
    ds.blit(image,(0,0))    #draw the image on the display window
    pixels=pygame.surfarray.pixels3d(image) #convert the image into an array of [r,g,b] values
    #to read the pixel value at a specific position use: pixels[x][y] which will return a 3-element array [r,g,b]
    
    mx,my=pygame.mouse.get_pos() #read mouse coordinates
    if mx<320 and my<240: # if the mouse is over the camera image
        color=pixels[mx][my]   #get the pixel value at the mouse location
    
        pygame.draw.rect(ds,color,(400,100,130,100),0) #draw a rectangle of that color
        font_surf=font24.render(f"R:{color[0]} G:{color[1]} B:{color[2]}",True,(255,255,255))
        ds.blit(font_surf,(400,210))
    
    font_surf=font24.render("F - motors forward for 0.5 seconds.",True,(255,255,255))
    ds.blit(font_surf,(100,500))
    font_surf=font24.render("B - motors backward for 0.5 seconds.",True,(255,255,255))
    ds.blit(font_surf,(100,520))
    font_surf=font24.render("T - 440Hz tone for 0.1 seconds.",True,(255,255,255))
    ds.blit(font_surf,(100,540))
    font_surf=font24.render(f"E - read encoder values. encoder1={encoder1}  encoder2={encoder2}",True,(255,255,255))
    ds.blit(font_surf,(100,560))
    font_surf=font24.render("R - reset encoder values.",True,(255,255,255))
    ds.blit(font_surf,(100,580))
    font_surf=font24.render("L - random LED colors.",True,(255,255,255))
    ds.blit(font_surf,(100,600))
    font_surf=font24.render(f"I - read input push-button byte. button_byte={button_byte}",True,(255,255,255))
    ds.blit(font_surf,(100,620))
    font_surf=font24.render("ESC - exit.",True,(255,255,255))
    ds.blit(font_surf,(100,640))
    
    
    pygame.display.update() #update the display
    
pygame.display.quit()