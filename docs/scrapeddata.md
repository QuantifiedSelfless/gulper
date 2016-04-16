{
    'fblikes': ['like1', ], //array of the names of things the user liked on facebook
    
    *------------------------*    
    
    'fbprofile': { //basic profile information
        'birthday' :
        'bio' :
        'education' : {
            'school' : {
                'name' :
                'degree' : 
            }
        }
        'sex_preference' :
        'hometown' :
        'political' :
        'relationship_status' :
        'religion' :
        'work' : {
            'name' :
            'position' :
            'location' :
        }
    }

    *------------------------*    

    'gmail' : [{ //array of emails with text as the email's text, the snippet is a synapsis of the email and the people are the emails involved
        'text' :
        'snippet' :
        'people' : 
    }, ]
 
    *------------------------*    

    'reddit' : { 
        'subs' : {
            'name' :
            'url' :
            'count' :
        }
        'text' : {
            'body' :
            'author' :
            'comment' :
            'count' :
        }
        'submission' : {
            'title' :
            'url' :
            'score' :
            'subreddit' :
            'count' :
        }
        'comment_karma' :
        'link_karma' :
        'like' : {
            'title' :
            'url' :
            'count' :
        }
        'dislikes' : {
            'title' :
            'url' :
            'count' :
        }
    }     
    
    *------------------------*    

    'tumblr' : {
        'source_title' :
        'post_url' :
        'date' :
        'summary' :
        'photos' :
        'blog_name' :
        'content' :
        'likes' :
        'posts' :
    }

    *------------------------*    
    
    'spotify' : {
        'artists' : [{
            'id' :
            'name' :
            'popularity' :
        }, ]
        'tracks' : [{
            'name' :
            'id' :
            'artist' :
            'albulm' :
        }, ]
        'playlist' : [{
            'name' :
            'id' : 
            'track_number' :
            'owner' :
        }, ]
    }

    *------------------------*    

    'fbevents' : [{
        'description' :
        'name' :
        'status' :
    }, ]

    *------------------------*    

    'gphotos' : [
        {
            'faces': : [
                {
                    'rect' : (x0, y0, x1, y1),
                    'score' : float,
                    'pose' : int,
                    'face_hash' : float[128]
                }
            ]
            ... 
            data from:
            https://developers.google.com/drive/v3/reference/files#resource-representations
            ...
        }
    ]

    *------------------------*    

    'fbtext' : {
        'text' :
        'links' :
    }

    *------------------------*    

    'twitter' : {
    }

    *------------------------*    

    'fbphotos' : {
        "me": [
            {
                ...
                fields from:
                https://developers.facebook.com/docs/graph-api/reference/photo/
                ...
                'faces' : [
                    {
                        'rect' : (x0, y0, x1, y1),
                        'score' : float,
                        'pose' : int,
                        'face_hash' : float[128]
                    }
                ]
            }
        ],
        "friends": [
            {
                ...
                fields from:
                https://developers.facebook.com/docs/graph-api/reference/photo/
                ...
                'faces' : [
                    {
                        'rect' : (x0, y0, x1, y1),
                        'score' : float,
                        'pose' : int,
                        'face_hash' : float[128]
                    }
                ]
            }
        ],
        "uploaded": [
            {
                ...
                fields from:
                https://developers.facebook.com/docs/graph-api/reference/photo/
                ...
                'faces' : [
                    {
                        'rect' : (x0, y0, x1, y1),
                        'score' : float,
                        'pose' : int,
                        'face_hash' : float[128]
                    }
                ]
            }
        ],
    },

    *------------------------*    

    'gphotos' : {
        'photos' : {
            'faces' :
        }
    },

    *------------------------*    

    'youtube' : {
        "subscriptions" : ,
        "playlists" : ,
        "userinfo" : ,
        "special_videos" : 
    }
    
}
