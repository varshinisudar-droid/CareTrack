# =========================================================
# CARETRACK - PATIENT HEALTHCARE FOLLOW-UP SYSTEM
# app/app.py
# =========================================================

# ---------------------------------------------------------
# PATH SETUP
# ---------------------------------------------------------

import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------
# STANDARD LIBRARY
# ---------------------------------------------------------

from datetime import date


# ---------------------------------------------------------
# THIRD-PARTY LIBRARIES
# ---------------------------------------------------------

import pandas as pd
import plotly.express as px
import streamlit as st

import fitz
import pytesseract

from PIL import Image


# ---------------------------------------------------------
# CARETRACK PROJECT IMPORTS
# ---------------------------------------------------------

from database.db_connection import get_connection

from models.explainability import (
    explain_review_attention
)

from models.follow_up_logic import (
    assess_follow_up
)

from models.medical_nlp import (
    extract_medical_information
)

from models.follow_up_model import (
    load_model
)


# ---------------------------------------------------------
# TESSERACT OCR CONFIGURATION
# ---------------------------------------------------------

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="CareTrack",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main {
        padding-top: 1rem;
    }

    h1 {
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    h2 {
        font-weight: 650;
    }

    h3 {
        font-weight: 600;
    }

    [data-testid="stMetric"] {
        background: rgba(31, 41, 55, 0.65);
        border: 1px solid rgba(156, 163, 175, 0.18);
        border-radius: 14px;
        padding: 18px;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.85rem;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
    }

    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(156, 163, 175, 0.15);
    }

    .stButton > button {
        border-radius: 9px;
        font-weight: 600;
        min-height: 42px;
    }

    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
    }

    [data-testid="stExpander"] {
        border-radius: 12px;
    }

    hr {
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
    }

    .caretrack-note {
        padding: 12px 16px;
        border-radius: 10px;
        background: rgba(59, 130, 246, 0.08);
        border: 1px solid rgba(59, 130, 246, 0.18);
        font-size: 0.85rem;
        margin-top: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# DATABASE FUNCTIONS
# =========================================================

def get_patients():

    connection = get_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            patient_id,
            patient_name,
            age,
            gender,
            phone,
            created_at
        FROM patients
        ORDER BY patient_name
        """
    )

    patients = cursor.fetchall()

    cursor.close()
    connection.close()

    return patients


def get_patient(patient_id):

    connection = get_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT *
        FROM patients
        WHERE patient_id = %s
        """,
        (patient_id,)
    )

    patient = cursor.fetchone()

    cursor.close()
    connection.close()

    return patient


def get_checkins(patient_id):

    connection = get_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            checkin_id,
            patient_id,
            checkin_date,
            mood,
            pain_level,
            sleep_hours,
            medication_taken,
            symptoms
        FROM health_checkins
        WHERE patient_id = %s
        ORDER BY checkin_date DESC, checkin_id DESC
        """,
        (patient_id,)
    )

    checkins = cursor.fetchall()

    cursor.close()
    connection.close()

    return checkins


def get_records(patient_id):

    connection = get_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            record_id,
            patient_id,
            file_name,
            file_path,
            uploaded_at,
            extracted_text
        FROM medical_records
        WHERE patient_id = %s
        ORDER BY uploaded_at DESC
        """,
        (patient_id,)
    )

    records = cursor.fetchall()

    cursor.close()
    connection.close()

    return records


def get_appointments(patient_id):

    connection = get_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            appointment_id,
            patient_id,
            appointment_date,
            reason,
            status,
            created_at
        FROM appointments
        WHERE patient_id = %s
        ORDER BY appointment_date
        """,
        (patient_id,)
    )

    appointments = cursor.fetchall()

    cursor.close()
    connection.close()

    return appointments


# =========================================================
# OCR
# =========================================================

def extract_text_from_file(uploaded_file):

    file_name = uploaded_file.name.lower()

    file_bytes = uploaded_file.getvalue()

    # -----------------------------------------------------
    # IMAGE
    # -----------------------------------------------------

    if file_name.endswith(
        (".png", ".jpg", ".jpeg")
    ):

        image = Image.open(
            uploaded_file
        )

        text = pytesseract.image_to_string(
            image
        )

        return text


    # -----------------------------------------------------
    # PDF
    # -----------------------------------------------------

    if file_name.endswith(".pdf"):

        pdf = fitz.open(
            stream=file_bytes,
            filetype="pdf"
        )

        extracted_text = ""

        for page in pdf:

            page_text = page.get_text()

            if page_text.strip():

                extracted_text += (
                    page_text + "\n"
                )

            else:

                pixmap = page.get_pixmap(
                    matrix=fitz.Matrix(2, 2)
                )

                image = Image.frombytes(
                    "RGB",
                    [
                        pixmap.width,
                        pixmap.height
                    ],
                    pixmap.samples
                )

                extracted_text += (
                    pytesseract.image_to_string(
                        image
                    )
                    + "\n"
                )

        pdf.close()

        return extracted_text


    return ""


# =========================================================
# ML PREDICTION
# =========================================================

def get_ml_prediction(checkins):

    model = load_model()

    if model is None:
        return None

    if len(checkins) < 3:
        return None

    recent_checkins = checkins[:3]

    dataframe = pd.DataFrame(
        recent_checkins
    )

    features = pd.DataFrame(
        [{
            "avg_mood":
                dataframe["mood"].mean(),

            "avg_pain":
                dataframe["pain_level"].mean(),

            "avg_sleep":
                dataframe["sleep_hours"].mean(),

            "high_pain_count":
                (
                    dataframe["pain_level"] >= 5
                ).sum(),

            "low_mood_count":
                (
                    dataframe["mood"] <= 2
                ).sum(),

            "low_sleep_count":
                (
                    dataframe["sleep_hours"] < 6
                ).sum(),

            "missed_medication_count":
                (
                    dataframe["medication_taken"] == False
                ).sum()
        }]
    )

    prediction = model.predict(
        features
    )[0]

    probability = None

    if hasattr(
        model,
        "predict_proba"
    ):

        probabilities = model.predict_proba(
            features
        )[0]

        classes = list(
            model.classes_
        )

        if 1 in classes:

            index = classes.index(1)

            probability = probabilities[
                index
            ]

    return {
        "prediction": int(prediction),
        "probability": probability
    }


# =========================================================
# SAVE CHECK-IN
# =========================================================

def save_checkin(
    patient_id,
    checkin_date,
    mood,
    pain_level,
    sleep_hours,
    medication_taken,
    symptoms
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO health_checkins
        (
            patient_id,
            checkin_date,
            mood,
            pain_level,
            sleep_hours,
            medication_taken,
            symptoms
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """,
        (
            patient_id,
            checkin_date,
            mood,
            pain_level,
            sleep_hours,
            medication_taken,
            symptoms
        )
    )

    connection.commit()

    cursor.close()
    connection.close()


# =========================================================
# SAVE APPOINTMENT
# =========================================================

def save_appointment(
    patient_id,
    appointment_date,
    reason,
    status
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO appointments
        (
            patient_id,
            appointment_date,
            reason,
            status
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s
        )
        """,
        (
            patient_id,
            appointment_date,
            reason,
            status
        )
    )

    connection.commit()

    cursor.close()
    connection.close()


# =========================================================
# GET PATIENTS
# =========================================================

try:

    patients = get_patients()

except Exception as error:

    st.error(
        "Unable to connect to the CareTrack database."
    )

    st.exception(error)

    st.stop()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🩺 CareTrack")

st.sidebar.caption(
    "Patient healthcare follow-up and monitoring"
)

st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "👤 Patient Profile",
        "📋 Medical Records",
        "❤️ Daily Check-in",
        "📅 Appointments",
        "📈 Health Trends",
        "🕒 Patient Timeline",
        "🩺 Provider Dashboard"
    ]
)


# =========================================================
# NO PATIENTS
# =========================================================

if not patients:

    st.title("🩺 CareTrack")

    st.warning(
        "No patients found. Add a patient first."
    )

    st.stop()


# =========================================================
# PATIENT SELECTOR
# =========================================================

patient_names = [
    f"{patient['patient_name']} "
    f"(ID: {patient['patient_id']})"
    for patient in patients
]

selected_patient_name = st.sidebar.selectbox(
    "Select patient",
    patient_names
)

selected_index = patient_names.index(
    selected_patient_name
)

selected_patient = patients[
    selected_index
]

patient_id = selected_patient[
    "patient_id"
]


# =========================================================
# DASHBOARD
# =========================================================

if page == "🏠 Dashboard":

    st.title("🏠 CareTrack Dashboard")

    st.caption(
        "Patient healthcare follow-up and longitudinal monitoring"
    )

    st.subheader(
        f"Welcome, {selected_patient['patient_name']}"
    )

    checkins = get_checkins(
        patient_id
    )

    records = get_records(
        patient_id
    )

    appointments = get_appointments(
        patient_id
    )

    recent_checkins = checkins[:3]

    follow_up = assess_follow_up(
        recent_checkins
    )

    upcoming_appointments = [
        appointment
        for appointment in appointments
        if appointment["status"] == "Upcoming"
    ]

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Age",
        selected_patient["age"]
    )

    col2.metric(
        "Check-ins",
        len(checkins)
    )

    col3.metric(
        "Medical Records",
        len(records)
    )

    col4.metric(
        "Upcoming Appointments",
        len(upcoming_appointments)
    )

    st.divider()

    # -----------------------------------------------------
    # FOLLOW-UP
    # -----------------------------------------------------

    st.subheader(
        "Follow-up Monitoring"
    )

    if follow_up["status"] == "Review Recommended":

        st.warning(
            f"Status: {follow_up['status']}"
        )

    elif follow_up["status"] == "Monitor Closely":

        st.info(
            f"Status: {follow_up['status']}"
        )

    elif follow_up["status"] == "Insufficient Data":

        st.info(
            f"Status: {follow_up['status']}"
        )

    else:

        st.success(
            f"Status: {follow_up['status']}"
        )

    st.write(
        f"Monitoring score: "
        f"**{follow_up['score']}**"
    )

    st.write(
        follow_up["recommendation"]
    )

    if follow_up["reasons"]:

        st.write(
            "### Contributing Indicators"
        )

        for reason in follow_up["reasons"]:

            st.write(
                f"• {reason}"
            )

    # -----------------------------------------------------
    # ML
    # -----------------------------------------------------

    st.divider()

    st.subheader(
        "🤖 ML Review Attention"
    )

    st.caption(
        "Random Forest prototype using recent patient "
        "check-in patterns."
    )

    ml_result = get_ml_prediction(
        checkins
    )

    if ml_result is None:

        st.warning(
            "At least 3 check-ins are required "
            "for the ML prototype."
        )

    else:

        if ml_result["prediction"] == 1:

            st.warning(
                "Review attention detected by "
                "the ML prototype."
            )

            st.subheader(
                "🔎 Contributing Monitoring Indicators"
            )

            explanations = (
                explain_review_attention(
                    checkins
                )
            )

            for explanation in explanations:

                st.write(
                    f"• {explanation}"
                )

        else:

            st.success(
                "No review attention detected by "
                "the ML prototype."
            )

        if ml_result["probability"] is not None:

            st.write(
                "Model probability for review attention: "
                f"**{ml_result['probability']:.1%}**"
            )

        st.caption(
            "This is an academic monitoring prototype "
            "and is not a medical diagnosis."
        )

    # -----------------------------------------------------
    # NEXT APPOINTMENT
    # -----------------------------------------------------

    if upcoming_appointments:

        st.divider()

        st.subheader(
            "Next Appointment"
        )

        next_appointment = (
            upcoming_appointments[0]
        )

        col1, col2 = st.columns(2)

        col1.write(
            f"**Date:** "
            f"{next_appointment['appointment_date']}"
        )

        col2.write(
            f"**Reason:** "
            f"{next_appointment['reason']}"
        )


# =========================================================
# PATIENT PROFILE
# =========================================================

elif page == "👤 Patient Profile":

    st.title("👤 Patient Profile")

    st.caption(
        "View patient information and add new patients."
    )

    st.subheader(
        "Current Patient"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            f"**Name:** "
            f"{selected_patient['patient_name']}"
        )

        st.write(
            f"**Age:** "
            f"{selected_patient['age']}"
        )

    with col2:

        st.write(
            f"**Gender:** "
            f"{selected_patient['gender']}"
        )

        st.write(
            f"**Phone:** "
            f"{selected_patient['phone']}"
        )

    st.divider()

    st.subheader(
        "Add New Patient"
    )

    with st.form(
        "add_patient_form"
    ):

        name = st.text_input(
            "Patient name"
        )

        age = st.number_input(
            "Age",
            min_value=0,
            max_value=120,
            value=25
        )

        gender = st.selectbox(
            "Gender",
            [
                "Female",
                "Male",
                "Other"
            ]
        )

        phone = st.text_input(
            "Phone"
        )

        submitted = st.form_submit_button(
            "Add Patient"
        )

        if submitted:

            if not name.strip():

                st.error(
                    "Please enter a patient name."
                )

            else:

                connection = get_connection()

                cursor = connection.cursor()

                cursor.execute(
                    """
                    INSERT INTO patients
                    (
                        patient_name,
                        age,
                        gender,
                        phone
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        name.strip(),
                        age,
                        gender,
                        phone.strip()
                    )
                )

                connection.commit()

                cursor.close()
                connection.close()

                st.success(
                    "Patient added successfully."
                )

                st.rerun()


# =========================================================
# MEDICAL RECORDS
# =========================================================

elif page == "📋 Medical Records":

    st.title("📋 Medical Records")

    st.caption(
        "Upload medical records and extract information using OCR."
    )

    st.subheader(
        f"Records for {selected_patient['patient_name']}"
    )

    uploaded_file = st.file_uploader(
        "Upload medical record",
        type=[
            "pdf",
            "png",
            "jpg",
            "jpeg"
        ]
    )

    if uploaded_file is not None:

        if st.button(
            "Upload and Extract"
        ):

            records_folder = os.path.join(
                PROJECT_ROOT,
                "data",
                "medical_records"
            )

            os.makedirs(
                records_folder,
                exist_ok=True
            )

            file_path = os.path.join(
                records_folder,
                uploaded_file.name
            )

            with open(
                file_path,
                "wb"
            ) as file:

                file.write(
                    uploaded_file.getbuffer()
                )

            with st.spinner(
                "Extracting text..."
            ):

                extracted_text = (
                    extract_text_from_file(
                        uploaded_file
                    )
                )

            connection = get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO medical_records
                (
                    patient_id,
                    file_name,
                    file_path,
                    extracted_text
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    patient_id,
                    uploaded_file.name,
                    file_path,
                    extracted_text
                )
            )

            connection.commit()

            cursor.close()
            connection.close()

            st.success(
                "Medical record uploaded successfully."
            )

            if extracted_text.strip():

                st.subheader(
                    "Extracted Text"
                )

                st.text_area(
                    "OCR output",
                    extracted_text,
                    height=250
                )

                information = (
                    extract_medical_information(
                        extracted_text
                    )
                )

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        "**Medications**"
                    )

                    if information["medications"]:

                        for medication in information[
                            "medications"
                        ]:

                            st.write(
                                f"• {medication}"
                            )

                    else:

                        st.write(
                            "No medications detected."
                        )

                    st.write(
                        "**Dates**"
                    )

                    if information["dates"]:

                        for item in information[
                            "dates"
                        ]:

                            st.write(
                                f"• {item}"
                            )

                    else:

                        st.write(
                            "No dates detected."
                        )

                with col2:

                    st.write(
                        "**Symptoms**"
                    )

                    if information["symptoms"]:

                        for symptom in information[
                            "symptoms"
                        ]:

                            st.write(
                                f"• {symptom}"
                            )

                    else:

                        st.write(
                            "No symptoms detected."
                        )

                    st.write(
                        "**Medical Terms**"
                    )

                    if information["medical_terms"]:

                        for term in information[
                            "medical_terms"
                        ]:

                            st.write(
                                f"• {term}"
                            )

                    else:

                        st.write(
                            "No medical terms detected."
                        )

            else:

                st.warning(
                    "No text could be extracted."
                )

    st.divider()

    records = get_records(
        patient_id
    )

    if records:

        st.subheader(
            "Uploaded Records"
        )

        for record in records:

            with st.expander(
                record["file_name"]
            ):

                st.write(
                    f"Uploaded: "
                    f"{record['uploaded_at']}"
                )

                st.text_area(
                    "Extracted text",
                    record["extracted_text"] or "",
                    height=200,
                    key=(
                        f"record_"
                        f"{record['record_id']}"
                    )
                )

    else:

        st.info(
            "No medical records uploaded yet."
        )


# =========================================================
# DAILY CHECK-IN
# =========================================================

elif page == "❤️ Daily Check-in":

    st.title("❤️ Daily Check-in")

    st.caption(
        "Record daily patient-reported monitoring information."
    )

    st.write(
        f"Patient: "
        f"**{selected_patient['patient_name']}**"
    )

    with st.form(
        "checkin_form"
    ):

        checkin_date = st.date_input(
            "Check-in date",
            value=date.today()
        )

        mood = st.slider(
            "Mood",
            min_value=1,
            max_value=5,
            value=3
        )

        pain_level = st.slider(
            "Pain level",
            min_value=0,
            max_value=10,
            value=0
        )

        sleep_hours = st.number_input(
            "Sleep hours",
            min_value=0.0,
            max_value=24.0,
            value=8.0,
            step=0.5
        )

        medication_taken = st.checkbox(
            "Medication taken",
            value=True
        )

        symptoms = st.text_area(
            "Symptoms / notes"
        )

        submitted = st.form_submit_button(
            "Save Check-in"
        )

        if submitted:

            save_checkin(
                patient_id,
                checkin_date,
                mood,
                pain_level,
                sleep_hours,
                medication_taken,
                symptoms
            )

            st.success(
                "Check-in saved successfully."
            )

            st.rerun()


# =========================================================
# APPOINTMENTS
# =========================================================

elif page == "📅 Appointments":

    st.title("📅 Appointments")

    st.caption(
        "Create and review patient appointments."
    )

    with st.form(
        "appointment_form"
    ):

        appointment_date = st.date_input(
            "Appointment date"
        )

        reason = st.text_input(
            "Reason"
        )

        status = st.selectbox(
            "Status",
            [
                "Upcoming",
                "Completed",
                "Cancelled"
            ]
        )

        submitted = st.form_submit_button(
            "Add Appointment"
        )

        if submitted:

            if not reason.strip():

                st.error(
                    "Please enter a reason."
                )

            else:

                save_appointment(
                    patient_id,
                    appointment_date,
                    reason.strip(),
                    status
                )

                st.success(
                    "Appointment added."
                )

                st.rerun()

    st.divider()

    appointments = get_appointments(
        patient_id
    )

    if appointments:

        appointment_df = pd.DataFrame(
            appointments
        )

        st.dataframe(
            appointment_df[
                [
                    "appointment_date",
                    "reason",
                    "status"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No appointments found."
        )


# =========================================================
# HEALTH TRENDS
# =========================================================

elif page == "📈 Health Trends":

    st.title("📈 Health Trends")

    st.caption(
        "Visualize longitudinal patient-reported trends."
    )

    checkins = get_checkins(
        patient_id
    )

    if not checkins:

        st.info(
            "No check-in data available."
        )

    else:

        dataframe = pd.DataFrame(
            checkins
        )

        dataframe["checkin_date"] = (
            pd.to_datetime(
                dataframe["checkin_date"]
            )
        )

        dataframe = dataframe.sort_values(
            "checkin_date"
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Average Mood",
            f"{dataframe['mood'].mean():.2f}"
        )

        col2.metric(
            "Average Pain",
            f"{dataframe['pain_level'].mean():.2f}"
        )

        col3.metric(
            "Average Sleep",
            f"{dataframe['sleep_hours'].mean():.2f} hrs"
        )

        st.divider()

        st.subheader(
            "Mood Trend"
        )

        mood_chart = px.line(
            dataframe,
            x="checkin_date",
            y="mood",
            markers=True,
            title="Mood over time"
        )

        st.plotly_chart(
            mood_chart,
            use_container_width=True
        )

        st.subheader(
            "Pain Trend"
        )

        pain_chart = px.line(
            dataframe,
            x="checkin_date",
            y="pain_level",
            markers=True,
            title="Pain level over time"
        )

        st.plotly_chart(
            pain_chart,
            use_container_width=True
        )

        st.subheader(
            "Sleep Trend"
        )

        sleep_chart = px.line(
            dataframe,
            x="checkin_date",
            y="sleep_hours",
            markers=True,
            title="Sleep hours over time"
        )

        st.plotly_chart(
            sleep_chart,
            use_container_width=True
        )


# =========================================================
# PATIENT TIMELINE
# =========================================================

elif page == "🕒 Patient Timeline":

    st.title("🕒 Patient Timeline")

    st.caption(
        "Combined view of check-ins, appointments, "
        "and medical records."
    )

    timeline = []

    checkins = get_checkins(
        patient_id
    )

    appointments = get_appointments(
        patient_id
    )

    records = get_records(
        patient_id
    )

    # -----------------------------------------------------
    # CHECK-INS
    # -----------------------------------------------------

    for checkin in checkins:

        timeline.append(
            {
                "Date":
                    checkin["checkin_date"],

                "Type":
                    "Check-in",

                "Details":
                    (
                        f"Mood: {checkin['mood']} | "
                        f"Pain: {checkin['pain_level']} | "
                        f"Sleep: "
                        f"{checkin['sleep_hours']} hrs"
                    )
            }
        )

    # -----------------------------------------------------
    # APPOINTMENTS
    # -----------------------------------------------------

    for appointment in appointments:

        timeline.append(
            {
                "Date":
                    appointment[
                        "appointment_date"
                    ],

                "Type":
                    "Appointment",

                "Details":
                    (
                        f"{appointment['reason']} "
                        f"({appointment['status']})"
                    )
            }
        )

    # -----------------------------------------------------
    # MEDICAL RECORDS
    # -----------------------------------------------------

    for record in records:

        timeline.append(
            {
                "Date":
                    record["uploaded_at"],

                "Type":
                    "Medical Record",

                "Details":
                    record["file_name"]
            }
        )

    if timeline:

        timeline_df = pd.DataFrame(
            timeline
        )
        timeline_df["Date"] = pd.to_datetime(timeline_df["Date"])
        
        timeline_df = timeline_df.sort_values(
            "Date",
            ascending=False
        )

        st.dataframe(
            timeline_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No timeline events available."
        )


# =========================================================
# PROVIDER DASHBOARD
# =========================================================

elif page == "🩺 Provider Dashboard":

    st.title(
        "🩺 Provider Dashboard"
    )

    st.caption(
        "Overview of patient monitoring, appointments, "
        "and recent activity."
    )

    connection = get_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    # -----------------------------------------------------
    # TOTAL PATIENTS
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM patients
        """
    )

    total_patients = cursor.fetchone()[
        "count"
    ]

    # -----------------------------------------------------
    # TOTAL CHECK-INS
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM health_checkins
        """
    )

    total_checkins = cursor.fetchone()[
        "count"
    ]

    # -----------------------------------------------------
    # TOTAL RECORDS
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM medical_records
        """
    )

    total_records = cursor.fetchone()[
        "count"
    ]

    # -----------------------------------------------------
    # UPCOMING APPOINTMENTS
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM appointments
        WHERE status = 'Upcoming'
        """
    )

    upcoming_appointments = (
        cursor.fetchone()["count"]
    )

    cursor.close()
    connection.close()

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Patients",
        total_patients
    )

    col2.metric(
        "Total Check-ins",
        total_checkins
    )

    col3.metric(
        "Medical Records",
        total_records
    )

    col4.metric(
        "Upcoming Appointments",
        upcoming_appointments
    )

    st.divider()

    # -----------------------------------------------------
    # PATIENT MONITORING
    # -----------------------------------------------------

    st.subheader(
        "Patient Monitoring Overview"
    )

    monitoring_rows = []

    for patient in patients:

        current_patient_id = (
            patient["patient_id"]
        )

        current_checkins = get_checkins(
            current_patient_id
        )

        recent_checkins = (
            current_checkins[:3]
        )

        rule_result = assess_follow_up(
            recent_checkins
        )

        ml_result = get_ml_prediction(
            current_checkins
        )

        if ml_result is None:

            ml_status = (
                "Insufficient Data"
            )

        elif ml_result["prediction"] == 1:

            ml_status = (
                "Review Attention"
            )

        else:

            ml_status = "Routine"

        monitoring_rows.append(
            {
                "Patient":
                    patient["patient_name"],

                "Rule-based Status":
                    rule_result["status"],

                "ML Status":
                    ml_status,

                "Monitoring Score":
                    rule_result["score"]
            }
        )

    monitoring_df = pd.DataFrame(
        monitoring_rows
    )

    st.dataframe(
        monitoring_df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # -----------------------------------------------------
    # UPCOMING APPOINTMENTS
    # -----------------------------------------------------

    st.subheader(
        "Upcoming Appointments"
    )

    connection = get_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            a.appointment_date,
            p.patient_name,
            a.reason,
            a.status
        FROM appointments AS a
        JOIN patients AS p
            ON a.patient_id = p.patient_id
        WHERE a.status = 'Upcoming'
        ORDER BY a.appointment_date
        """
    )

    upcoming = cursor.fetchall()

    cursor.close()
    connection.close()

    if upcoming:

        upcoming_df = pd.DataFrame(
            upcoming
        )

        st.dataframe(
            upcoming_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No upcoming appointments."
        )

    st.divider()

    # -----------------------------------------------------
    # RECENT CHECK-INS
    # -----------------------------------------------------

    st.subheader(
        "Recent Check-ins"
    )

    connection = get_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            h.checkin_date,
            p.patient_name,
            h.mood,
            h.pain_level,
            h.sleep_hours,
            h.medication_taken
        FROM health_checkins AS h
        JOIN patients AS p
            ON h.patient_id = p.patient_id
        ORDER BY h.checkin_date DESC
        LIMIT 20
        """
    )

    recent_checkins = cursor.fetchall()

    cursor.close()
    connection.close()

    if recent_checkins:

        recent_checkins_df = pd.DataFrame(
            recent_checkins
        )

        st.dataframe(
            recent_checkins_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No check-ins available."
        )


# =========================================================
# FOOTER
# =========================================================

st.sidebar.divider()

st.sidebar.markdown(
    """
    **CareTrack**

    Patient healthcare follow-up and monitoring system.

    This application is an academic prototype.
    Monitoring and ML outputs are not medical diagnoses
    and should not replace professional healthcare advice.
    """
)