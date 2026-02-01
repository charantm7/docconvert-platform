from fastapi import HTTPException, status
from api_gateway.authentication.config import Oauth2


class TwitterOAuthClient:

    async def fetch_twitter_userinfo(self, token: str) -> dict:
        try:
            user = await Oauth2.oauth.twitter.get(
                "https://api.x.com/2/users/me",
                token=token,
                params={"user.fields": "id,name,username,profile_image_url"}
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Twitter user info not found"
            )

        return user.json()
