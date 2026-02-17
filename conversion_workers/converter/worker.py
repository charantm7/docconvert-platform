import tempfile
import shutil
import subprocess
import time
import os
from pathlib import Path
from typing import Optional
from supabase import Client

from conversion_workers.settings import settings

# Exceptions


class LibreOfficeNotFoundError(Exception):
    pass


class ConversionTimeoutError(Exception):
    pass


class ConversionFailedError(Exception):
    pass


class LibreOfficeConverter:

    def __init__(
        self,
        soffice_path: Optional[str] = None,
        timeout_seconds: int = 120,
    ):
        self.soffice_path = soffice_path or self._detect_soffice()
        self.timeout_second = timeout_seconds

    def convert(self, input_path: Path, output_dir: Path, target_ext: str) -> Path:

        convert_arg = target_ext
        if target_ext.lower() == "docx":
            convert_arg = "docx:MS Word 2007 XML"

        lo_user_profile = output_dir / "lo_user_profile"
        lo_user_profile.mkdir(exist_ok=True)

        env = os.environ.copy()
        env["HOME"] = str(output_dir)  # Changed back to output_dir
        env["UserInstallation"] = f"file:///{lo_user_profile}"

        cmd = [
            self.soffice_path,
            f"-env:UserInstallation=file:///{lo_user_profile}",
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "--norestore",
            "--convert-to",
            convert_arg,
            "--outdir",
            str(output_dir),
            str(input_path)
        ]

        print(f"[DEBUG] Running command: {' '.join(cmd)}")
        print(f"[DEBUG] Input file exists: {input_path.exists()}")
        print(f"[DEBUG] Input file size: {input_path.stat().st_size if input_path.exists() else 'N/A'}")
        print(f"[DEBUG] Output dir writable: {os.access(output_dir, os.W_OK)}")

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout_second,
                check=True,
                env=env,
            )
            print(f"[DEBUG] STDOUT: {result.stdout.decode(errors='ignore')}")
            print(f"[DEBUG] STDERR: {result.stderr.decode(errors='ignore')}")
        except subprocess.TimeoutExpired as e:
            raise ConversionTimeoutError(
                "LibreOffice Conversion timeout error") from e

        except subprocess.CalledProcessError as e:
            print(f"[DEBUG] CalledProcessError STDERR: {e.stderr.decode(errors='ignore')}")
            raise ConversionFailedError(
                e.stderr.decode(errors="ignore")) from e
        
        print(f"[DEBUG] Files in output_dir: {list(output_dir.iterdir())}")
        
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

    def convert_pdf_to_docx(self, job_id: str, path: str):
        """
        Docstring for convert_pdf_to_docx

        PDF (supabase) -> DOX -> Supabase
        """

        print(f"[wroker] starting convertion for job id {job_id}")

        file_byte = self.supabase_client.storage.from_(
            settings.SUPABASE_RAW_BUCKET).download(path=path)
        print(file_byte)


        with tempfile.TemporaryDirectory() as tempdir:
            tempdir = Path(tempdir)

            suffix = Path(path).suffix.lower()

            if suffix != ".pdf":
                raise ConversionFailedError(
                    f"Unsupported input format: {suffix}")
            
            input_pdf = f"input.pdf"
            output_dir = tempdir

            print("Temp input file:", input_pdf)
            print("File size:", len(file_byte))

            input_pdf_path = tempdir / input_pdf
            with open(input_pdf_path, "wb") as f:
                f.write(file_byte)

            start = time.time()
            output_file = self._libreoffice_converter.convert(
                input_path=input_pdf_path,
                output_dir=output_dir,
                target_ext="docx"
            )
            duration = time.time() - start
            print(
                f"[worker] conversion finished for job {job_id} in {duration: .2f}s")

            output_storage_path = path.replace(
                "original.pdf", "converted.docx")

            with open(output_file, "rb") as f:
                self.supabase_client.storage.from_(settings.SUPABASE_CONVERTED_BUCKET).upload(
                    output_storage_path,
                    f,
                    {
                        "content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "x-upsert": "true"
                    },
                )
        print(f"[worker] upload complete for job {job_id}")
