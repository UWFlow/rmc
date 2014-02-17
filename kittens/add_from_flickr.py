#!/usr/bin/env python
from StringIO import StringIO
import os
import re
import sys

import requests
from PIL import Image

import rmc.shared.secrets as s
import rmc.shared.constants as c
import rmc.kittens.data as kitten_data


def get_photo_info_from_flickr(photo_id):
    print >>sys.stderr, 'Getting information about photo id:', photo_id
    url = ("http://api.flickr.com/services/rest/?method=flickr.photos.getInfo"
           "&api_key=%s"
           "&photo_id=%s"
           "&format=json"
           "&nojsoncallback=1") % (s.FLICKR_API_KEY, photo_id)

    return requests.get(url).json["photo"]

COLOR_WIDTH = 150
COLOR_HEIGHT = 150
GREY_WIDTH = 50
GREY_HEIGHT = 50

BASE_OUTDIR = os.path.join(c.RMC_ROOT, 'server', 'static', 'img', 'kittens')


def download_photo(photo_info, index):
    photo_url = ('http://farm%(farm_id)s.staticflickr.com/'
                 '%(server_id)s/%(photo_id)s_%(secret_id)s.jpg') % {
                    'farm_id': photo_info['farm'],
                    'server_id': photo_info['server'],
                    'photo_id': photo_info['id'],
                    'secret_id': photo_info['secret'],
                }

    print >>sys.stderr, 'Downloading', photo_url, '...'
    photo_content = requests.get(photo_url).content
    color_img = Image.open(StringIO(photo_content))

    width, height = color_img.size

    min_dim = min(width, height)

    # Crop to square
    crop_box = (
        (width - min_dim) / 2,
        (height - min_dim) / 2,
        width - (width - min_dim) / 2,
        height - (height - min_dim) / 2
    )
    color_img = color_img.crop(crop_box)

    try:
        grey_img = color_img.copy().convert('L')
    except IOError:
        print >>sys.stderr
        print >>sys.stderr, 'WARNING! You might be missing libjpeg.'
        print >>sys.stderr, 'On OSX:     brew install libjpeg'
        print >>sys.stderr, 'On Ubuntu:  sudo apt-get install libjpeg-dev'
        print >>sys.stderr, 'On Fedora:  yum install libjpeg-devel'
        print >>sys.stderr
        print >>sys.stderr, 'After you have libjpeg installed:'
        print >>sys.stderr, 'pip uninstall Pillow'
        print >>sys.stderr, 'pip install -r requirements.txt'
        print >>sys.stderr
        raise

    color_img.thumbnail((COLOR_WIDTH, COLOR_HEIGHT), Image.ANTIALIAS)
    grey_img.thumbnail((GREY_WIDTH, GREY_HEIGHT), Image.ANTIALIAS)

    color_img_path = os.path.join(BASE_OUTDIR, 'color', '%d.png' % index)
    grey_img_path = os.path.join(BASE_OUTDIR, 'grey', '%d.png' % index)

    color_img.save(color_img_path)
    print >>sys.stderr, 'Saved', os.path.normpath(color_img_path)
    grey_img.save(grey_img_path)
    print >>sys.stderr, 'Saved', os.path.normpath(grey_img_path)


new_flickr_url = sys.argv[1]
new_photo_id = re.compile('\d+').findall(new_flickr_url)[-1]
new_photo_info = get_photo_info_from_flickr(new_photo_id)

index = kitten_data.add_kitten_data(new_photo_info)
download_photo(new_photo_info, index)
