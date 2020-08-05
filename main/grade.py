from __future__ import division
from django.core.files.storage import FileSystemStorage
import bcrypt
from PIL import Image, ImageDraw
from .serializers import FileSerializer
from django.core.mail import EmailMessage
from django.conf import settings

import io
import os
import random
import cv2
import numpy as np
import requests
from copy import deepcopy


# initialize global variables
number_of_defects = 0
area_of_defects_1 = 0
area_of_defects_2 = 0
total_area_of_defects = 0
area_of_specimen_1 = 0
area_of_specimen_2 = 0
total_area_of_specimen = 0
percentage_of_defects = 0
orange_grade = ''
i = 1
# define range of red color in HSV
lower_red2 = np.array([170, 50, 50])
upper_red2 = np.array([180, 255, 255])
lower_red1 = np.array([0, 50, 50])
upper_red1 = np.array([10, 255, 255])
#orange_lower_1 = np.array([0, 150, 150])
#orange_upper_1 = np.array([20, 255, 255])
kernelOpen = np.ones((5, 5))
kernelClose = np.ones((20, 20))

def preProcess2(image1):
    # at white background and also black backgorund for other parameters have to change======================
    gray = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray, 75, 255, cv2.THRESH_BINARY)
    image1[thresh == 255] = 0
    # imS = cv2.resize(image1, (960, 940))
    #cv2.imshow('boundaery image', image1)
    cv2.destroyAllWindows()
    # print("2")
    # =============================change colour image to gray image======================================================
    image1gray = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    # imS = cv2.resize(image1gray, (960, 940))
    #cv2.imshow('boundary image', image1gray)
    cv2.destroyAllWindows()
    # =========================changing gray image to binary for time efficiency================================================================
    # ===If the pixel value is smaller than the threshold, it is set to 0, otherwise it is set to a maximum value===========
    # its input 1 argument is source Image,2nd is threshold pixel ,3rd is maximum pixel,4th is type of thresholding
    # its output 1st argument is thresholding value use ie.. 2nd argument of imput
    ret, thresh = cv2.threshold(image1gray, 45, 255, 0)
    # =====================finding contours=================================
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def preProcess(image1):
        # Convert image from BGR to HSV.
    hsv = cv2.cvtColor(image1, cv2.COLOR_BGR2HSV)
        # Define lower and upper boundaries of orange in HSV.
        # HSV uses max values as H: 180, S: 255, V: 255 for HSV.
        # This compares to the normal max values of H: 360, S: 100, V: 100.
        # Setting upper and lower bounds for first mask.
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    redmask = mask1 + mask2
        # Bitwise-AND mask and original image (combine the two).
    result = cv2.bitwise_and(image1, image1, mask=redmask)
    #maskOpen = cv2.morphologyEx(redmask, cv2.MORPH_OPEN, kernelOpen)
    #maskClose = cv2.morphologyEx(maskOpen, cv2.MORPH_CLOSE, kernelClose)
    #maskFinal = maskClose

    cv2.imwrite(os.path.join(settings.PROJECT_ROOT, '../media/bitwise{}.jpg'.format(i)), result)

    gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        # ret, thresh = cv2.threshold(gray, 127, 255, 3)
    contours, hierarchy = cv2.findContours(gray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def gradeByColor(test_image, fruitName):
    global i

    # resize image
    scale_percent = 10  # percent of original size
    width = int(test_image.shape[1] * scale_percent / 100)
    height = int(test_image.shape[0] * scale_percent / 100)
    dim = (width, height)
    imgOriginalScene = cv2.resize(test_image, dim, interpolation=cv2.INTER_AREA)

    #cv2.imwrite(i+'.jpeg', test_image)

    frame = imgOriginalScene
    edge_img = deepcopy(imgOriginalScene)

    # finds edges in the input image image and
    # marks them in the output map edges
    edged = cv2.Canny(edge_img, 50, 100)
    edged = cv2.dilate(edged, None, iterations=1)
    edged = cv2.erode(edged, None, iterations=1)

    # find contours in the edge map
    cnts, h = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    max_contA = cv2.contourArea(cnts[0])
    max_cont = max(cnts, key=cv2.contourArea)

    for i in range(len(cnts)):
        x, y, w, h = cv2.boundingRect(max_cont)
        cv2.rectangle(edge_img, (x, y), (x+w, y+h), (0, 0, 255), 2)
    croppedk = frame[y:y+h, x:x+w]

    # Display the fruit
    # cv2.imshow('Edges',edge_img)

    # save edge_img to /media
    cv2.imwrite(os.path.join(settings.PROJECT_ROOT, '../media/cnt{}.jpg'.format(i)), edged)
    cnt_file_url = '/media/cnt{}.jpg'.format(i)
    print(cnt_file_url)

    cv2.imwrite(os.path.join(settings.PROJECT_ROOT, '../media/edge{}.jpg'.format(i)), edge_img)
    edge_file_url = '/media/edge{}.jpg'.format(i)

    cv2.imwrite(os.path.join(settings.PROJECT_ROOT, '../media/cropped{}.jpg'.format(i)), croppedk)
    cropped_file_url = '/media/cropped{}.jpg'.format(i)
    print(cropped_file_url)

    frame = croppedk

    # converting BGR to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # define range of red color in HSV

    # create a red HSV colour boundary and
    # threshold HSV image
    redmask1 = cv2.inRange(hsv, lower_red1, upper_red1)

    # create a red HSV colour boundary and
    # threshold HSV image
    redmask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    redmask = redmask1+redmask2

    cnt_r = 0
    for r in redmask:
        cnt_r = cnt_r+list(r).count(255)
    print("Redness ", cnt_r)

    lower_green = np.array([50, 50, 50])
    upper_green = np.array([70, 255, 255])
    greenmask = cv2.inRange(hsv, lower_green, upper_green)
    # cv2.imshow('Green_Mask:',greenmask)
    cnt_g = 0
    for g in greenmask:
        cnt_g = cnt_g+list(g).count(255)
    print("Greenness ", cnt_g)

    lower_yellow = np.array([20, 50, 50])
    upper_yellow = np.array([30, 255, 255])
    yellowmask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    # cv2.imshow('Yellow_Mask:',yellowmask)
    cnt_y = 0
    for y in yellowmask:
        cnt_y = cnt_y+list(y).count(255)
    print("Yellowness ", cnt_y)

    print(fruitName)
    maskOpen = None
    if fruitName == 'tomato':
        maskOpen = cv2.morphologyEx(redmask, cv2.MORPH_OPEN, kernelOpen)
    elif fruitName == 'apple':
        maskOpen = cv2.morphologyEx(greenmask, cv2.MORPH_OPEN, kernelOpen)
    elif fruitName == 'papaya' or fruitName == 'orange':
        maskOpen = cv2.morphologyEx(yellowmask, cv2.MORPH_OPEN, kernelOpen)

    maskClose = cv2.morphologyEx(maskOpen, cv2.MORPH_CLOSE, kernelClose)
    maskFinal = maskClose
    
    # cv2.imshow('Red_Mask:',maskFinal)
    cv2.imwrite(os.path.join(settings.PROJECT_ROOT, '../media/mask{}.jpg'.format(i)), maskFinal)
    mask_file_url = '/media/mask{}.jpg'.format(i)
    print(mask_file_url)

    # Calculate ripeness
    tot_area = cnt_r+cnt_y+cnt_g
    rperc = cnt_r/tot_area
    yperc = cnt_y/tot_area
    gperc = cnt_g/tot_area

    # Adjust the limits for your fruit
    ylimit = 0.3
    rlimit = 0.8
    glimit = 0.4
    ripe_rate = ''
    ripe_perc = rperc * 100
    orange_ripe_perc = yperc * 100
    apple_ripe_perc = gperc * 100
    color_grade = ''

    if fruitName == 'tomato':
        if ripe_perc < 30:
            ripe_rate = "Low Ripeness"
            color_grade = "C"
        elif ripe_perc > 30 and ripe_perc < 80:
            ripe_rate = "Medium Ripeness"
            color_grade = "B"
        else:
            ripe_rate = "High Ripeness"
            color_grade = "A"
    elif fruitName == 'orange':
        if orange_ripe_perc < 30:
            ripe_rate = "Low Ripeness"
            color_grade = "C"
        elif orange_ripe_perc > 30 and orange_ripe_perc < 80:
            ripe_rate = "Medium Ripeness"
            color_grade = "B"
        else:
            ripe_rate = "High Ripeness"
            color_grade = "A"
    elif fruitName == 'apple':
        if apple_ripe_perc < 30:
            ripe_rate = "Low Ripeness"
            color_grade = "C"
        elif apple_ripe_perc > 30 and apple_ripe_perc < 80:
            ripe_rate = "Medium Ripeness"
            color_grade = "B"
        else:
            ripe_rate = "High Ripeness"
            color_grade = "A"
    elif fruitName == 'papaya':
        if orange_ripe_perc < 30:
            ripe_rate = "Low Ripeness"
            color_grade = "C"
        elif orange_ripe_perc > 30 and orange_ripe_perc < 80:
            ripe_rate = "Medium Ripeness"
            color_grade = "B"
        else:
            ripe_rate = "High Ripeness"
            color_grade = "A"
    else:
        pass

    

    #cv2.imshow('FOriginal', test_image)
    #gradeByDefect(test_image)
    #print(orange_grade)
    #print(percentage_of_defects)
    #print("Image size: {}".format(img_size))

    color_context = {
        'cnt_file_url': cnt_file_url,
        'edge_file_url': edge_file_url,
        'cropped_file_url': cropped_file_url,
        'mask_file_url': mask_file_url,
        'ripe_perc': str(round(ripe_perc, 2)),
        'orange_ripe_perc': str(round(orange_ripe_perc, 2)),
        'apple_ripe_perc': str(round(apple_ripe_perc, 2)),
        'ripe_rate': ripe_rate,
        'color_grade': color_grade
        #'percentage_of_defects': str(round(percentage_of_defects, 2)),
        #'orange_grade': orange_grade
        #'img_size': img_size
    }
    return color_context

def gradeBySize(contours):
    largest_contour = []
    largest_area = 0
    i = 0
    for contour in contours:
        # print(i)
        # i=i+1
        area = cv2.contourArea(contour)
        if area > largest_area:
            largest_area = area
            largest_contour = contour
    #print("COntour Area is: {}".format(largest_area))
    start_x, start_y, width, height = cv2.boundingRect(largest_contour)
    # print(start_x,start_y,width,height)
    # print("area of apple is ",width*height)
    size = -1
    size_grade = ''
    if((largest_area) <= 64000):
        size = "SMALL"
        size_grade = "C"
    if((largest_area) > 64000 and (largest_area) <= 1500000):
        size = "MEDIUM"
        size_grade = "B"
    else:
        size = "LARGE"
        size_grade = "A"

    # print(largest_contour,largest_area)
    # cv2.drawContours(image2, [largest_contour], -1, (255, 255, 255), 3)
    # cv2.rectangle(image2, (start_x,start_y), (start_x+width, start_y+height), (255, 255, 255), 2)
    # # imS = cv2.resize(image2, (960, 940))
    # cv2.imshow('boundaery image',image2)
    # cv2.destroyAllWindows()
    # image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2RGB)
    # image2=Image.fromarray((image2).astype(np.uint8))
    # image2.save('out.jpg')
    #print("contour h*w: {}".format(width*height))
    size_context = {
        'size': size,
        'size_grade': size_grade
    }
    return size_context

def gradeByDefect(prepImage, contours):
    # Grade orange
    grade_img(prepImage, contours)
    defect_context = calculate_defect_grade()
    return defect_context


def grade_img(image1, contours):
    # cv2.drawContours(result, contours, -1, (0, 255, 0), 1).
    specimen_area_1 = 0
    global area_of_defects_1
    area_of_defects_1 = 0
    global area_of_specimen_1, i
    # Loop through the contours found in the image.
    for c in contours:
        # If contour area is big enough, then continue with loop.
        if cv2.contourArea(c) <= 1500:
            continue
        # Largest contour will be area of the specimen.
        if cv2.contourArea(c) > specimen_area_1:
            specimen_area_1 = cv2.contourArea(c)
            area_of_specimen_1 = specimen_area_1

        # Add to number of defects.
        
        # Get the location and radius of a cirlce that covers the contour area.
        (x, y), radius = cv2.minEnclosingCircle(c)
        # Set center and radius values.
        center = (int(x), int(y))
        radius = int(radius)
        # Draw circle on original image where contour was found.
        cv2.circle(image1, center, radius, (0, 255, 0), 10)
        # Add area of contours to the area_of_defects to get total area of defects.


        cv2.imwrite(os.path.join(settings.PROJECT_ROOT, '../media/defect{}.jpg'.format(i)), image1)
        defect_file_url = '/media/defect{}.jpg'.format(i)


        area_of_defects_1 += cv2.contourArea(c)


    # Depending on which specimen is being analysed, save the image with suffix '1' or '2'.
    #print("Image 1 analysed and saved")


def calculate_defect_grade():
    global percentage_of_defects
    global orange_grade
    global total_area_of_specimen
    global area_of_specimen_1

    # Total area of specimen.
    total_area_of_specimen = area_of_specimen_1
    # Total defected area.
    total_area_of_defects = area_of_defects_1
    # Take total area from area of defects to get total area of defects.
    total_area_of_defects = total_area_of_defects - total_area_of_specimen
    # Work out percentage of defected area in relation to the area of the orange.
    #percentage_of_defects = (total_area_of_defects / total_area_of_specimen) * 100
    percentage_of_defects = (total_area_of_defects / total_area_of_specimen) * 100
    # Look at number of defects and area of defects of selected orange and grade the orange appropriately.
    if percentage_of_defects < 10:
        orange_grade = 'A'
    elif percentage_of_defects > 10 and percentage_of_defects < 40:
        orange_grade = 'B'
    else:
        orange_grade = 'C'
    #ui.defects_label.setText("Number of Defects: " + str(number_of_defects) + '.')

    defect_context = {
        'orange_grade': orange_grade,
        'percentage_of_defects': percentage_of_defects
    }
    return defect_context