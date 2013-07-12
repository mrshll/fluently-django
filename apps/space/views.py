# django libraries
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404, render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User, Group
from django.template import Context
from django.core.context_processors import csrf
from django.template.loader import get_template
from apps.face.models import UserProfile

# general python packages
import uuid
import sys
import time
import os
import requests
import json
import collections

# third party packages
from vendor.TokBox import OpenTokSDK
import crocodoc
from crocodoc import CrocodocError

# models
from models import Space

class TokBox:

  api_key = '25204042' # Replace with your OpenTok API key.
  api_secret = '28ae8c58d5b4e013841581e5cd26df2c9851a818' # Replace with your OpenTok API secret.
  session_address = 'http://localhost:8000' # Replace with the representative URL of your session.

  @classmethod
  def generate_session_id(self):
    opentok_sdk = OpenTokSDK.OpenTokSDK(self.api_key, self.api_secret)
    session = opentok_sdk.create_session(self.session_address)
    print 'created session: ' + session.session_id
    return session.session_id

  @classmethod
  def generate_token(self, session_id):
    opentok_sdk = OpenTokSDK.OpenTokSDK(self.api_key, self.api_secret)
    connectionMetadata = ''
    token = opentok_sdk.generate_token(session_id, OpenTokSDK.RoleConstants.PUBLISHER, None, connectionMetadata)
    print 'created token: ' + token
    return token

class Crocodoc:
  c = crocodoc
  c.api_token = 'Tw6f4QKEneJ8qiHzCRL7bOlF'

  @classmethod
  def upload(self, file_handle):
    sys.stdout.write('  Uploading... ')
    uuid = None
    try:
      uuid = self.c.document.upload(file=file_handle)
      print '  UUID is ' + uuid
      return uuid
    except CrocodocError as e:
      print '  Error Code: ' + str(e.status_code)
      print '  Error Message: ' + e.error_message
      return None

  @classmethod
  def generate_session_id(self, uuid):
    try:
      session_id = self.c.session.create(uuid)
      print '  session is ' + session_id
      return session_id
    except CrocodocError as e:
      print '  Error Code: ' + str(e.status_code)
      print '  Error Message: ' + e.error_message
      return None

@require_http_methods(["GET"])
def dispatch(request):
  print 'in dispatch'
  s = Space(tok_session_id = TokBox.generate_session_id(), url_id=uuid.uuid4())
  s.save()

  return redirect('/space/%s/' % str(s.url_id))

@require_http_methods(["GET"])
def main(request, space_url_id):
  s = get_object_or_404(Space, url_id=space_url_id)

  croco_session = ''
  if s.croco_uuid:
    croco_session = Crocodoc.generate_session_id(s.croco_uuid)

  tok_token = TokBox.generate_token(s.tok_session_id)
  # tok_token=None

  print 'user',request.user

  return render(request, 'space/index.html',
                {
                  "space"          : s,
                  "tok_token"      : tok_token,
                  "tok_session_id" : s.tok_session_id,
                  "croco_session"  : croco_session,
                  "user"           : request.user,
                })

def usersContextList():
    keyorder = {k:v for v,k in enumerate(
        ['id', 'name', 'email', 'phone', 'location', 'specialties']
    )}
    users = User.objects.all()
    usersContextList = []
    for user in users:
        userDict = {}
        userDict['specialties'] = user.userprofile.specialties
        userDict['location'] = user.userprofile.location
        userDict['phone'] = user.userprofile.phone
        userDict['email'] = user.username
        userDict['name'] = user.userprofile.name
        userDict['id'] = user.pk
        dictItems = sorted(userDict.items(), key=lambda i:keyorder.get(i[0]))
        userDict = collections.OrderedDict(dictItems)
        usersContextList.append(userDict)
    return usersContextList

def save_profile(request):
    u = request.user
    print u
    if not u.is_authenticated():
        return redirect('/face/')
    response_json = {
        "status": "fail",
    }
    if request.POST:
        print "post save"
        firstName = request.POST.get('firstName', "")
        lastName = request.POST.get('lastName', "")
        location = request.POST.get('loc', "")
        aboutMe = request.POST.get('aboutMe', "")
        certifications = request.POST.get('certifications', "")
        experience = request.POST.get('experience', "")
        therapyApproach = request.POST.get('therapyApproach', "")
        u.userprofile.first_name = firstName
        u.userprofile.last_name = lastName
        u.userprofile.location = location
        u.userprofile.about_me = aboutMe
        u.userprofile.certifications = certifications
        u.userprofile.experience = experience
        u.userprofile.therapy_approach = therapyApproach
        u.userprofile.save()
        print firstName
        print lastName
        print aboutMe
        print location
        print certifications
        print experience
        print therapyApproach
        response_json = {   
            "status": "success",
        }
    return HttpResponse(json.dumps(response_json), mimetype="application/json")

def public_profile(request, user_url):
    print "pub"
    try:
        u = UserProfile.objects.filter(user_url=user_url)[0].user  
        template = get_template('space/public_profile.html')
        firstName = u.userprofile.first_name
        lastName = u.userprofile.last_name
        location = u.userprofile.location
        aboutMe = u.userprofile.about_me
        certifications = u.userprofile.certifications
        experience = u.userprofile.experience
        therapyApproach = u.userprofile.therapy_approach
        context = Context({
            "firstName": firstName,
            "lastName": lastName,
            "location": location,
            "aboutMe": aboutMe,
            "certifications": certifications,
            "experience": experience,
            "therapyApproach": therapyApproach
        })
        print aboutMe
        context.update(csrf(request))
        return HttpResponse(template.render(context))
    except:
        return redirect('/face/')

def contact(request, user_url):
    try:
        u = UserProfile.objects.filter(user_url=user_url)[0].user
        template = get_template('space/contact_student_modal.html')
        firstName = u.userprofile.first_name
        lastName = u.userprofile.last_name
        context = Context({
            "firstName": firstName,
            "lastName": lastName
        })
        context.update(csrf(request))
        return HttpResponse(template.render(context))
    except:
        return redirect('/face/')

def profile(request):
    u = request.user
    template = get_template('space/profile.html')
    if not u.is_authenticated():
        return redirect('/face/')
    if u.username == "jack@fluentlynow.com":
        print "CEO will get..."
        context = Context({
            "users": usersContextList()
        })
        context.update(csrf(request))
        return HttpResponse(template.render(context))
    firstName = u.userprofile.first_name
    lastName = u.userprofile.last_name
    location = u.userprofile.location
    aboutMe = u.userprofile.about_me
    certifications = u.userprofile.certifications
    experience = u.userprofile.experience
    therapyApproach = u.userprofile.therapy_approach
    context = Context({
        "firstName": firstName,
        "lastName": lastName,
        "location": location,
        "aboutMe": aboutMe,
        "certifications": certifications,
        "experience": experience,
        "therapyApproach": therapyApproach
    })
    context.update(csrf(request))
    return HttpResponse(template.render(context))

def profile_picture(request):
    print "profile picture"
    response_json = {"status": "fail"}
    u = request.user
    if request.POST:
        pic_url = request.POST.get('pic_url', "")
        if pic_url:
            u.userprofile.pic_url = pic_url
            u.userprofile.save()
            response_json = {"status": "success"}
        else:
            response_json = {"status": "success", 
                             "pic_url": u.userprofile.pic_url}
    return HttpResponse(json.dumps(response_json), mimetype="application/json")

def account(request):
  u = request.user
  if not u.is_authenticated():
    return redirect('/')
  if not u.userprofile.confirmed:
    return render(request, 'space/unconfirmed.html')
  else:
    try:
      other_users = Group.objects.get(name=u.userprofile.company).user_set.exclude(username=u.username)
      active_users = other_users.filter(userprofile__confirmed=True)
      invited_users = other_users.filter(userprofile__confirmed=False)
      active_usernames = [n[0] for n in active_users.values_list('username')]
      invited_usernames = [n[0] for n in invited_users.values_list('username')]
      print "printing active and invited"
      print active_usernames
      print invited_usernames
      template = get_template('space/account.html')
      context = Context({"invited_users":invited_users})
      context.update(csrf(request))
      return HttpResponse(template.render(context))
    except:
      return render(request, 'space/account.html')

@require_http_methods(["GET","POST"])
def upload(request):
  print 'in upload view'
  print request.FILES

  space_id = request.POST.get('space_id')
  space = Space.objects.get(id=space_id)

  croco_uuid = handle_uploaded_file(request.FILES['file'])
  croco_session = Crocodoc.generate_session_id(croco_uuid)

  space.croco_uuid = croco_uuid
  space.save()

  responseDict = {
    'croco_session' : croco_session,
    'croco_uuid'    : croco_uuid
  }

  print 'responseDict', responseDict

  return HttpResponse(json.dumps(responseDict), content_type="application/json")

def handle_uploaded_file(f):
  croco_session = None
  try:
    croco_uuid = Crocodoc.upload(f)
  except CrocodocError as e:
    print '  Error Code: ' + str(e.status_code)
    print '  Error Message: ' + e.error_message
    return None
  return croco_uuid

