from sys import winver
from internal_classes import *
import cv2
import math  
import json
import numpy as np

def get_rectangle_points(centerPoint, dimensions, angle):
    x, y = centerPoint
    width, height = dimensions
    _angle = angle * math.pi / 180.0
    b = math.cos(_angle) * 0.5
    a = math.sin(_angle) * 0.5
    point1 = (int(x - a * height - b * width), int(y + b * height - a * width))
    point2 = (int(x + a * height - b * width), int(y - b * height - a * width))
    point3 = (int(2 * x - point1[0])         , int(2 * y - point1[1]))
    point4 = (int(2 * x - point2[0])         , int(2 * y - point2[1]))

    return np.array([point1, point2, point3, point4])

def draw_angled_rectangle(image, centerPoint, dimensions, angle, color , fill:bool):        
    points = get_rectangle_points(centerPoint, dimensions, angle)
    contours = [points]
    if fill:
        cv2.fillPoly(image, pts = contours, color = color)
    else:
        thickness = 2
        cv2.drawContours(image, contours, 0, color, thickness)        

def drawShape(img, shape):
    if not hasattr(shape, 'type_id'):
        print(json.dumps(shape))
        return img

    if shape.type_id == 2:
        ## draw rotated rectangle        
        draw_angled_rectangle(img, (shape.x, shape.y), (shape.h, shape.w), -90 + shape.rot_deg, (shape.color.b, shape.color.g, shape.color.r), True)                

    elif shape.type_id == 1:
        ## draw rectangle
        img = cv2.rectangle(img, (shape.x, shape.y), (shape.h,shape.w), (shape.color.b, shape.color.g, shape.color.r), thickness=-1)        

    elif shape.type_id == 4:  # triangle
        ## draw rectangle for now
        img = cv2.rectangle(img, (shape.x, shape.y), (shape.h,shape.w), (shape.color.b, shape.color.g, shape.color.r), thickness=-1)  
    elif shape.type_id == 16:
        ## draw ellipse
        img = cv2.ellipse(img, (shape.x, shape.y), (shape.h,shape.w), -90 + shape.rot_deg, 0., 360, (shape.color.b, shape.color.g, shape.color.r), thickness=-1)    
    else:
        raise Exception("Unsupported shape type {0:x}".format(shape.type_id))
    return img


def appendAt(data, index:int, value):
    dataLength = len(data)
    if dataLength < index:
        raise Exception("appendAt currently does not support shorter Array {0:x}, {1:x}".format(dataLength, index ))
    if dataLength == index:
        data.append(value)    # Add zero rotation angle
    elif dataLength > index:
        data[index] = value
    return data

def appendZeroDegree(data):
    return appendAt(data, 4, 0)


def htmlRectangleToRotatingRectangle(hShape) -> Shape:
    hShape['type'] = 2 # Rotated rectangle
    appendZeroDegree(hShape['data'])    
    return htmlShapeToRotatingRectangle(hShape)

def htmlShapeToEllipsis(hShape):
    # Rotated ellipsis
    # hShape.color = [r,g,b,a]
    # hShape.data = [x,y,w,h,rot_deg]
    x,y,w,h,rot_deg = hShape['data']
    r,g,b,a         = hShape['color']
    return Shape(hShape['type'], x, y, w, h, rot_deg, Color(r,g,b,a), False)

def htmlShapeToRotatingRectangle(hShape) -> Shape:
    # Rotated rectangle
    x1,y1,x2,y2,rot_deg = hShape['data']
    r,g,b,a             = hShape['color']
    width = x2 - x1
    heigh = y2 - y1
    x = x1 + width//2
    y = y1 + heigh//2
    return Shape(hShape['type'], x, y, width, heigh, rot_deg, Color(r,g,b,a), False)

def htmlShapeToRotatingTriangle(hShape):
    # Rotated rectangle
    x1,y1,x2,y2,x3,y3 = hShape['data']
    r,g,b,a           = hShape['color']

    rot_deg = 0
    width = x2 - x1
    heigh = (y3 - y1)
    x = x1 + width//2
    y = y1 + heigh//2
    heigh = - heigh
    return Shape(hShape['type'], x, y, width, heigh, rot_deg, Color(r,g,b,a), False)

def convertCircleToRotatingEllipse(hShape):     
    if (hShape['type'] != 32): 
        raise Exception("Can only convert circles (type 32) to rotating ellipse (type 16), but got type {0:x}".format(hShape['type']))
    
    x, y, r = hShape['data']
    appendAt(hShape['data'], 3, r)
    appendZeroDegree(hShape['data'])    
    hShape['type'] = 16         # change type from circle to rotating ellipse    

    return hShape

def convertEllipseToRotatingEllipse(hShape):     
    if (hShape['type'] != 8): 
        raise Exception("Can only convert ellipse (type 8) to rotating ellipse (type 16), but got type {0:x}".format(hShape['type']))
    hShape['type'] = 16         # change type from circle to rotating ellipse
    appendZeroDegree(hShape['data'])    

    return hShape

def convertToKnownShape(hShape):
    shapeType = hShape['type']

    if shapeType == 32:     # Circle
        hShape = convertCircleToRotatingEllipse(hShape)        

    elif shapeType == 8:      # Ellipse
        hShape = convertEllipseToRotatingEllipse(hShape)

    return hShape

def htmlShapeToShape(hShape) -> Shape:    
    # Currently only supporting circles, ellipsis, rotated ellipsis and rectangels, rotated rectangels
    hShape = convertToKnownShape(hShape)

    shapeType = hShape['type']    
    
    if shapeType == 1:   # Rectangle        
        return htmlRectangleToRotatingRectangle(hShape)
    elif shapeType == 2:     # Rotating Rectangle
        return htmlShapeToRotatingRectangle(hShape)    
    elif shapeType == 4:     # Triangle
        return htmlShapeToRotatingTriangle(hShape)    
    elif shapeType == 16:  # Rotating Ellipse
        # Rotated ellipsis       
        return htmlShapeToEllipsis(hShape)
    
    raise Exception("Unsupported shape type {0:x}".format(shapeType))


def addValidShape(shapes, shape) -> bool:
    sType = shape['type']
    # regtangles 1, rotated regtangles 2, triangle 4, ellipsis 8, rotated ellipsis 16 and circles 32 
    if sType == 1 or sType == 2 or sType == 4 or sType == 8 or sType == 16 or sType == 32:
        shapes.append(htmlShapeToShape(shape))
    else:
        # Not handling other shapes currently
        print("Unsupported shape in geometry file.\nCurrently only supporting circles, ellipsis, rotated ellipsis, triangles, regtangles and rotated regtangles.")
        return False
  
    return True