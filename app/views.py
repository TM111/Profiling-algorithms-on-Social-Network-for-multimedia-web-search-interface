# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from allauth.socialaccount.models import SocialToken
from django.shortcuts import render, redirect
from .models import *
from django.contrib.auth import login, authenticate
from forms import *
import threading
from app.Index_new_user_data import *
from django.http import HttpResponse
import datetime

solr_string='https://ss440210-eu-west-1-aws.searchstax.com/solr/demo/'
solr = pysolr.Solr(solr_string)
IndexManager=FbIndexManager(solr)

    
def open_file(request):
    if 'name' not in request.GET.keys():
        return redirect('/')
    name=str(request.GET.__getitem__('name'))
    for key in request.GET.keys():
        if str(key)!='name' and str(key)!='_type_':
            name=name+'&'+key+'='+request.GET.__getitem__(key)
    if not request.user.is_anonymous():
        thread= threading.Thread(target=update_file_history, args=(request.user.username,name,request.GET.__getitem__('_type_'),solr,0,))
        thread.start()
    return redirect(name)
    
def history(request):
    print request.user.username
    if request.user.is_anonymous():
        return redirect('/')
    if 'delete' in request.GET.keys():
        solr.delete(q='doc_type:history AND user:'+str(request.user.username))
        solr.commit()
        return render(request, 'app/history.html',{'history':[]})
    response=solr.search(q='doc_type:history AND user:'+str(request.user.username),sort='num desc',rows=1000000,wt='python')
    history=[]
    for result in response:
        s=Search()
        s.title=result['title'][0]
        s.time=result['time'][0]
        s.type=result['type'][0]
        s.f=result['f'][0]
        history.append(s)
    return render(request, 'app/history.html',{'history':history})


def welcome(request):
    try:
        token=SocialToken.objects.filter(account__user=request.user, account__provider='facebook')[0]
        thread= threading.Thread(target=index_data, args=(token,solr,IndexManager,0,))
        thread.start()
        return render(request, 'app/results_list.html')
    except:
        print 'errore'
        return render(request, 'app/results_list.html')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('/')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

def results_list(request):
    print request.GET
    logged= not request.user.is_anonymous()
    if 'click_index' in request.GET.keys():
        if logged:
            user_name=request.user.get_full_name()
        else:
            user_name='not logged'
        doc=[{"doc_type":'history',
             "user_name":user_name,
              "query" : request.GET.__getitem__('query'),
              "filter":request.GET.__getitem__('filter'),
              "click_index":request.GET.__getitem__('click_index'),
              "data":str(datetime.datetime.now())[:19]}]
        solr.add(doc)
        solr.commit()
        
    if logged:
        token=SocialToken.objects.filter(account__user=request.user, account__provider='facebook')[0]
        IndexManager.takeANDindexProfPic(token)
        graph = facebook.GraphAPI (access_token = token)
        tmp_json = graph.get_object(id='me', fields='albums{name,id,photos{images}}')

        user_id=str(tmp_json['id'])
        tmp_json=tmp_json['albums']['data']
        for a in tmp_json:
            if a['name']=="Profile Pictures":
                album=a
                break
        profpic=album['photos']['data'][0]['images'][0]['source']
        
        response=solr.search(q='doc_type:score -score:0 AND (userA:'+user_id+' OR userB:'+user_id+')',rows=pow(10,6),wt='python')

        score_list=[]
        for i in response:
            doc={}
            if str(i['userA'][0])==user_id:
                second_user=i['userB'][0]
            else:
                second_user=i['userA'][0]
            doc.update({'user_id':str(second_user)})
            doc.update({'score':i['score'][0]})
    
            if 'places_' in str(i['type'][0]):
                type='place'
        
            elif 'age_' in str(i['type'][0]):
                type='age'
        
            elif 'books_' in str(i['type'][0]):
                type='book'
            
            elif 'music_' in str(i['type'][0]):
                type='music'
        
            elif 'television_' in str(i['type'][0]):
                type='TV'
        
            elif 'movies_' in str(i['type'][0]):
                type='movie'
        
            elif 'generic_' in str(i['type'][0]):
                type='page'
   
            doc.update({'type':type})
            score_list.append(doc)
        if 1==0:
            return render(request, 'app/results_list.html', {'profpic': profpic,'user_id':user_id,'score_list': score_list,'solr': solr_string})

        thread= threading.Thread(target=index_data, args=(token,solr,IndexManager,0,))
        thread.start()
        return render(request, 'app/results_list.html', {'profpic': profpic,'user_id':user_id,'score_list': score_list,'solr': solr_string})
    return render(request, 'app/results_list.html',{'profpic': 0,'solr': solr_string})