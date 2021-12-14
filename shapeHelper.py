from internal_classes import *
import cv2
import math  
import json

def draw_angled_rec(x0, y0, width, height, angle, color, img):
    _angle = angle * math.pi / 180.0
    b = math.cos(_angle) * 0.5
    a = math.sin(_angle) * 0.5
    pt0 = (int(x0 - a * height - b * width),
           int(y0 + b * height - a * width))
    pt1 = (int(x0 + a * height - b * width),
           int(y0 - b * height - a * width))
    pt2 = (int(2 * x0 - pt0[0]), int(2 * y0 - pt0[1]))
    pt3 = (int(2 * x0 - pt1[0]), int(2 * y0 - pt1[1]))

    cv2.line(img, pt0, pt1, color, 3)
    cv2.line(img, pt1, pt2, color, 3)
    cv2.line(img, pt2, pt3, color, 3)
    cv2.line(img, pt3, pt0, color, 3)

def drawShape(img, shape):
    if not hasattr(shape, 'type_id'):
        print(json.dumps(shape))
        return img

    if shape.type_id == 2:
        ## draw rotated rectangle
        draw_angled_rec(shape.x, shape.y, shape.h, shape.w, -90 + shape.rot_deg, (shape.color.b, shape.color.g, shape.color.r) , img)                
    elif shape.type_id == 1:
        ## draw rectangle
        img = cv2.rectangle(img, (shape.x, shape.y), (shape.h,shape.w), (shape.color.b, shape.color.g, shape.color.r), thickness=-1)        
    elif shape.type_id == 16:
        ## draw ellipse
        img = cv2.ellipse(img, (shape.x, shape.y), (shape.h,shape.w), -90 + shape.rot_deg, 0., 360, (shape.color.b, shape.color.g, shape.color.r), thickness=-1)    
    else:
        raise Exception("Unsupported shape type {0:x}".format(shape.type_id))
    return img

def appendZeroDegree(data):
    dataLength = len(data)
    if dataLength == 4:
        data.append(0)    # Add zero rotation angle
    elif dataLength > 4:
        data[4] = 0

def htmlRectangleToRotatingRectangle(hShape):    
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

def htmlShapeToRotatingRectangle(hShape):
    # Rotated rectangle
    x1,y1,x2,y2,rot_deg = hShape['data']
    r,g,b,a             = hShape['color']
    width = x2 - x1
    heigh = y2 - y1
    x = x1 + width//2
    y = y1 + heigh//2
    return Shape(hShape['type'], x, y, width, heigh, rot_deg, Color(r,g,b,a), False)

def convertCircleToRotatingEllipse(hShape):     
    if (hShape['type'] != 32): 
        raise Exception("Can only convert circles (type 32) to rotating ellipse (type 16), but got type {0:x}".format(hShape['type']))
    
    x, y, r = hShape['data']
    hShape['data'] = [x, y, r, r, 0]
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

def htmlShapeToShape(hShape):    
    # Currently only supporting circles, ellipsis, rotated ellipsis and rectangels, rotated rectangels
    hShape = convertToKnownShape(hShape)

    shapeType = hShape['type']    
    
    if shapeType == 1:   # Rectangle        
        return htmlRectangleToRotatingRectangle(hShape)
    elif shapeType == 2:     # Rotating Rectangle
        return htmlShapeToRotatingRectangle(hShape)    
    elif shapeType == 16:  # Rotating Ellipse
        # Rotated ellipsis       
        return htmlShapeToEllipsis(hShape)
    
    raise Exception("Unsupported shape type {0:x}".format(shapeType))


def addValidShape(shapes, shape):   
    sType = shape['type']
    # regtangles 1, rotated regtangles 2, ellipsis 8, rotated ellipsis 16 and circles 32 
    if sType == 1 or sType == 2 or sType == 8 or sType == 16 or sType == 32:
        shapes.append(htmlShapeToShape(shape))
    else:
        # Not handling other shapes currently
        print("Unsupported shape in geometry file.\nCurrently only supporting circles, ellipsis, rotated ellipsis , regtangles and rotated regtangles.")
        return False
  
    return True