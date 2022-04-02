import commonmark
import requests

def get_post(remote_nodes, remote_posts, team8_authors, author):
    
    team = author[1]
    author_id = author[0]
    if team == "team8":
        node = remote_nodes["team8"]
        posts_url = node.url + 'api/authors/' + author_id + '/posts/'
        r =  requests.get(posts_url, auth=(node.outgoing_username, node.outgoing_password))
        if r.status_code == 200:
            data = r.json()
            team8_posts = data["items"]
            for post in team8_posts:
                if not post['unlisted']:
                    if post['visibility'] == 'PUBLIC':
                        post_id = str(post["id"]).split('/')[-2]
                    
                        if post["contentType"] == 'text/markdown':
                            post["content"] = commonmark.commonmark(str(post["content"]))
                        author_image = post['author']['profileImage'] if post['author'][
                            'profileImage'] else 'static/img/profile_picture.png'
                        for comment in post['commentsSrc']['comments']:
                            comment['author_displayName'] = team8_authors[comment["author"].split('/')[-2]] #placeholder
                            comment['id'] = comment["id"].split('/')[-2]
                            comment['num_likes'] = comment['likeCount']
                            comment['comment'] = commonmark.commonmark(comment["comment"])
                        post_data = {
                            'author_username': post["author"]["displayName"],
                            'author_displayName': post["author"]["displayName"],
                            'title': post["title"],
                            'id': post_id,
                            'remote': "true",
                            'description': post['description'],
                            'source': post["source"],
                            'origin': "https://project-socialdistribution.herokuapp.com/",
                            'content_type': post["contentType"],
                            'content': post["content"],
                            'author': post["author"],
                            'author_id': author_id,
                            'categories': post["categories"],
                            'published': post["published"],
                            'visibility': post['visibility'].lower(),
                            'unlisted': post['unlisted'],
                            'author_image': author_image,
                            'comments': '',
                            'commentsSrc': {
                                'size': len(post['commentsSrc']['comments']),
                                'comments': post['commentsSrc']['comments']
                            },
                            'num_likes': post['likeCount']

                        }
                        remote_posts.append(post_data)

    elif team == "team5":
        node = remote_nodes["team5"]
        posts_url = node.url + 'service/server_api/authors/' + author_id + '/posts/'
        r =  requests.get(posts_url)
        if r.status_code == 200:
            data =  r.json()
            team5_posts = data["items"]
            for post in team5_posts:
                if not post['unlisted']:

                    if post['visibility'].upper() == 'PUBLIC':
                        post_id = str(post["id"]).split('/')[-1]

                        # post with comments
                        if post["contentType"] == 'text/markdown':
                            post["content"] = commonmark.commonmark(str(post["content"]))
                        author_image = post['author']['profileImage'] if post['author'][
                            'profileImage'] else '/static/img/profile_picture.png'
                        for comment in post['commentsSrc']:
                            comment['id'] = comment["id"].split('/')[-1]
                            comment['num_likes'] = comment['likeCount']
                            comment['comment'] = commonmark.commonmark(comment['comment'])
                        post_data = {
                            'author_username': post["author"]["displayName"],
                            'author_displayName': post["author"]["displayName"],
                            'title': post["title"],
                            'id': post_id,
                            'remote': "true",
                            'description': post['description'],
                            'source': post["id"],
                            'origin': "https://cmput404-w22-project-backend.herokuapp.com/",
                            'content_type': post["contentType"],
                            'content': post["content"],
                            'author': post["author"],
                            'author_id': author_id,
                            'categories': post["categories"],
                            'published': post["published"],
                            'visibility': post["visibility"].lower(),
                            'author_image': author_image,
                            'comments': '',
                            'commentsSrc': {
                                'size': len(post['commentsSrc']),
                                'comments': post['commentsSrc']
                            },
                            'num_likes': post['likeCount']

                        }
                        remote_posts.append(post_data)