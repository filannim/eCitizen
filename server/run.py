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
import braintree

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
    app.debug = False
    app.secret_key = 'A0Zr85j/3yX-R~XFH!jmN]31X/,?RT'

    braintree.Configuration.configure(braintree.Environment.Sandbox,
                                      '3tcypjcppzymsqf2', 'hvxbq8zf85jbdzr4',
                                      '3094158c6893e98caa71d411e9950a22')

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
    def best_users(methods=['GET']):
        conn = sqlite3.connect('../db/snaps.db')
        curs = conn.cursor()
        category = request.args.get('category', 'all')
        if category != 'all':
            query = str('SELECT username, COUNT(*) FROM snaps WHERE ' +
                        'category="{}" GROUP BY username ORDER BY ' +
                        'COUNT(*) DESC;').format(category)
        else:
            query = str('SELECT username, COUNT(*) FROM snaps GROUP BY ' +
                        'username ORDER BY COUNT(*) DESC;')
        curs.execute(query)
        records = curs.fetchall()
        maximum = sum((r[1] for r in records))
        title_category = category.replace('_', ' ').title()
        return render_template('contributors.html', category=title_category,
                               records=records, maximum=maximum,
                               selcat=category)

    # BRAINTREE APIs
    @app.route('/stats')
    def stats():
        conn = sqlite3.connect('../db/snaps.db')
        curs = conn.cursor()
        curs.execute('SELECT * FROM snaps;')
        records = curs.fetchall()
        return render_template('stats.html', records=records)

    @app.route("/client_token", methods=["GET"])
    def client_token():
        return braintree.ClientToken.generate()

    @app.route('/token')
    def token():
        token = client_token()
        return render_template('requestToken.html', token=token)

    @app.route("/purchases", methods=["POST"])
    def create_purchase():
        nonce = request.form["payment_method_nonce"]
        braintree.Transaction.sale({"amount": "10.00",
                                    "payment_method_nonce": nonce})
        return "Thank you"

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

        try:
            orientation = image_exif[274]
            if orientation == 8:
                image = image.rotate(90)
            elif orientation == 3:
                image = image.rotate(180)
            elif orientation == 6:
                image = image.rotate(-90)
        except TypeError:
            pass

        # check the extension
        shot_name, shot_extension = splitfilename(shot.filename)
        if shot_extension.lower() not in ALLOWED_EXTENSIONS:
            return '.{} format not allowed!'.format(shot_extension.upper())

        # check the GPS coordinates
        gps_dec_tag = 34853
        try:
            exif_gps = image_exif[gps_dec_tag]
            latitude = (exif_gps[1], [d[0] / d[1] for d in exif_gps[2]])
            longitude = (exif_gps[3], [d[0] / d[1] for d in exif_gps[4]])
            longitude = decimal_coord(longitude[1][0], longitude[1][1],
                                      longitude[1][2], longitude[0])
            latitude = decimal_coord(latitude[1][0], latitude[1][1],
                                     latitude[1][2], latitude[0])
        except (KeyError, TypeError):
            # the GPS coordinate decimal tag is not found in the picture
            # read from the upload form
            longitude = request.form['longitude']
            latitude = request.form['latitude']
            if not (longitude or latitude):
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
        username = request.form['username']
        timestamp = datetime.datetime.utcnow()
        records = [(shot_id, category, comment, longitude, latitude, username,
                    timestamp)]
        curs.executemany('INSERT INTO snaps VALUES (?,?,?,?,?,?,?)', records)
        conn.commit()
        conn.close()

        return redirect(url_for('thanks'))

    @app.route('/thanks')
    def thanks():
        # geographical recommendation
        # business recommendation
        return render_template('thanks.html')

    app.run(host="127.0.0.1", port=5010, use_reloader=True)

if __name__ == '__main__':
    main()
