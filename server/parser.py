from flask import Flask,request
import json, os, requests, sendgrid

extentions = ['jpeg','jpg','png']
app = Flask(__name__)
@app.route('/incoming',methods=['POST'])
def form():
  data = {}
  data['category'] = request.form['subject']
  data['comment'] = request.form['text']
  data['username'] = request.form['from']
  attachment = request.files.get(('attachment1'))
  attachment = {'shot_file':attachment.read()}

  resp = requests.post("/upload", data=data, files=attachment)

  sg = sendgrid.SendGridClient('Ansem-eco', 'slpvynom1')
 
  message = sendgrid.Mail()
  message.add_to(data['username'])
  message.set_subject('Re: '+data['category'])
  message.set_html("")
  message.set_text("Thank You")
  message.set_from('eCitizen@vynom.bymail.in')
  #sg.send(message)
    
  return "OK"

if __name__=="__main__":
        app.run()

  # pic = json.loads(request.form['attachment-info'])
  # fileExtension = os.path.splitext(pic[u'attachment1'][u'name'])[1]
  # print fileExtension
  # if fileExtension.lower() in extentions: