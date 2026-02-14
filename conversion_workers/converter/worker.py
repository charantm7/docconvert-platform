import tempfile
import os
from pdf2docx import Converter

from conversion_workers.storage.s3_client import supabase
from conversion_workers.settings import settings


def convert_pdf_to_docx(job_id: str, path: str):
    """
    Docstring for convert_pdf_to_docx

    :param job_id: Description
    :type job_id: str
    :param path: Description
    :type path: str

    PDF (supabase) -> DOX -> Supabase
    """

    print(f"[wroker] starting convertion for job id {job_id}")

    file_byte = supabase.storage.from_(
        settings.SUPABASE_RAW_BUCKET).download(path=path)

    with tempfile.TemporaryDirectory() as tempdir:
        input_pdf = os.path.join(tempdir, "input.pdf")
        output_docx = os.path.join(tempdir, "output.docx")

        with open(input_pdf, "wb") as f:
            f.write(file_byte)

        cv = Converter(input_pdf)
        cv.convert(output_docx)
        cv.close()

        print(f"[worker] conversion finished for job {job_id}")

        output_storage_path = path.replace("original.pdf", "converted.docx")

        with open(output_docx, "rb") as f:
            supabase.storage.from_(settings.SUPABASE_CONVERTED_BUCKET).upload(
                output_storage_path,
                f,
                {
                    "content-type":
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                },
            )
    print(f"[worker] upload complete for job id {job_id}")
