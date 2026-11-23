# ARTERIX: Milestone 1 backend (weeks 1–2)

Backend for Milestone 1 of *Artery Segmentation and Stenosis Detection Using Advanced DL Techniques*.

| Milestone 1 task | Where |
|---|---|
| Dataset selected and analysed (ARCADE, CC0) | `training/prepare_arcade.py`, `data/processed/eda.json` |
| Database schema | `app/models.py` (users, sessions, audit log, patients, cases, images, analyses, alerts) |
| Authentication: register, login, JWT, roles, sessions, lockout, audit log | `app/security.py`, `app/routers/auth.py` |
| Case management: patients and cases | `app/routers/cases.py` |
| Image upload with validation (PNG, JPG, TIFF, BMP, DICOM; size limit), encrypted at rest | `app/routers/cases.py`, `app/storage.py` |
| Preprocessing pipeline: validation, resizing, normalisation, denoising, CLAHE, ROI, quality checks | `app/ml/preprocessing.py` |

Roles: Radiologist / Clinician, Medical Researcher, Data Scientist / ML Engineer, Administrator.

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API. A first administrator, `admin@artery.ai`, is created
with the password `Admin@123`. Change it, and set `JWT_SECRET` in a `.env` file (see `.env.example`).

## Dataset

Download ARCADE from https://zenodo.org/records/10390295, unzip it into `data/raw/arcade/`, then run
`python -m training.prepare_arcade`. It writes the training masks and the analysis in `data/processed/eda.json`.

## Tests

```bash
pytest -q
```
