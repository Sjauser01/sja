from flask import Flask, render_template, request, redirect, url_for
import re, time
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import smtplib, imaplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email_validator import validate_email, EmailNotValidError

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

#app initialization
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///inquiry.db"
app.config['SQLALCHEMY TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#define table struicture
class inquiry(db.Model):
    sno = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100),nullable=False)
    email = db.Column(db.String(100),nullable=False)
    phone = db.Column(db.String(100),nullable=False)
    company = db.Column(db.String(100),nullable=False)
    industrytype = db.Column(db.String(100),nullable=False)
    title = db.Column(db.String(100),nullable=False)
    req = db.Column(db.String(500),nullable=False)

    def __init__(self,name,email,phone,company,industrytype,title,req):
        self.name = name
        self.email = email
        self.phone = phone
        self.company = company
        self.industrytype = industrytype
        self.title = title
        self.req = req
    
    def __repr__(self) -> str:
        return f"{self.title} - {self.req}"


#create table in the database
with app.app_context():
    db.create_all()


@app.route('/',methods=['GET','POST'])
def html():
    return render_template('main.html')

@app.route('/send_email', methods=['POST'])
def send_email():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        company = request.form['company']
        industrytype = request.form['industrytype']
        title = request.form['title']
        req = request.form['req']
        
        # Validate email
        try:
            valid = validate_email(email,check_deliverability=False)
            email = valid.email  # Normalized email address
        except EmailNotValidError as e:
            return f"Invalid email address: {str(e)}"
        
        # Save data to database and send emails
        En = inquiry(name=name, email=email, title=title, req=req, phone=phone, company=company, industrytype=industrytype)
        db.session.add(En)
        db.session.commit()

        with open('output.txt', 'a') as file:
            file.write("\n{},{},{},{},{},{},{}".format(name, email, phone, company, industrytype, title, req))

        # Email configuration
        sender_email = "info@sanjoseautomation.com"
        admin_emails = ["umeshbobade2002@gmail.com","amarpalapure@live.com","jadhav.prashant123@outlook.com"]
        receiver_email = email
        password = "Sja@unoligent24"

        # Admin email
        admin_msg = MIMEMultipart()
        admin_msg['From'] = sender_email
        admin_msg['To'] = ','.join(admin_emails)
        admin_msg['Subject'] = f"Inquiry from {name} for {title}"
        admin_body = f"Name: {name}\nEmail: {email}\nPhone: {phone}\nCompany: {company}\nIndustry: {industrytype}\nTitle: {title}\nRequirements:\n\n{req}"
        admin_msg.attach(MIMEText(admin_body, 'plain'))

        # User email
        user_msg = MIMEMultipart()
        user_msg['From'] = sender_email
        user_msg['To'] = receiver_email
        user_msg['Subject'] = f"Inquiry from {name} for {title}"
        user_body = f"""
        Dear {name},

        Thank you for reaching out to us. We have received your inquiry and will get back to you as soon as possible.

        Best regards,
        San Jose Automation
        """
        user_msg.attach(MIMEText(user_body, 'plain'))

        try:
            # Connect to the SMTP server
            with smtplib.SMTP_SSL('smtp.hostinger.com', 465) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, admin_emails, admin_msg.as_string())
                server.sendmail(sender_email, receiver_email, user_msg.as_string())
                print("Email sent successfully!")
            
            with imaplib.IMAP4_SSL('imap.hostinger.com', 993) as mail:
                mail.login(sender_email, password)
                mail.select('"INBOX.Sent"')  # For Gmail, change according to your provider
                mail.append('"INBOX.Sent"', '\\Seen', imaplib.Time2Internaldate(time.time()), admin_msg.as_bytes())
                mail.append('"INBOX.Sent"', '\\Seen', imaplib.Time2Internaldate(time.time()), user_msg.as_bytes())
                print("Sent email saved to Sent folder.")
        except Exception as e:
            return str(e)

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
