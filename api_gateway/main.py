from fastapi import FastAPI, Response, status

app = FastAPI(
    title="DocMe",
    description="A Document Converter from one file type to another!",
    version="1.0.0",
    contact={
        "name": "Charan T M",
        "url": "https://www.linkedin.com/in/charantm/",
        "email": "charanntm.dev@gmail.com"
    }

)


@app.get("/favicon.ico")
def health_route():
    return Response(status_code=status.HTTP_200_OK)
