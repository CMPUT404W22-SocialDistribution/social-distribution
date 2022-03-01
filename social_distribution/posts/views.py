import commonmark
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import ListView
from rest_framework import generics, authentication, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from author_manager.models import *
from posts.forms import PostForm
from .models import Post
from .serializers import PostSerializer


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
                'type': 'post'
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
            # TODO: inbox private posts
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
        if request.user.author != author:
            error = "401 Unauthorized"
            return render(request, 'posts/post_create.html', {'error': error}, status=401)

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
    # TODO: permission for DM posts (Jun)

    if request.method == "GET":
        author = Author.objects.get(id=author_id)
        post = get_object_or_404(Post, id=post_id)
        # check if logged in user is author of post
        if request.user.author == author:
            isAuthor = True
        else:
            # auth user is not user
            isAuthor = False
            if post.visibility == "private":
                # post only visible if owner shared post with user
                error = "404 Not Found"
                return render(request, 'posts/post_create.html', {'error': error}, status=404)

            elif post.visibility == "friends":
                # post only visible if user is friend to owner
                if not (request.user.author in author.followings.all() and request.user.author in author.followers.all()):
                    error = "404 Not Found"
                    return render(request, 'posts/post_create.html', {'error': error}, status=404)
        if post.content_type == 'text/markdown':
            post.content = commonmark.commonmark(post.content)  # parse and render markdown content
        context = {
            "post": post,
            "isAuthor": isAuthor
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
        return queryset


class PostsAPI(APIView):
    '''
    API endpoint that gathers all public posts, friends posts, my posts to display in stream.
    
    Method: 
        GET:    - check if user is authenticated.
                - get all posts visible to current user.
                - respond to requests with information and status code.
    '''
    # basic auth for remote nodes, session auth for local node
    authentication_classes = [authentication.BasicAuthentication, authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer

    def get(self, request):
        user = request.user
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
        # get my posts
        my_posts = Post.objects.filter(author=author, unlisted=False).order_by('-published')
        posts = public_posts | my_posts | friend_posts
        for post in posts:
            if post.content_type == 'text/markdown':
                post.content = commonmark.commonmark(post.content)  # parse and render content of type markdown
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, 200)


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
    
    authentication_classes = [authentication.BasicAuthentication, authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer

    def get(self, request, author_id):

        author = Author.objects.get(id=author_id)

        posts = author.posts.filter().order_by('-published')
        current_user = Author.objects.get(user=request.user)
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

    def post(self, request, author_id):
        author = Author.objects.get(id=author_id)
        if request.user.author != author:
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
    authentication_classes = [authentication.BasicAuthentication, authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer

    def get(self, request, author_id, post_id):
        # TODO: remote
        current_user = request.user
        if current_user.author.id==author_id:
            post = get_object_or_404(Post, id=post_id)
        else:
            post = get_object_or_404(Post, id=post_id, visibility='public')

        if post:
            serializer = PostSerializer(post)
            return Response(serializer.data, 200)
        return Response({'detail': 'Not Found!'}, 404)

    def post(self, request, author_id, post_id):
        # update post
        try:
            post = get_object_or_404(Post, id=post_id)
        except Post.DoesNotExist:
            # cannot edit post as post doesn't exist
            return Response({'detail': 'Post Does Not Exist'}, 404)

        current_user = request.user
        if current_user.author.id != author_id:
            return Response({'detail': 'Current user is not authorized to do this operation'}, 401)
        elif current_user.author.id==author_id:
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
        try:
            post = get_object_or_404(Post, id=post_id)
        except Post.DoesNotExist:
            return Response({'detail': 'Post Does Not Exist'}, 404)

        current_user = request.user
        if current_user.author.id==author_id:
            post.delete()
            content = {
                'status': 0,
                'detail': 'Post deleted'
            }
            return Response(content, 200)
        else:
            return Response({'detail': 'Current user is not authorized to do this operation'}, 401)

    def put(self, request, author_id, post_id):
        current_user = request.user
        if not current_user.author.id==author_id:
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
            

class PostImageAPI(generics.GenericAPIView):
    authentication_classes = [authentication.BasicAuthentication, authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, author_id, post_id):
        post = get_object_or_404(Post, id=post_id, author_id=author_id)
        if post.image:
            return redirect(post.image.url)

        return Response({'detail': 'Post Image Does Not Exist'}, 404)
