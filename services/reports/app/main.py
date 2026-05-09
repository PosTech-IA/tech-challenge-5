from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from upload.app.database import get_db
from upload.app.models import Analysis

app = FastAPI(title="Reports Service")

@app.get("/reports/{analysis_id}")
def generate_report(analysis_id: str, db: Session = Depends(get_db)):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    
    if not analysis or analysis.status != "analyzed":
        return {"error": "Relatório ainda não disponível ou não encontrado."}
    
    # Lógica de formatação do relatório estruturado
    return {
        "analysis_id": analysis.id,
        "filename": analysis.filename,
        "generated_at": analysis.updated_at,
        "content": analysis.result_data # Dados vindos da IA
    }