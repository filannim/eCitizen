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

from __future__ import division

import datetime
from PIL import Image
import sqlite3
import os
from os.path import splitext as splitfilename

from flask import Flask, render_template, redirect, url_for, request


UPL_FOLDER = os.path.abspath('static')
ALLOWED_EXTENSIONS = set(['.jpg', '.jpeg', '.png'])


def decimal_coord(degrees, minutes, seconds, direction):
    result = degrees + (minutes / 60) + (seconds / 3600)
    if direction in ('W', 'S'):
        return -result
    else:
        return result


def main():
    # Web server initialisation
    app = Flask("boo")
    app.config['UPL_FOLDER'] = UPL_FOLDER
    app.debug = True
    app.secret_key = 'A0Zr85j/3yX-R~XFH!jmN]31X/,?RT'

    # GENERAL
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/about')
    def about():
        return render_template('about.html')

    # VISUALISATION
    @app.route('/map')
    def map():
        # connect to the DB
        conn = sqlite3.connect('../db/snaps.db')
        curs = conn.cursor()
        curs.execute('SELECT * FROM snaps;')
        records = curs.fetchall()
        return render_template('map.html', records=records)

    @app.route('/heat')
    def heat():
        conn = sqlite3.connect('../db/snaps.db')
        curs = conn.cursor()
        curs.execute('SELECT * FROM snaps;')
        records = curs.fetchall()
        return render_template('heat_map.html', records=records)

    @app.route('/best_users')
    def best_users():
        conn = sqlite3.connect('../db/snaps.db')
        curs = conn.cursor()
        curs.execute('select * from TopContributors order by graffiti desc limit 5;')
        graffiti = curs.fetchall()
        curs.execute('select * from TopContributors order by broken_streets desc limit 5;')
        broken_streets = curs.fetchall()
        curs.execute('select * from TopContributors order by broken_labels desc limit 5;')
        broken_labels = curs.fetchall()
        curs.execute('select * from TopContributors order by fire desc limit 5;')
        fire = curs.fetchall()
        curs.execute('select * from TopContributors order by lightning desc limit 5;')
        lightning = curs.fetchall()
        curs.execute('select * from TopContributors order by garbage desc limit 5;')
        garbage = curs.fetchall()
        return render_template('contributors.html', graffiti=graffiti,broken_streets=broken_streets,broken_labels=broken_labels,fire=fire,lightning=lightning,garbage=garbage)	
	
	
    @app.route('/stats')
    def stats():
        conn = sqlite3.connect('../db/snaps.db')
        curs = conn.cursor()
        curs.execute('SELECT * FROM snaps;')
        records = curs.fetchall()
        return render_template('stats.html', records=records)

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
        image_exif = image._getexif()
        orientation = image_exif[274]
        if orientation == 8:
            image = image.rotate(90)
        elif orientation == 3:
            image = image.rotate(180)
        elif orientation == 6:
            image = image.rotate(-90)

        # check the extension
        shot_name, shot_extension = splitfilename(shot.filename)
        if shot_extension.lower() not in ALLOWED_EXTENSIONS:
            return '.{} extension not allowed!'.format(shot_extension.upper())

        # check the GPS coordinates
        gps_dec_tag = 34853
        latitude, longitude = None, None
        try:
            exif_gps = image_exif[gps_dec_tag]
            latitude = (exif_gps[1], [d[0] / d[1] for d in exif_gps[2]])
            longitude = (exif_gps[3], [d[0] / d[1] for d in exif_gps[4]])
        except Exception:
            return 'No GPS coordinates found!'

        # Next Snap ID
        # Search for the maximum ID in the upload folder and increment it by 1.
        shot_id = -1
        for filename in os.listdir(app.config['UPL_FOLDER']):
            try:
                filename = int(splitfilename(filename)[0])
            except ValueError:
                continue
            if filename > shot_id:
                shot_id = filename
        shot_id = str(shot_id + 1) + ".jpg"

        # store the picture
        image.save(os.path.join(app.config['UPL_FOLDER'], shot_id), "JPEG")

        # store its thumbnail
        scaling = image.size[1] / 100
        thumb_size = (int(image.size[0] / scaling), 100)
        image.thumbnail(thumb_size, Image.ANTIALIAS)
        image.save(os.path.join(app.config['UPL_FOLDER'], 'thumbnails',
                                shot_id), "JPEG")

        # add a record to the DB
        conn = sqlite3.connect('../db/snaps.db')
        curs = conn.cursor()
        category = request.form['category']
        comment = request.form['comment']
        longitude = decimal_coord(longitude[1][0], longitude[1][1], longitude[1][2], longitude[0])
        latitude = decimal_coord(latitude[1][0], latitude[1][1], latitude[1][2], latitude[0])
        username = request.form['username']
        timestamp = datetime.datetime.utcnow()
        records = [(shot_id, category, comment, longitude, latitude, username,
                    timestamp)]
        curs.executemany('INSERT INTO snaps VALUES (?,?,?,?,?,?,?)', records)
        conn.commit()
        curs.execute('SELECT '+category+' from TopContributors where username='+username)
        records = curs.fetchall()
        cat = 0
        for r in records:
            cat = r[0]+1
        curs.execute("UPDATE TopContributors SET "+category+"=? WHERE username=?", (cat, username))        
        conn.commit()
        conn.close()

        return redirect(url_for('thanks'))
    
	
		
	

    @app.route('/thanks')
    def thanks():
        # geographical recommendation
        # business recommendation
        return render_template('thanks.html')

    app.run(host="127.0.0.1", port=5005, use_reloader=True)

if __name__ == '__main__':
    main()
