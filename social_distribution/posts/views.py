from django.shortcuts import get_object_or_404, render
from rest_framework import generics, authentication, permissions

from .serializers import PostSerializer
from .models import Post
from author_manager.models import *
from rest_framework.response import Response

class PostsAPI(generics.GenericAPIView):
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer
    def get(self,request, author_id):
        # TODO: remote
        author = Author.objects.get(id=author_id)
        posts = author.posts.filter(unlisted=False).all()
        current_user = Author.objects.get(user=request.user)
        if current_user.id != author.id:
            posts = posts.filter(visibility='public')

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
        #TODO: remote        
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
        #update post
        try: 
            post = get_object_or_404(Post, id=post_id)
        except Post.DoesNotExist:
            return Response({'detail':'Post Does Not Exist'}, 404)
        
        current_user = request.user
        if current_user.id.equals(author_id):
            #authenticated
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
        return({'detail':'Current user is not authorized to do this operation'}, 401)

    def delete(self, request, author_id, post_id):
        try: 
            post = get_object_or_404(Post, id=post_id)
        except Post.DoesNotExist:
            return Response({'detail':'Post Does Not Exist'}, 404)

        current_user = request.user
        if current_user.id.equals(author_id):
            post.delete()
            content = {
                'status': 0,
                'detail': 'Post deleted'
            }
            return Response(content, 200)
        else:
            return({'detail':'Current user is not authorized to do this operation'}, 401)

    def put(self, request, author_id, post_id):
        current_user = request.user
        if not current_user.id.equals(author_id):
            return Response({'detail':'Current user is not authorized to do this operation'}, 401)
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
                