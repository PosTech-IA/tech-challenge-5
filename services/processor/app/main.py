import json
import os
import re
from anthropic import Anthropic
import mimetypes
from app.celery_app import celery
from app.config import settings
from shared.models import Analysis
import shared.database as db
from shared.storage import download_file, encode_image, init_storage


# Initialize on module load
db.init_db(settings)
init_storage(settings)


@celery.task(name="processor.tasks.process_diagram")
def process_diagram(analysis_id: str, file_ref: str):
    session = db.SessionLocal()

    try:
        analysis = (
            session.query(Analysis)
            .filter(Analysis.id == analysis_id)
            .first()
        )

        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        analysis.status = "processing"
        session.commit()

        file_bytes = download_file(file_ref, settings)

        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        mime_type, _ = mimetypes.guess_type(file_ref)
        mime_type = mime_type or "image/jpeg"

        content_block = {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": mime_type,
                "data": encode_image(file_bytes),
            },
        }

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            temperature=0,
            system="Return ONLY JSON: components, risks, recommendations",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze architecture diagram."},
                    content_block
                ]
            }]
        )

        result_text = response.content[0].text if response.content else ""
        clean = re.sub(r"```json|```", "", result_text).strip()

        try:
            result_json = json.loads(clean)
        except Exception:
            result_json = {"raw": result_text}
        analysis.status = "analyzed"
        analysis.result_data = json.dumps(result_json)
        session.commit()

        return analysis_id  # 👈 FIX DO "None"

    except Exception as e:
        session.rollback()

        if analysis:
            analysis.status = "error"
            analysis.error_message = str(e)
            session.commit()

        raise

    finally:
        session.close()