from flask import Flask,render_template,request,redirect,url_for,session,send_file,Response
from flask_mysqldb import MySQL
import os,face_recognition,cv2
import numpy as np
import csv,io


from datetime import date,datetime
from flask_mail import Mail,Message


app = Flask(__name__,static_url_path='/static')
app.secret_key = "MyKey"


#Mail Configuration

app.config['MAIL_SERVER'] = 'smtp.elasticemail.com'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '12345.vs95@gmail.com'
app.config['MAIL_PASSWORD'] = '287BCD20BD98CABF118BDFE395B0CAA7DA9D'
app.config['MAIL_DEFAULT_SENDER'] = 'shikshanam.academicportal@gmail.com'

mail = Mail(app)

#MySQL Configuration
app.config['MYSQL_UNIX_SOCKET'] = '/opt/lampp/var/mysql/mysql.sock'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'sikshanam'
mysql = MySQL(app)
 



# Load a sample picture and learn how to recognize it.
vikram_image = face_recognition.load_image_file("static/images/vikram.png")
vikram_face_encoding = face_recognition.face_encodings(vikram_image)[0]

# Load a second sample picture and learn how to recognize it.
tejas_image = face_recognition.load_image_file("static/images/tejas.jpg")
tejas_face_encoding = face_recognition.face_encodings(vikram_image)[0]

# Create arrays of known face encodings and their names
known_face_encodings = [
    vikram_face_encoding,
    tejas_face_encoding
]
known_face_names = [
    "Vikram",
    "Tejas"
]
# Initialize some variables
face_locations = []
face_encodings = []
face_names = []
process_this_frame = True

def gen_frames(subname):  
    #VideoApp
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

            # Only process every other frame of video to save time
           
            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            face_names = []
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"
                # Or instead, use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]

                face_names.append(name)
            

            # Display the results
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
                if (name != "Unknown"):
                    camera.release()
                    cv2.destroyAllWindows()
                    break
            if (name != "Unknown"):
                today = date.today()
                date1 = today.strftime("%B %d, %Y")
                print(date1,name,subname)
                with app.app_context():
                    cur = mysql.connection.cursor()
                    cur.execute(f"INSERT INTO `attendance` (`date`,`student_name`,`subject_name`) VALUES ('{date1}','{name}','{subname}')")
                    mysql.connection.commit()
                    cur.close()
                    

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
 





#All the routes
@app.route('/')
def hello_world():
    try:
        if 'usertype' in session:
            return redirect(url_for('home'))
        else:
            return render_template("about.html")
    except:
        return "<h3><b>Oops Something went wrong please login again!</b></h3>"

@app.route('/sendmail',methods=['GET','POST'])
def sendmail():
    try:    
        if request.method == 'POST':
            year = request.form['year']
            subject = request.form['subject']
            body = request.form['subject']
            cur = mysql.connection.cursor()
            cur.execute(f"select email from student where year = '{year}'")
            recipi = cur.fetchall()
            cur.close()
            recipient=[]
            for i in recipi:
                recipient.append(i[0])
            msg = Message(subject, recipients=recipient)
            msg.body = body
            mail.send(msg)
            return redirect(url_for('dashboard'))
    except:
        return "<h3><b>Oops Something went wrong please login again!</b></h3>"


@app.route('/home')
def home():
    try:
        return render_template("home.html",subjects=session['subjects'],usertype=session['usertype'])
    except:
        return "<h3><b>Oops Something went wrong please login again!</b></h3>"

@app.route('/timetable')
def timetable():
    try:
        cur = mysql.connection.cursor()
        if session['usertype'] == 'student':
            cur.execute(f"select * from timetable_new where year = '{session['studentyear']}'")
            timetable = cur.fetchall()
            session['timetable'] = timetable
            cur.close()
        else:
            cur.execute(f"select * from timetable_new where year = 'firstyear'")
            fytimetable = cur.fetchall()
            session['fytimetable'] = fytimetable

            cur.execute(f"select * from timetable_new where year = 'secondyear'")
            sytimetable = cur.fetchall()
            session['sytimetable'] = sytimetable

            cur.close()

        if 'usertype' in session:
            if session['usertype'] == 'student':
                return render_template("timetable.html",usertype=session['usertype'],timetable=session['timetable'])
            else:
                return render_template("timetable.html",usertype=session['usertype'],fytimetable=session['fytimetable'],sytimetable=session['sytimetable'])
    except:
        return "<h3><b>Oops Something went wrong please login again!</b></h3>"
    
@app.route('/update_timetable',methods =['GET','POST'])
def updateTimetable():
    try:
        subject_name = request.args.get('name')
        subject_id = request.args.get('id')
        
        if request.method == 'POST':
            cur = mysql.connection.cursor()
            status = request.form['status'] 
            id = request.form['id']
            print("ID:",id)
            cur.execute(f"UPDATE timetable_new SET status = '{status}' WHERE id ='{id}';")
            mysql.connection.commit()
            
            cur.execute(f"select * from timetable_new where year = 'firstyear'")
            fytimetable = cur.fetchall()
            session['fytimetable'] = fytimetable
            cur.execute(f"select * from timetable_new where year = 'secondyear'")
            sytimetable = cur.fetchall()
            session['sytimetable'] = sytimetable
            cur.close()

            if 'usertype' in session:
                return render_template("timetable.html",usertype=session['usertype'],fytimetable=session['fytimetable'],sytimetable=session['sytimetable'])

        return render_template("timetable_form.html",id=subject_id,name=subject_name)
    except:
        return "<h3><b>Oops Something went wrong please login again!</b></h3>"

@app.route('/notification',methods =['GET','POST'])
def notification():
    try:
        if request.method == 'POST':
            if(request.form['type'] == 'notification'):
                title = request.form['title']
                content = request.form['content']
                year = request.form['year']
                today = date.today()
                date1 = today.strftime("%B %d, %Y")
                cur = mysql.connection.cursor()
                cur.execute(f"INSERT INTO `notifications` (`date`,`title`,`content`,`year`) VALUES ('{date1}','{title}','{content}','{year}')")
                mysql.connection.commit()
                cur.close()
        cur = mysql.connection.cursor()
        if session['usertype'] == "student":
            cur.execute(f"select * from notifications where year='{session['studentyear']}'")
        else:
            cur.execute(f"select * from notifications where year in ('firstyear','secondyear','thirdyear')")
        session['notifications'] = cur.fetchall()
        cur.close() 
        if 'usertype' in session:
            return render_template("notification.html",usertype=session['usertype'],notification=session['notifications'])
    except:
        return "<h3><b>Oops Something went wrong please login again!</b></h3>"
@app.route('/delete/<id>')
def delete_notification(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute(f"DELETE FROM notifications WHERE id='{id}'")
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('notification',usertype=session['usertype'],notification=session['notifications']))
    except:
        return "<h3><b>Oops Something went wrong please login again!</b></h3>"

@app.route('/update_notification/<id>',methods =['GET','POST'])
def update_notification(id):
    try:
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            cur = mysql.connection.cursor()
            cur.execute(f"UPDATE notifications SET title = '{title}', content = '{content}' WHERE id='{id}'")
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('notification'))
        cur = mysql.connection.cursor()
        cur.execute(f"select * from notifications WHERE id='{id}'")
        selectednoti = cur.fetchone()
        cur.close()
        return render_template("update_notification.html",notification=selectednoti)
    except:
        return "<h3><b>Oops Something went wrong please login again!</b></h3>"
    
@app.route('/papers/<filename>')
def serve_pdf(filename):
    try:
        pdf_path = f'static\media\papers\{filename}'
        return send_file(pdf_path)
    except:
        return "<h3><b>Oops Something went wrong please login again!</b></h3>"

@app.route('/dashboard',methods =['GET','POST'])
def dashboard():
    try:
        if(request.args.get('sets') == 'setsubject'):
            session['subname'] = request.args.get('subject')
        if request.method == 'POST': 

            if(request.form['type'] == 'papers'):
                file = request.files['file']
                displayname = request.form['papername']
                upload_folder = 'static\media\papers'
                file.save(os.path.join(upload_folder,file.filename))
                file.save(file.filename)
                cur = mysql.connection.cursor()
                cur.execute(f"INSERT INTO `papers` (`display_name`,`filename`,`subject_id`) VALUES ('{displayname}','{file.filename}','{sid[0]}')")
                mysql.connection.commit()
                cur.close()
            elif(request.form['type'] == 'notes'):
                file = request.files['file']
                displayname = request.form['notename']
                upload_folder = 'static\media\\notes'
                file.save(os.path.join(upload_folder,file.filename))
                file.save(file.filename)
                cur = mysql.connection.cursor()
                cur.execute(f"INSERT INTO `notes` (`display_name`,`filename`,`subject_id`) VALUES ('{displayname}','{file.filename}','{sid[0]}')")
                mysql.connection.commit()
                cur.close()

        cur = mysql.connection.cursor()
        cur.execute(f"select id from subject where name='{session['subname']}'")
        sid = cur.fetchone()
        cur.execute(f"select * from papers where subject_id='{sid[0]}'")
        session['papers'] = cur.fetchall()
        cur.execute(f"select * from notes where subject_id='{sid[0]}'")
        session['notes'] = cur.fetchall()
        cur.close() 
        
        if 'usertype' in session:
            return render_template("dashboard.html",usertype=session['usertype'],papers=session['papers'],notes=session['notes'])
    except:
        return "<h3><b>Oops Something went wrong please login again!</b></h3>"
    
@app.route('/profile')
def profile():
    try:
        if 'usertype' in session:
            return render_template("profile.html",usertype=session['usertype'])
    except:
        return "<h3><b>Oops Something went wrong please login again!</b></h3>"
    
@app.route('/about')
def about():
    try:
        if 'usertype' in session:
            return render_template("about.html",usertype=session['usertype'])
        else:
            return render_template("about.html")
    except:
        return "<h3><b>Oops Something went wrong please login again!</b></h3>"
    
@app.route('/login', methods =['GET','POST'])
def login():
        if request.method == 'POST':
            print("req-form",request.form)
            usertype = request.form['usertype']
            session['usertype'] = usertype
            email = request.form['email']
            password = request.form['password']
            cur = mysql.connection.cursor()
            if usertype == 'teacher':
                cur.execute(f"select email,password,id from teacher where email = '{email}'")
            elif usertype == 'student':
                cur.execute(f"select email,password,id,year from student where email = '{email}'")
            user = cur.fetchone()
            if usertype == "student":
                session['studentyear'] = user[3]
                student_id = user[2]
                cur.execute(f"SELECT subject.name,subject.image_name,subject.id,subject.description FROM student_subject JOIN subject ON student_subject.subject_id = subject.id WHERE student_subject.student_id = '{student_id}'")
                session['subjects'] = cur.fetchall()
                cur.close()
            else:
                teacher_id = user[2]
                print('id',teacher_id)
                cur.execute(f"SELECT name,image_name,id,description FROM subject where teacher_id = '{teacher_id}'")
                session['subjects'] = cur.fetchall()
                cur.close()

            if user and password == user[1]:
                return redirect(url_for('home'))
            else:
                return render_template("login.html", error='Invalid Username or Password')
        return render_template("login.html")
    
@app.route('/register', methods =['GET','POST'])
def register():
    try:
        if request.method == 'POST':
            print(request.form)
            usertype = request.form['usertype']
            firstname = request.form['firstname']
            lastname = request.form['lastname']
            email = request.form['email']
            year = request.form['year']
            if request.form['password'] == request.form['password_two']:
                password = request.form['password']
            cur = mysql.connection.cursor()
            if usertype == 'teacher':
                cur.execute(f"INSERT INTO `teacher` (`firstname`, `lastname`, `email`, `password`) VALUES ('{firstname}','{lastname}','{email}','{password}')")
            elif usertype == 'student':
                cur.execute(f"INSERT INTO `student` (`firstname`, `lastname`, `email`, `year`, `password`) VALUES ('{firstname}','{lastname}','{email}','{year}','{password}')")
            mysql.connection.commit()
            cur.close()
            return render_template("login.html")
        return render_template("register.html")
    except:
        return "<h3><b>Oops Something went wrong please login again!</b></h3>"
    
@app.route('/attendance-download', methods =['GET','POST'])
def AttendanceDownload():
    # try:
        if request.method == 'POST':
            SubjectName = session['subname']
            Date = request.form['attendancedate']
            formatted_date = datetime.strptime(Date, '%Y-%m-%d').strftime('%B %d, %Y')
            print(SubjectName,formatted_date)
            cur = mysql.connection.cursor() 
            cur.execute(f"SELECT * FROM attendance WHERE subject_name='{SubjectName}' and date='{formatted_date}';")
            attendenceData = cur.fetchall()
            
            print(attendenceData)

            csv_file_name = f"{SubjectName}-{formatted_date}-Attendance.csv"
            with open(csv_file_name, 'w', newline='') as csv_file:
            # Create a CSV writer object
                csv_writer = csv.writer(csv_file)
            
            # Write header row
                csv_writer.writerow([i[0] for i in cur.description])
            
            # Write data rows
                for row in attendenceData:
                    csv_writer.writerow(row)

            with open(csv_file_name, 'rb') as csv_file:
                # Create a StringIO object and initialize it with the CSV file content
                csv_data = io.BytesIO(csv_file.read())

            
            cur.close()
            return send_file(csv_data,
                         mimetype='text/csv',
                         download_name=f"{SubjectName}-{formatted_date}-Attendance.csv",
                         as_attachment=True)
        return 'ok'
    # except:
    #     return "<h3><b>Oops Something went wrong please login again!</b></h3>"
    
@app.route('/logout')
def logout():
    try:
        session.clear()
        return redirect(url_for('login'))
    except:
        return "<h3><b>Oops Something went wrong please login again!</b></h3>"
    
@app.route('/attendence')
def attendence():
    try:
        subname=session['subname']
        return Response(gen_frames(subname), mimetype='multipart/x-mixed-replace; boundary=frame')
    except:
        return "<h3><b>Oops Something went wrong please login again!</b></h3>"
    
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=2000)
    
