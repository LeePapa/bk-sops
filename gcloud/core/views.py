# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云PaaS平台社区版 (BlueKing PaaS Community
Edition) available.
Copyright (C) 2017-2019 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""

import datetime
import traceback
import logging

from django.http import HttpResponseRedirect
from django.utils.translation import check_for_language
from django.shortcuts import render

from blueapps.account.middlewares import LoginRequiredMiddleware

from gcloud.conf import settings
from gcloud.core.roles import FUNCTOR, AUDITOR, NORMAL
from gcloud.core.api_adapter import is_user_functor, is_user_auditor
from gcloud.core.project import prepare_projects, get_default_project_for_user

logger = logging.getLogger("root")


def page_not_found(request):
    user = LoginRequiredMiddleware.authenticate(request)
    # 未登录重定向到首页，跳到登录页面
    if not user:
        return HttpResponseRedirect(settings.SITE_URL)
    request.user = user
    return render(request, 'core/base_vue.html', {})


def home(request):
    user_role = NORMAL
    if is_user_functor(request):
        user_role = FUNCTOR
    if is_user_auditor(request):
        user_role = AUDITOR

    try:
        prepare_projects(request)
    except Exception:
        logger.error('an error occurred when sync user business to projects: {detail}'.format(
            detail=traceback.format_exc()
        ))

    default_project = get_default_project_for_user(request.user.username)

    ctx = {
        'user_role': user_role,
        'default_project_id': default_project.id if default_project else None
    }

    return render(request, 'core/base_vue.html', ctx)


def project_home(request, project_id):
    """
    @note: only use to authentication
    @param request:
    @param biz_cc_id:
    @return:
    """
    ctx = {
        'project_id': project_id
    }
    return render(request, 'core/base_vue.html', ctx)


def set_language(request):
    next = None
    if request.method == 'GET':
        next = request.GET.get('next', None)
    elif request.method == 'POST':
        next = request.POST.get('next', None)

    if not next:
        next = request.META.get('HTTP_REFERER', None)
    if not next:
        next = '/'
    response = HttpResponseRedirect(next)

    if request.method == 'GET':
        lang_code = request.GET.get('language', None)
        if lang_code and check_for_language(lang_code):
            if hasattr(request, 'session'):
                request.session["blueking_language"] = lang_code
            max_age = 60 * 60 * 24 * 365
            expires = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age),
                                                 "%a, %d-%b-%Y %H:%M:%S GMT")
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code, max_age, expires)
    return response
