import commonmark
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import ListView
from django.http import JsonResponse
from rest_framework.views import APIView
from posts.forms import PostForm
from rest_framework import generics, authentication, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import PostSerializer, CommentSerializer
from .models import Post, Comment
from author_manager.models import *
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from rest_framework import status




@login_required
def post_create(request, author_id):
    # TODO: inbox
    author = Author.objects.get(id=author_id)
    if request.user.author != author:
        error = "401 Unauthorized"
        return render(request, 'posts/post_create.html', {'error': error}, status=401)

    if request.method == "GET":
        form = PostForm()
        return render(request, 'posts/post_create.html', {'form': form})

    elif request.method == "POST":
        if request.user.author != author:
            error = "401 Unauthorized"
            return render(request, 'posts/post_create.html', {'error': error}, status=401)

        updated_request = request.POST.copy()
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
            return redirect('posts:post_detail', author_id, post.id)
        else:
            print(form.errors)
            return redirect('posts:post_create', author_id)


@login_required
def post_edit(request, author_id, post_id):
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

        updated_request = request.POST.copy()

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
            print(form.errors)
            return redirect('posts:post_create', author_id)


@login_required
def post_detail(request, author_id, post_id):
    # TODO: permission for posts visible to friends

    if request.method == "GET":
        author = Author.objects.get(id=author_id)
        post = get_object_or_404(Post, id=post_id)
        if request.user.author == author:
            isAuthor = True
        else:
            isAuthor = False
            if post.visibility == "private":
                error = "404 Not Found"
                return render(request, 'posts/post_create.html', {'error': error}, status=404)

            elif post.visibility == "friends":
                # TODO:
                # if request.user is not friend to author:
                #       error = "404 Not Found"
                # return render(request, 'posts/post_detail.html', {'error': error})
                pass
        if post.content_type == 'text/markdown':
            post.content = commonmark.commonmark(post.content)
        comments = post.commentsSrc.all().order_by('-published')

        context = {
            "comments": comments,
            "post": post,
            "isAuthor": isAuthor
        }
        return render(request, 'posts/post_detail.html', context)


@login_required
def post_delete(request, author_id, post_id):
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
    if request.method == "GET":
        return render(request, 'posts/my_posts.html', {'author_id': author_id})


class SearchView(ListView):
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
    # API endpoint that gathers all public posts, friends posts, my posts in my node 
    authentication_classes = [authentication.BasicAuthentication, authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer

    def get(self, request):
        user = request.user
        author = Author.objects.get(user=request.user)
        # public posts
        public_posts = Post.objects.filter(visibility='public', unlisted=False).order_by('-published')
        # get friends: friends = author.following.all() & author.follower.all()
        followers = author.followers.all()
        followings = author.followings.all()
        friends = followings & followers
        friend_posts = Post.objects.filter(author__in=friends, visibility="friends", unlisted=False).order_by(
            '-published')
        my_posts = Post.objects.filter(author=author).order_by('-published')
        posts = public_posts | my_posts | friend_posts
        for post in posts:
            if post.content_type == 'text/markdown':
                post.content = commonmark.commonmark(post.content)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, 200)


class MyPostsAPI(generics.GenericAPIView):
    # API endpoint that has to do with one's posts
    authentication_classes = [authentication.BasicAuthentication, authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer
    def get(self, request, author_id):

        author = Author.objects.get(id=author_id)

        posts = author.posts.filter().order_by('-published')
        current_user = Author.objects.get(user=request.user)
        if current_user.id != author.id:
            # TODO: if friend: posts = post.objects.get(Q(visibility='public')|Q(visibility='friends'), unlisted=False)
            # elif not friend: 
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
    authentication_classes = [authentication.BaseAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer

    def get(self, request, author_id, post_id):
        # TODO: remote
        current_user = request.user
        if current_user.id.equals(author_id):
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
            return Response({'detail': 'Post Does Not Exist'}, 404)

        current_user = request.user
        if current_user.id.equals(author_id):
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
        return ({'detail': 'Current user is not authorized to do this operation'}, 401)

    def delete(self, request, author_id, post_id):
        try:
            post = get_object_or_404(Post, id=post_id)
        except Post.DoesNotExist:
            return Response({'detail': 'Post Does Not Exist'}, 404)

        current_user = request.user
        if current_user.id.equals(author_id):
            post.delete()
            content = {
                'status': 0,
                'detail': 'Post deleted'
            }
            return Response(content, 200)
        else:
            return ({'detail': 'Current user is not authorized to do this operation'}, 401)

    def put(self, request, author_id, post_id):
        current_user = request.user
        if not current_user.id.equals(author_id):
            return Response({'detail': 'Current user is not authorized to do this operation'}, 401)
        else:
            author = Author.objects.get(id=author_id)
            post, created = Post.objects.get_or_create(id=post_id, author=author)
            if created:
                serializer = PostSerializer(post, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, 200)
                else:
                    return Response(serializer.errors, 400)
            else:
                return Response({'detail': 'Post with this id already exists'}, 400)
                



@login_required
def create_comment(request, author_id, post_id):
    current_author = Author.objects.get(id=author_id)
    post = get_object_or_404(Post, id=post_id)
    comments = post.commentsSrc.all()  #get all comments from that post_id

    if request.method == "POST":
        comment=request.POST['comment']
        postID=request.POST['post']
        post=Post.objects.get(id=postID) # Obtain the instance
        author = Author.objects.get(user=request.user) # Obtain the instance
        
        comment = Comment.objects.create(author=author, post=post, comment=comment)
        return JsonResponse({"bool":True, 'published': comment.published})


class CommentsAPI(APIView):
    """
    GET [local, remote] get the list of comments of the post whose id is POST_ID (paginated)
    """
    
    def get(self, request, author_id, post_id):
        currentUserID = Author.objects.get(user=request.user).id
        # US: Comments on friend posts are private only to me the original author.
        if (currentUserID == author_id):
            post = get_object_or_404(Post, id=post_id)
            comments = post.commentsSrc.all()  #get all comments from that post_id
            serializer = CommentSerializer(comments, many=True,  remove_fields=['author_displayName'])  #many=True
            #page,id
            response = {
            'type':  "comments",
            'size':len(serializer.data),
            'post': post_id,
            'comments': serializer.data,
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response({'detail': 'Not Found!'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, author_id, post_id):
        author = Author.objects.get(user=request.user)
        post = Post.objects.get(id=post_id)

        comment = Comment.objects.create(author=author, post=post)
        serializer = CommentSerializer(comment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class PostImageAPI(generics.GenericAPIView):
    authentication_classes = [authentication.BasicAuthentication, authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, author_id, post_id):
        post = get_object_or_404(Post, id=post_id, author_id=author_id)
        if post.image:
            return redirect(post.image.url)

        return Response({'detail': 'Post Image Does Not Exist'}, 404)
