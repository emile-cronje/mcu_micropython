from machine import Pin,SPI,PWM
import framebuf
import time
import os
from LCD_3inch5 import LCD_3inch5

if __name__=='__main__':
    LCD = LCD_3inch5()
    LCD.bl_ctrl(100)
    LCD.fill(LCD.WHITE)
    LCD.fill_rect(140,5,200,30,LCD.GREEN)
    LCD.text("Raspberry Pi Pico",170,17,LCD.WHITE)
    display_color = LCD.GREEN
    LCD.text("3.5' IPS LCD TEST",170,57,LCD.BLACK)
    
    for i in range(0,12):      
        LCD.fill_rect(i*30+60,100,30,50,(display_color))
        display_color = display_color << 1
        
    LCD.show_up()
    
    while True:      
        get = LCD.touch_get()
        
        if get != None: 
            X_Point = int((get[1]-430)*480/3270)
            
            if(X_Point>480):
                X_Point = 480
            elif X_Point<0:
                X_Point = 0
                
            Y_Point = 320-int((get[0]-430)*320/3270)
            
            if(Y_Point>220):
                LCD.fill(LCD.WHITE)
                
                if(X_Point<120):
                    LCD.fill_rect(0,60,120,100,LCD.RED)
                    LCD.text("Button 0",20,110,LCD.WHITE)
                elif(X_Point<240):
                    LCD.fill_rect(120,60,120,100,LCD.RED)
                    LCD.text("Button 1",150,110,LCD.WHITE)
                elif(X_Point<360):
                    LCD.fill_rect(240,60,120,100,LCD.RED)
                    LCD.text("Button 2",270,110,LCD.WHITE)
                else:
                    LCD.fill_rect(360,60,120,100,LCD.RED)
                    LCD.text("Button 3",400,110,LCD.WHITE)           
        else :
           LCD.fill(LCD.WHITE)
           LCD.text("Button 0",20,110,LCD.BLACK)
           LCD.text("Button 1",150,110,LCD.BLACK)
           LCD.text("Button 2",270,110,LCD.BLACK)
           LCD.text("Button 3",400,110,LCD.BLACK)
        
        LCD.show_down()  
        time.sleep(0.5)


