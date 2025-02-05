from flask import Flask, render_template, request, redirect, url_for, flash
import time, requests, re, smtplib, imaplib
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

#app initialization
app = Flask(__name__)
app.secret_key = "gfcvhbdhfluesrhbb7652153r4gvg"

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


def validate_name(name):
    """Check if name contains only alphabets."""
    return bool(re.fullmatch(r"^[A-Za-z\s]{1,50}$", name))

def validate_text_field(text):
    """Validate fields like company name, title, and request.
    - Allows alphabets, numbers, full stops (.)
    - No URLs (http, www, .com, etc.)
    """
    if re.search(r"(http|www|\.com|\.net|\.org)", text, re.IGNORECASE):
        return False
    return bool(re.fullmatch(r"^[A-Za-z0-9.\s]{1,100}$", text))

def validate_email(email):
    """Check if the email is valid using an external API."""
    try:
        response = requests.get(f"https://emailvalidation.abstractapi.com/v1/?api_key=935198eca9e6496299769a5e2489357f&email={email}")
        data = response.json()
        return data.get("is_valid_format", {}).get("value", False)
    except:
        return False

@app.route('/', methods=['GET','POST'])
def home():
    form_data ={}
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        company = request.form['company']
        industrytype = request.form['industrytype']
        title = request.form['title']
        req = request.form['req']

        form_data = {
            "name": request.form.get('name'),
            "email": request.form.get('email'),
            "phone": request.form.get('phone'),
            "company" : request.form.get('company'),
            "industrytype" : request.form.get('industrytype'),
            "title" : request.form.get('title'),
            "req": request.form.get('req'),
            }
        
        # Field-specific validation
        if not validate_name(form_data["name"]):
            flash("❌ Name must contain only alphabets!", "error")
            return render_template("main.html", form_data=form_data)

        if not validate_email(form_data["email"]):
            flash("❌ Email is not valid!", "error")
            return render_template("main.html", form_data=form_data)

        if not validate_text_field(form_data["company"]):
            flash("❌ Invalid Company Name!", "error")
            return render_template("main.html", form_data=form_data)

        if not validate_text_field(form_data["title"]):
            flash("❌ Invalid Title!", "error")
            return render_template("main.html", form_data=form_data)

        if not validate_text_field(form_data["req"]):
            flash("❌ Invalid Inquiry", "error")
            return render_template("main.html", form_data=form_data)
        
        # Save data to database and send emails
        En = inquiry(name=name, email=email, title=title, req=req, phone=phone, company=company, industrytype=industrytype)
        db.session.add(En)
        db.session.commit()

        with open('output.txt', 'a') as file:
            file.write("\n{},{},{},{},{},{},{}".format(name, email, phone, company, industrytype, title, req))

        # Email configuration
        sender_email = "info@sanjoseautomation.com"
        #,"amarpalapure@live.com","jadhav.prashant123@outlook.com"
        admin_emails = ["umeshbobade2002@gmail.com"]
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
    return render_template("main.html", form_data=form_data)

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
