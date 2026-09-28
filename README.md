# CareTrack

## Patient Healthcare Follow-up & Monitoring System

CareTrack is a healthcare monitoring application developed as an academic Data Science project.

It helps organize patient information, medical records, daily health check-ins, appointments, and longitudinal health patterns.

The system also includes OCR, basic medical text extraction, rule-based follow-up assessment, machine learning, and explainability.

## Features

- Patient management
- Medical record upload
- OCR text extraction
- Basic medical information extraction
- Daily health check-ins
- Health trend visualization
- Appointment management
- Patient timeline
- Follow-up monitoring
- Machine learning-based review attention
- Explainability
- Provider dashboard

## Technologies Used

- Python
- Streamlit
- MySQL
- Pandas
- Plotly
- Scikit-learn
- PyMuPDF
- Tesseract OCR
- Pytesseract
- Pillow
- Joblib

## Project Structure

CareTrack/
├── app/
│   └── app.py
├── data/
│   └── medical_records/
├── database/
│   ├── db_connection.py
│   └── update_database.py
├── models/
│   ├── explainability.py
│   ├── follow_up_logic.py
│   ├── follow_up_model.py
│   └── medical_nlp.py
├── notebooks/
│   ├── train_follow_up_model.py
│   └── test_follow_up.py
└── README.md

## Machine Learning

CareTrack uses a Random Forest classifier as an academic prototype for identifying patient check-in patterns that may require healthcare-provider review.

The model uses features such as:

- Average mood
- Average pain
- Average sleep
- High pain count
- Low mood count
- Low sleep count
- Missed medication count

The trained model is stored as:

models/follow_up_model.pkl

## OCR and Medical NLP

Medical documents can be uploaded to the application.

The system uses Tesseract OCR to extract text from documents.

The extracted text is then processed to identify basic:

- Medications
- Dates
- Symptoms
- Medical terms

## Database

CareTrack uses MySQL.

The main database tables are:

- patients
- medical_records
- health_checkins
- appointments

## How to Run

Open Command Prompt and navigate to the project folder:

cd /d "E:\Data Science Projects\CareTrack"

Activate the virtual environment:

.venv\Scripts\activate.bat

Run the application:

streamlit run app\app.py

## Project Purpose

The purpose of CareTrack is to demonstrate how Data Science can be applied to healthcare monitoring using structured data, OCR, NLP, visualization, machine learning, and explainability.

## Limitations

This project is an academic prototype.

The machine learning labels are based on predefined monitoring rules and are not based on clinically validated outcomes.

The system does not diagnose diseases or provide treatment recommendations.

OCR and medical text extraction may also produce errors depending on document quality.

## Future Enhancements

- Advanced medical NLP
- Named Entity Recognition
- Transformer-based NLP
- Improved OCR
- Time-series analysis
- SHAP-based explainability
- Patient authentication
- Doctor authentication
- Role-based access control
- Secure deployment
- Notification system
- Mobile application

## Author

Varshini A

M.Sc. Applied Data Science  
SRM University, Ramapuram

## Disclaimer

CareTrack is an academic project developed for educational and demonstration purposes.

The system does not provide medical diagnosis, treatment recommendations, or emergency medical advice.

Any monitoring indication should be reviewed by an appropriately qualified healthcare professional.
