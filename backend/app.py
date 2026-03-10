from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import random
import smtplib
from email.message import EmailMessage
import os
import json
import traceback
from datetime import datetime
import uuid



app = Flask(__name__)
CORS(app)

bcrypt = Bcrypt(app)


DATABASE_URL = "postgresql://postgres.pxnangovncbvfbjywnbv:omSriganesha06@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)



# 🔥 CHANGE THIS (KEEP SECRET)
ADMIN_SECRET = "supersecret123"

EMAIL_USER = "avulakarthik189@gmail.com"
EMAIL_PASS = "eiigbdbsyfawqzbr"
# -----------------------------
# DATABASE CONNECTION
# -----------------------------



# -----------------------------
# CREATE TABLES
# -----------------------------
try:
    with engine.connect() as conn:
        print("✅ Connected to Supabase successfully!")
except Exception as e:
    print("❌ Connection failed:", e)

@app.route("/")
def home():
    return "Backend is running ✅"

# -----------------------------
# EMAIL FUNCTION
# -----------------------------
def send_email(receiver, otp):

    sender_email = "avulakarthik189@gmail.com"
    sender_password = "eiigbdbsyfawqzbr"

    msg = EmailMessage()
    msg["Subject"] = "Password Reset OTP"
    msg["From"] = sender_email
    msg["To"] = receiver

    msg.set_content(f"""
Hello,

Your OTP for password reset is:

{otp}

If you did not request this, ignore this email.
""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.send_message(msg)


# temporary OTP store
otp_store = {}

def send_booking_email(data):

    receiver = data.get("customer_email")

    # 🔥 SAFETY CHECK (VERY IMPORTANT)
    if not receiver:
        print("No customer email found — skipping email.")
        return

    msg = EmailMessage()
    msg["Subject"] = "🚗 Your Car Booking is Confirmed!"
    msg["From"] = EMAIL_USER
    msg["To"] = receiver

    html = f"""
    <html>
    <body style="font-family:Arial;background:#f2f3f5;padding:20px;">

        <div style="
            max-width:600px;
            background:white;
            padding:30px;
            border-radius:12px;
            box-shadow:0px 3px 10px rgba(0,0,0,0.1);
        ">

            <h2 style="color:#28a745;">✅ Booking Confirmed</h2>

            <p>Hello <b>{data.get("customer_name")}</b>,</p>

            <p>
            Your car booking has been <b>successfully confirmed</b>.  
            Below are your booking details:
            </p>

            <hr>

            <h3 style="color:#333;">🚘 Booking Details</h3>

            <p><b>Car:</b> {data.get("car_name")}</p>
            <p><b>Rental Type:</b> {data.get("rental_type")}</p>
            <p><b>Pickup Location:</b> {data.get("pickup_location")}</p>
            <p><b>Drop Location:</b> {data.get("drop_location")}</p>

            <p><b>Pickup Time:</b> {data.get("pickup_datetime")}</p>
            <p><b>Drop Time:</b> {data.get("drop_datetime")}</p>

            <h2 style="color:#007bff;">
                💰 Total Fare: ₹{data.get("total_cost")}
            </h2>
    """

    # ⭐ ONLY SHOW DRIVER DETAILS IF "WITH DRIVER"
    if data.get("rental_type") == "With Driver":
        html += f"""
            <hr>

            <h3 style="color:#333;">👨‍✈️ Driver Details</h3>

            <p><b>Name:</b> {data.get("driver_name")}</p>
            <p><b>Mobile:</b> {data.get("driver_mobile")}</p>

            <p style="color:#666;font-size:13px;">
            Please contact the driver only for trip coordination.
            </p>
        """

    html += """
            <hr>

            <p style="color:gray;">
            Thank you for choosing our service 🚗  
            Wishing you a safe and comfortable journey!
            </p>

        </div>

    </body>
    </html>
    """

    msg.add_alternative(html, subtype='html')

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)

        print("✅ Booking email sent successfully!")

    except Exception as e:
        # 🔥 NEVER CRASH BOOKING BECAUSE OF EMAIL
        print("❌ Email failed but booking is saved:", e)


# -----------------------------
# SIGNUP (USER ONLY)
# -----------------------------
from datetime import datetime
import uuid

@app.route("/signup", methods=["POST"])
def signup():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"success": False, "message": "Invalid request ❌"}), 400

    first = data.get("first_name")
    last = data.get("last_name")
    email = data.get("email")
    password = data.get("password")

    if not all([first, last, email, password]):
        return jsonify({"success": False, "message": "All fields required ❌"}), 400

    email = email.lower().strip()

    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

    created_at = datetime.now().strftime("%d %b %Y")
    account_id = "CRP-" + str(uuid.uuid4())[:8].upper()

    try:
        with engine.begin() as conn:

            conn.execute(text("""
                INSERT INTO signup
                (first_name, last_name, email, account_id, created_at)
                VALUES (:first, :last, :email, :account_id, :created_at)
            """), {
                "first": first,
                "last": last,
                "email": email,
                "account_id": account_id,
                "created_at": created_at
            })

            conn.execute(text("""
                INSERT INTO login (email, password)
                VALUES (:email, :password)
            """), {
                "email": email,
                "password": hashed_pw
            })

        return jsonify({
            "success": True,
            "message": "Signup successful ✅ Please login"
        })

    except Exception as e:
        print("Signup Error:", e)
        return jsonify({
            "success": False,
            "message": "Email already exists ❌"
        })

# -----------------------------
# 🔥 SINGLE LOGIN (ADMIN + USER)
# -----------------------------
@app.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"success": False, "message": "Invalid request ❌"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"success": False, "message": "Email & password required ❌"}), 400

    email = email.lower().strip()

    with engine.begin() as conn:

        # Check admin
        result = conn.execute(
            text("SELECT * FROM admintable WHERE email=:email"),
            {"email": email}
        )
        admin = result.mappings().first()

        if admin:
            if not bcrypt.check_password_hash(admin["password"], password):
                return jsonify({"success": False, "message": "Incorrect password ❌"}), 401

            return jsonify({
                "success": True,
                "message": "Admin login successful ✅",
                "role": "admin",
                "user": {
                    "name": admin["name"],
                    "email": admin["email"]
                }
            })

        # Check user
        result = conn.execute(
            text("SELECT * FROM login WHERE email=:email"),
            {"email": email}
        )
        user = result.mappings().first()

        if not user:
            return jsonify({"success": False, "message": "User not found ❌"}), 404

        if not bcrypt.check_password_hash(user["password"], password):
            return jsonify({"success": False, "message": "Incorrect password ❌"}), 401

        return jsonify({
            "success": True,
            "message": "Login successful ✅",
            "role": "user",
            "user": {"email": email}
        })


# -----------------------------
# FORGOT PASSWORD
# -----------------------------
@app.route("/forgot-password", methods=["POST"])
def forgot_password():

    data = request.get_json()
    email = data.get("email")

    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT * FROM signup WHERE email=:email"),
            {"email": email}
        )
        user = result.fetchone()

    if not user:
        return jsonify({
            "success": False,
            "message": "Email not registered ❌"
        })

    otp = str(random.randint(100000, 999999))
    otp_store[email] = otp

    try:
        send_email(email, otp)
    except:
        print("Email failed — printing OTP instead:", otp)

    return jsonify({
        "success": True,
        "message": "OTP sent to email ✅"
    })
# -----------------------------
# RESET PASSWORD
# -----------------------------
@app.route("/reset-password", methods=["POST"])
def reset_password():

    data = request.get_json()

    email = data.get("email")
    otp = data.get("otp")
    new_password = data.get("new_password")

    if otp_store.get(email) != otp:
        return jsonify({
            "success": False,
            "message": "Invalid OTP ❌"
        })

    hashed_pw = bcrypt.generate_password_hash(new_password).decode('utf-8')

    with engine.begin() as conn:

        conn.execute(text("""
            UPDATE login
            SET password=:password
            WHERE email=:email
        """), {
            "password": hashed_pw,
            "email": email
        })

        conn.execute(text("""
            INSERT INTO resetpassword(email, otp, new_password)
            VALUES(:email, :otp, :new_password)
        """), {
            "email": email,
            "otp": otp,
            "new_password": hashed_pw
        })

    otp_store.pop(email, None)

    return jsonify({
        "success": True,
        "message": "Password reset successful ✅ Please login"
    })
# -----------------------------
# 🔥 CREATE ADMIN (SECURED)
# -----------------------------
@app.route("/create-admin", methods=["POST"])
def create_admin():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"success": False}), 400

    if data.get("secret") != ADMIN_SECRET:
        return jsonify({
            "success": False,
            "message": "Unauthorized ❌"
        }), 403

    name = data.get("name")
    email = data.get("email").lower().strip()
    password = data.get("password")

    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

    with engine.begin() as conn:

        # Check if already exists
        result = conn.execute(
            text("SELECT id FROM admintable WHERE email=:email"),
            {"email": email}
        )

        if result.fetchone():
            return jsonify({
                "success": False,
                "message": "Admin already exists ❌"
            })

        conn.execute(text("""
            INSERT INTO admintable(name, email, password)
            VALUES(:name, :email, :password)
        """), {
            "name": name,
            "email": email,
            "password": hashed_pw
        })

    return jsonify({
        "success": True,
        "message": "Admin created successfully ✅"
    })


@app.route("/add-car", methods=["POST"])
def add_car():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "Invalid request data ❌"
        }), 400

    owner_email = data.get("owner_email", "").lower().strip()
    listing_type = data.get("listing_type", "").strip().title()

    company = data.get("company")
    model = data.get("model")
    reg_number = data.get("reg_number", "").upper().strip()

    if not owner_email or not listing_type or not company or not model or not reg_number:
        return jsonify({
            "success": False,
            "message": "Missing required fields ❌"
        }), 400

    try:
        with engine.begin() as conn:

            # 🔥 Prevent duplicate registration
            result = conn.execute(
                text("SELECT id FROM cars WHERE reg_number=:reg"),
                {"reg": reg_number}
            )

            if result.fetchone():
                return jsonify({
                    "success": False,
                    "message": "Car already registered ❌"
                }), 400

            # 🔥 Insert car and return ID
            result = conn.execute(text("""
                INSERT INTO cars(
                    owner_email,
                    listing_type,
                    company,
                    model,
                    reg_number,
                    year,
                    fuel,
                    transmission,
                    seats,
                    km,
                    driver_name,
                    driver_mobile,
                    location,
                    price_month,
                    deposit,
                    notes,
                    images
                )
                VALUES(
                    :owner_email,
                    :listing_type,
                    :company,
                    :model,
                    :reg_number,
                    :year,
                    :fuel,
                    :transmission,
                    :seats,
                    :km,
                    :driver_name,
                    :driver_mobile,
                    :location,
                    :price_month,
                    :deposit,
                    :notes,
                    :images
                )
                RETURNING id
            """), {
                "owner_email": owner_email,
                "listing_type": listing_type,
                "company": company,
                "model": model,
                "reg_number": reg_number,
                "year": data.get("year"),
                "fuel": data.get("fuel"),
                "transmission": data.get("transmission"),
                "seats": data.get("seats"),
                "km": data.get("km"),
                "driver_name": data.get("driver_name"),
                "driver_mobile": data.get("driver_mobile"),
                "location": data.get("location"),
                "price_month": data.get("price_month") or 0,
                "deposit": data.get("deposit") or 0,
                "notes": data.get("notes"),
                "images": json.dumps(data.get("images", []))
            })

            inserted_id = result.fetchone()[0]

        return jsonify({
            "success": True,
            "message": "Car submitted for approval ✅",
            "car_id": inserted_id
        })

    except Exception as e:
        print("ADD CAR ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Database error ❌"
        }), 500


@app.route("/approved-cars/<email>/<listing_type>")
def approved_cars(email, listing_type):

    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT *
            FROM cars
            WHERE status='Approved'
            AND LOWER(owner_email) != LOWER(:email)
            AND listing_type=:listing_type
        """), {
            "email": email,
            "listing_type": listing_type
        })

        cars = [dict(row) for row in result.mappings().all()]

    return jsonify({
        "success": True,
        "cars": cars
    })

@app.route("/admin/pending-cars")
def pending_cars():

    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT *
            FROM cars
            WHERE status='Pending'
        """))

        cars = [dict(row) for row in result.mappings().all()]

    return jsonify({
        "success": True,
        "cars": cars
    })

@app.route("/admin/update-car-status", methods=["POST"])
def update_status():

    data = request.get_json()

    car_id = data.get("car_id")
    status = data.get("status").capitalize()

    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE cars
            SET status=:status
            WHERE id=:car_id
        """), {
            "status": status,
            "car_id": car_id
        })

    return jsonify({"success": True})

@app.route("/my-car-status/<email>")
def my_car_status(email):

    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT *
            FROM cars
            WHERE owner_email=:email
            ORDER BY created_at DESC
        """), {
            "email": email
        })

        cars = [dict(row) for row in result.mappings().all()]

    return jsonify({
        "success": True,
        "cars": cars
    })


@app.route("/book-car", methods=["POST"])
def book_car():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Invalid request ❌"
        }), 400

    try:
        with engine.begin() as conn:

            # 🔥 Auto-update booking statuses
            conn.execute(text("""
                UPDATE bookings
                SET booking_status='Ongoing'
                WHERE pickup_datetime <= CURRENT_TIMESTAMP
                AND drop_datetime > CURRENT_TIMESTAMP
                AND booking_status='Confirmed'
            """))

            conn.execute(text("""
                UPDATE bookings
                SET booking_status='Completed'
                WHERE drop_datetime <= CURRENT_TIMESTAMP
                AND booking_status IN ('Confirmed','Ongoing')
            """))

            customer_email = data.get("customer_email")
            if not customer_email:
                return jsonify({
                    "success": False,
                    "message": "Customer email missing ❌"
                }), 400

            customer_email = customer_email.lower().strip()
            car_id = data.get("car_id")
            rental_type = data.get("rental_type")

            if not car_id:
                return jsonify({
                    "success": False,
                    "message": "Missing car ID ❌"
                }), 400

            if rental_type not in ["Rental Only", "With Driver"]:
                return jsonify({
                    "success": False,
                    "message": "Invalid rental type ❌"
                }), 400

            # 🔥 Check car exists
            result = conn.execute(text("""
                SELECT owner_email, status
                FROM cars
                WHERE id=:car_id
            """), {"car_id": car_id})

            car = result.mappings().first()

            if not car:
                return jsonify({
                    "success": False,
                    "message": "Car not found ❌"
                }), 404

            if car["status"] != "Approved":
                return jsonify({
                    "success": False,
                    "message": "Car not available ❌"
                }), 400

            if car["owner_email"].lower() == customer_email:
                return jsonify({
                    "success": False,
                    "message": "You cannot book your own car ❌"
                }), 400

            pickup = data.get("pickup_datetime")
            drop = data.get("drop_datetime")

            if not pickup or not drop:
                return jsonify({
                    "success": False,
                    "message": "Pickup & Drop required ❌"
                }), 400

            # 🔥 Conflict check
            conflict = conn.execute(text("""
                SELECT 1 FROM bookings
                WHERE car_id=:car_id
                AND booking_status IN ('Confirmed','Ongoing')
                AND pickup_datetime < :drop
                AND drop_datetime > :pickup
            """), {
                "car_id": car_id,
                "pickup": pickup,
                "drop": drop
            }).fetchone()

            if conflict:
                return jsonify({
                    "success": False,
                    "message": "Car already booked for selected time ❌"
                }), 400

            # 🔥 Insert booking
            result = conn.execute(text("""
                INSERT INTO bookings(
                    car_id,
                    car_name,
                    owner_email,
                    customer_name,
                    customer_email,
                    customer_mobile,
                    nominee,
                    rental_type,
                    pickup_location,
                    drop_location,
                    pickup_datetime,
                    drop_datetime,
                    driver_name,
                    driver_mobile,
                    passenger_count,
                    total_cost,
                    booking_status
                )
                VALUES(
                    :car_id,
                    :car_name,
                    :owner_email,
                    :customer_name,
                    :customer_email,
                    :customer_mobile,
                    :nominee,
                    :rental_type,
                    :pickup_location,
                    :drop_location,
                    :pickup_datetime,
                    :drop_datetime,
                    :driver_name,
                    :driver_mobile,
                    :passenger_count,
                    :total_cost,
                    'Confirmed'
                )
                RETURNING id
            """), {
                "car_id": car_id,
                "car_name": data.get("car_name"),
                "owner_email": car["owner_email"],
                "customer_name": data.get("customer_name"),
                "customer_email": customer_email,
                "customer_mobile": data.get("customer_mobile"),
                "nominee": data.get("nominee"),
                "rental_type": rental_type,
                "pickup_location": data.get("pickup_location"),
                "drop_location": data.get("drop_location"),
                "pickup_datetime": pickup,
                "drop_datetime": drop,
                "driver_name": data.get("driver_name"),
                "driver_mobile": data.get("driver_mobile"),
                "passenger_count": int(data.get("passenger_count") or 0),
                "total_cost": int(data.get("total_cost") or 0)
            })

            booking_id = result.fetchone()[0]

        # 🔥 Send email after commit
        try:
            send_booking_email(data)
        except:
            pass

        return jsonify({
            "success": True,
            "message": "Booking confirmed ✅",
            "booking_id": booking_id
        })

    except Exception as e:
        print("BOOKING ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Booking failed ❌"
        }), 500


@app.route("/admin/block-car", methods=["POST"])
def block_car():

    data = request.get_json()
    car_id = data.get("car_id")

    if not car_id:
        return jsonify({
            "success": False,
            "message": "Car ID required ❌"
        }), 400

    try:
        with engine.begin() as conn:

            # 🔥 Check if car has active booking
            result = conn.execute(text("""
                SELECT 1 FROM bookings
                WHERE car_id=:car_id
                AND booking_status='Confirmed'
            """), {
                "car_id": car_id
            })

            if result.fetchone():
                return jsonify({
                    "success": False,
                    "message": "Car has active booking ❌ Cannot block"
                }), 400

            # 🔥 Block car
            conn.execute(text("""
                UPDATE cars
                SET status='Blocked'
                WHERE id=:car_id
            """), {
                "car_id": car_id
            })

        return jsonify({
            "success": True,
            "message": "Car blocked successfully 🚫"
        })

    except Exception as e:
        print("BLOCK ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Database error ❌"
        }), 500

@app.route("/sell-car", methods=["POST"])
def sell_car():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"success": False}), 400

    owner_email = data.get("owner_email", "").lower().strip()
    reg_number = data.get("reg_number", "").upper().strip()

    if not owner_email or not reg_number:
        return jsonify({
            "success": False,
            "message": "Missing required fields ❌"
        }), 400

    try:
        with engine.begin() as conn:

            # 🔥 Prevent duplicate registration
            result = conn.execute(text("""
                SELECT id FROM selling
                WHERE reg_number=:reg
            """), {
                "reg": reg_number
            })

            if result.fetchone():
                return jsonify({
                    "success": False,
                    "message": "Car already listed for sale ❌"
                }), 400

            # 🔥 Insert selling car
            conn.execute(text("""
                INSERT INTO selling(
                    owner_email,
                    company,
                    model,
                    reg_number,
                    year,
                    fuel,
                    transmission,
                    km,
                    owner_type,
                    location,
                    selling_price,
                    description,
                    images
                )
                VALUES(
                    :owner_email,
                    :company,
                    :model,
                    :reg_number,
                    :year,
                    :fuel,
                    :transmission,
                    :km,
                    :owner_type,
                    :location,
                    :selling_price,
                    :description,
                    :images
                )
            """), {
                "owner_email": owner_email,
                "company": data.get("company"),
                "model": data.get("model"),
                "reg_number": reg_number,
                "year": data.get("year"),
                "fuel": data.get("fuel"),
                "transmission": data.get("transmission"),
                "km": data.get("km"),
                "owner_type": data.get("owner_type"),
                "location": data.get("location"),
                "selling_price": data.get("selling_price"),
                "description": data.get("description"),
                "images": json.dumps(data.get("images", []))
            })

        return jsonify({
            "success": True,
            "message": "Car submitted for approval ✅"
        })

    except Exception as e:
        print("SELL CAR ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Database error ❌"
        }), 500


@app.route("/admin/pending-selling")
def pending_selling():

    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT *
            FROM selling
            WHERE status='Pending'
        """))

        cars = [dict(row) for row in result.mappings().all()]

    return jsonify({
        "success": True,
        "cars": cars
    })

@app.route("/admin/update-selling-status", methods=["POST"])
def update_selling_status():

    data = request.get_json()

    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE selling
            SET status=:status
            WHERE id=:car_id
        """), {
            "status": data.get("status"),
            "car_id": data.get("car_id")
        })

    return jsonify({"success": True})

@app.route("/admin/approve-sell/<int:car_id>", methods=["POST"])
def approve_sell(car_id):

    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE selling
            SET status='Approved'
            WHERE id=:car_id
        """), {
            "car_id": car_id
        })

    return jsonify({
        "success": True,
        "message": "Car Approved ✅"
    })

@app.route("/admin/reject-sell/<int:car_id>", methods=["POST"])
def reject_sell(car_id):

    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE selling
            SET status='Rejected'
            WHERE id=:car_id
        """), {
            "car_id": car_id
        })

    return jsonify({
        "success": True,
        "message": "Car Rejected ❌"
    })


@app.route("/approved-selling/<email>")
def approved_selling(email):

    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT *
            FROM selling
            WHERE status='Approved'
            AND LOWER(owner_email) != LOWER(:email)
        """), {
            "email": email
        })

        cars = [dict(row) for row in result.mappings().all()]

    return jsonify({
        "success": True,
        "cars": cars
    })

@app.route("/my-selling-status/<email>")
def my_selling_status(email):

    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT *
            FROM selling
            WHERE LOWER(owner_email)=LOWER(:email)
            ORDER BY created_at DESC
        """), {
            "email": email
        })

        cars = [dict(row) for row in result.mappings().all()]

    return jsonify({
        "success": True,
        "cars": cars
    })
# ==============================
# GET PROFILE IMAGE
# ==============================
@app.route("/get-profile-image/<email>")
def get_profile_img(email):

    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT profile_img
            FROM signup
            WHERE email=:email
        """), {
            "email": email.lower().strip()
        })

        row = result.fetchone()

    if row and row[0]:
        return jsonify({
            "success": True,
            "image": row[0]
        })

    return jsonify({
        "success": False
    })
# ==============================
# UPLOAD PROFILE IMAGE
# ==============================

@app.route("/upload-profile-image", methods=["POST"])
def upload_profile_img():

    data = request.json
    email = data.get("email")
    image = data.get("image")

    if not email or not image:
        return jsonify({
            "success": False,
            "message": "Missing data ❌"
        }), 400

    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE signup
            SET profile_img=:image
            WHERE email=:email
        """), {
            "image": image,
            "email": email.lower().strip()
        })

    return jsonify({"success": True})

# ==============================
# GET FULL PROFILE
# ==============================
@app.route("/get-profile/<email>", methods=["GET"])
def get_profile(email):

    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                SELECT
                    first_name,
                    last_name,
                    email,
                    phone,
                    account_id,
                    created_at,
                    profile_img
                FROM signup
                WHERE email=:email
            """), {
                "email": email.lower().strip()
            })

            row = result.mappings().first()

        if not row:
            return jsonify({
                "success": False,
                "message": "User not found ❌"
            })

        return jsonify({
            "success": True,
            "profile": dict(row)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })

@app.route("/create-buy-request", methods=["POST"])
def create_buy_request():

    data = request.json

    car_id = data.get("car_id")
    buyer_email = data.get("buyer_email")
    offered_price = data.get("offered_price")

    if not car_id or not buyer_email:
        return jsonify({"success": False, "message": "Missing data ❌"}), 400

    with engine.begin() as conn:

        # Get seller email
        result = conn.execute(text("""
            SELECT owner_email, selling_price
            FROM selling
            WHERE id=:car_id AND status='Approved'
        """), {"car_id": car_id})

        car = result.mappings().first()

        if not car:
            return jsonify({"success": False, "message": "Car not available ❌"}), 404

        conn.execute(text("""
            INSERT INTO buy_requests(
                car_id,
                seller_email,
                buyer_email,
                offered_price
            )
            VALUES(
                :car_id,
                :seller_email,
                :buyer_email,
                :offered_price
            )
        """), {
            "car_id": car_id,
            "seller_email": car["owner_email"],
            "buyer_email": buyer_email,
            "offered_price": offered_price or car["selling_price"]
        })

    return jsonify({
        "success": True,
        "message": "Buy request sent to seller ✅"
    })

@app.route("/my-buy-requests/<email>")
def my_buy_requests(email):

    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT *
            FROM buy_requests
            WHERE seller_email = :email
            AND status != 'Rejected'
            ORDER BY created_at DESC
        """), {"email": email})

        requests = [dict(row) for row in result.mappings().all()]

    return jsonify({
        "success": True,
        "requests": requests
    })

@app.route("/update-buy-request", methods=["POST"])
def update_buy_request():

    data = request.json
    request_id = data.get("request_id")
    status = data.get("status")

    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE buy_requests
            SET status=:status
            WHERE id=:request_id
        """), {
            "status": status,
            "request_id": request_id
        })

    return jsonify({"success": True})

# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3000, debug=True)
