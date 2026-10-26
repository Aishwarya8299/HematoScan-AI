# Hematoscan

Production-grade B2B Diagnostic Decision Support System for hospital **Lab Technicians**.

**Project location:** `D:\hematoscan`

## Current foundation

- FastAPI async application skeleton
- Environment-driven configuration (`pydantic-settings`)
- Structured logging
- Health endpoint: `GET /api/v1/system/health`
- Async MongoDB connection lifecycle with startup ping
- MongoDB collection definitions and repeatable index initialization
- Authentication core with bcrypt passwords, JWTs, and role guards
- Auth API with login, current-user, logout, and development account seeding
- Gatekeeper-first ML inference: invalid images are rejected before leukemia classification
- Technician-only multipart upload endpoint with MongoDB case persistence
- Local `.h5` models loaded at startup when enabled

## Quick start

```powershell
# 1. Enter project (D: drive)
cd D:\hematoscan

# 2. Environment
copy .env.example .env

# 3. Virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate

# 4. Install dependencies
pip install -r backend\requirements.txt

# 5. Run API
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Verify: [http://localhost:8000/api/v1/system/health](http://localhost:8000/api/v1/system/health)

Initialize MongoDB indexes manually when needed:

```powershell
python scripts\init_indexes.py
```

Seed local development accounts:

```powershell
python scripts\seed_users.py
```

The seeded accounts use the temporary password `ChangeMe123!`; change or remove
them before using a shared environment.

## ML inference

The local models are loaded at API startup when `ML_MODELS_ENABLED=true`.
Inference resizes images to `128x128`, applies MobileNetV2 preprocessing, and
passes them through `gatekeeper_model.h5` first. A gatekeeper result below
`GATEKEEPER_VALID_THRESHOLD` is rejected and never reaches the leukemia model.
Accepted images are classified using `ALL`, `AML`, `CLL`, `CML`, and `HEALTHY`.

The current default assumes the gatekeeper sigmoid positive class means
"valid blood smear". Set `GATEKEEPER_POSITIVE_IS_VALID=false` if the model was
trained with the opposite label polarity.

Technicians upload images with:

```text
POST /api/v1/technician/upload
Content-Type: multipart/form-data
Fields: patient_id, image
```

Accepted image types are JPEG, PNG, and WebP. The configured upload limit is
10 MB by default. Cases finish as `rejected` or `awaiting_review`.

Doctors review cases with:

```text
GET   /api/v1/doctor/queue
GET   /api/v1/doctor/case/{case_id}
PATCH /api/v1/doctor/case/{case_id}/review
```

The queue places non-`HEALTHY` predictions first and then sorts by newest
upload. Review updates can add notes and transition a case to `reviewed`.

## Project layout

```text
D:\hematoscan\
├── .env.example
├── backend/
│   ├── main.py                 # FastAPI entry
│   ├── requirements.txt
│   ├── app/
│   │   ├── core/               # config, logging
│   │   ├── db/                 # MongoDB client, collections, indexes
│   │   ├── api/v1/             # routes (system health)
│   │   └── schemas/            # Pydantic models
│   ├── models/                 # .h5 weights (add later)
│   └── uploads/                # runtime file storage
└── frontend/                   # HTML/CSS/JS (Step 5+)
```

## Adding trained models later

1. Place files in `backend/models/`:
   - `gatekeeper_model.h5`
   - `leukemia_classifier_model.h5`
2. Set `ML_MODELS_ENABLED=true` in `.env`
3. Complete Steps 12–15 to wire inference

## Development roadmap

Built step-by-step — confirm **"Proceed to next step"** before each module.

| Step | Module |
|------|--------|
| 1 | Project scaffold & environment ✅ |
| 2 | MongoDB integration ✅ |
| 3 | Auth core ✅ |
| 4 | Auth API routes ✅ |
| 4 | Auth API routes |
| 5+ | Frontend, upload pipeline, ML, doctor workstation |
