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
from main.models import *
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


class FileView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file_serializer = FileSerializer(data=request.data)
        if file_serializer.is_valid():
            file_serializer.save()
            return Response(file_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def index(request):
    return render(request, 'home/home_page.html')


def home(request):
    return render(request, 'home/home_page.html')

def index2(request):
    form = LoginForm(request.POST or None)

    msg = None

    if request.method == "POST":

        if form.is_valid():
            login_username = form.cleaned_data.get("username")
            login_password = form.cleaned_data.get("password")

            if (User.objects.filter(username=login_username).exists()):
                user = User.objects.filter(username=login_username)[0]
                if (bcrypt.checkpw(login_password.encode('utf-8'), user.password.encode('utf-8'))):
                    request.session['id'] = user.id
                    request.session['name'] = user.first_name
                    request.session['surname'] = user.last_name
                    request.session['email'] = user.email
                    request.session['username'] = user.username
                    messages.add_message(request, messages.INFO, 'Welcome to fruit quality detection system ' + user.first_name+' '+user.last_name)
                    return redirect(success)
                else:
                    messages.error(request, 'Oops, Wrong password, please try a diffrerent one')
                    return redirect('/login')
            else:
                messages.error(request, 'Oops, This User does not exist')
                return redirect('/login')

        else:
            msg = 'Error validating the form'
    return render(request, "session/login2.html", {"form": form, "msg": msg})


def addUser(request):
    return render(request, 'home/add_user.html')

def addCompany(request):
    return render(request, 'home/add_company.html')

def addBranch(request):
    return render(request, 'home/add_branch.html')

def showRegister(request):
    msg = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            signup_firstname = form.cleaned_data.get("name")
            signup_lastname = form.cleaned_data.get("surname")
            signup_email = form.cleaned_data.get("email")
            signup_username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            hashed_password = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt())

            user = User.objects.create(
                first_name=signup_firstname,
                last_name=signup_lastname,
                username=signup_username,
                email=signup_email,
                password=hashed_password.decode('utf-8'))
            user.save()

            # send activation email
            email_subject = "Activate your account"
            email_body = "Test body :)"
            email_sender = "audreyndum@gmail.com"
            email_recipient = [signup_email]
            email = EmailMessage(
                email_subject,
                email_body,
                email_sender,
                email_recipient
            )
            email.send(fail_silently=True)
            # end

            messages.add_message(request, messages.INFO, 'User successfully created. Please Sign In')
            success = True

            return redirect(index2)

        else:
            msg = 'Form is not valid'
    else:
        form = SignUpForm()
    return render(request, "session/register.html", {"form": form, "msg": msg, "success": success})

def logout_view(request):
    logout(request)
    messages.add_message(request, messages.INFO, "Successfully logged out")
    return redirect(home)


def dashboard(request):
    return render(request, 'home/dashboard.html')


def viewUsers(request):
    users = User.objects.all()
    context = {
        "users": users
    }
    return render(request, 'home/view_users.html', context)

def saveUser(request):
    errors = User.objects.validator(request.POST)
    if len(errors):
        for tag, error in errors.items():
            messages.error(request, error, extra_tags=tag)
        return redirect(addUser)

    hashed_password = bcrypt.hashpw(request.POST['password'].encode(), bcrypt.gensalt())
    user = User.objects.create(
        first_name=request.POST['first_name'],
        last_name=request.POST['last_name'],
        email=request.POST['email'],
        password=hashed_password)
    user.save()
    messages.add_message(request, messages.INFO, 'User successfully added')
    return redirect(viewUsers)

def viewCompanies(request):
    companies = Company.objects.all()
    companies = Company.objects.filter(user__id = request.session['id'])
    context = {
        "companies": companies
    }
    return render(request, 'home/view_companies.html', context)

def saveCompany(request):
    errors = Company.objects.validator(request.POST)
    if len(errors):
        for tag, error in errors.items():
            messages.error(request, error, extra_tags=tag)
        return redirect(addCompany)

    company = Company.objects.create(
        name = request.POST['name'],
        user_id = request.session['id']
        )
    company.save()
    messages.add_message(request, messages.INFO, 'Company successfully added')
    return redirect(viewCompanies)

def viewBranches(request):
    branches = Branch.objects.all()
    branches = Branch.objects.filter(user__id = request.session['id'])
    context = {
        "branches": branches
    }
    return render(request, 'home/view_branches.html', context)

def saveBranch(request):
    errors = Branch.objects.validator(request.POST)
    if len(errors):
        for tag, error in errors.items():
            messages.error(request, error, extra_tags=tag)
        return redirect(addBranch)

    branch = Branch.objects.create(
        name = request.POST['name'],
        user_id = request.session['id']
        )
    branch.save()
    messages.add_message(request, messages.INFO, 'Branch successfully added')
    return redirect(viewBranches)

def register(request):
    return redirect(index)

def viewReports(request):
    return render(request, "home/reports.html")

def success(request):
    user = User.objects.get(id=request.session['id'])
    context = {
        "user": user
    }
    return render(request, 'home/welcome.html', context)


def results(request):
    return render(request, 'home/results.html')




def checkFruit(request):
    global context, show_main_results

    # This is an example of processing a single image in order to grade it
    # and drawing a green contour line around fruit for good image, red line for bad image

    # Load a sample picture and learn how to grade it.

    # upload image
    if request.method == 'POST' and request.FILES['image']:
        myfile = request.FILES['image']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)

        print(uploaded_file_url)
        show_main_results = True

        # The name of the image file to annotate
        #i = time.strftime("%d-%m-%y_%H-%M-%S")

        test_image = cv2.imread(os.path.join(settings.PROJECT_ROOT, ".."+uploaded_file_url))
        
        colorStats = gradeByColor(test_image)
        contours = preProcess(test_image)
        #sizeStats = gradeBySize(contours)
        #defectStats = gradeByDefect(test_image, contours)

        context = {
            'colorStats': colorStats,
            #'sizeStats': sizeStats,
            'uploaded_file_url': uploaded_file_url

        }

        return render(request, 'home/results.html', context)

    return render(request, 'home/welcome.html')


def gotoCamResults(request):
    camera_grading = True

    camera = cv2.VideoCapture("http://10.216.2.121:8080/video")
    context = {
        'camera_grading': camera_grading
    }

    return render(request, 'home/results.html', context)

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def detectWithCamera(request):
    return StreamingHttpResponse(gen(IPWebCam()), content_type='multipart/x-mixed-replace; boundary=frame')

def startCamGrading(request):
    global context, show_main_results

    # This is an example of processing a single image in order to grade it
    # and drawing a green contour line around fruit for good image, red line for bad image

    # Load a sample picture and learn how to grade it.

    # upload image
    if request.method == 'POST' and request.FILES['image']:
        myfile = request.FILES['image']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)

        print(uploaded_file_url)
        show_main_results = True

        # The name of the image file to annotate
        #i = time.strftime("%d-%m-%y_%H-%M-%S")

        test_image = cv2.imread(os.path.join(settings.PROJECT_ROOT, ".."+uploaded_file_url))
        
        colorStats = gradeByColor(test_image)
        contours = preProcess(test_image)
        #sizeStats = gradeBySize(contours)
        #defectStats = gradeByDefect(test_image, contours)

        context = {
            'colorStats': colorStats,
            #'sizeStats': sizeStats,
            'uploaded_file_url': uploaded_file_url

        }

        return render(request, 'home/results.html', context)

    return render(request, 'home/welcome.html')
