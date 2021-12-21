# Discord: A-Dawg#0001 (AE)
# Supports: Forza Horizon 5
# Offically (OTHER v1.405.2.0, MS STORE v3.414.967.0, STEAM v1.414.967.0)
# Unofficially (most versions should work)
# License: MIT
# Year: 2021

import sys
import json
import cv2
import numpy as np
import ctypes, sys
import psutil
import ctypes
import struct
from native import *
from internal_classes import *
import colorsys
import os
import settings
import shapeHelper
import memoryDrawer

mySettings = settings.getSettings()

def lbInit():
    settings.printData(mySettings)
    settings.printData(mySettings.minimum)
    return

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def show_image(image):
    cv2.imshow("preview", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def get_pid():
    for proc in psutil.process_iter():
        try:
            if "ForzaHorizon5.exe" in proc.name():
                return proc.pid
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    print("ForzaHorizon5.exe is not running")
    return -1

def calculate_CLivery(pid):
    base_addr = get_base_address(pid)
    print("Attempting to scan for address:")
    start_address = base_addr + 0x08000000
    preAddrA = scan_block(pid, start_address, 0x02000000, b'\x12\x47\x9B\x13\x29\xD9\xA2\xB1')
    if preAddrA == -1:
        print("Unsupported version and cannot find matching pattern.")
        print("Create an issue on the Github repo...")
        return -1
    print("{0:x}".format(preAddrA))
    preAddrA += start_address
    if read_long(pid, preAddrA) == read_long(pid, preAddrA + 0x70):
        print("{0:x}".format(preAddrA))
        addrA = dereference_pointer(pid, preAddrA + 0xB8)
        print("Found at Base+{0:x}".format(preAddrA + 0xB8 - base_addr))
    addrB = dereference_pointer(pid, addrA + 0xA58)
    if addrB == 0:
        print("Create Vinyl Group menu not detected")
        return -1
    cLivery = dereference_pointer(pid, addrB + 0x8)
    if cLivery == 0:
        print("Create Vinyl Group menu not detected")
        return -1
    return cLivery

def getSaleDivisorForShapeType(typeId: int): 
     scale_divisor = 63 
     if typeId == 2:
        scale_divisor = 127
     elif typeId == 16:
        scale_divisor = 63
     else: 
        scale_divisor = 127

     return scale_divisor

def main(args):    
    lbInit();
    if not is_64bit():
        print("Your Python version is 32-bit. Please install 64-bit Python.\nThis is required for IPC with Forza Horizon as it is 64-bit.")
        return
    if len(args) == 1:
        print("You must pass in a Geometrize exported .json file as an argument!")
        return
    path = " ".join(args[1:])
    if not os.path.isfile(path):
        print("{} is not a valid file path!".format(path))
    if path.split('.')[-1].lower() != "json":
        print("Expected 1 file as the only argument.\nAn exported json geometry file from the Geometrize application.")
        return
    with open(path) as f:
        # load our json
        try:
            data = json.load(f)
            # Validate the loaded json
            try:
                valid = True # len(data['shapes'][0]['data']) == 4
                print(data['shapes'][0]['type'])
                valid = valid and data['shapes'][0]['type'] > 0
                valid = valid and len(data['shapes'][0]['color']) == 4
                if not valid:
                    print("Not a valid Geometrize geometry export .json file")
                    return
            except:
                print("Not a valid Geometrize geometry export .json file")
                return
        except:
            print("Not a valid .json file")
            return

    # validation and build our collection of shapes
    image_w, image_h = data['shapes'][0]['data'][2:]
    bg_r, bg_g, bg_b, bg_a = data['shapes'][0]['color']
    shapes = []
    
    # If the exported geometry has a rectangle background, add it
    if bg_a > 0:
        shapes.append(Shape(1, int(image_w//2), int(image_h//2), image_w, image_h, 0, Color(bg_r,bg_g,bg_b,bg_a), False))

    for shape in data['shapes'][1:]:
        if shapeHelper.addValidShape(shapes, shape):
            continue
        else:
            return
        
    if len(shapes) == 0:
        print("No shapes were loaded. Check your exported Geometrize geometry .json")
        return
    
    # draw our validated shapes as a preview
    preview = np.zeros((image_h, image_w, 3), np.uint8)
    preview = cv2.rectangle(preview, (0,0), (image_w, image_h), (bg_b, bg_g, bg_r, bg_a), thickness=-1)
    for shape in shapes:
        preview = shapeHelper.drawShape(preview, shape)
    
    # show our preview before putting it in forza
    print("Here is a preview of your image, click it then press any key to start!")
    show_image(preview)
    cv2.imwrite("preview.png", preview)
    
    # Finding the game PID
    pid = get_pid()

    # Calculate the pointer chain to the cLiveryLayerTable
    cLivery = calculate_CLivery(pid)
    if cLivery == -1:
        return
    print("CLivery found at {0:x}".format(cLivery))
    cLiveryGroup = dereference_pointer(pid, cLivery + 0x20)
    if cLiveryGroup == 0:
        print("cLiveryGroup is invalid...")
        print("You are probably not in `Create Vinyl Group` menu...")
        return
    print("CLiveryGroup found at {0:x}".format(cLiveryGroup))
    
    # If we have less than 100 shapes, user has likely made a mistake
    current_livery_count = read_int(pid, cLiveryGroup + 0x5A)

    #LB change minimum from 100 to 2
    if current_livery_count < mySettings.minimum:
        print("READ THE INSTRUCTIONS")
        print("You must load a vinyl group (ALL SPHERES) with your desired shape count (minimum {0:x}) first!".format(mySettings.minimum))
        print("500, 1000, 1500, 2000 or 3000 is recommended")
        print("Make sure to ungroup the vinyl before starting also!")
        return

    cLiveryLayerTable = dereference_pointer(pid, cLiveryGroup + 0x78)
    if cLiveryLayerTable == 0:
        print("cLiveryLayer table is invalid...")
        print("You are probably not in `Create Vinyl Group` menu..")
        return
    print("CLiveryLayer table found at {0:x}".format(cLiveryLayerTable))

    # Trim the shapes back to 3000 minus the 4 masking rectangles if necessary
    if len(shapes) > 2996:
        shapes = shapes[:2996]
    
    # Trim the shapes back to current_livery_count minus the 4 masking rectangles if necessary
    if len(shapes) > int(current_livery_count - 4):
        shapes = shapes[:int(current_livery_count-4)]

    # Add the 4 masking rectangles
    shapes.append(Shape(1, -int(image_w//4), int(image_h//2), int(image_w//2), int(image_h*1.5), 0, Color(0,0,0,255), True))
    shapes.append(Shape(1, image_w + int(image_w//4), int(image_h//2), int(image_w//2), int(image_h*1.5), 0, Color(0,0,0,255), True))
    shapes.append(Shape(1, int(image_w//2), -int(image_h//4), image_w + int(image_w), int(image_h//2), 0, Color(0,0,0,255), True))
    shapes.append(Shape(1, int(image_w//2), image_h + int(image_h//4), image_w + int(image_w), int(image_h//2), 0, Color(0,0,0,255), True))
    
    # Enumerate the shapes, drawing them as we go
    for i,shape in enumerate(shapes):
        memoryDrawer.draw_memory_shape(pid, shape, i, cLiveryLayerTable, current_livery_count)
    
    print("DONE!")

    # Show the background color as the ideal car color in HSV format
    h,s,v = colorsys.rgb_to_hsv(bg_r / float(255), bg_g / float(255), bg_b / float(255))
    print("The ideal background color for the car is:\n{:.2f},{:.2f},{:.2f}".format(h,s,v))

if __name__ == "__main__":
    if is_admin():
        # Capture any exceptions
        try:
            main(sys.argv)
        except BaseException:
            import sys
            print(sys.exc_info()[0])
            import traceback
            print(traceback.format_exc())
        finally:
            print("Press Enter to continue ...")
            input()
    else:
        # Run as admin
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)