from __future__ import division
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, HttpResponse, redirect
from django.contrib import messages
from django.http.response import StreamingHttpResponse
from django.http import JsonResponse
import bcrypt
from PIL import Image, ImageDraw
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .serializers import FileSerializer
from django.contrib.auth import logout
from .forms import *
from main.models import *
from django.core.mail import EmailMessage
from django.conf import settings
from main.camera import IPWebCam
from main.grade import *
from copy import deepcopy

import io
import os
import random
import cv2
import numpy as np
import requests
import time
from datetime import datetime

# initialize global variables
percentage_of_defects = 0
asessment_style = ''
i = 1


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
    if request.session.get('id') != None:
        userId = request.session.get('id')
        userName = request.session.get('name')
        context = {
            'userId': userId,
            'userName': userName
        }
        return render(request, 'home/home_page.html', context)
    else:
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
                    request.session['role'] = user.role

                    messages.add_message(request, messages.INFO, 'Welcome to fruit quality detection system ' + user.first_name+' '+user.last_name)
                    return redirect(dashboard)
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

def addFruit(request):
    return render(request, 'home/add_fruit.html')

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
            email_subject = "Welcome to Tavi"
            email_body = "Thank you for creating an account with us. We hope you have the best of experiences while using the system to grade your products, and look forward to hearing from you. Best of Luck, Audrey"
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
    return redirect('/home/home_page.html')


def dashboard(request):
    users = User.objects.all()
    context = {
        'users': users
    }
    return render(request, 'home/dashboard.html', context)


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
    userId = request.session['id']
    userRole = request.session['role']
    if userRole == 'ADMIN':
        companies = Company.objects.all()
    else:
        companies = Company.objects.filter(user__id = userId)
    context = {
        "companies": companies
    }
    return render(request, 'home/view_companies.html', context)

def saveCompany(request):
    errors = Company.objects.validator(request.POST)
    if len(errors):
        for tag, error in errors.items():
            messages.error(request, error, extra_tags=tag)
        return redirect("/add_company")

    company = Company.objects.create(
        name = request.POST['name'],
        user_id = request.session['id']
        )
    company.save()
    messages.add_message(request, messages.INFO, 'Company successfully added')
    return redirect(viewCompanies)

def updateCompany(request, id):  
    company = Company.objects.get(id=id)  
    if request.method == 'POST':
        errors = Company.objects.validator(request.POST)
        if len(errors):
            for tag, error in errors.items():
                messages.error(request, error, extra_tags=tag)
            return redirect("/view_companies")
        form = CompanyForm(request.POST)
        if form.is_valid():
            company.name = form.cleaned_data.get("name")
            company.save()
            messages.add_message(request, messages.INFO, 'Company successfully updated')
            return redirect(viewCompanies)
          
    return render(request, 'home/edit_company.html', {'company': company})
      
def deleteCompany(request, id):  
    company = Company.objects.get(id=id)  
    company.delete()  
    return redirect("/view_companies")

def viewBranch(request, companyId, branchId):
    branch = Branch.objects.get(id = branchId)
    company = Company.objects.get(id = companyId)
    fruits = Fruit.objects.all()
    context = {
        "fruits": fruits,
        "branch": branch,
        "company": company
        }
    if request.method == 'POST':
        errors = Fruit.objects.validator(request.POST)
        if len(errors):
            for tag, error in errors.items():
                messages.error(request, error, extra_tags=tag)
            return redirect("/view_fruits")
        form = FruitForm(request.POST)
        if form.is_valid():
            fruitName = form.cleaned_data.get("name")
            fruit = Fruit.objects.get(name = fruitName)
            fruit.branch.add(branch)
            context2 = {
                "branch": branch,
                "fruit": fruit,
                "company": company
            }
            return render(request, 'home/welcome.html', context2)
    
    return render(request, 'home/view_branch.html', context)

#view all fruits only seen by admin
def viewFruits(request):
    fruits = Fruit.objects.all()
    userRole = request.session['role']
    context = {
        "fruits": fruits,
        "userRole": userRole
    }
    return render(request, 'home/view_fruits.html', context)

#save fruit only seen by admin
def saveFruit(request):
    errors = Fruit.objects.validator(request.POST)
    if len(errors):
        for tag, error in errors.items():
            messages.error(request, error, extra_tags=tag)
        return redirect("/add_fruit")

    fruit = Fruit.objects.create(
        name = request.POST['name']
        )
    fruit.save()
    messages.add_message(request, messages.INFO, 'Fruit successfully added')
    return redirect(viewFruits)

def updateFruit(request, fruitId):  
    fruit = Fruit.objects.get(id = fruitId)  
    if request.method == 'POST':
        errors = Fruit.objects.validator(request.POST)
        if len(errors):
            for tag, error in errors.items():
                messages.error(request, error, extra_tags=tag)
            return redirect("/view_fruits")
        form = FruitForm(request.POST)
        if form.is_valid():
            fruit.name = form.cleaned_data.get("name")
            fruit.save()
            messages.add_message(request, messages.INFO, 'Fruit successfully updated')
            return redirect(viewFruits)
          
    return render(request, 'home/edit_fruit.html', {'fruit': fruit})
      
def deleteFruit(request, fruitId):  
    fruit = Fruit.objects.get(id = fruitId)  
    fruit.delete()  
    return redirect("/view_fruits")  

def viewBranches(request, companyId):
    branches = Branch.objects.filter(company_id = companyId)
    company = Company.objects.get(id = companyId)
    context = {
        "branches": branches,
        "company": company
    }
    return render(request, 'home/view_branches.html', context)

def addBranch(request, companyId):
    company = Company.objects.get(id = companyId)
    context = {
        "company": company
    }
    return render(request, 'home/add_branch.html', context)

def saveBranch(request, companyId):
    errors = Branch.objects.validator(request.POST)
    if len(errors):
        for tag, error in errors.items():
            messages.error(request, error, extra_tags=tag)
        return redirect(addBranch)

    branch = Branch.objects.create(
        name = request.POST['name'],
        company_id = companyId
        )
    branch.save()
    messages.add_message(request, messages.INFO, 'Branch successfully added')
    return redirect("/view_branches/" + companyId)

def updateBranch(request, companyId, branchId):  
    branch = Branch.objects.get(id = branchId)  
    if request.method == 'POST':
        errors = Branch.objects.validator(request.POST)
        if len(errors):
            for tag, error in errors.items():
                messages.error(request, error, extra_tags=tag)
            return redirect("/view_branches/" + companyId)
        form = BranchForm(request.POST)
        if form.is_valid():
            branch.name = form.cleaned_data.get("name")
            branch.save()
            messages.add_message(request, messages.INFO, 'Branch successfully updated')
            return redirect("/view_branches/" + companyId)
          
    return render(request, 'home/edit_branch.html', {'branch': branch})
      
def deleteBranch(request, companyId, branchId):  
    branch = Branch.objects.get(id=branchId)  
    branch.delete()  
    messages.add_message(request, messages.INFO, 'Branch successfully deleted')
    return redirect("/view_branches/" + companyId)

def register(request):
    return redirect(index)

def viewReports(request):
    return render(request, "home/reports.html")

def success(request):
    user = User.objects.get(id=request.session['id'])
    context = {
        'user': user
    }
    return render(request, 'home/welcome.html', context)


def results(request):
    fruits = Fruit.objects.all()
    return render(request, 'home/results.html', {"fruits": fruits})


def checkFruit(request, branchId, fruitId):
    global context, show_main_results
    fruit = Fruit.objects.get(id = fruitId)
    overall_assessment = ''
    assessment_style = ''
    companyId = Branch.objects.get(id = branchId).company_id

    # This is an example of processing a single image in order to grade it
    # and drawing a green contour line around fruit for good image, red line for bad image

    # Load a sample picture and learn how to grade it.

    # upload image
    if request.method == 'POST' and request.FILES['image']:
        myfile = request.FILES['image']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)

        show_main_results = True

        # The name of the image file to annotate
        #i = time.strftime("%d-%m-%y_%H-%M-%S")

        test_image = cv2.imread(os.path.join(settings.PROJECT_ROOT, ".."+uploaded_file_url))
        
        colorStats = gradeByColor(test_image, fruit.name)
        contours = preProcess(test_image, fruit.name)
        sizeStats = gradeBySize(contours)

        ripe_perc = 0
        if fruit.name == 'tomato':
            ripe_perc = colorStats["ripe_perc"]
        elif fruit.name == 'apple':
            ripe_perc = colorStats["apple_ripe_perc"]
        elif fruit.name == 'orange' or fruit.name == 'papaya':
            ripe_perc = colorStats["orange_ripe_perc"]

        if colorStats["color_grade"] == 'C' or colorStats["color_grade"] == 'B' or sizeStats["size_grade"] == 'C':
            overall_assessment = 'fail'
            asessment_style = 'danger'
        else:
            overall_assessment = 'pass'
            asessment_style = 'success'

        print("assessment_style: " + asessment_style)
        context = {
            'edge_file_url': colorStats["edge_file_url"],
            'mask_file_url': colorStats["mask_file_url"],
            'cnt_file_url': colorStats["cnt_file_url"],
            'cropped_file_url': colorStats["cropped_file_url"],
            'ripe_perc': ripe_perc,
            'ripe_rate': colorStats["ripe_rate"],
            'color_grade': colorStats["color_grade"],
            'sizeStats': sizeStats,
            'uploaded_file_url': uploaded_file_url,
            'fruit': fruit,
            'companyId': companyId,
            'branchId': branchId,
            'overall_assessment': overall_assessment,
            'asessment_style': asessment_style,
        }
        return render(request, 'home/results.html', context)

    return render(request, 'home/welcome.html')

def gotoCamResults(request, branchId, fruitId):
    global camera
    camera_grading = True
    i = 1
    branch = Branch.objects.get(id = branchId)
    fruit = Fruit.objects.get(id = fruitId)
    companyId = branch.company_id
    context = {
        "camera_grading": camera_grading,
        "branch": branch,
        "fruit": fruit,
        "companyId": companyId
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
    global i, context
    total_fruit_num = 0
    total_def = 0
    overall_assessment = ''
    assessment_style = ''
    branchId = request.GET['branchIid']
    fruitId = request.GET['fruitIid']
    fruitname = Fruit.objects.get(id = fruitId).name
    today_date = datetime.date(datetime.now())
    
    camera = cv2.VideoCapture("http://192.168.1.3:8080/video")
    time.sleep(10)
    _, frame = camera.read() 
      
    # save fruit_img to /media
    cv2.imwrite(os.path.join(settings.PROJECT_ROOT, '../media/fruit_img{}.jpg'.format(i)), frame)
    fruit_img_url = '/media/fruit_img{}.jpg'.format(i)
    test_image = cv2.imread(os.path.join(settings.PROJECT_ROOT, ".."+fruit_img_url))

    colorStats = gradeByColor(test_image, fruitname)
    contours = preProcess(test_image, fruitname)
    sizeStats = gradeBySize(contours)
    #defectStats = gradeByDefect(test_image, contours)

    ripe_perc = 0
    if fruitname == 'tomato':
        ripe_perc = colorStats["ripe_perc"]
    elif fruitname == 'apple':
        ripe_perc = colorStats["apple_ripe_perc"]
    elif fruitname == 'orange' or fruitname == 'papaya':
        ripe_perc = colorStats["orange_ripe_perc"]

    if colorStats["color_grade"] == 'C' or colorStats["color_grade"] == 'B' or sizeStats["size_grade"] == 'C':
        overall_assessment = 'fail'
        total_def += 1
        asessment_style = 'danger'
    else:
        overall_assessment = 'pass'
        asessment_style = 'success'

    # update report entry if it already exists
    if (Report.objects.filter(check_date = today_date, branch_id = branchId, fruit_id = fruitId).exists()):
        today_report = Report.objects.filter(check_date = today_date, branch_id = branchId, fruit_id = fruitId)[0]
        total_fruit_num = today_report.total_fruit_num
        total_fruit_num += 1
        total_def = today_report.total_def + total_def
        # update total_fruit_num and total_def columns
        today_report.total_fruit_num = total_fruit_num
        today_report.total_def = total_def
        today_report.save()
    # create report entry if it doesn't already exists
    else:
        report = Report.objects.create(
        check_date = today_date,
        branch_id = branchId,
        fruit_id = fruitId,
        total_fruit_num = total_fruit_num + 1,
        total_def = total_def
        )
        report.save()
    
    print("asessment_style: " + asessment_style)
    context = {
            'edge_file_url': colorStats["edge_file_url"],
            'cnt_file_url': colorStats["cnt_file_url"],
            'cropped_file_url': colorStats["cropped_file_url"],
            'mask_file_url': colorStats["mask_file_url"],
            'ripe_perc': colorStats["ripe_perc"],
            'ripe_rate': colorStats["ripe_rate"],
            'color_grade': colorStats["color_grade"],
            'overall_assessment': overall_assessment,
            'asessment_style': asessment_style,
            'sizeStats': sizeStats,
            'uploaded_file_url': fruit_img_url,
        }
    i += 1  
    #return render(request, 'home/results.html', context)
    return JsonResponse(context)

def viewReport(request, companyId, branchId):
    company_name = Company.objects.get(id = companyId).name
    branch_name = Branch.objects.get(id = branchId).name
    reports = Report.objects.filter(branch_id = branchId)
    pie_data = Report.objects.filter(check_date = datetime.date(datetime.now()), branch_id = branchId)[0]
    context = {
        'reports': reports,
        'company_name': company_name,
        'branch_name': branch_name,
        'pie_data': pie_data
    }
    return render(request, 'home/reports.html', context)



from django.http import HttpResponse
from django.views.generic import View
from main.utils import render_to_pdf #created in step 4

class GeneratePdf(View):
    def get(self, request, *args, **kwargs):
        data = {
             'today': datetime.date(datetime.now()), 
             'amount': 39.99,
            'customer_name': 'Cooper Mann',
            'order_id': 1233434,
        }
        pdf = render_to_pdf('home/reports.html', data)
        return HttpResponse(pdf, content_type='application/pdf')