import random
from pathlib import Path

from app.core.database import SessionFactory
from app.domain.models import ContextDocument, Passage, Practice
from app.domain.tables import DocumentRow, PassageRow
from app.services.pdf_service import extract_paragraphs


class DocumentRepository:
    def import_pdf(self, pdf_path: Path) -> ContextDocument:
        paragraphs = extract_paragraphs(pdf_path)
        if not paragraphs:
            raise ValueError("No usable paragraphs found in this PDF.")
        with SessionFactory() as session:
            row = DocumentRow(filename=pdf_path.name)
            row.passages = [PassageRow(text=p) for p in paragraphs]
            session.add(row)
            session.commit()
            session.refresh(row)
            return ContextDocument(
                id=row.id,
                filename=row.filename,
                use_for_typing=row.use_for_typing,
                use_for_reading=row.use_for_reading,
            )

    def list_documents(self) -> list[ContextDocument]:
        with SessionFactory() as session:
            return [
                ContextDocument(
                    id=row.id,
                    filename=row.filename,
                    use_for_typing=row.use_for_typing,
                    use_for_reading=row.use_for_reading,
                )
                for row in session.query(DocumentRow).all()
            ]

    def set_usage(
        self, document_id: int, use_for_typing: bool, use_for_reading: bool
    ) -> None:
        with SessionFactory() as session:
            row = session.get(DocumentRow, document_id)
            if row is not None:
                row.use_for_typing = use_for_typing
                row.use_for_reading = use_for_reading
                session.commit()

    def random_passage(self, practice: Practice) -> Passage | None:
        with SessionFactory() as session:
            flag = (
                DocumentRow.use_for_typing
                if practice == "typing"
                else DocumentRow.use_for_reading
            )
            rows = session.query(PassageRow).join(DocumentRow).filter(flag).all()
            if not rows:
                return None
            row = random.choice(rows)
            return Passage(id=row.id, text=row.text, document_id=row.document_id)
