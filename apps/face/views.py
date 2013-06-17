from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.http import HttpResponse
from models import UserProfile
from utils import email_template
import json
import requests
import uuid

def main(request):
  return render(request, 'face/landing.html')

def signin(request):
  return render(request, 'face/signin.html')

def signin_user(request):
  email = password = ''
  if request.POST:
    email = request.POST.get('signin_email')
    password = request.POST.get('signin_password')
    print 'trying to log in with ', email, password
    user = authenticate(username=email, password=password)
    print user
    if user is not None:
      if user.is_active:
        login(request, user)
        print 'user active and logged in!'
        return redirect('/space/')
      else:
       print 'user not active'
    else:
      print 'invalid user'
  return redirect('/')

def register_user(request):
  return render(request, 'face/register.html')

def register_blocks(request):
  return render(request, 'face/register_blocks.html')

"""
Receives ajax call from register page and parses POST to check for validity on
the server side.

Responses:
  OK - all good, continue to the next step
  INV - email invalid
  DUP - email already taken
"""
def register_account_handler(request):
  response_string = '{"status":"INV"}'
  if request.POST:
    stage = request.POST.get('stage', "")   
    if stage == "account":
      first_name = request.POST.get('firstName', "")
      last_name  = request.POST.get('lastName', "")
      email      = request.POST.get('email', "")
      password   = request.POST.get('password', "")
      print email
      u, created = User.objects.get_or_create(username=email)
      print User.objects.all()
      print u
      print created
      if created:
        u.set_password(password)
        u.userprofile.join_id = str(uuid.uuid1())
        u.first_name = first_name
        u.last_name  = last_name
        u.save()
        u.userprofile.save()
        template_content = [{
          "name": "joinlink", 
          "content": "<a href='http://www.fluentlynow.com/face/register?id=" + 
                     u.userprofile.join_id + 
                     "'>http://www.fluentlynow.com/face/register?id=" + 
                     u.userprofile.join_id + 
                     "</a>"
          }]
        mandrill_email_template = email_template("invite-user", template_content, email, first_name + " " + last_name, "")
        print mandrill_email_template
        mandrill_url = "https://mandrillapp.com/api/1.0/messages/send-template.json"
        r = requests.post(mandrill_url, data=mandrill_email_template)
        response_string = '{"status":"OK"}'
      else:
        response_string = '{"status":"DUP"}'
    elif stage == "confirmation":
      join_id = request.POST.get('join_id', "")
      email = UserProfile.objects.filter(join_id=join_id)[0].user.username
      response_string = '{"status":"OK", "email":"' + email + '"}'
    elif stage == "certification":
      email = request.POST.get('email', "")
      admin_request = request.POST.get('adminRequest', "")
      try:
        u = User.objects.get(username = email)
        u.userprofile.admin = admin_request
        u.userprofile.save()
        mandrill_email_template = email_template("submit-user", [], email, u.first_name + " " + u.last_name, "")
        mandrill_url = "https://mandrillapp.com/api/1.0/messages/send-template.json"
        r = requests.post(mandrill_url, data=mandrill_email_template)
        response_string = '{"status":"OK"}'
      except User.DoesNotExist:
        pass
  return HttpResponse(json.dumps(response_string), mimetype="application/json")
