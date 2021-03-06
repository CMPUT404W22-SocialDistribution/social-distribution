import asyncio
from functools import partial
import json
import sys
import datetime
import aiohttp
import commonmark
import requests
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import ListView
from requests.auth import HTTPBasicAuth
from rest_framework import status, generics, authentication
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from author_manager.models import *
from node.authentication import basic_authentication
from node.models import Node
from posts.forms import PostForm
from .models import Post, Comment, Like
from .serializers import PostSerializer, CommentSerializer, LikeSerializer
from .helper import get_post
import concurrent.futures

HEADERS = {'Referer': 'http://squawker-cmput404.herokuapp.com/', 'Mode': 'no-cors', 'Access-Control-Allow-Origin': '*'}
URL = 'http://squawker-cmput404.herokuapp.com/'


@login_required
def post_create(request, author_id):
    '''
    This function allows creating new post for given author ID.

    Method:
        GET:  - get form.
        POST: - save form if valid.
    '''
    author = Author.objects.get(id=author_id)
    # check if the current user is authorized to create post with the author_id
    if request.user.author != author:
        error = "401 Unauthorized"
        return render(request, 'posts/post_create.html', {'error': error}, status=401)

    # get a new form
    if request.method == "GET":
        form = PostForm()
        return render(request, 'posts/post_create.html', {'form': form})

    elif request.method == "POST":

        updated_request = request.POST.copy()  # using deepcopy() to make a mutable copy of the object

        updated_request.update(
            {
                'author': author,
                'type': 'post',
                'origin': author.host.strip('/')
            }
        )
        form = PostForm(updated_request, request.FILES)

        if form.is_valid():
            post = form.save(commit=False)
            post.source = author.host + 'authors/' + str(author.id) + '/posts/' + str(post.id)
            post.save()
            if post.visibility == "public":
                # send public posts to follower. Since friends are also followers so friends also receive then in their inboxes
                for follower in author.followers.all():
                    follower.inbox.posts.add(post)
                # send public posts to remote authors
                for node in Node.objects.all():
                    # Clone
                    
                    if node.url == 'https://squawker-dev.herokuapp.com/':
                        authors = []
                        authors_url = f'{node.url}api/authors'
                        response = requests.get(authors_url, headers=HEADERS,
                                                auth=(node.outgoing_username, node.outgoing_password))
                        if response.status_code == 200:
                            clone_authors = response.json()['items']
                            for item in clone_authors:
                                authors.append(item["id"].split('/')[-1])
                            for item in authors:
                                inbox_url = f'{authors_url}/{item}/inbox'
                                payload = {
                                    'type': 'post',
                                    'id': post.source,
                                    'author': {
                                        'id': author.url,
                                        'type': 'author',
                                        'host': author.host,
                                        'displayName': author.displayName,
                                        'github': author.github,
                                        'profileImage': '/static/img/' + author.profileImage,
                                        'url': author.url  
                                    }
                                }
                                response = requests.post(inbox_url, json=payload,
                                                         auth=(node.outgoing_username, node.outgoing_password))
                                
                    elif node.url == "http://project-socialdistribution.herokuapp.com/":
                        authors = []
                        authors_url = f'{node.url}api/authors'
                        response = requests.get(authors_url, headers=HEADERS,
                                                auth=(node.outgoing_username, node.outgoing_password))
                        if response.status_code == 200:
                            team8_authors = response.json()['items']
                            for item in team8_authors:
                                authors.append(item["id"].split('/')[-2])
                            for item in authors:
                                inbox_url = f'{authors_url}/{item}/inbox/'
                                payload = {
                                    'type': 'post',
                                    'visibility': 'public',
                                    'author': item,
                                    'id': author.host + 'api/authors/' + str(author.id) + '/posts/' + str(post.id)
                                }
                                response = requests.post(inbox_url, json=payload, headers=HEADERS,
                                                         auth=HTTPBasicAuth(node.outgoing_username, node.outgoing_password))

                    
                    elif node.url == "https://cmput404-w22-project-backend.herokuapp.com/":
                        authors = []
                        authors_url = f'{node.url}service/server_api/authors/'
                        response = requests.get(authors_url, auth=(node.outgoing_username, node.outgoing_password))
                        if response.status_code == 200:
                            team5_authors = response.json()['items']
                            for item in team5_authors:
                                authors.append(item["id"].split('/')[-1])

                            # post_serializer = PostSerializer(post)
                            for item in authors:
                                inbox_url = f'{authors_url}{item}/inbox'
                                payload = {
                                    'type': 'post',
                                    'title': post.title,
                                    'id': post.source
                                }
                                response = requests.post(inbox_url, json=payload)
                    '''  
                    elif node.url == 'https://website404.herokuapp.com/':
                        authors = []
                        authors_url = f'{node.url}authors?size=100'
                        response = requests.get(authors_url)
                        print('ok')
                        if response.status_code == 200:
                            print('ok2')
                            team3_authors = response.json()['items']
                            for item in team3_authors:
                                authors.append(item["id"].split('/')[-1])

                            for item in authors:
                                inbox_url = f'{node.url}authors/{item}/inbox'  
                                payload = {
                                    'type': 'post',
                                    'author': {
                                        'id': author.url
                                    },
                                    'id': post.source
                                }               
                                response = requests.post(inbox_url, json=payload, auth=(node.outgoing_username, node.outgoing_password))
                                print(response.status_code)
                    '''

            elif post.visibility == "friends":
                friends = author.followers.all() & author.followings.all()
                for friend in friends:
                    friend.inbox.posts.add(post)
            elif post.visibility == "private":
                visible_follower = post.visibleTo
                visible_user = User.objects.get(username=visible_follower)
                notify_user = Author.objects.get(user=visible_user)
                notify_user.inbox.posts.add(post)
            return redirect('posts:post_detail', author_id, post.id)
        else:
            # if form is invalid, return the same html page
            return redirect('posts:post_create', author_id)


@login_required
def post_edit(request, author_id, post_id):
    '''
    This function allows editing a post of post_id for given author_id.

    Method:
        GET:  - get the current version of post.
        POST: - validate new changes with Django form and save.
    '''
    author = Author.objects.get(id=author_id)
    if request.user.author != author:
        error = "401 Unauthorized"
        return render(request, 'posts/post_create.html', {'error': error}, status=401)

    if request.method == "GET":
        post = get_object_or_404(Post, id=post_id)
        form = PostForm(instance=post)
        context = {
            'form': form,
            'edit': True,
            'profile': author,
        }
        return render(request, 'posts/post_create.html', context)

    elif request.method == "POST":
        updated_request = request.POST.copy()  # using deepcopy() to make a mutable copy of the object

        updated_request.update(
            {
                'author': author,
                'type': 'post'
            }
        )
        post = get_object_or_404(Post, id=post_id)
        form = PostForm(updated_request, request.FILES, instance=post)

        if form.is_valid():
            # TODO: remove old image upload if one exists and is being replaced
            post_updated = form.save(commit=False)
            post_updated.save()
            return redirect('posts:post_detail', author_id, post_id)
        else:
            return redirect('posts:post_create', author_id)


@login_required
def post_share(request, author_id, post_id):
    '''
    This function allows sharing a post of post_id of author_id.

    Method:
        GET:    - get current verision of post
        POST:   - Create (Share) a public post with the given post_id
    '''

    if request.method == "GET":
        author = Author.objects.get(id=author_id)
        current_author = request.user.author
        post = get_object_or_404(Post, id=post_id)
        form = PostForm(instance=post)
        form.fields['title'].disabled = True
        form.fields['description'].disabled = True
        form.fields['content_type'].disabled = True
        form.fields['visibility'].disabled = True
        form.fields['visibleTo'].disabled = True
        form.fields['categories'].disabled = True
        form.fields['content'].disabled = True
        form.fields['image'].disabled = True
        form.fields['unlisted'].disabled = True
        context = {
            'form': form,
            'share': True,
            # 'profile': current_author,
        }
        return render(request, 'posts/post_create.html', context)

    elif request.method == 'POST':
        try:
            author = Author.objects.get(id=author_id)
            current_author = request.user.author
            post = get_object_or_404(Post, id=post_id)
        except Post.DoesNotExist:
            error = "404 Not Found"
            return render(request, 'posts/post_create.html', {'error': error}, status=404)

        if post.visibility == 'public':
            updated_request = request.POST.copy()  # using deepcopy() to make a mutable copy of the object

            source = request.build_absolute_uri()
            source = source.replace(str(current_author.id), str(author_id))
            source = source.replace("/share", "")
            origin = post.origin
            title = post.title
            content_type = post.content_type
            visibility = post.visibility
            content = post.content
            description = post.description
            categories = post.categories

            image_url = post.image.name

            updated_request.update(
                {
                    'author': current_author,
                    'type': 'post',
                    'source': source,
                    'origin': origin,
                    'title': title,
                    'content_type': content_type,
                    'visibility': visibility,
                    'content': content,
                    'description': description,
                }
            )

            form = PostForm(updated_request, request.FILES)
            if form.is_valid():
                share_post = form.save(commit=False)
                if post.image:
                    share_post.image = image_url
                share_post.save()
                return redirect('posts:post_detail', current_author.id, share_post.id)
            else:
                return redirect('posts:post_create', current_author.id)

        elif post.visibility == 'friends':
            updated_request = request.POST.copy()  # using deepcopy() to make a mutable copy of the object

            source = request.build_absolute_uri()
            source = source.replace(current_author.id, author_id)
            source = source.replace("/share", "")
            origin = post.origin
            title = post.title
            content_type = post.content_type
            visibility = post.visibility
            content = post.content
            description = post.description

            image_url = post.image.name

            updated_request.update(
                {
                    'author': current_author,
                    'type': 'post',
                    'source': source,
                    'origin': origin,
                    'title': title,
                    'content_type': content_type,
                    'visibility': visibility,
                    'content': content,
                    'description': description,
                }
            )
            form = PostForm(updated_request, request.FILES)
            if form.is_valid():
                share_post = form.save(commit=False)
                if post.image:
                    share_post.image = image_url
                share_post.save()
                return redirect('posts:post_detail', current_author.id, share_post.id)
            else:
                return redirect('posts:post_create', current_author.id)


        else:
            error = "403 Forbidden"
            return render(request, 'posts/post_create.html', {'error': error}, status=403)


@login_required
def post_detail(request, author_id, post_id):
    '''
    This function allows viewing detail of a post of post_id of author_id.

    Method:
        GET:    - get the current version of post.
                - check if user is authorized to see post.
            
    '''
    if request.method == "GET":
        if not request.GET.get("remote"):
            current_user = request.user
            # Using user name to get author 
            # current_user = Author.objects.get(user=user)
            author = Author.objects.get(id=author_id)
            post = get_object_or_404(Post, id=post_id)
            numLikes = Like.objects.filter(post__id__exact=post.id, comment__id__isnull=True).count()
            # check if logged in user is author of post
            notSharePost = True
            current_source = str(request.build_absolute_uri())
            current_source = current_source.replace("http://", "https://")
            post_source = post.source
            post_source = post_source.replace("http://", "https://")
            if current_source != post_source:
                notSharePost = False
            if current_user.author == author:
                isAuthor = True
            else:
                # auth user is not user
                isAuthor = False
                if post.visibility == "private":
                    if post.visibleTo == current_user.username:
                        comments = CommentSerializer(post.commentsSrc.all().order_by('-published'), many=True).data
                        context = {
                            "comments": comments,
                            "post": post,
                            "isAuthor": isAuthor,
                            "numLikes": numLikes,
                            "notSharePost": notSharePost,
                        }
                        return render(request, 'posts/post_detail.html', context)
                    else:
                        error = "404 Not Found"
                        return render(request, 'posts/post_create.html', {'error': error}, status=404)

                elif post.visibility == "friends":
                    # post only visible if user is friend to owner
                    if not (
                            request.user.author in author.followings.all() and request.user.author in author.followers.all()):
                        error = "404 Not Found"
                        return render(request, 'posts/post_create.html', {'error': error}, status=404)
            if post.content_type == 'text/markdown':
                post.content = commonmark.commonmark(post.content)
            
            comments = CommentSerializer(post.commentsSrc.all().order_by('-published'), many=True).data
            # for comment in comments:
            #     comment["comment"] =  commonmark.commonmark(comment["comment"])
            context = {
                "comments": comments,
                "post": post,
                "isAuthor": isAuthor,
                "numLikes": numLikes,
                "notSharePost": notSharePost,
            }
            return render(request, 'posts/post_detail.html', context)
        else:
            node_url = request.GET.get("remote")
            if node_url[-1] != "/":
                node_url += "/"
            # Team 8
            if node_url == "https://project-socialdistribution.herokuapp.com/":
                node_url = node_url.replace("https", "http")
                node = Node.objects.get(url=node_url)
                post_url = f"{node_url}api/authors/{author_id}/posts/{post_id}"
                response = requests.get(post_url, auth=(node.outgoing_username, node.outgoing_password))
                if response.status_code == 200:
                    data = response.json()

                    if data["contentType"] == 'text/markdown':
                        data["content"] = commonmark.commonmark(str(data["content"]))

                    image = data["image"] if "image" in data else ''
                    author_image = data['author']['profileImage'] if data['author'][
                        'profileImage'] else '/static/img/profile_picture.png'
                    post = {
                        "title": data["title"],
                        "description": data["description"],
                        "source": data["source"],
                        "origin": data["origin"],
                        "published": data["published"],
                        "visibility": data["visibility"].lower(),
                        "content": data["content"],
                        "image": image,
                        "author": {
                            "displayName": data["author"]["displayName"],
                            "host": data["author"]["host"],
                            "profileImage": author_image,
                        },
                        "num_likes": data.get('likeCount', 0)
                    }
                    for comment in data["commentsSrc"]["comments"]:
                        comment['num_likes'] = comment.get('likeCount', 0)
                        comment['comment'] = commonmark.commonmark(comment["comment"])
                        comment['author'] =  {
                                    'displayName': 'abc',
                                    'host': node_url
                        } # temp
                    context = {
                        "post": post,
                        "comments": data["commentsSrc"]["comments"]
                    }
            # Team 5
            elif node_url == "https://cmput404-w22-project-backend.herokuapp.com/":
                post_url = f"{node_url}service/server_api/authors/{author_id}/posts/{post_id}"
                source = f"{node_url}authors/{author_id}/posts/{post_id}"
                node = Node.objects.get(url=node_url)
                response = requests.get(post_url, auth=(node.outgoing_username, node.outgoing_password))
                if response.status_code == 200:
                    print('ok')
                    data = response.json()
                    if data["contentType"] == 'text/markdown':
                        data["content"] = commonmark.commonmark(str(data["content"]))
                    image = data["image"] if data["image"] else ''
                    author_image = data['author']['profileImage'] if data['author'][
                        'profileImage'] else '/static/img/profile_picture.png'
                    post = {
                        "title": data["title"],
                        "description": data["description"],
                        "source": source,
                        "origin": node_url,
                        "published": data["published"],
                        "visibility": data["visibility"].lower(),
                        "content": data["content"],
                        "image": image,
                        "author": {
                            "displayName": data["author"]["displayName"],
                            "host": data["author"]["host"],
                            "profileImage": author_image,
                        },
                        'num_likes': data.get('likeCount', 0)
                    }

                    for comment in data["commentsSrc"]:
                        comment['num_likes'] = comment.get('likeCount', 0)
                        comment['comment'] = commonmark.commonmark(comment["comment"])
                    context = {
                        "post": post,
                        "comments": data["commentsSrc"]
                    }

            elif node_url == "https://website404.herokuapp.com/":
                post_url = f"{node_url}authors/{author_id}/posts/{post_id}"
                response = requests.get(post_url)
                if response.status_code == 200:
                    data = response.json()
                    if data["contentType"] == 'text/markdown':
                        data["content"] = commonmark.commonmark(str(data["content"]))
                    
                    author_image = data['author']['profileImage'] if data['author'][
                        'profileImage'] else '/static/img/profile_picture.png'
                    post = {
                        "title": data["title"],
                        "description": data["description"],
                        "source": post_url,
                        "origin": node_url,
                        "published": data["published"],
                        "visibility": data["visibility"].lower(),
                        "content": data["content"],
                        "image": '',
                        "author": {
                            "displayName": data["author"]["displayName"],
                            "host": data["author"]["host"],
                            "profileImage": author_image,
                        },
                        'num_likes': data.get('likeCount', 0)
                    }

                    for comment in data["commentsSrc"]['comments']:
                        comment['num_likes'] = comment.get('likeCount', 0)
                        comment['comment'] = commonmark.commonmark(comment["comment"])
                    context = {
                        "post": post,
                        "comments": data["commentsSrc"]['comments']
                    }


            # Dev
            elif node_url == "http://squawker-dev.herokuapp.com/" or node_url == "https://squawker-dev.herokuapp.com/":
                posts_url = f"{node_url}api/authors/{author_id}/posts/{post_id}"
                response = requests.get(posts_url, headers=HEADERS, auth=("squawker", "cmput404"))
                if response.status_code == 200:
                    data = response.json()
                    if data["content_type"] == 'text/markdown':
                        data["content"] = commonmark.commonmark(str(data["content"]))
                    image = data["image"] if data["image"] else ''
                    post = {
                        "title": data["title"],
                        "description": data["description"],
                        "source": data["source"],
                        "origin": data["origin"],
                        "published": data["published"],
                        "visibility": data["visibility"],
                        "content": data["content"],
                        "image": image,
                        "author": {
                            "displayName": data["author_username"],
                            "host": data["author"]["host"],
                            "profileImage": data["author"]["host"] + "static/img/" + data["author"]["profileImage"],
                        },
                        'num_likes': data.get('likeCount', 0)
                    }
                    context = {
                        "post": post,
                        "comments": data["commentsSrc"]["comments"]
                    }
            elif node_url == 'http://squawker-cmput404.herokuapp.com/' or node_url == 'https://squawker-cmput404.herokuapp.com/':
                posts_url = f"{node_url}api/authors/{author_id}/posts/{post_id}"
                response = requests.get(posts_url, headers=HEADERS, auth=("squawker", "cmput404"))
                if response.status_code == 200:
                    data = response.json()
                    if data["content_type"] == 'text/markdown':
                        data["content"] = commonmark.commonmark(str(data["content"]))
                    image = data["image"] if data["image"] else ''
                    post = {
                        "title": data["title"],
                        "description": data["description"],
                        "source": data["source"],
                        "origin": data["origin"],
                        "published": data["published"],
                        "visibility": data["visibility"],
                        "content": data["content"],
                        "image": image,
                        "author": {
                            "displayName": data["author_username"],
                            "host": data["author"]["host"],
                            "profileImage": data["author"]["host"] + "static/img/" + data["author"]["profileImage"],
                        },
                        'num_likes': data.get('likeCount', 0)
                    }
                    context = {
                        "post": post,
                        "comments": data["commentsSrc"]["comments"]
                    }

            try:
                inbox = Inbox.objects.get(author=request.user.author)
                post = Post.objects.get(id=post_id)
                inbox.posts.remove(post)
            except:
                None
            return render(request, 'posts/post_detail_remote.html', context)


@login_required
def post_delete(request, author_id, post_id):
    '''
    This function allows deleting a post of post_id of author_id.

    Method:
        GET:    - check if current user is post's owner.
                - delete post.
            
    '''
    if request.method == "GET":
        author = Author.objects.get(id=author_id)
        post = get_object_or_404(Post, id=post_id)
        if request.user.author == author:
            post.delete()
            return redirect('author_manager:home')
        else:
            error = "401 Unauthorized"
            return render(request, 'posts/post_create.html', {'error': error}, status=401)


@login_required
def my_posts(request, author_id):
    '''
    This function gets all posts of an author of author_id.

    Method:
        GET:    - check if current user has author_id and fetch all posts.
                - returns error if unauthorized.
            
    '''
    if request.method == "GET":
        author = Author.objects.get(id=author_id)
        if request.user.author == author:
            return render(request, 'posts/my_posts.html', {'author_id': author_id})
        else:
            error = "401 Unauthorized"
            return render(request, 'posts/post_create.html', {'error': error}, status=401)


class SearchView(ListView):
    '''
    This function allows searching for posts.

    Method:
        GET:    - filers public posts that contain given input.
                - input can be title, description, author username, author name.
            
    '''
    model = Post
    template_name = 'posts/search_results.html'

    def get_queryset(self):
        query = self.request.GET.get('q')
        queryset = Post.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(author__user__username__icontains=query) |
            Q(author__displayName__icontains=query),
            visibility="public",
        )
        # search remote
        return queryset


@login_required
@api_view(['GET'])
def RemotePostsAPI(request):
    ''' API endpoint that gets all remote public and friend posts'''
    # Team 8 hasn't had private posts yet 
    import time

    start_time = time.time()

    remote_posts = []
    remote_authors = []
    remote_nodes = {}
    for node in Node.objects.all():
        # Clone
        if node.url == 'https://squawker-dev.herokuapp.com/':
            posts_url = node.url + 'api/posts/'
            response = requests.get(posts_url, headers=HEADERS, auth=(node.outgoing_username, node.outgoing_password))

            if response.status_code == 200:
                clone_posts = response.json()['posts']
                for post in clone_posts:
                    if not post['unlisted']:
                        post['source'] = post['id']
                        post['remote'] = "true"
                        post['id'] = str(post["id"]).split('/')[-1]          
                        post['author_id'] = post["author"]["id"].split('/')[-1]
                        if post["content_type"] == 'text/markdown':
                            post["content"] = commonmark.commonmark(str(post["content"]))
                        post['author_image'] = '/static/img/' + post['author_image']
                        remote_posts.append(post)
                        for comment in post['commentsSrc']['comments']:
                            comment['comment'] = commonmark.commonmark(comment["comment"])

        # Team 8
        elif node.url == 'http://project-socialdistribution.herokuapp.com/':
            remote_nodes["team8"] = node
            # get all authors of the remote node
            authors_url = node.url + 'api/authors/'
            response = requests.get(authors_url, headers=HEADERS, auth=(node.outgoing_username, node.outgoing_password))
            team8_authors = dict() #temp
            if response.status_code == 200:
                print('ok')
                team8 = response.json()['items']
                for author in team8:
                    remote_authors.append((author["id"].split('/')[-2], 'team8'))
                    team8_authors[author["id"].split('/')[-2]] = author["displayName"] #temp 
        # Team 5
        elif node.url == 'https://cmput404-w22-project-backend.herokuapp.com/':
            remote_nodes["team5"] = node
            authors_url = node.url + 'service/server_api/authors/'
            response = requests.get(authors_url, headers=HEADERS, auth=(node.outgoing_username, node.outgoing_password))
            if response.status_code == 200:
                team5_authors = response.json()['items']
                for author in team5_authors:
                    new_id = str(author["id"])
                    remote_authors.append((new_id.split('/')[-1], 'team5'))
        
        # Team 3
        elif node.url == 'https://website404.herokuapp.com/':
            remote_nodes["team3"] = node
            authors_url = node.url + 'authors?size=100'
            response = requests.get(authors_url)  #no auth header yet
            if response.status_code == 200:
                print('ok')
                team3_authors = response.json()['items']
                for author in team3_authors:
                    remote_authors.append((author['id'].split('/')[-1], 'team3'))

    fn = partial(get_post, remote_nodes, remote_posts, team8_authors)
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(fn, remote_authors)
        
    remote_posts = sorted(remote_posts, key=lambda k: k['published'], reverse=True)

    print("--- %s seconds ---" % (time.time() - start_time))

    return JsonResponse({"posts": remote_posts}, status=200)



class PostsAPI(APIView):
    # local use
    '''
    API endpoint that gathers all public posts, friends posts, my posts to display in stream.
    
    Method: 
        GET:    - check if user is authenticated.
                - get all posts visible to current user.
                - respond to requests with information and status code.
    '''
    # basic auth for remote nodes, session auth for local node
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = []
    serializer_class = PostSerializer

    def get(self, request):
        local, remote = basic_authentication(request)
        if not local and not remote:
            return Response({'detail': 'Access denied'}, 401)
        if local:
            author = Author.objects.get(user=request.user)
            # get public posts
            public_posts = Post.objects.filter(visibility='public', unlisted=False, author__isnull=False).order_by(
                '-published')
            # get friends of current user
            followers = author.followers.all()
            followings = author.followings.all()
            friends = followings & followers
            # get friends' posts that have visibility= friends
            friend_posts = Post.objects.filter(author__in=friends, visibility="friends", unlisted=False,
                                               author__isnull=False).order_by(
                '-published')
            # private post only visible to certain people that author shared to
            # eg. visibleTo is eqaul to certain author.
            private_posts = Post.objects.filter(visibility="private", visibleTo=author.user, unlisted=False,
                                                author__isnull=False).order_by(
                '-published')
            my_posts = Post.objects.filter(author=author, unlisted=False, author__isnull=False).order_by('-published')
            local_posts = public_posts | my_posts | friend_posts | private_posts

            for post in local_posts:
                if post.content_type == 'text/markdown':
                    post.content = commonmark.commonmark(post.content)  # parse and render content of type markdown

            # paginator = PageNumberPagination()
            # result_page = paginator.paginate_queryset(local_posts, request)
            # serializer = PostSerializer(result_page, many=True)
            serializer = PostSerializer(local_posts, many=True)
            response = {
                'count': len(local_posts),
                'posts': serializer.data
            }
            return Response(response, 200)
        else:
            visibilities = ['public', 'friends']
            public_posts = Post.objects.filter(visibility__in=visibilities, unlisted=False,
                                               author__isnull=False).order_by('-published')
            serializer = PostSerializer(public_posts, many=True)
            post_data = serializer.data
            for post in post_data:
                post['id'] = post["author"]["url"] + '/posts/' + post['id']
                if post["content_type"].lower() in ["image/png;base64", "image/jpeg;base64"] or post["image"]:
                    post["image"] = post["origin"] + post["image"]
                post['author']['id'] = post["author"]["url"]
                for comment in post['commentsSrc']['comments']:
                    comment['author']['id'] = comment['author']['url']
                    comment['id'] = '/'.join((post['comments'].rstrip('/'), comment['id']))
            response = {
                'posts': post_data
            }
            return Response(response, 200)


class MyPostsAPI(generics.GenericAPIView):
    '''
    The class defines and API endpoint that allows user to get all posts of author of given author_id,
    and add post if current user has author_id

    Method: 
        GET:    - handle get requests from external APIs.
                - checks for authorization header of request or session cookie.
                - get all posts of author_id that can be visible to current user.

        POST:   - handle post requests.
                - post and validate data with default serializer.
                - responds to requests with status code.

    '''

    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = []
    serializer_class = PostSerializer

    # local & remote
    def get(self, request, author_id):
        local, remote = basic_authentication(request)
        if not local and not remote:
            return Response({'detail': 'Access denied'}, 401)

        author = get_object_or_404(Author, id=author_id)

        posts = author.posts.filter().order_by('-published')
        if local:
            current_user = get_object_or_404(Author, user=request.user)
            if current_user.id != author.id:
                # local 
                posts = posts.filter(visibility='public', unlisted=False)

            for post in posts:
                if post.content_type == 'text/markdown':
                    post.content = commonmark.commonmark(post.content)

            serializer = PostSerializer(posts, many=True)

            content = {
                'current user': request.user.username,
                'author': author.displayName,
                'posts': serializer.data
            }
            return Response(content, 200)

        if remote:
            posts = author.posts.filter().order_by('-published')
            for post in posts:
                if post.content_type == 'text/markdown':
                    post.content = commonmark.commonmark(post.content)
            serializer = PostSerializer(posts, many=True)
            post_data = serializer.data
            for post in post_data:
                post['id'] = author.url + '/posts/' + post['id']
                post['author']['id'] = author.url
                if post["content_type"].lower() in ["image/png;base64", "image/jpeg;base64"] or post["image"]:
                    post["image"] = post["origin"] + post["image"]
                for comment in post['commentsSrc']['comments']:
                    comment['author']['id'] = comment['author']['url']
                    comment['id'] = post['comments'].replace('api/', '') + '/' + comment['id']
            return Response({'posts': post_data}, 200)

    def post(self, request, author_id):
        author = Author.objects.get(id=author_id)
        local, remote = basic_authentication(request)
        if not local or request.user.author != author:
            return Response({'detail': 'Access denied'}, 401)

        post = Post.objects.create(author=author)
        serializer = PostSerializer(post, data=request.data)
        if serializer.is_valid():
            serializer.save()
            content = {
                'status': 0,
                'post': serializer.data
            }
            return Response(content, 200)
        return Response(serializer.errors, 400)


class PostDetailAPI(generics.GenericAPIView):
    '''
    The class defines and API endpoint that allows user to get detail of post of post_id.
    Owner of author id and post of post_id can add, edit, delete that post. 

    Method: 
        GET:    - handle get requests from external APIs.
                - checks for authorization header of request or session cookie.
                - get post of post_id if it can be visible to current user.

        POST:   - handle post requests.
                - update and validate data with default serializer.
                - responds to requests with status code.
        
        PUT:    - handle put requests.
                - create new post with post_id if it doesn't exist in db (Abram's spec).
                - responds to requests with status code.

        DELETE: - handle delete requests.
                - delete post with post_id if it existed in db.
                - respons to requests with status code.

    '''
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = []
    serializer_class = PostSerializer

    def get(self, request, author_id, post_id):
        local, remote = basic_authentication(request)
        if not local and not remote:
            return Response({'detail': 'Access denied'}, 401)
        author = get_object_or_404(Author, id=author_id)

        if local:
            # local user 
            current_user = request.user
            if current_user.author.id == author_id:
                post = get_object_or_404(Post, id=post_id, author=author)
            else:
                post = get_object_or_404(Post, id=post_id, author=author, visibility='public')

            if post:
                serializer = PostSerializer(post)
                return Response(serializer.data, 200)
            return Response({'detail': 'Not Found!'}, 404)
        if remote:
            post = get_object_or_404(Post, id=post_id, author=author, visibility='public')
            if post:
                serializer = PostSerializer(post)
                data = serializer.data
                data['id'] = author.url + '/posts/' + data['id']

                if data["content_type"].lower() in ["image/png;base64", "image/jpeg;base64"] or data["image"]:
                    data["image"] = data["origin"] + data["image"]

                data['author']['id'] = author.url
                for comment in data['commentsSrc']['comments']:
                    comment['author']['id'] = comment['author']['url']
                    comment['id'] = data['comments'].replace('api/', '') + '/'+ comment['id']
                return Response(data, 200)
            return Response({'detail': 'Not Found!'}, 404)

    def post(self, request, author_id, post_id):
        # update post
        local, remote = basic_authentication(request)
        if not local:
            return Response({'detail': 'Access denied'}, 401)

        try:
            post = get_object_or_404(Post, id=post_id)
        except Post.DoesNotExist:
            # cannot edit post as post doesn't exist
            return Response({'detail': 'Post Does Not Exist'}, 404)

        current_user = request.user
        if current_user.author.id != author_id:
            return Response({'detail': 'Current user is not authorized to do this operation'}, 401)
        elif current_user.author.id == author_id:
            # authenticated
            serializer = PostSerializer(post, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                content = {
                    'status': 0,
                    'post': serializer.data
                }
                return Response(content, 200)
            else:
                return Response(serializer.errors, 400)

    def delete(self, request, author_id, post_id):
        local, remote = basic_authentication(request)
        if not local:
            return Response({'detail': 'Access denied'}, 401)

        try:
            post = get_object_or_404(Post, id=post_id)
        except Post.DoesNotExist:
            return Response({'detail': 'Post Does Not Exist'}, 400)

        current_user = request.user
        if current_user.author.id == author_id:
            post.delete()
            content = {
                'status': 0,
                'detail': 'Post deleted'
            }
            return Response(content, 200)
        else:
            return Response({'detail': 'Current user is not authorized to do this operation'}, 401)

    def put(self, request, author_id, post_id):
        local, remote = basic_authentication(request)
        if not local:
            return Response({'detail': 'Access denied'}, 401)

        current_user = request.user
        if not current_user.author.id == author_id:
            return Response({'detail': 'Current user is not authorized to do this operation'}, 401)
        else:
            author = Author.objects.get(id=author_id)
            post, created = Post.objects.get_or_create(id=post_id, author=author)

            # if post was just created, update the post with new data in payload.
            if not created:
                return Response({'detail': 'Post with this id already exists'}, 400)
            else:
                serializer = PostSerializer(post, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, 200)
                else:
                    return Response(serializer.errors, 400)




@login_required
def create_comment(request, author_id, post_id):
    if request.method == "POST":
        # comment=request.POST['comment']
        comment = json.load(request)['comment']
        comment = commonmark.commonmark(comment)
        post = Post.objects.get(id=post_id)  # Obtain the instance
        postAuthor = post.author
        author = Author.objects.get(user=request.user)  # Obtain the instance
        comment = Comment.objects.create(author=author, post=post, comment=comment)
        num_likes = Like.objects.filter(comment__id__exact=comment.id).count()
        # Add comment to post author's inbox
        if (author.id != postAuthor.id):
            postAuthor.inbox.comments.add(comment)
        # postAuthor.inbox.comments.remove(comment)

    return JsonResponse(
        {"bool": True, 'comment': comment.comment, 'published': comment.published, 'id': comment.id,
         'author': author.id, 'num_likes': num_likes})


class CommentsAPI(APIView):
    """
    GET [local, remote] get the list of comments of the post whose id is POST_ID (paginated)
    Methods:
        GET:
            Retrieve a list of comments from a post
        POST:
            Create new comment
    """
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = []

    def get(self, request, author_id, post_id):
        local, remote = basic_authentication(request)
        if not local and not remote:
            return Response({'detail': 'Access denied'}, 401)

        author = get_object_or_404(Author, id=author_id)
        # User see comments from posts they have access to 
        # US: Comments on friend posts are private only to me the original author.
        post_author = get_object_or_404(Author, id=author_id)  # Check if post author exist
        post = get_object_or_404(Post, id=post_id, author=post_author)  # Check if post exist
        comments = post.commentsSrc.all()  # get all comments from that post_id
        serializer = CommentSerializer(comments, many=True, remove_fields=['author_displayName'])  # many=True

        data = serializer.data

        if remote:
            # for remote only
            for comment in data:
                comment['id'] = post_author.url + '/posts/' + str(post.id) + '/comments/' + comment['id']
                comment['author']['id'] = comment['author']['url']

        # page,id
        response = {
            'type': "comments",
            'size': len(serializer.data),
            'post': post_id,
            'comments': data,
        }
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, author_id, post_id):
        # For now, User can add comments for posts they have access to 
        # OR public posts can have comments from friends ??
        post_author = get_object_or_404(Author, id=author_id)  # check on post author id given in url
        post = get_object_or_404(Post, id=post_id)
        current_author = Author.objects.get(user=request.user)

        comment = Comment.objects.create(author=current_author, post=post)
        serializer = CommentSerializer(comment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostImageAPI(generics.GenericAPIView):
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = []

    def get(self, request, author_id, post_id):
        local, remote = basic_authentication(request)
        if not local and not remote:
            return Response({'detail': 'Access denied'}, 401)
        post = get_object_or_404(Post, id=post_id, author_id=author_id)
        if post.image:
            return redirect(post.image.url)

        return Response({'detail': 'Post Image Does Not Exist'}, 404)


class PostLikesAPI(generics.GenericAPIView):
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = []
    serializer_class = LikeSerializer

    def get(self, request, author_id, post_id):
        local, remote = basic_authentication(request)
        if local and remote:
            return HttpResponseBadRequest('Node cannot be local and remote')

        post = get_object_or_404(Post, id=post_id, author_id__exact=author_id)
        likes = post.likes.all()
        serializer = self.serializer_class(likes, many=True)
        return Response(
            data={
                'type': 'likes',
                'size': len(serializer.data),
                'likes': serializer.data
            },
            status=status.HTTP_200_OK)


class RemotePostLikesAPI(generics.GenericAPIView):
    POST_LIKES_API_ENDPOINT = 'api/authors/{}/posts/{}/likes/'

    def get(self, request, author_id, post_id):
        if 'node' not in request.headers:
            return HttpResponseBadRequest("Missing header 'node: node_url'")
        node_url = request.headers['node']

        # backwards compatibility can be painful
        if node_url == 'http://squawker-dev.herokuapp.com/':
            node_url = node_url.replace('http', 'https')

        node = get_object_or_404(Node, url=node_url)

        # Handle URL special cases for each remote node
        post_likes_url = node.url + self.POST_LIKES_API_ENDPOINT.format(author_id, post_id)
        if node.url == 'https://squawker-dev.herokuapp.com/':
            post_likes_url = post_likes_url.rstrip('/')

        with requests.get(post_likes_url,
                          auth=HTTPBasicAuth(node.outgoing_username, node.outgoing_password)) as response:
            # print(f'{response.reason=}, {response.content=}')
            if response.ok:
                return Response(data=response.json(), status=response.status_code)
        return Response({'detail': f'Unable to get Likes for Post object {post_likes_url}'}, status=response.status_code)


class RemoteCommentLikesAPI(generics.GenericAPIView):
    COMMENT_LIKES_API_ENDPOINT = 'api/authors/{}/posts/{}/comments/{}/likes/'

    def get(self, request, author_id, post_id, comment_id):
        if 'node' not in request.headers:
            return HttpResponseBadRequest("Missing header 'node: node_url'")

        # backwards compatibility
        node_url = request.headers['node']
        if node_url == 'http://squawker-dev.herokuapp.com/':
            node_url = node_url.replace('http', 'https')

        node = get_object_or_404(Node, url=node_url)
        comment_likes_url = node.url + self.COMMENT_LIKES_API_ENDPOINT.format(author_id, post_id, comment_id)
        if node.url == 'https://squawker-dev.herokuapp.com/':
            comment_likes_url = comment_likes_url.rstrip('/')
        with requests.get(comment_likes_url,
                          auth=HTTPBasicAuth(node.outgoing_username, node.outgoing_password)) as response:
            if response.ok:
                return Response(data=response.json(), status=response.status_code)
        return Response({'detail': f'Unable to get Likes for Comment object {comment_likes_url}'},
                        status=response.status_code)


class CommentLikesAPI(generics.GenericAPIView):
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = []
    serializer_class = LikeSerializer

    def get(self, request, author_id, post_id, comment_id):
        comment = get_object_or_404(Comment, id=comment_id, post__exact=post_id)
        likes = comment.likes.all()
        serializer = self.serializer_class(likes, many=True)
        return Response(
            data={
                'type': 'likes',
                'size': len(serializer.data),
                'likes': serializer.data
            },
            status=status.HTTP_200_OK)





def format_published(timestamp):
    '''
    Helper function to beautify github timestamp based on system's locale and language settings
    Params: timestamp - published time
    Return: customized Python date object
    '''
    date = datetime.datetime.strptime(str(timestamp), "%Y-%m-%dT%H:%M:%SZ")
    date = date.strftime('%c')
    return date