import httpx
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class GoogleOAuthClient:
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    VALID_ISSUERS = {"https://accounts.google.com", "accounts.google.com"}

    async def fetch_userinfo(self, access_token: str) -> dict:
        logger.info(
            "Google user fetch attempted",
            extra={
                "stage": "fetch_google_user_attempt"
            }
        )
        async with httpx.AsyncClient() as client:
            reponse = await client.get(
                self.USERINFO_URL,
                headers={
                    "Authorization": f"Bearer {access_token}"
                }
            )

        if reponse.status_code != 200:
            logger.warning(
                "Failed to fetch google user",
                extra={
                    "stage": "google_user_fetch_error"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to fetch Google user info"
            )

        return reponse.json()

    def validate_user(self, iss: str):
        if iss not in self.VALID_ISSUERS:
            logger.warning(
                "Google user not in valid issuers",
                extra={
                    "stage": "google_user_not_in_valid_issuers"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google authentication failed.")
