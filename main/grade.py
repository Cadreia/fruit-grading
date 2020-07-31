from __future__ import division
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, HttpResponse, redirect
from django.contrib import messages
from django.http.response import StreamingHttpResponse
import bcrypt
from PIL import Image, ImageDraw
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .serializers import FileSerializer
from django.contrib.auth import logout
from .forms import LoginForm, SignUpForm
from main.models import User, Person, ThiefLocation
from django.core.mail import EmailMessage
from django.conf import settings
from main.camera import IPWebCam
from main.grade import *

import io
import os
import random
import cv2
import numpy as np
import time
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
sample = 3
# define range of red color in HSV
lower_red2 = np.array([170, 50, 50])
upper_red2 = np.array([180, 255, 255])
#orange_lower_1 = np.array([0, 150, 150])
#orange_upper_1 = np.array([20, 255, 255])

def preProcess(image1):
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

def gradeByColor(test_image):
    #test_image = cv2.imread("../media/IMG_20200704_125357_057_2SLvqQx.jpg")
    #test_image = cv2.imread(os.path.join(settings.PROJECT_ROOT, ".."+uploaded_file_url))

    #img_size = gradeBySize(test_image)

    kernelOpen = np.ones((5, 5))
    kernelClose = np.ones((20, 20))

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
    cv2.imwrite(os.path.join(settings.PROJECT_ROOT, '../media/edge.jpg'), edge_img)
    edge_file_url = '../media/edge.jpg'

    frame = edge_img

    # converting BGR to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # define range of red color in HSV
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])

    # create a red HSV colour boundary and
    # threshold HSV image
    redmask1 = cv2.inRange(hsv, lower_red1, upper_red1)

    # create a red HSV colour boundary and
    # threshold HSV image
    redmask2 = cv2.inRange(hsv, lower_red2, upper_red2)

    redmask = redmask1+redmask2
    maskOpen = cv2.morphologyEx(redmask, cv2.MORPH_OPEN, kernelOpen)
    maskClose = cv2.morphologyEx(maskOpen, cv2.MORPH_CLOSE, kernelClose)

    maskFinal = maskClose
    # cv2.imshow('Red_Mask:',maskFinal)
    cv2.imwrite(os.path.join(settings.PROJECT_ROOT, '../media/mask.jpg'), maskFinal)
    mask_file_url = '../media/mask.jpg'

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
    color_grade = ''

    if ripe_perc < 30:
        print("Low Ripeness")
        ripe_rate = "Low Ripeness"
        color_grade = "C"
    elif ripe_perc > 30 and ripe_perc < 80:
        print("Medium Ripeness")
        ripe_rate = "Medium Ripeness"
        color_grade = "B"
    else:
        print("High Ripeness")
        ripe_rate = "High Ripeness"
        color_grade = "A"

    #cv2.imshow('FOriginal', test_image)
    #gradeByDefect(test_image)
    #print(orange_grade)
    #print(percentage_of_defects)
    #print("Image size: {}".format(img_size))

    color_context = {
        'edge_file_url': edge_file_url,
        'mask_file_url': mask_file_url,
        'ripe_perc': str(round(ripe_perc, 2)),
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
    print("COntour Area is: {}".format(largest_area))
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
    print("contour h*w: {}".format(width*height))
    size_context = {
        'size': size,
        'size_grade': size_grade
    }
    return size_context

def gradeByDefect(prepImage, contours):
    # Grade orange
    grade_img(prepImage, 1, contours)
    grade_img(prepImage, 2, contours)
    calculate_defect_grade()


def grade_img(image1, number, contours):
    # cv2.drawContours(result, contours, -1, (0, 255, 0), 1).
    specimen_area_1 = 0
    specimen_area_2 = 0
    global number_of_defects
    global area_of_defects_1
    global area_of_defects_2
    global area_of_specimen_1
    global area_of_specimen_2
    # Loop through the contours found in the image.
    for c in contours:
        # If contour area is big enough, then continue with loop.
        if cv2.contourArea(c) <= 1500:
            continue
        # Largest contour will be area of the specimen.
        if number == 1:
            if cv2.contourArea(c) > specimen_area_1:
                specimen_area_1 = cv2.contourArea(c)
                area_of_specimen_1 = specimen_area_1
        elif number == 2:
            if cv2.contourArea(c) > specimen_area_2:
                specimen_area_2 = cv2.contourArea(c)
                area_of_specimen_2 = specimen_area_2
                print(area_of_specimen_2)

        # Add to number of defects.
        number_of_defects += 1
        # Get the location and radius of a cirlce that covers the contour area.
        (x, y), radius = cv2.minEnclosingCircle(c)
        # Set center and radius values.
        center = (int(x), int(y))
        radius = int(radius)
        # Draw circle on original image where contour was found.
        cv2.circle(image1, center, radius, (0, 255, 0), 10)
        # Add area of contours to the area_of_defects to get total area of defects.
        if number == 1:
            area_of_defects_1 += cv2.contourArea(c)
        elif number == 2:
            area_of_defects_2 += cv2.contourArea(c)

    print("contour area is: {}".format(area_of_specimen_1))

    # Depending on which specimen is being analysed, save the image with suffix '1' or '2'.
    if number == 1:
        print("Image 1 analysed and saved")
    elif number == 2:
        print("Image 2 analysed and saved")


def calculate_defect_grade():
    global percentage_of_defects
    global orange_grade
    global total_area_of_specimen
    global area_of_specimen_1
    global area_of_specimen_2

    # Total area of specimen.
    total_area_of_specimen = (area_of_specimen_1 + area_of_specimen_2)
    # Total defected area.
    total_area_of_defects = (area_of_defects_1 + area_of_defects_2)
    # Take total area from area of defects to get total area of defects.
    total_area_of_defects = total_area_of_defects - total_area_of_specimen
    # Work out percentage of defected area in relation to the area of the orange.
    #percentage_of_defects = (total_area_of_defects / total_area_of_specimen) * 100
    percentage_of_defects = (total_area_of_defects / total_area_of_specimen) * 100
    print(percentage_of_defects)
    # Look at number of defects and area of defects of selected orange and grade the orange appropriately.
    if percentage_of_defects < 10:
        orange_grade = 'A'
        print(orange_grade)
    elif percentage_of_defects > 10 and percentage_of_defects < 40:
        orange_grade = 'B'
        print(orange_grade)
    else:
        orange_grade = 'C'
        print(orange_grade)
    print("Percentage Damaged: " + str(round(percentage_of_defects, 3)) + "%.")
    #ui.defects_label.setText("Number of Defects: " + str(number_of_defects) + '.')
    print("Grade of Specimen " + str(orange_grade) + '.')
