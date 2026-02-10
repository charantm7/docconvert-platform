from uuid import uuid4


def build_storage_path(user_id: str, filename: str) -> str:
    ext = filename.split(".")[-1]
    job_id = str(uuid4())
    return f"{user_id}/{job_id}/original.{ext}", job_id
