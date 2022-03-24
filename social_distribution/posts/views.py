import commonmark
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import ListView
from rest_framework import generics, authentication, permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view
import requests

from author_manager.models import *
from posts.forms import PostForm
from .models import Post, Comment, Like
from .serializers import PostSerializer, CommentSerializer, LikeSerializer
from node.models import Node
from node.authentication import basic_authentication

from django.views.decorators.cache import cache_page

import asyncio
import aiohttp

HEADERS = {'Referer': 'http://squawker-cmput404.herokuapp.com/', 'Mode': 'no-cors'}
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
        if 'Origin' in request.headers:
            origin = str(request.headers['Origin'])
            origin = origin.replace('https', 'http')
        else:
            origin=''

        updated_request.update(
            {
                'author': author,
                'type': 'post',
                'origin': origin
            }
        )
        form = PostForm(updated_request, request.FILES)

        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            if post.visibility == "public":
                # send public posts to follower. Since friends are also followers so friends also receive then in their inboxes
                for follower in author.followers.all():
                    follower.inbox.posts.add(post)
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
def post_detail(request, author_id, post_id):
    '''
    This function allows viewing detail of a post of post_id of author_id.

    Method:
        GET:    - get the current version of post.
                - check if user is authorized to see post.
            
    '''
    if request.method == "GET":
        current_user = request.user
        # Using user name to get author 
        # current_user = Author.objects.get(user=user)
        author = Author.objects.get(id=author_id)
        post = get_object_or_404(Post, id=post_id)
        numLikes = Like.objects.filter(post__id__exact=post.id, comment__id__isnull=True).count()
        # check if logged in user is author of post
        if current_user.author == author:
            isAuthor = True
        else:
            # auth user is not user
            isAuthor = False
            if post.visibility == "private":
                if post.visibleTo == current_user.username:
                    comments = post.commentsSrc.all().order_by('-published')
                    context = {
                        "comments": comments,
                        "post": post,
                        "isAuthor": isAuthor,
                        "numLikes": numLikes
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

        context = {
            "comments": comments,
            "post": post,
            "isAuthor": isAuthor,
            "numLikes": numLikes
        }
        return render(request, 'posts/post_detail.html', context)


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
    for node in Node.objects.all():
        # Clone
        if node.url == 'https://squawker-dev.herokuapp.com/':
            posts_url = node.url + 'api/posts/'
            response = requests.get(posts_url, headers=HEADERS, auth=(node.outgoing_username, node.outgoing_password))
        
            if response.status_code == 200:
                clone_posts = response.json()['posts']
                for post in clone_posts:
                    post['post_id'] =  str(post["id"]).split('/')[-1]
                    if post["content_type"].lower() in ["image/png;base64", "image/jpeg;base64"]:
                        post["image"] = post["origin"] + post["image"]
                    remote_posts.append(post)
            

        # Team 8
        elif node.url == 'http://project-socialdistribution.herokuapp.com/':
            # get all authors of the remote node
            authors_url = node.url + 'api/authors/'
            response = requests.get(authors_url, headers=HEADERS, auth=(node.outgoing_username, node.outgoing_password))
            if response.status_code == 200:
                remote_authors = []
                team8_authors = response.json()['items']
                for author in team8_authors:
                    new_id = str(author["id"])
                    remote_authors.append(new_id.split('/')[-2])

                async def get_post(author_id, session):
                    posts_url = node.url + 'api/authors/' + author_id + '/posts/'
                    r = await session.get(posts_url, auth=aiohttp.BasicAuth(node.outgoing_username, node.outgoing_password))
                    data = await r.json()
                    team8_posts = data["items"]
                    for post in team8_posts:
        
                        if post['visibility'] == 'PUBLIC':
                            # Need Comment API to create comment objects
                            # need to convert categories, comments to arr
                            
                            # for each post, get all comments
                            # comments_url = str(post["comments"]) commented out since T08 hasn't have this field set yet
                            comments = []
                            post_id = str(post["id"])
                            comments_url = node.url + 'api/authors/' + author_id + '/posts/' + post_id +'/comments/'
                            res = requests.get(comments_url, auth=(node.outgoing_username, node.outgoing_password))
                            if res.status_code == 200:
                                post_comments =  response.json['items']
                                for comment in post_comments:
                                    # comment_id = str(comment["id"]).split('/')[-2]
                                    comment_data = {
                                        'author': {
                                            'id': comment["author"]["id"],
                                            'host': comment["author"]["host"],
                                            'displayName': comment["author"]["displayName"],
                                            'profileImage': 'profile_picture.png',
                                            'url': comment["author"]["url"]
                                        },
                                        'author_displayName' : comment["author"]["displayName"],
                                        'comment': comment["comment"],
                                        'contentType': comment["contentType"],
                                        'published': comment["published"],
                                        'id': comment["id"]
                                    }
                                    comments.append(comment_data)
                            comments = sorted(comments, key=lambda k:k['published'], reverse=True)
                            # post with comments
                            if post["contentType"] == 'text/markdown':
                                post["content"] = commonmark.commonmark(str(post["content"]))
                            post_data = {
                                'author_username' : post["author"]["displayName"],
                                'author_displayName' : post["author"]["displayName"],
                                'title' : post["title"],
                                'id' : post["id"],
                                'source' : post["source"],
                                'origin' : "https://project-socialdistribution.herokuapp.com/",
                                'content_type' : post["contentType"],
                                'content' : post["content"],
                                'author' : post["author"],
                                'categories': post["categories"],
                                'published': post["published"],
                                'visibility': 'public',
                                'unlisted': post['unlisted'],
                                'author_image': "profile_picture.png",
                                'comments': '',
                                'commentsSrc': {
                                        'size': len(comments),
                                        'comments': comments
                                }
                            }
                            remote_posts.append(post_data)

                        elif post['visibility'] == 'FRIENDS':
                            # get all friends posts of my remote friend
                            friend_url = node.url + '/authors/' + author_id +'/'
                            # for each post, get my comments and the friend's comments only
                            # comments_url = str(post["comments"]) commented out since T08 hasn't have this field set yet
                            comments = []
                            post_id = str(post["id"])
                            comments_url = node.url + 'api/authors/' + author_id + '/posts/' + post_id +'/comments/'
                            res = requests.get(comments_url, auth=(node.outgoing_username, node.outgoing_password))
                            if res.status_code == 200:
                                post_comments =  response.json['items']
                                for comment in post_comments:
                                    comment_id = str(comment["id"]).split('/')[-2]
                                    if str(comment["author"]["url"]) == request.user.author.url or str(comment["author"]["url"])== friend_url:                                    
                                        comment_data = {
                                            'author': {
                                                'id': comment["author"]["id"],
                                                'host': comment["author"]["host"],
                                                'displayName': comment["author"]["displayName"],
                                                'profileImage': 'profile_picture.png',
                                                'url': comment["author"]["url"]
                                            },
                                            'author_displayName' : comment["author"]["displayName"],
                                            'comment': comment["comment"],
                                            'contentType': comment["contentType"],
                                            'published': comment["published"],
                                            'id': comment_id
                                    }
                                    comments.append(comment_data)
                            if post["contentType"] == 'text/markdown':
                                post["content"] = commonmark.commonmark(str(post["content"]))
                            post_data = {
                                'author_username' : post["author"]["displayName"],
                                'author_displayName' : post["author"]["displayName"],
                                'title' : post["title"],
                                'id' : post["id"],
                                'source' : post["source"],
                                'origin' : "https://project-socialdistribution.herokuapp.com/",
                                'content_type' : post["contentType"],
                                'content' : post["content"],
                                'author' : post["author"],
                                'categories': post["categories"],
                                'published': post["published"],
                                'visibility': 'friends',
                                'unlisted': post['unlisted'],
                                'author_image': "profile_picture.png",
                                'comments': '',
                                'commentsSrc': {
                                        'size': len(comments),
                                        'comments': comments
                                }
                            }
                            remote_posts.append(post_data)

                async def get_posts(remote_authors):
                    async with aiohttp.ClientSession() as session:
                        tasks = []
                        for author_id in remote_authors:
                            tasks.append(
                                get_post(author_id, session)
                            )
                        results = await asyncio.gather(*tasks)
                        return results
                
                tmp = asyncio.run(get_posts(remote_authors))

        # Team 3
        elif node.url == 'https://website404.herokuapp.com/':
            pass
        remote_posts = sorted(remote_posts, key=lambda k:k['published'], reverse=True)

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
            public_posts = Post.objects.filter(visibility='public', unlisted=False).order_by('-published')
            # get friends of current user
            followers = author.followers.all()
            followings = author.followings.all()
            friends = followings & followers
            # get friends' posts that have visibility= friends
            friend_posts = Post.objects.filter(author__in=friends, visibility="friends", unlisted=False).order_by(
                '-published')
            # private post only visible to certain people that author shared to
            # eg. visibleTo is eqaul to certain author.
            private_posts = Post.objects.filter(visibility="private", visibleTo=author.user, unlisted=False).order_by(
                '-published')
            my_posts = Post.objects.filter(author=author, unlisted=False).order_by('-published')
            local_posts = public_posts | my_posts | friend_posts | private_posts
            
            for post in local_posts:
                if post.content_type == 'text/markdown':
                    post.content = commonmark.commonmark(post.content)  # parse and render content of type markdown
            
            
            paginator = PageNumberPagination()
            result_page = paginator.paginate_queryset(local_posts,request)
            serializer = PostSerializer(result_page, many=True)
            response = {
                'count': len(local_posts),
                'posts': serializer.data
            }
            return Response(response, 200)
        else: 
            visibilities = ['public', 'friends']
            public_posts = Post.objects.filter(visibility__in=visibilities, unlisted=False).order_by('-published')
            serializer = PostSerializer(public_posts, many=True)
            post_data = serializer.data
            for post in post_data:
                post['id'] = post["author"]["url"] + '/posts/' + post['id']
                post['author']['id'] = post["author"]["url"]
                for comment in post['commentsSrc']['comments']:
                    comment['author']['id'] = comment['author']['url']
                    comment['id'] = post['comments'] + comment['id']
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
                for comment in post['commentsSrc']['comments']:
                    comment['author']['id'] = comment['author']['url']
                    comment['id'] = post['comments'] + comment['id']
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
                
                data['author']['id'] = author.url
                for comment in data['commentsSrc']['comments']:
                    comment['author']['id'] = comment['author']['url']
                    comment['id'] = data['comments'] + comment['id']
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
        comment=request.POST['comment']
        postID=request.POST['post']
        post=Post.objects.get(id=postID) # Obtain the instance
        postAuthor = post.author
        author = Author.objects.get(user=request.user) # Obtain the instance
        
        comment = Comment.objects.create(author=author, post=post, comment=comment)
        num_likes = Like.objects.filter(comment__id__exact=comment.id).count()
        # Add comment to post author's inbox
        if (author.id != postAuthor.id):
            postAuthor.inbox.comments.add(comment)
        # postAuthor.inbox.comments.remove(comment)
                
    return JsonResponse({"bool":True, 'published': comment.published, 'id': comment.id, 'author': author.id, 'num_likes': num_likes})

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
                comment['id'] = post_author.url + '/posts/' + post.id + '/comments/' + comment['id']
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


class CommentLikesAPI(generics.GenericAPIView):
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = []
    serializer_class = LikeSerializer

    def get(self, request, author_id, post_id, comment_id):
        comment = get_object_or_404(Comment, id=comment_id, post__exact=post_id, author__exact=author_id)
        likes = comment.likes.all()
        serializer = self.serializer_class(likes, many=True)
        return Response(
            data={
                'type': 'likes',
                'size': len(serializer.data),
                'likes': serializer.data
            },
            status=status.HTTP_200_OK)
