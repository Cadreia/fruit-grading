from __future__ import unicode_literals
from django.db import models

class UserManager(models.Manager):
    def validator(self, postData):
        errors = {}
        if (postData['first_name'].isalpha()) == False:
            if len(postData['first_name']) < 2:
                errors['first_name'] = "First name can not be shorter than 2 characters"

        if (postData['last_name'].isalpha()) == False:
            if len(postData['last_name']) < 2:
                errors['last_name'] = "Last name can not be shorter than 2 characters"

        if (postData['username'].isalpha()) == False:
            if len(postData['username']) < 2:
                errors['username'] = "Username can not be shorter than 2 characters"

        if len(postData['email']) == 0:
            errors['email'] = "You must enter an email"

        if len(postData['password']) < 8:
            errors['password'] = "Password is too short!"

        return errors

class CompanyManager(models.Manager):
    def validator(self, postData):
        errors = {}
        if (postData['name'].isalpha()) == False:
            if len(postData['name']) == 0:
                errors['name'] = "Company name can not be empty"

        return errors

class BranchManager(models.Manager):
    def validator(self, postData):
        errors = {}
        if (postData['name'].isalpha()) == False:
            if len(postData['name']) == 0:
                errors['name'] = "Branch name can not be empty"

        return errors

class FruitManager(models.Manager):
    def validator(self, postData):
        errors = {}
        if (postData['name'].isalpha()) == False:
            if len(postData['name']) == 0:
                errors['name'] = "Fruit name can not be empty"

        return errors

class User(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    email = models.CharField(max_length=255,default=None)
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)
    role = models.CharField(max_length=255, default="USER")
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    objects = UserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['username', 'password']

class File(models.Model):
    file = models.FileField(blank=False, null=False)
    remark = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)

class Company(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = CompanyManager()

class Branch(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = BranchManager()

class Fruit(models.Model):
    name = models.CharField(max_length=255)
    branch = models.ManyToManyField(Branch)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = FruitManager()

class Report(models.Model):
    check_date = models.DateField()
    total_fruit_num = models.BigIntegerField(default=0)
    total_def = models.BigIntegerField(default=0)
    fruit = models.ForeignKey(Fruit, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)