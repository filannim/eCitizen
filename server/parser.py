#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Copyright 2015 Yazan Mehyar, Michele Filannino
#
#   All rights reserved. This program and the accompanying materials
#   are made available under the terms of the GNU General Public License.
#
#   authors: Yazan Mehyar, Michele Filannino
#   e-mail : stcyazan25@gmail.com, filannino.m@gmail.com
#
#   For details, just contact us! ;)

import json
import os
import requests
from flask import Flask,request

import sendgrid


app = Flask(__name__)

@app.route('/incoming', methods=['POST'])
def form():
  category = request.form['subject']
  comment = request.form['text']
  username = request.form['from']
  filetype = json.loads(request.form['attachment-info'])[u'attachment1'][u'type']
  filename = json.loads(request.form['attachment-info'])[u'attachment1'][u'name']
  attachment = request.files.get('attachment1').read()
  form = {"comment":comment, "username":username,"category":category}
  files = {'shot_file': (filename, attachment, filetype)}


  r = requests.post("http://127.0.0.1:5005/upload",data=form,files=files)

  sg = sendgrid.SendGridClient('Ansem-eco', 'slpvynom1')
 
  message = sendgrid.Mail()
  message.add_to(username)
  message.set_subject('Re: '+category)
  message.set_text("")
  message.set_html("<!DOCTYPE html><html><head><meta charset='utf-8'>" +
                   "<style type='text/css'></style></head><body>Your " +
                   "report has been registered.<br>Thank you for your" +
                   " contribution.</body></html>")
  message.set_from('eCitizen@vynom.bymail.in')
  sg.send(message)
    
  return "OK"

if __name__=="__main__":
  app.run(host="127.0.0.1", port=5000, use_reloader=True)
