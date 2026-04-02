# Baby Monitor System

## Description
Système de surveillance bébé avec STM32, backend Python et interface React.

## Architecture
STM32 → USB (Serial) → Backend (FastAPI) → Frontend (React)

## Installation

### Backend
cd backend  
pip install -r requirements.txt  
python -m uvicorn app:app --reload  

### Frontend
cd frontend  
npm install  
npm run dev  

## Important
Modifier le port COM dans backend/app.py selon votre STM32.
