from flask import Flask, request, Response,render_template,send_file
import jsonpickle
import numpy as np
import os
import cv2
from flask import json, flash, redirect, session, abort
from flask_cors import CORS, cross_origin
from flask import jsonify
from keras.applications.inception_v3 import preprocess_input
from keras.models import load_model
from keras.preprocessing.image import img_to_array,load_img
import matplotlib.pyplot as plt
import cv2
import warnings
from sqlalchemy.orm import sessionmaker
from db import *

warnings.filterwarnings('ignore')

def pred(img_path):    
    img = load_img(img_path,target_size = (299,299)) #Load the image and set the target size to the size of input of our model
    x = img_to_array(img) #Convert the image to array
    x = np.expand_dims(x,axis=0) #Convert the array to the form (1,x,y,z) 
    x = preprocess_input(x) # Use the preprocess input function o subtract the mean of all the images
    p = np.argmax(model.predict(x)) # Store the argmax of the predictions
    ##PS : MODEL GIVES INDEX WE NEED TO RETURN LABEL
    return rev_label[p]

model = load_model('saved_models/new_data.hdf5')
model._make_predict_function()
app = Flask(__name__)
Labels ={'Acne': 0, 'Alopecia': 1, 'Normal Skin': 2, 'Tinea': 3}
rev_label = {val:key for key,val in Labels.items()}
engine = create_engine('sqlite:///skiai.db', echo=True)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

CORS(app, resources=r'/upload/*', allow_headers='Content-Type')


@app.route('/',methods=['POST','GET'])
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('index.html')


@app.route('/admin-login',methods=['POST'])
def admin_login():
    if request.form['password'] =='password' and request.form['username'] =='admin':
        session['logged_in'] = True
    else:
        flash("Wrong password!")
        return home()

@app.route('/login',methods=['POST','GET'])
def login():
    POST_USERNAME = str(request.form['username'])
    POST_PASSWORD = str(request.form['password'])
    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(User).filter(User.username.in_([POST_USERNAME]), User.password.in_([POST_PASSWORD]) )
    res1 = query.first()
    if not res1:
        flash("Wrong Password")
        return home()
    
    result = query.all()
    dbobj = result[0]
    role = str(dbobj.district)

    if role=="No":
        session['logged_in'] = True
        return home()
    else:
        
        return render_template('district.html')

@app.route('/entries',methods=['POST','GET'])
def show_entries():
    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(Data)
    try:
        res = query.all()
    except Exception as e:
        res = ["Sorry couldnt fetch"]
        print(e)
    finally:
        print("HEREREEE",res)
        return render_template('district.html',res=res)

@app.route('/logout')
def logout():
    session['logged_in'] = False
    return home()

@app.route('/image', methods=['POST'])
def test():
    #print(request.form)
    #file pick and predict --not to touch
    Session = sessionmaker(bind=engine)
    s = Session()
    fname = request.form.get('firstname')
    lname = request.form.get('lastname')
    gender = request.form.get('gender')
    age = request.form.get('age')
    Historyofpresentillness = request.form.get('Historyofpresentillness',default='-',type=str)
    history1 = request.form.get('history1',default='-',type=str)
    history2 = request.form.get('history2',default='-',type=str)
    history3 = request.form.get('history3',default='-',type=str)
    history4 = request.form.get('history4',default='-',type=str)
    symptom1 = request.form.get('symptom1',default='-',type=str)
    symptom2 = request.form.get('symptom2',default='-',type=str)
    symptom3 = request.form.get('symptom3',default='-',type=str)
    symptom4 = request.form.get('symptom4',default='-',type=str)
    symptom5 = request.form.get('symptom5',default='-',type=str)
    Drugshistory = request.form.get('Drugshistory',default='-',type=str)
    print("\n\n MYDRUG",Drugshistory,'\n\n')
    target = os.path.join(APP_ROOT, 'static/image/')
    if not os.path.isdir(target):
        os.mkdir(target)
    for file in request.files.getlist("file"):
        filename = file.filename
        destination = "/".join([target, filename])
        file.save(destination)
        model_pred = pred(destination)
        row = Data(fname,lname,gender,age,Historyofpresentillness,
                    history1,history2,history3,history4,
                    symptom1,symptom2,symptom3,symptom4,symptom5,
                    Drugshistory,destination,model_pred)
        s.add(row)
    s.commit()
    
    return render_template('pred.html',pred = model_pred)

@app.route('/case/<id>',methods=['POST','GET'])
def cases(id):

    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(Data).filter(Data.id.in_([int(id)+1]))
    res = query.all()
    res_arr = []
    res_dict = res[0].__dict__
    path = res_dict['path']
    path = path.split("//")
    path = path[-1]
    send_me = dict()
    for key,val in res_dict.items():
        if(val != '-'):
            send_me[key] = val
    
    send_me['path'] = '../../static/image/'+path
    print('\n\n\n',send_me,'\n\n\n')
    return render_template('cases.html',caseno=int(id)+1,case=send_me)
    

if __name__ == '__main__':
    app.secret_key = "dbmsisboring"
    app.run(host='0.0.0.0', port=5000,debug = True)