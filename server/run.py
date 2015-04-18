#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Copyright 2015 Michele Filannino, Nikola Milošević
#
#   All rights reserved. This program and the accompanying materials
#   are made available under the terms of the GNU General Public License.
#
#   authors: Michele Filannino, Nikola Milošević
#   e-mail : filannino.m@gmail.com, nikola.milosevic86@gmail.com
#
#   For details, just contact us! ;)

from PIL import Image
import os

from flask import Flask, render_template, redirect, url_for, request
from werkzeug import secure_filename


UPL_FOLDER = os.path.abspath('../pictures')
ALLOWED_EXTENSIONS = set(['.jpg', '.jpeg', '.png'])


def main():
    # Web server initialisation
    app = Flask("boo")
    app.config['UPL_FOLDER'] = UPL_FOLDER
    app.debug = True
    app.secret_key = 'A0Zr85j/3yX-R~XFH!jmN]31X/,?RT'

    # VISUALISATION
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/heat')
    def heat():
        return render_template('heat_map.html')

    # UPLOAD
    @app.route('/upload_shot')
    def upload_picture():
        return render_template('upload.html')

    @app.route('/upload', methods=['POST'])
    def upload():
        shot = request.files['shot_file']
        if not shot:
            return 'Picture unreadable!'
        image = Image.open(shot)

        # check for extension
        shot_name, shot_extension = os.path.splitext(shot.filename)
        if shot_extension.lower() not in ALLOWED_EXTENSIONS:
            return '.{} extension not allowed!'.format(shot_extension.upper())

        # check for GPS coordinates
        gps_dec_tag = 34853
        gps_latitude, gps_longitude = None, None
        try:
            exif_gps = image._getexif()[gps_dec_tag]
            gps_latitude = (exif_gps[1], exif_gps[2])
            gps_longitude = (exif_gps[3], exif_gps[4])
            print 'Latitude:', gps_latitude
            print 'Longitude:', gps_longitude
        except Exception:
            return 'No GPS coordinates found!'

        # store the picture
        shot_name = secure_filename(shot.filename)
        shot.save(os.path.join(app.config['UPL_FOLDER'], shot_name))

        # store its coordinates

        # store its thumbnail
        scaling = image.size[1] / 100
        thumb_size = (image.size[0] / scaling, 100)
        image.thumbnail(thumb_size, Image.ANTIALIAS)
        image.save(os.path.join(app.config['UPL_FOLDER'], 'thumbnails',
                                shot.filename),
                   "JPEG")

        return redirect(url_for('thanks'))

    @app.route('/thanks')
    def thanks():
        # geographical recommendation
        # business recommendation
        return render_template('thanks.html')

    app.run(host="127.0.0.1", port=5005, use_reloader=True)

if __name__ == '__main__':
    main()
