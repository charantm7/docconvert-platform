from importlib.resources import files
import tempfile
import shutil
import subprocess
import time
import os
from pathlib import Path
from typing import Optional
from supabase import Client
from pdf2docx import Converter

from conversion_workers.settings import settings

# Exceptions
from conversion_workers.exception import (
    LibreOfficeNotFoundError,
    FileNotFoundError,
    ConversionTimeoutError,
    ConversionFailedError,
    UploadFailedError,
)


class LibreOfficeConverter:

    def __init__(
        self,
        soffice_path: Optional[str] = None,
        timeout_seconds: int = 120,
    ):
        self.soffice_path = soffice_path or self._detect_soffice()
        self.timeout_second = timeout_seconds

    def convert(self, input_path: Path, output_dir: Path, target_ext: str) -> Path:

        cmd = [
            self.soffice_path,
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "--norestore",
            "--convert-to",
            target_ext,
            "--outdir",
            str(output_dir),
            str(input_path)
        ]

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout_second,
                check=True,
            )
    
        except subprocess.TimeoutExpired as e:
            raise ConversionTimeoutError(
                "LibreOffice Conversion timeout error") from e

        except subprocess.CalledProcessError as e:
            print(f"[DEBUG] CalledProcessError STDERR: {e.stderr.decode(errors='ignore')}")
            raise ConversionFailedError(
                e.stderr.decode(errors="ignore")) from e
        
        
        expected_output = output_dir / f"{input_path.stem}.{target_ext.lower()}"
        if expected_output.exists():
            return expected_output

        for file in output_dir.iterdir():
            if file.suffix.lower() == f".{target_ext.lower()}" and file != input_path:
                return file

        raise ConversionFailedError(
            f"LibreOffice produced no output.\nSTDERR:\n{result.stderr.decode(errors='ignore')}"
        )

    def _detect_soffice(self) -> str:
        candidates = [
            shutil.which("soffice"),
            "/usr/bin/soffice",
            "/usr/local/bin/soffice",
            "C:\\Program Files\\LibreOffice\\program\\soffice.exe",
        ]

        for path in candidates:
            if path and Path(path).exists():
                return str(path)
        raise LibreOfficeNotFoundError(
            "Libreoffice not installed in the system")


class Conversion:
    def __init__(self, supabase: Client):
        self.supabase_client = supabase
        self._libreoffice_converter = LibreOfficeConverter()

    def convert_pdf_to_ppt(self, job_id: str, path:str):
        """
        Docstring for convert_pdf_to_ppt
        
        :param self: Description
        :param job_id: Description
        :type job_id: str
        :param path: Description
        :type path: str
        Converter PDF (supabase) -> PPT -> Supabase
        """

        try:

            file_byte = self.supabase_client.storage.from_(
                settings.SUPABASE_RAW_BUCKET).download(path=path)   
        except Exception as e:
            print(f"[worker] error downloading file for job {job_id}: {str(e)}")
            raise FileNotFoundError(f"File not found in storage: {path}") from e
        
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir = Path(tempdir)

            suffix = Path(path).suffix.lower()

            if suffix != ".pdf":
                raise ConversionFailedError(f"Unsupported input format: {suffix}")
            
            input_pdf = tempdir / "input.pdf"
            output_dir = tempdir / "output.pptx"

            with open(input_pdf, "wb") as f:
                f.write(file_byte)
            
            output_file = self._libreoffice_converter.convert(input_path=input_pdf, output_dir=output_dir, target_ext='pptx')

            if not output_file.exists():    
                raise ConversionFailedError("Conversion failed: No output file found")
            output_storage_path = path.replace(
                "original.pdf", "converted.pptx")
            
            try:
                with open(output_file, "rb") as f:
                    self.supabase_client.storage.from_(settings.SUPABASE_CONVERTED_BUCKET).upload(
                        output_storage_path,
                        f,
                        {
                            "content-type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            "x-upsert": "true"
                        },
                    )
            except Exception as e:
                print(f"[worker] error uploading file for job {job_id}: {str(e)}")
                raise UploadFailedError(f"Upload failed: {str(e)}") from e
        print(f"[worker] upload complete for job {job_id}")
            
    def convert_docx_to_pdf(self, job_id: str, path: str):
        """
        Docstring for convert_docx_to_pdf
        
        :param self: Description
        :param job_id: Description
        :type job_id: str
        :param path: Description
        :type path: str

        Converter DOCX (supabase) -> PDF -> Supabase
        """

        try:

            file_byte = self.supabase_client.storage.from_(
                settings.SUPABASE_RAW_BUCKET).download(path=path)
        except Exception as e:
            print(f"[worker] error downloading file for job {job_id}: {str(e)}")
            raise FileNotFoundError(f"File not found in storage: {path}") from e
        
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir = Path(tempdir)

            suffix = Path(path).suffix.lower()

            if suffix != ".docx":
                raise ConversionFailedError(f"Unsupported input format: {suffix}")

            input_docx = tempdir / 'input.docx'
            output_dir = tempdir / "output.pdf"

            with open(input_docx, "wb") as f:
                f.write(file_byte)

            output_file = self._libreoffice_converter.convert(input_path=input_docx, output_dir=output_dir, target_ext='pdf')

            if not output_file.exists():
                raise ConversionFailedError("Conversion failed: No output file found")
            output_storage_path = path.replace(
                "original.docx", "converted.pdf")
            
            try:
                with open(output_file, "rb") as f:
                    self.supabase_client.storage.from_(settings.SUPABASE_CONVERTED_BUCKET).upload(
                        output_storage_path,
                        f,
                        {
                            "content-type": "application/pdf",
                            "x-upsert": "true"
                        },
                    )
            except Exception as e:
                print(f"[worker] error uploading file for job {job_id}: {str(e)}")
                raise UploadFailedError(f"Upload failed: {str(e)}") from e
        print(f"[worker] upload complete for job {job_id}")
    
                

    def convert_pdf_to_docx(self, job_id: str, path: str):
        """
        Docstring for convert_pdf_to_docx

        PDF (supabase) -> DOX -> Supabase
        """

        print(f"[wroker] starting convertion for job id {job_id}")

        try:

            file_byte = self.supabase_client.storage.from_(
                settings.SUPABASE_RAW_BUCKET).download(path=path)
        except Exception as e:
            print(f"[worker] error downloading file for job {job_id}: {str(e)}")
            raise FileNotFoundError(f"File not found in storage: {path}") from e


        with tempfile.TemporaryDirectory() as tempdir:
            tempdir = Path(tempdir)

            suffix = Path(path).suffix.lower()

            if suffix != ".pdf":
                raise ConversionFailedError(
                    f"Unsupported input format: {suffix}")
            
            input_pdf = Path(tempdir) / "input.pdf"
            output_dir = Path(tempdir) / "output.docx"

            with open(input_pdf, "wb") as f:
                f.write(file_byte)

            try:
                cv = Converter(str(input_pdf))
                cv.convert(str(output_dir))
                cv.close()   
            except Exception as e:
                print(f"[worker] error during conversion for job {job_id}: {str(e)}")     
                raise ConversionFailedError(f"Conversion failed: {str(e)}") from e


            if not output_dir.exists():
                raise ConversionFailedError("Conversion failed: No output file found")
        
            output_storage_path = path.replace(
                "original.pdf", "converted.docx")
            
            try:

                with open(output_dir, "rb") as f:
                    self.supabase_client.storage.from_(settings.SUPABASE_CONVERTED_BUCKET).upload(
                        output_storage_path,
                        f,
                        {
                            "content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            "x-upsert": "true"
                        },
                    )
            except Exception as e:
                print(f"[worker] error uploading file for job {job_id}: {str(e)}")
                raise UploadFailedError(f"Upload failed: {str(e)}") from e
            
        print(f"[worker] upload complete for job {job_id}")
