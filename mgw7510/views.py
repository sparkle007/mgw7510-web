from django.shortcuts import render
from django.http import HttpResponse
from mgw7510.forms import WebUserForm
from mgw7510.models import WebUser
from django.http import HttpResponseRedirect
from django.core.mail import send_mail
from python_script import ce_deploy_scripts
import os
# import logging
import json
import shutil


# global var
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# logger = logging.getLogger("django")

# Create your views here.

# request an home page
def index(request):

    # if find the cookie, then we think the user has been logged in
    uname = request.session.get('username')
    if uname:
        return render(request, 'login_in.html', {'user': uname})

    # first par:  request
    # second par: auto search template path
    # logger.debug("This is an debug message by xuxiao: web user request home page")
    return render(request,'index.html')

# under construction page
def under_con(request):
    return render(request,'under-construction.html')


# register page
def register(request):
    return render(request,'register/register.html')

# change password page
def changePasswd(request):
    p1 = request.GET.get('p1')
    return render(request, 'register/change_password.html', {'paramUser': p1})

# click submit on the changepassword page
def changePasswdOk(request):
    if request.method == 'POST':
        wuf = WebUserForm(request.POST)
        if wuf.is_valid():
            cleanData = wuf.cleaned_data

            cp_uname = cleanData['username']
            cp_old_passwd = cleanData['password']
            cp_new_passwd = cleanData['newPassword']
            cp_confirm_new_passwd = cleanData['confirmNewPassword']

            # check if the user exist
            UserExist = WebUser.objects.filter(username__exact=cp_uname)

            if not UserExist:
                return HttpResponse('user not exist, please check!')
            else:
                # if user exist, get the user object, and then get
                # the attr password of the object
                MatchUser = WebUser.objects.get(username=cp_uname)
                db_passwd = MatchUser.password

                if db_passwd == cp_old_passwd:
                    # auth passed
                    if cp_new_passwd == cp_confirm_new_passwd:
                        # change db_passwd to cp_new_passwd
                        MatchUser.password = cp_new_passwd
                        MatchUser.save()
                        # # clear the cookie
                        # try:
                        #     del request.session['username']
                        # except KeyError:
                        #     pass
                        return HttpResponse('ok')
                    else:
                        return HttpResponse('new password and confirm new password not same')
                else:
                    return HttpResponse('old password is not correct')
        else:
            return HttpResponse('invalid input')
    else:
        return HttpResponse('not post method')


# regist a new web user
def signup(request):
    if request.method == 'POST':
        # logger.debug("The sign up form is posted to django")

        hp_uname = request.POST['username']
        hp_passwd = request.POST['password']
        hp_cpasswd = request.POST['confirmPassword']

        if (hp_passwd != hp_cpasswd):
            return HttpResponse('password not same, please check')

        # database query,
        userExist = WebUser.objects.filter(username__exact=hp_uname)

        if userExist:
            return HttpResponse('user exists, please change to another username')
        else:
            # set cookie; write username into cookie, valid timer is 3600s
            request.session['username'] = hp_uname
            # request.set_cookie('username', username, 3600)

            # create directory per user
            user_work_dir = hp_uname.replace("@","_")
            user_work_dir = BASE_DIR + "/UserWorkDir/" + user_work_dir

            # user_work_dir = settings.BASE_DIR + "/UserWorkDir/" + user_work_dir
            print user_work_dir

            if not os.path.isdir(user_work_dir):
                os.mkdir(user_work_dir)

            WebUser.objects.create(username=hp_uname,
                                   password=hp_passwd,
                                   userWorkDir=user_work_dir)
            return HttpResponse('ok')

def loginIn(request, loginParam):
    print loginParam

    # user is a template var
    return render(request, 'login_in.html', {'user':loginParam})

def logout(request):
    # delete the cookies
    try:
        del request.session['username']
    except KeyError:
        pass
    return HttpResponseRedirect("/")

def signin(request):
    if request.method == 'POST':
        wuf = WebUserForm(request.POST)
        if wuf.is_valid():
            cleanData = wuf.cleaned_data
            hp_uname = cleanData['username']
            hp_passwd = cleanData['password']

            # check if the user exist
            UserExist = WebUser.objects.filter(username__exact=hp_uname)

            if not UserExist:
                return HttpResponse('user not exist, please register first!')
            else:
                # if user exist, get the user object, and then get
                # the attr password of the object
                MatchUser = WebUser.objects.get(username=hp_uname)
                passwd_db = MatchUser.password
                # print ("pasword in database is %s"%(passwd_db))
                if hp_passwd == passwd_db:
                    # auth passed
                    # then set cookie
                    request.session['username'] = hp_uname
                    return HttpResponse('ok')
                else:
                    return HttpResponse('password is not correct')
        else:
            return HttpResponse('username/password should not be empty \nusername should be email address ')
    else:
        return HttpResponse('not post method')

def forgetPasswd(request):
    if request.method == 'POST':
        wuf = WebUserForm(request.POST)
        if wuf.is_valid():
            cleanData = wuf.cleaned_data
            hp_uname = cleanData['username']

            # check if the user exist
            UserExist = WebUser.objects.filter(username__exact=hp_uname)

            if not UserExist:
                return HttpResponse('user not exist, please check!')
            else:
                MatchUser = WebUser.objects.get(username=hp_uname)
                passwd_db = MatchUser.password
                # send mail to the hp_uname and return ok
                passwd_info = 'Dear, \n\nyour password is '+passwd_db

                print passwd_info
                print [hp_uname]
                send_mail('Your own password in www.sbc.nokia.com(135.251.216.181)', # subject
                          passwd_info, # body
                          'no-reply@sbc.nokia.com', # from mail
                          [hp_uname] # to mail
                          )
                info = 'your password has been sent to ' + hp_uname
                return HttpResponse(info)
        else:
            return HttpResponse('username should not be empty \nusername should be email address ')
    else:
        return HttpResponse('not post method')

def settings(request):
    # if user logged
    uname = request.session.get('username')
    if uname:
        return render(request, 'settings.html', {'user': uname})
    else:
        return HttpResponse("please login in first!")

def getCurrentConfig(request):
    uname = request.session.get('username')
    if uname:
        user_found = WebUser.objects.get(username=uname)

        config_data = {'pakServerIp': user_found.pakServerIp, 'pakServerUsername': user_found.pakServerUsername,
                       'pakServerPasswd': user_found.pakServerPasswd, 'pakServerFp': user_found.pakServerFp}

    jstr = json.dumps(config_data)

    return HttpResponse(jstr, content_type='application/json')

def saveConfig(request):
    uname = request.session.get('username')

    if uname:
        user_found = WebUser.objects.get(username=uname)

        # parse the json data from front-end
        new_config_data = json.loads(request.body)

        user_found.pakServerIp = new_config_data['pakServerIp']
        user_found.pakServerUsername = new_config_data['pakServerUsername']
        user_found.pakServerPasswd = new_config_data['pakServerPasswd']
        user_found.pakServerFp = new_config_data['pakServerFp']

        user_found.save()

        return HttpResponse('ok')

    else:
        return HttpResponse('user not found')


# request an home page for ce deploy
def ceDeploy(request):
    if request.session.get("ce_deploy_state") == "ongoing":
        # there is an ongoing task
        uname = request.session.get('username')
        user_found = WebUser.objects.get(username=uname)
        select_rel = request.session.get('selectRel')
        select_pak = request.session.get('selectPak')
        user_input_file_name = user_found.userInputFileName

        return render(request, 'ce_deployment/ce_deploy_onging.html', {'user': uname,
                                                                       'selectRel': select_rel,
                                                                       'selectPak': select_pak,
                                                                       'userInputFileName': user_input_file_name})

    elif request.session.get("ce_deploy_state") == "stopped":
        uname = request.session.get('username')
        user_found = WebUser.objects.get(username=uname)
        select_rel = request.session.get('selectRel')
        select_pak = request.session.get('selectPak')
        user_input_file_name = user_found.userInputFileName
        return render(request, 'ce_deployment/ce_deploy_stopped.html', {'user': uname,
                                                                        'selectRel': select_rel,
                                                                        'selectPak': select_pak,
                                                                        'userInputFileName': user_input_file_name})
    else:
        # if user logged
        uname = request.session.get('username')
        if uname:

            user_found = WebUser.objects.get(username=uname)

            # if ce_deploydir not exist, then create it
            user_work_dir = user_found.userWorkDir
            user_ce_deploy_dir = user_work_dir + "/ce_deploy_dir"
            if not os.path.isdir(user_ce_deploy_dir):
                os.mkdir(user_ce_deploy_dir)

            # clear flag
            user_found.userInputUploadedFlag = "nok"
            user_found.save()

            return render(request, 'ce_deployment/ce_deploy.html', {'user': uname})
        else:
            return HttpResponse("please login in first!")

# ce deploy process function
def ceCheckPak(request):
    if request.method == 'POST':
        # request.POST ====> <QueryDict: {u'selectPak': [u'none']}>
        # request.body ====> selectPak=none

        # if request.POST.has_key('selectPak'):
        #     if request.POST['selectPak'] == 'none':
        #         print "ok"

        uname = request.session.get('username')

        user_found = WebUser.objects.get(username=uname)

        select_rel = request.POST['selectRel']
        select_rel = "7510" + select_rel.replace(".", "")

        # /viewstores/public/SLP/7510C71
        pak_path = user_found.pakServerFp + "/" + select_rel

        pak_ip = user_found.pakServerIp
        pak_username = user_found.pakServerUsername
        pak_passwd = user_found.pakServerPasswd

        print pak_path

        pak_list = ce_deploy_scripts.get_pak_list(pak_ip,
                                                  pak_username,
                                                  pak_passwd,
                                                  pak_path)
        jstr = json.dumps(pak_list)
        return HttpResponse(jstr, content_type='application/json')

def uploadFile(request):
    if request.method == 'POST':
        uname = request.session.get('username')
        user_found = WebUser.objects.get(username=uname)
        uname = uname.replace("@", "_")

        # remove all files under user directory if exists
        file_path = BASE_DIR + "/media/" + uname
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)

        user_found.tmpPath = uname
        user_found.userInputFile = request.FILES['userInputFile']
        file_name = request.FILES['userInputFile'].name
        user_found.userInputFileName = file_name
        user_found.userInputUploadedFlag = "ok"
        user_found.save()

        files = [{'name': file_name}]
        data = {'files': files}
        jstr = json.dumps(data)

        return HttpResponse(jstr, content_type='application/json')

def updateProgress(request):
    if request.method == 'GET':
        uname = request.session.get('username')
        user_found = WebUser.objects.get(username=uname)
        progress = user_found.progressBarData
        return HttpResponse(progress)


def ceDeoployStart(request):
    if request.method == 'POST':
        uname = request.session.get('username')
        # parse the json data from front-end
        user_data = json.loads(request.body)

        select_rel = user_data['selectRel']
        select_pak = user_data['selectPak']

        ce_deploy_scripts.start_ce_deployment(uname, select_rel, select_pak)

        # set cookie;
        request.session['ce_deploy_state'] = "ongoing"
        request.session['selectRel'] = select_rel
        request.session['selectPak'] = select_pak

        return HttpResponse("ok")

def ceDeoployStop(request):
    if request.method == 'GET':
        request.session['ce_deploy_state'] = "stopped"
        return HttpResponse("ok")


def ceDeoployReset(request):
    if request.method == 'GET':
        del request.session['ce_deploy_state']
        del request.session['selectRel']
        del request.session['selectPak']
        return HttpResponseRedirect('/ce-deploy/')

def getCdpLog(request):
    if request.method == 'GET':

        # directly send the log data to html
        uname = request.session.get('username')
        user_found = WebUser.objects.get(username=uname)
        log_file = user_found.userWorkDir + "/ce_deploy_dir/" + "ce_deploy.log"
        log_file_data = open(log_file, "rb").read()
        return HttpResponse(log_file_data, content_type="text/plain")

        # # download the log file
        # uname = request.session.get('username')
        # user_found = WebUser.objects.get(username=uname)
        # file_name = "ce_deploy.log"
        # path_to_file = user_found.userWorkDir + "/ce_deploy_dir/"
        # response = HttpResponse(content_type='application/force-download')
        # response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(file_name)
        # response['X-Sendfile'] = smart_str(path_to_file)
        # return response

def queryUserInput(request):
    if request.method == 'GET':
        uname = request.session.get('username')
        user_found = WebUser.objects.get(username=uname)
        flag = user_found.userInputUploadedFlag
        return HttpResponse(flag)









