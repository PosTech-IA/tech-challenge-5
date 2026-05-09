import json
import os

from anthropic import Anthropic
import mimetypes
from app.celery_app import celery
from app.config import settings
from app.models import SessionLocal, Analysis
from app.storage import download_file, encode_image


@celery.task(name="processor.tasks.process_diagram")
def process_diagram(analysis_id: str, file_ref: str):
    db = SessionLocal()
    analysis = None
    try:
        # 1. Atualiza status para processing
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis is None:
            raise ValueError(f"Analysis with id {analysis_id} not found in database")
        
        analysis.status = "processing"
        db.commit()

        # 2. Download do arquivo e chamada à IA
        file_bytes = download_file(file_ref)
        
        # IA: Prompt Engineering & Guardrails [IADT]
        api_key = os.getenv("ANTHROPIC_API_KEY")
        client = Anthropic(api_key=api_key)

# Build payload defensively
        try:
            # Detecta o MIME type baseado na extensão do arquivo
            mime_type, _ = mimetypes.guess_type(file_ref)
            if not mime_type:
                mime_type = "image/jpeg"  # Fallback

            # Define a estrutura baseada no tipo de arquivo (PDF vs Imagem)
            if "pdf" in mime_type:
                content_block = {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": encode_image(file_bytes)
                    }
                }
            else:
                content_block = {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": encode_image(file_bytes)
                    }
                }

            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                temperature=0,
                system="You are an expert software architect. Analyze the provided architecture diagram. Return ONLY a valid JSON object with exactly these fields: components, risks, recommendations.",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analise este diagrama de arquitetura. Identifique componentes, riscos de segurança e recomendações técnicos em formato JSON."},
                        content_block
                    ]
                }]
            )

            # Normalize response to a string result
            result_text = None
            if hasattr(response, "content") and len(response.content) > 0:
                result_text = response.content[0].text
            else:
                result_text = json.dumps(response.__dict__, default=str)

            analysis.status = "analyzed"
            analysis.result_data = result_text
            db.commit()
        except Exception as ai_exc:
            # Record AI error and mark analysis accordingly
            analysis.status = "error"
            analysis.error_message = f"AI error: {str(ai_exc)}"
            db.commit()
        
    except Exception as e:
        if analysis is not None:
            analysis.status = "error"
            analysis.error_message = str(e)
            db.commit()
        else:
            import logging
            logging.error(f"Error processing task (analysis_id={analysis_id}): {e}")
    finally:
        db.close()