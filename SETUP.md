# PneumoDetect — Setup & Run Guide

## Prerequisites
- Python 3.9+ (3.10 recommended) — https://python.org/downloads
- MySQL 8.0+ or XAMPP — https://www.apachefriends.org
- Git (optional)

---

## 1. Clone / Extract the Project

```bash
cd C:\Users\PC\Downloads
# already extracted to: pneumonia\
cd pneumonia
```

---

## 2. Create and Activate Virtual Environment

```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# If execution policy blocks it:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

---

## 3. Install Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

> TensorFlow (~600 MB) will be downloaded. This may take several minutes.

---

## 4. Configure Environment

```powershell
copy .env.example .env
notepad .env
```

**Minimum required settings in `.env`:**
```dotenv
SECRET_KEY=your_random_32_char_key_here
DB_HOST=localhost
DB_PORT=3306
DB_NAME=pneumonia_db
DB_USER=root
DB_PASSWORD=your_mysql_root_password
```

Generate a secret key:
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 5. Set Up Database

Start MySQL (via XAMPP Control Panel → Start MySQL, or your MySQL service).

```powershell
mysql -u root -p < database\schema.sql
```

Or open phpMyAdmin → SQL tab → paste contents of `database/schema.sql` → Execute.

---

## 6. Download Dataset (for training)

Download the **Chest X-Ray Images (Pneumonia)** dataset from Kaggle:
https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia

Extract so the structure matches:
```
DATASET\
  train\
    NORMAL\
    PNEUMONIA\
  test\
    NORMAL\
    PNEUMONIA\
```

---

## 7. Train ML Models

> Skip this step if you already have `.h5` model files in `saved_models\`.

```powershell
# Train ResNet50 (recommended — ~30 min on GPU, longer on CPU)
python ml\train_resnet.py

# Train MobileNetV2 (faster)
python ml\train_mobilenet.py
```

Trained models will be saved to `saved_models\resnet50.h5` and `saved_models\mobilenetv2.h5`.

---

## 8. Run the Application

### Development mode
```powershell
python run.py
```
Open: http://127.0.0.1:5000

### Production mode (Windows — Waitress)
```powershell
$env:FLASK_ENV="production"
waitress-serve --port=5000 --threads=4 wsgi:app
```

### Production mode (Linux — Gunicorn)
```bash
bash deployment/start_linux.sh
```

---

## 9. Run Tests

```powershell
pytest tests\ -v
```

---

## 10. Typical User Flow

1. Open http://127.0.0.1:5000
2. Click **Register** → fill in details → submit
3. Click **Login** → enter email + password
4. Click **Analyze** → upload a chest X-ray JPG/PNG → choose model → submit
5. View prediction result with confidence score and clinical guidance
6. Click **View History** to see past predictions
7. Click your name → **Logout**

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: flask` | Run `pip install -r requirements.txt` inside the venv |
| `mysql.connector.errors.DatabaseError` | Verify MySQL is running and `.env` credentials are correct |
| `FileNotFoundError: saved_models/resnet50.h5` | Train the model first: `python ml\train_resnet.py` |
| `OSError: [Errno 13] uploads/` | Create the folder: `mkdir app\static\uploads` |
| TF install fails on Python 3.8 | Upgrade to Python 3.9+: `py -3.10 -m venv venv` |
| `ExecutionPolicy` error on Windows | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
