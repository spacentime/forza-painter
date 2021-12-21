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

class ForzaShapes:
    "This is Forza Shapes memory value"
    rectangle     = 101
    elipse        = 102
    triangle      = 103
    rightTriangle = 104




def draw_memory_shape(pid: int, shape: Shape, index: int, cLiveryLayerTable: int, liveryCount: int):
    if index >= liveryCount:
        return
    current_layer_address = dereference_pointer(pid, cLiveryLayerTable + (index * 0x8))
    print("{0:x}".format(current_layer_address))
    pos_data = struct.pack('f', shape.x) + struct.pack('f', -shape.y)
    
    write_process_memory(pid, current_layer_address + 0x18, pos_data)
    scale_divisor = 63 if shape.type_id == 16 else 127
    scale_data = struct.pack('f', shape.w / scale_divisor) + struct.pack('f', shape.h / scale_divisor)
    
    write_process_memory(pid, current_layer_address + 0x28, scale_data)
    rot_data = struct.pack('f', 360 - shape.rot_deg)
    
    write_process_memory(pid, current_layer_address + 0x50, rot_data)
    color_data = shape.color.get_struct()
    
    write_process_memory(pid, current_layer_address + 0x74, color_data)
    if shape.type_id == 16:   # Elipse
        shape_id_data = struct.pack('B', ForzaShapes.elipse)
        write_process_memory(pid, current_layer_address + 0x7A, shape_id_data)
    
    elif shape.type_id == 2:  # Rotating Rectangle
        shape_id_data = struct.pack('B', ForzaShapes.rectangle)
        write_process_memory(pid, current_layer_address + 0x7A, shape_id_data)
    
    elif shape.type_id == 1:  # Rectangle
        shape_id_data = struct.pack('B', ForzaShapes.rectangle)
        write_process_memory(pid, current_layer_address + 0x7A, shape_id_data)

    elif shape.type_id == 4:  # Triangle
        shape_id_data = struct.pack('B', ForzaShapes.rightTriangle)  
        write_process_memory(pid, current_layer_address + 0x7A, shape_id_data)
    
    mask_flag = struct.pack('B', 1 if shape.is_mask else 0)
    write_process_memory(pid, current_layer_address + 0x78, mask_flag)
