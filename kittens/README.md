# KITTENS!

We used to use http://placekitten.com/ for profile pictures for anonymous 
students and for all professors, but in order to serve no content over HTTP when 
we enabled HTTPS, we needed to serve the cat images over HTTPS, which 
placekitten has no support for. So we built our own solution.

We use only Creative Commons images found on flickr. If you'd like to add 
another image, you can do that by finding a pretty kitten picture on flickr, 
like this:

    http://www.flickr.com/photos/wapiko57/5324337308/

then running:

    PYTHONPATH=.. ./kittens/add_from_flickr.py http://www.flickr.com/photos/wapiko57/5324337308/

This will automatically create the necessary thumbnails and update the 
attribution data VIA the flickr API. You'll need to have a real working Flickr 
API key in `shared/secrets.py`, which you can generate yourself.
