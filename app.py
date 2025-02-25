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

# Google reCAPTCHA Secret Key (Replace with your actual key)
RECAPTCHA_SECRET_KEY = "6LevP-EqAAAAAChrqP77fMERqHb6SpHZekN95X0L"

@app.route("/", methods=["GET", "POST"])
def home():
    form_data = {}

    if request.method == 'POST':
        # Get CAPTCHA response
        recaptcha_response = request.form.get("g-recaptcha-response")

        # Verify CAPTCHA with Google's API
        recaptcha_verify_url = "https://www.google.com/recaptcha/api/siteverify"
        recaptcha_result = requests.post(recaptcha_verify_url, data={
            "secret": RECAPTCHA_SECRET_KEY,
            "response": recaptcha_response
        }).json()

        # If CAPTCHA fails, reload the form with an error
        if not recaptcha_result.get("success"):
            flash("❌ CAPTCHA validation failed. Please try again.", "error")
            return render_template("main.html", form_data=form_data)

        # Get form fields
        form_data = {
            "name": request.form.get('name'),
            "email": request.form.get('email'),
            "phone": request.form.get('phone'),
            "company": request.form.get('company'),
            "industrytype": request.form.get('industrytype'),
            "title": request.form.get('title'),
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

        # Save data to database
        En = inquiry(
            name=form_data["name"],
            email=form_data["email"],
            phone=form_data["phone"],
            company=form_data["company"],
            industrytype=form_data["industrytype"],
            title=form_data["title"],
            req=form_data["req"]
        )
        db.session.add(En)
        db.session.commit()

        # Log form submission in a text file
        with open('output.txt', 'a') as file:
            file.write("\n{},{},{},{},{},{},{}".format(
                form_data["name"], form_data["email"], form_data["phone"],
                form_data["company"], form_data["industrytype"],
                form_data["title"], form_data["req"]
            ))

        # Email configuration (Use environment variables for security)
        sender_email = "info@sanjoseautomation.com"
        sender_password = "Sja@unoligent24"  # Avoid hardcoding passwords (Use environment variables)
        admin_emails = ["umeshbobade2002@gmail.com"]
        receiver_email = form_data["email"]

        # Create email for admin
        admin_msg = MIMEMultipart()
        admin_msg['From'] = sender_email
        admin_msg['To'] = ','.join(admin_emails)
        admin_msg['Subject'] = f"Inquiry from {form_data['name']} for {form_data['title']}"
        admin_body = f"Name: {form_data['name']}\nEmail: {form_data['email']}\nPhone: {form_data['phone']}\nCompany: {form_data['company']}\nIndustry: {form_data['industrytype']}\nTitle: {form_data['title']}\nRequirements:\n\n{form_data['req']}"
        admin_msg.attach(MIMEText(admin_body, 'plain'))

        # Create email for user
        user_msg = MIMEMultipart()
        user_msg['From'] = sender_email
        user_msg['To'] = receiver_email
        user_msg['Subject'] = f"Inquiry from {form_data['name']} for {form_data['title']}"
        user_body = f"""
        Dear {form_data['name']},

        Thank you for reaching out to us. We have received your inquiry and will get back to you as soon as possible.

        Best regards,
        San Jose Automation
        """
        user_msg.attach(MIMEText(user_body, 'plain'))

        # Send emails
        try:
            with smtplib.SMTP_SSL('smtp.hostinger.com', 465) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, admin_emails, admin_msg.as_string())
                server.sendmail(sender_email, receiver_email, user_msg.as_string())

            # Save sent emails to Sent folder
            with imaplib.IMAP4_SSL('imap.hostinger.com', 993) as mail:
                mail.login(sender_email, sender_password)
                mail.select('"INBOX.Sent"')
                mail.append('"INBOX.Sent"', '\\Seen', imaplib.Time2Internaldate(time.time()), admin_msg.as_bytes())
                mail.append('"INBOX.Sent"', '\\Seen', imaplib.Time2Internaldate(time.time()), user_msg.as_bytes())

        except Exception as e:
            flash(f"❌ Email sending failed: {str(e)}", "error")
            return render_template("main.html", form_data=form_data)

        flash("✅ Inquiry submitted successfully!", "success")
        return redirect('/')

    return render_template("main.html", form_data=form_data)

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
