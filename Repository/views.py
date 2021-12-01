import json
from datetime import datetime

import requests
from django.http import JsonResponse,HttpResponse
from requests.adapters import HTTPAdapter

from Repository.models import Repository,Member
from Task.models import Task, Record
from django.core import serializers
from User.models import User


# 展示该用户参与的项目列表
def showRepo(request):
    if request.method == 'POST':
        result = {"message": "success", "data": []}
        u_id = int(request.POST.get('u_id'))  # 获取用户id
        print(u_id)
        user = User.objects.filter(pk=u_id)
        if not user:
            return JsonResponse({"message": 'id错误'})
        if not user.first().username:
            return JsonResponse({"message": "请先登录GitHub"})
        mem = Member.objects.filter(user_id_id=u_id, identity__in=[0, 1, 2, 3])  # 找出该用户的所有仓库
        if mem:
            for x in mem:
                repo_info = {"repo": []}
                repo = Repository.objects.filter(pk=x.repo_id_id)
                repo_info['repo'] = serializers.serialize('python', repo)
                repo_info['role'] = x.identity
                repo_info['member_id'] = x.pk
                result['data'].append(repo_info)
            return JsonResponse(result)
        return JsonResponse({"message": "用户未参与项目"})
    return JsonResponse({"message": '请求方式错误'})


# 展示项目的任务列表
def showTask(request):
    if request.method == 'POST':
        result = {"message": "success", "finish": [], "checking": [], "incomplete": []}
        repo_id = int(request.POST.get('repo_id'))
        print(repo_id)
        repos = Repository.objects.filter(pk=repo_id)
        if not repos:
            return JsonResponse({"message": "仓库id错误"})
        tasks = Task.objects.filter(repo_id=repo_id)
        if not tasks:
            return JsonResponse({"message": "当前项目没有任务"})
        # print(tasks)
        for x in tasks:  # 0代表未完成。1代表待审核，2代表已完成
            task = {'task_name': x.task_name, 'task_info': x.task_info, 'task_id': x.pk, 'repo_id': x.repo_id,
                    'member_id': x.member_id, 'title': ''}
            # print(task)
            ddl = x.deadline
            task['deadline'] = [ddl.year, ddl.month, ddl.day, ddl.hour, ddl.minute, ddl.second]
            record_id = x.record_id
            record = Record.objects.filter(pk=record_id)
            if record:
                task['title'] = record.first().title
            # print(task['deadline'])
            mem = Member.objects.filter(pk=x.member_id)
            if not mem:
                return JsonResponse({"message": "任务所分配给的成员不存在"})
            user = User.objects.filter(pk=mem.first().user_id_id)
            if not user:
                return JsonResponse({"message": "任务所分配给的成员不存在"})
            task['member_name'] = user.first().username
            if x.status == 0:
                result['incomplete'].append(task)
            elif x.status == 1:
                result['checking'].append(task)
            elif x.status == 2:
                result['finish'].append(task)
            else:
                return JsonResponse({"message": "任务状态异常"})
        return JsonResponse(result)
    return JsonResponse({"message": "请求方式错误"})


# 添加项目
def addRepo(request):
    if request.method == 'POST':
        url = str(request.POST.get('url'))
        print(url)
        repo_name = str(request.POST.get('repo_name'))
        print(repo_name)
        user_id = int(request.POST.get('user_id'))
        print(user_id)
        user = User.objects.filter(pk=user_id)
        if not user:
            return JsonResponse({"message": "用户id错误"})
        repo = Repository.objects.filter(url=url)
        if repo:
            return JsonResponse({"message": "该仓库已存在"})
        username = user.first().username
        new_repo = Repository(url=url, repo_name=repo_name)
        new_repo.save()
        repo_id = Repository.objects.get(url=url).pk
        new_member = Member(repo_id_id=repo_id, user_id_id=user_id, username=username, identity=0)
        new_member.save()
        return JsonResponse({"message": "success"})
    return JsonResponse({"message": "请求方式错误"})


# 获取当前用户GitHub账号的所有仓库
def getRepos(request):
    if request.method == 'POST':
        result = {"message": "success", "data": []}
        u_id = int(request.POST.get('u_id'))
        user = User.objects.filter(pk=u_id)
        if not user:
            return JsonResponse({"message": "用户id错误"})
        username = user.first().username
        token = user.first().token
        if not token:
            return JsonResponse({"message": "token为空"})
        info = getGithubRepo(username, token)
        json_dict = json.loads(info)
        # print(json_dict)
        for i in range(len(json_dict)):
            repo = {'url': json_dict[i].get('html_url'), 'repo_name': json_dict[i].get('full_name')}
            result['data'].append(repo)
        return JsonResponse(result)
    return JsonResponse({"message": "请求方式错误"})


# #根据关键词获取当前用户GitHub账号的仓库
def getReposByKeyword(request):
    if request.method == 'POST':
        result = {"message": "success", "data": []}
        u_id = int(request.POST.get('u_id'))
        keyword = request.POST.get('keyword')
        print(u_id, keyword)
        user = User.objects.filter(pk=u_id)
        if not user:
            return JsonResponse({"message": "用户id错误"})
        username = user.first().username
        token = user.first().token
        if not token:
            return JsonResponse({"message": "token为空"})
        info = getGithubRepo(username, token)
        json_dict = json.loads(info)
        # print(json_dict)
        for i in range(len(json_dict)):
            if not(keyword in json_dict[i].get('full_name')):
                continue
            repo = {'url': json_dict[i].get('html_url'), 'repo_name': json_dict[i].get('full_name')}
            result['data'].append(repo)
        return JsonResponse(result)
    return JsonResponse({"message": "请求方式错误"})


# #获取仓库信息
def getGithubRepo(username, token):
    url = f"https://api.github.com/users/{username}/repos"
    print(url)
    s = requests.Session()
    headers = {
        "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
        "Accept": "application/vnd.github.cloak-preview+json",
        "Authorization": "token " + token,
    }
    print(headers['Authorization'])
    s.mount('http://', HTTPAdapter(max_retries=3))
    s.mount('https://', HTTPAdapter(max_retries=3))
    try:
        res = s.get(url=url, timeout=10, headers=headers)
        # res = requests.get(url=url, headers=headers)
        print(1)
        # print(res.json())
        return res.text
    except requests.exceptions.RequestException as e:
        print(e)


# 获取项目管理员、开发者、游客列表
def getAllMember(request):
    if request.method == 'POST':
        result = {"message": 'success', "data": [], "owner": []}
        repo_id = int(request.POST.get('repo_id'))
        owner = Member.objects.filter(repo_id_id=repo_id, identity=0)
        if not owner:
            return JsonResponse({"message": "超级管理员出错"})
        result['owner'] = serializers.serialize('python', owner)
        developers = Member.objects.filter(repo_id_id=repo_id, identity__in=[0, 1, 2, 3]).order_by('identity')
        if not developers:
            return JsonResponse({"message": '暂无其他参与者'})
        result["data"] = serializers.serialize('python', developers)
        return JsonResponse(result)
    return JsonResponse({"message": "请求方式错误"})


# 仓库人员身份调整
def changeIdentity(request):
    if request.method == 'POST':
        result = {"message": "success"}
        mem = json.loads(request.body.decode("utf-8"))
        print(mem)
        # mem_id = int(mem['member_id'])
        # try:
        #     member = Member.objects.get(pk=mem_id)
        # except:
        #     return JsonResponse({"message": "member的id存在错误"})
        # if member.identity == 2:
        #     task = Task.objects.filter(member_id=mem.pk, status__in=[0, 1])
        #     if task:
        #         return JsonResponse({"message": "开发者任务为未完成或待审核，不能改变身份"})
        # identity = int(mem['identity'])
        # print(identity)
        # if identity == 0:
        #     return JsonResponse({"message": "不能修改为超级管理员"})
        # if identity == -1:
        #     return JsonResponse({"message": "不能修改为待审核状态"})
        # if identity == -2:
        #     return JsonResponse({"message": "不能修改为退出项目状态"})
        # print(mem_id, identity)
        # member.identity = identity
        # member.save()
        # return JsonResponse(result)
        for x in range(len(mem)):
            # print(x)
            mem_id = int(mem[x]['member_id'])
            print(mem_id)
            try:
                member = Member.objects.get(pk=mem_id)
            except:
                return JsonResponse({"message": "member的id存在错误"})
            if member.identity == 2:
                print(member.identity)
                task = Task.objects.filter(member_id=member.pk, status__in=[0, 1])
                if task:
                    return JsonResponse({"message": "有开发者任务为未完成或待审核，不能改变身份"})
            identity = int(mem[x]['identity'])
            print(identity)
            if identity == 0:
                return JsonResponse({"message": "不能修改为超级管理员"})
            if identity == -1:
                return JsonResponse({"message": "不能修改为待审核状态"})
            if identity == -2:
                return JsonResponse({"message": "不能修改为退出项目状态"})
            print(mem_id, identity)
            member.identity = identity
            member.save()
        return JsonResponse(result)
    return JsonResponse({"message": "请求方式错误"})


# 退出项目
def exitRepo(request):
    if request.method == 'POST':
        u_id = int(request.POST.get('u_id'))
        print(u_id)
        repo_id = int(request.POST.get('repo_id'))
        print(u_id, repo_id)
        try:
            mem = Member.objects.get(user_id_id=u_id, repo_id_id=repo_id)
        except:
            return JsonResponse({"message": "用户不在该仓库中"})
        if mem.identity == 0:
            return JsonResponse({"message": "该用户为项目创建者，不能退出！"})
        if mem.identity == -1:
            return JsonResponse({"message": "该用户为待审核状态，不能退出！"})
        if mem.identity == -2:
            return JsonResponse({"message": "该用户已退出项目，不能再次退出！"})
        tasks = Task.objects.filter(member_id=mem.pk, status__in=[0, 1])
        if tasks:
            return JsonResponse({"message": "有任务处于待审核或未完成状态，请在任务完成后再次退出！"})
        try:
            repo = Repository.objects.get(pk=repo_id)
        except:
            return JsonResponse({"message": "仓库不存在！"})
        repo.repo_member -= 1
        repo.save()
        mem.identity = -2
        mem.save()
        return JsonResponse({"message": "success"})
    return JsonResponse({"message": "请求方式错误"})


# 删除项目
def delRepo(request):
    if request.method == 'POST':
        u_id = int(request.POST.get('u_id'))
        repo_id = int(request.POST.get('repo_id'))
        try:
            repo = Repository.objects.get(pk=repo_id)
            mem = Member.objects.get(user_id_id=u_id, repo_id_id=repo_id)
        except:
            return JsonResponse({"message": "该用户非该项目成员"})
        if not(mem.identity == 0):
            return JsonResponse({"message": "该用户不是该项目的超级管理员"})
        repo.delete()
        return JsonResponse({"message": "success"})
    return JsonResponse({"message": "请求方式错误"})


def test(request):
    res = requests.get(url="https://api.github.com/users/zhoubin1022/repos", timeout=10)
    print(res.text)
    return JsonResponse({"aaa"})
