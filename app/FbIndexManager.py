# -*- coding: utf-8 -*-
from app.functions import * 

def id_list_page(solr):
    response=solr.search(q='doc_type:content AND type:facebook_page',rows=pow(10,6),wt='python')
    response2=solr.search(q='doc_type:page',rows=pow(10,6),wt='python')
    pages_list=[]
    pages_link=[]
    for page in response:
        link=str(page['link'])
        if link not in pages_link:
            pages_link.append(link)
        else:
            continue
        string=''
        for page_user in response2:
            if page['link']==page_user['link']:
                if str(page_user['user_id'][0]) not in string:
                    string=string+' '+str(page_user['user_id'][0])
        doc={}
        for key in page.keys():
            if str(key)=='id' or 'version' in str(key):
                continue
            if str(key)=='category_list':
                l=[]
                for cat in page[key]:
                    l.append(cat)
                doc.update({str(key):l})
                continue
            try:
                doc.update({str(key):str(page[key][0])})
            except:
                try:
                    doc.update({str(key):page[key][0]})
                except:
                    doc.update({str(key):str(page[key])})

        doc.update({'user_id':string})
        pages_list.append(doc)
    query='doc_type:content AND type:facebook_page'
    solr.delete(q=query)
    solr.add(pages_list)
        
        
    
def web_description(list,doc,link):
    try:
        title, description, image = web_preview(link)
        doc.update({'description':description})
        doc.update({'image':image})
        if str(image)=='None':
            doc.update({'image':str(image)})
    except:
        doc.update({'description':'__null__'})
        doc.update({'image':'None'})
    list.append(doc)
    
def image_size(list,doc,link):
    try:
        image_content = requests.get(link).content
        image_stream = io.BytesIO(image_content)
        img = Image.open(image_stream)
        doc.update({'width':img.width})
        doc.update({'height':img.height})
        doc.update({'aspect_ratio':float(img.width)/img.height})
    except:
        doc.update({'width':'__null__'})
        doc.update({'height':'__null__'})
        doc.update({'aspect_ratio':'__null__'})
    list.append(doc)
    
class FbIndexManager():
    solr='istanza di solr'
    
    def __init__(self,solr):
        self.solr=solr
        
    def token_is_valid(self,token):
        url='https://graph.facebook.com/me?access_token='+str(token)
        r = requests.get(url)
        if r.status_code==400:
            print 'token non valido'
            return 0
        return 1
        
    def takeANDindexPosts(self,token):
        if self.token_is_valid(token)==0:
            return
        start=time.clock()
        # 1) SCARICO I DATI IN UN FILE JSON
        graph = facebook.GraphAPI (access_token = token)
        tmp_json = graph.get_object(id='me', fields='name,posts.limit(999999999){status_type,story_tags,name,place,reactions{id},source,message,type,id,link,full_picture,created_time}')
        # 2) CREO UNA LISTA DI ELEMENTI DA AGGIUNGERE
        List=[]
        List.append({'doc_type':'post'})
        user_id=tmp_json['id']
        name=tmp_json['name']
        List.append({'user_id':str(user_id)})
        if 'posts' not in tmp_json.keys():
            return
        tmp_json=tmp_json['posts']['data']
        response=self.solr.search(q='doc_type:post AND user_id:'+str(user_id),rows=100000,wt='python')
        posts_id_list=[]
        Posts=[]
        for i in range(0,len(tmp_json)):
            Posts.append(str(tmp_json[i]['id']))

        for post in response:
            if str(post['id']) not in Posts:
                self.solr.delete(q='doc_type:post AND user_id:'+str(user_id)+' AND id:'+str(post['id']))
            posts_id_list.append(post['id'])
        # 3) FORMATTO E AGGIUNGO GLI ELEMENTI DELLA LISTA AL FILE JSON
        
        Posts=[]
        for i in range(0,len(tmp_json)):
            tmp_json[i].update({'data':str(tmp_json[i]['created_time'])})
            del tmp_json[i]['created_time']
            if 'place' in tmp_json[i].keys():
                place=tmp_json[i]['place']
                tmp_json[i].update({'place_id':place['id']})
                del tmp_json[i]['place']
            if 'reactions' in tmp_json[i].keys():
                tmp_json[i].update({'likes_users_id':tmp_json[i]['reactions']['data']})
                del tmp_json[i]['reactions']
            if 'story_tags' in tmp_json[i].keys():
                string=''
                for j in range(0,len(tmp_json[i]['story_tags'])):
                    if tmp_json[i]['story_tags'][j]['type']=='user': 
                        string=string + tmp_json[i]['story_tags'][j]['id'] + ' '
                del tmp_json[i]['story_tags']
                tmp_json[i].update({'tags_users_id':string})
            
            for j in range(0,len(List)):
                tmp_json[i].update(List[j])
                
            found=0
            for page in posts_id_list:
                if str(tmp_json[i]['id']) == str(page):
                    found=1
                    break
            if found==0:
                Posts.append(tmp_json[i])

        
        # 4) INDICIZZO IN SOLR
        #     E AGGIORNO CONTENUTI
        self.solr.add(Posts)
        self.solr.commit()
        self.takeANDindexPlaces(token)
        self.takeANDindexProfPic(token)
        response=self.solr.search(q='doc_type:profile_picture AND user_id:'+str(user_id),rows=10,wt='python')
        profPic=(response.docs)[0]['link2']
        link_list=[]
        nome=str(graph.get_object(id='me')['name'])
    
        doc_list=[]
        threads=[]
        Contents=[]
        for post in Posts:
            doc={}
            doc.update({'doc_type':'content'})
            doc.update({'type':post['type']})
            doc.update({'user_id':user_id})
            doc.update({'user_name':name})
            doc.update({'user_profile_picture':profPic})
            doc.update({'data':post['data']})
            if post['type']=='link':
                if 'status_type' in post.keys():
                    if 'mobile_status' in post['status_type']:
                        continue

            if ('name' in post.keys()) and (post['type']!='photo') and (post['name'] not in nome):
                doc.update({'name':post['name']})
                
            if 'message' in post.keys():
                doc.update({'message':post['message']})
            elif post['type']!='status':
                doc.update({'message':'__null__'})
            else:
                continue
                
            if 'place_id' in post.keys():
                response=self.solr.search(q='doc_type:place AND place_id:'+str(post['place_id']),rows=1,wt='python')
                for place in response:
                    if 'name' in place.keys():
                        doc.update({'place_name':place['name']})
                    doc.update({'city':place['city']})
                    doc.update({'country':place['country']})
                    
            if post['type']=='video':
                if 'autoplay=1' in str(post['source']):
                    doc.update({'type':'video_link'})
                    doc.update({'link':post['link']})
                else:
                    doc.update({'link':post['source']})
                response=self.solr.search(q='doc_type:content AND link:"'+doc['link']+'"',rows=100000,wt='python')
                if len(response)==0 and doc['link'] not in link_list:
                    if 'autoplay=1' in str(post['source']):
                        thread= threading.Thread(target=web_description, args=(doc_list,doc,post['link'],))
                        thread.start()
                        threads.append(thread)
                    else:
                        doc.update({'image':post['full_picture']})
                        Contents.append(doc)
                    link_list.append(doc['link'])
                
            elif post['type']=='photo':
                doc.update({'image':post['full_picture']})
                response=self.solr.search(q='doc_type:content AND link:"'+doc['image']+'"',rows=100000,wt='python')
                if len(response)==0 and doc['image'] not in link_list:
                    thread= threading.Thread(target=image_size, args=(doc_list,doc,doc['image'],))
                    thread.start()
                    threads.append(thread)
                    link_list.append(doc['image'])
            
            elif post['type']=='status':
                response=self.solr.search(q='doc_type:content AND message:"'+doc['message']+'"',rows=100000,wt='python')
                if len(response)==0 and doc['message'] not in link_list:
                    Contents.append(doc)
                    link_list.append(doc['message'])
                
            elif post['type']=='link':
                doc.update({'link':post['link']})
                response=self.solr.search(q='doc_type:content AND link:"'+doc['link']+'"',rows=100000,wt='python')
                if len(response)==0 and doc['link'] not in link_list:
                    thread= threading.Thread(target=web_description, args=(doc_list,doc,post['link'],))
                    thread.start()
                    threads.append(thread)
                    link_list.append(doc['link'])
            
        
        for t in threads:
            t.join()
        for doc in doc_list:
            Contents.append(doc)

        self.solr.add(Contents)
        self.solr.commit()
        query='doc_type:content AND type:(facebook_page or link) -description:*'
        self.solr.delete(q=query)
        self.solr.commit()
        tempo=str(time.clock()-start)[:4]
        print 'POST INDICIZZATI  '+tempo+' sec.'

        
    def takeANDindexPages(self,token):
        if self.token_is_valid(token)==0:
            return
        start=time.clock()
        
        # 1) SCARICO I DATI IN UN FILE JSON
        graph = facebook.GraphAPI (access_token = token)
        tmp_json = graph.get_object(id='me', fields='likes.limit(999999999){created_time,personal_interests,description,location,name,fan_count,category_list,link,genre,id},id')
        if 'likes' not in tmp_json.keys():
            return
        categories = graph.get_object(id='me', fields='music,television.limit(999999999),movies.limit(9999999999999),books.limit(9999999999)')
        Music_id=[]
        Movies_id=[]
        Books_id=[]
        TV_id=[]
        if 'music' in categories.keys():
            for i in categories['music']['data']:
                Music_id.append(str(i['id']))
        if 'books' in categories.keys():   
            for i in categories['books']['data']:
                Books_id.append(str(i['id']))
        if 'television' in categories.keys():       
            for i in categories['television']['data']:
                TV_id.append(str(i['id']))
        if 'movies' in categories.keys():
            for i in categories['movies']['data']:
                Movies_id.append(str(i['id']))
        # 2) CREO UNA LISTA DI ELEMENTI DA AGGIUNGERE
        List=[]
        List.append({'doc_type':'page'})
        user_id=tmp_json['id']
        List.append({'user_id':user_id})
        tmp_json=tmp_json['likes']['data']
        response=self.solr.search(q='doc_type:page AND user_id:'+str(user_id),rows=100000,wt='python')
        posts_id_list=[]
        Pages=[]
        for i in range(0,len(tmp_json)):
            Pages.append(str(tmp_json[i]['id']))

        for page in response:
            if str(page['page_id'][0]) not in Pages:
                self.solr.delete(q='doc_type:page AND user_id:'+str(user_id)+' AND page_id:'+str(page['page_id'][0]))
            posts_id_list.append(page['page_id'][0])
        
        # 3) FORMATTO E AGGIUNGO 'DOC_TYPE' E 'USER_ID' AL FILE JSON
        Pages=[]
        for i in range(0,len(tmp_json)):
            category_list=[]
            if str(tmp_json[i]['id']) in Music_id:
                tmp_json[i].update({'type':'music'})
            elif str(tmp_json[i]['id']) in TV_id:
                tmp_json[i].update({'type':'television'})
            elif str(tmp_json[i]['id']) in Books_id:
                tmp_json[i].update({'type':'book'})
            elif str(tmp_json[i]['id']) in Movies_id:
                tmp_json[i].update({'type':'movie'})
            else:
                tmp_json[i].update({'type':'generic'})
            tmp_json[i].update({'page_id':tmp_json[i]['id']})
            del tmp_json[i]['id']
            tmp_json[i].update({'data':str(tmp_json[i]['created_time'])})
            del tmp_json[i]['created_time']
            if 'category_list' in tmp_json[i].keys():
                for cat in tmp_json[i]['category_list']:
                    category_list.append(cat['name'])
            if 'genre' not in tmp_json[i].keys():
                tmp_json[i].update({'genre':'__null__'})
            if 'location' in tmp_json[i].keys():
                if 'city' in tmp_json[i]['location'].keys():
                    tmp_json[i].update({'city':tmp_json[i]['location']['city']})
                if 'country' in tmp_json[i]['location'].keys():
                    tmp_json[i].update({'country':tmp_json[i]['location']['country']})
                del tmp_json[i]['location']
            tmp_json[i].update({'category_list':category_list})
            for j in range(0,len(List)):
                tmp_json[i].update(List[j])
                
            found=0
            for page in posts_id_list:
                if str(tmp_json[i]['page_id']) == str(page):
                    found=1
                    break
            if found==0:
                Pages.append(tmp_json[i])
        self.solr.add(Pages)
        self.solr.commit()

        # 4) INDICIZZO IN SOLR
        #   E AGGIORNO CONTENUTI
        doc_list=[]
        threads=[]
        Contents=[]
        for post in Pages:
            doc={}
            doc.update({'doc_type':'content'})
            doc.update({'type':'facebook_page'})
            doc.update({'link':post['link']})
            doc.update({'name':post['name']})
            doc.update({'category_list':post['category_list']})
            doc.update({'genre':post['genre']})
            
            thread= threading.Thread(target=web_description, args=(doc_list,doc,post['link'],))
            thread.start()
            threads.append(thread)
            
        for t in threads:
            t.join()
        for doc in doc_list:
            Contents.append(doc)
                

        self.solr.add(Contents)
        self.solr.commit()
        id_list_page(self.solr)
        tempo=str(time.clock()-start)[:4]
        
        print 'PAGINE INDICIZZATI  '+tempo+' sec.'
        

    def takeANDindexFriends(self,token):
        if self.token_is_valid(token)==0:
            return
        start=time.clock()
        # 1) SCARICO I DATI IN UN FILE JSON
        graph = facebook.GraphAPI (access_token = token)
        tmp_json = graph.get_object(id='me', fields='friends.limit(999999999){id},id')
        if len(tmp_json['friends']['data'])==0:
            id_friends=0
        else:
            id_friends=[]
            for friend in tmp_json['friends']['data']:
                id_friends.append(friend['id'])
            
        query='doc_type:friends_list AND user_id:'+str(tmp_json['id'])
        self.solr.delete(q=query)
        self.solr.add([{'doc_type':'friends_list',
             'user_id':tmp_json['id'],
             'friends_id':id_friends,
             'friends_count':tmp_json['friends']['summary']['total_count'],
             }])
        self.solr.commit()
        tempo=str(time.clock()-start)[:4]
        print 'LISTA AMICI INDICIZZATA  '+tempo+' sec.'
        
    def takeANDindexAge(self,token):
        if self.token_is_valid(token)==0:
            return
        start=time.clock()
        # 1) SCARICO I DATI IN UN FILE JSON
        graph = facebook.GraphAPI (access_token = token)
        tmp_json = graph.get_object(id='me', fields='id,birthday')
        if 'birthday' not in tmp_json.keys():
            return
        index =0
        numbers=['0','1','2','3','4','5','6','7','8','9']
        string=str(tmp_json['birthday'])
        for i in range(0,len(string)):
            if string[i] not in numbers:
                index=i
        try:
            age=int(string[index+1:])
        except:
            return
        query='doc_type:age AND user_id:'+str(tmp_json['id'])
        self.solr.delete(q=query)
        self.solr.add([{'doc_type':'age',
             'user_id':tmp_json['id'],
             'age':age,
             }])
        self.solr.commit()
        tempo=str(time.clock()-start)[:4]
        print 'ETA INDICIZZATA  '+tempo+' sec.'
        
    def takeANDindexProfPic(self,token):
        if self.token_is_valid(token)==0:
            return
        start=time.clock()
        # 1) SCARICO I DATI IN UN FILE JSON
        graph = facebook.GraphAPI (access_token = token)
        tmp_json = graph.get_object(id='me', fields='albums{name,photos{images}}')
        if 'albums' not in tmp_json.keys():
            return
        user_id=tmp_json['id']
        tmp_json=tmp_json['albums']['data']
        for a in tmp_json:
            if a['name']=="Profile Pictures":
                album=a
                break
        
        image=album['photos']['data'][0]['images'][0]['source']
        middle=int(len(album['photos']['data'][0]['images'])-len(album['photos']['data'][0]['images'])/4.0)
        image2=album['photos']['data'][0]['images'][middle]['source']
        query='doc_type:profile_picture AND user_id:'+str(user_id)
        self.solr.delete(q=query)
        self.solr.add([{'doc_type':'profile_picture',
             'user_id':user_id,
             'link':image,
             'link2':image2,
             }])
        self.solr.commit()
        tempo=str(time.clock()-start)[:4]
        print 'PROFPIC INDICIZZATA '+tempo+' sec.'
        
        
    def takeANDindexPlaces(self,token):
        if self.token_is_valid(token)==0:
            return
        start=time.clock()
        # 1) SCARICO I DATI IN UN FILE JSON
        graph = facebook.GraphAPI (access_token = token)
        tmp_json = graph.get_object(id='me', fields='posts{place,created_time},tagged_places,id')
        
        # 2) CREO UNA LISTA DI ELEMENTI DA AGGIUNGERE
        List=[]
        List.append({'doc_type':'place'})
        user_id=tmp_json['id']
        List.append({'user_id':user_id})
        tmp_json2=[]
        
        if 'posts' not in tmp_json.keys():
            return
        tmp_json1=tmp_json['posts']['data']
        for i in range(0,len(tmp_json1)):
            if 'place' not in tmp_json1[i].keys():
                continue
            place=tmp_json1[i]['place']
            tmp_json1[i].update({'place_id':place['id']})
            tmp_json1[i].update({'name':place['name']})
            place=place['location']
            if 'city' not in place.keys():
                tmp_place=get_place(place['latitude'],place['longitude'])
                place.update({'city':tmp_place[0]})
                place.update({'country':tmp_place[1]})
            del place['latitude']
            del place['longitude']
            tmp_json1[i].update(place)
            del tmp_json1[i]['place']
            del tmp_json1[i]['id']
            for j in range(0,len(List)):
                tmp_json1[i].update(List[j])
            tmp_json2.append(tmp_json1[i])
            
            
        dates_list=[]
        for place in tmp_json2:
            dates_list.append(place['created_time'])
            
        if 'tagged_places' not in tmp_json.keys():
            return
        tmp_json1=tmp_json['tagged_places']['data']
        for i in range(0,len(tmp_json1)):
            if tmp_json1[i]['created_time'] in dates_list:
                continue
            place=tmp_json1[i]['place']
            tmp_json1[i].update({'place_id':place['id']})
            tmp_json1[i].update({'created_time':str(tmp_json1[i]['created_time'])})
            tmp_json1[i].update({'name':place['name']})
            place=place['location']
            if 'city' not in place.keys():
                tmp_place=get_place(place['latitude'],place['longitude'])
                place.update({'city':tmp_place[0]})
                place.update({'country':tmp_place[1]})
            del place['latitude']
            del place['longitude']
            tmp_json1[i].update(place)
            del tmp_json1[i]['place']
            del tmp_json1[i]['id']
            for j in range(0,len(List)):
                tmp_json1[i].update(List[j])
            tmp_json2.append(tmp_json1[i])
            


        # 4) INDICIZZO IN SOLR
        query='doc_type:place AND user_id:'+str(user_id)
        self.solr.delete(q=query)
            
        self.solr.add(tmp_json2)
        self.solr.commit()
        tempo=str(time.clock()-start)[:4]
        print 'LUOGHI INDICIZZATI  '+tempo+' sec.'
