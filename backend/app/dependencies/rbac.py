from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from app.dependencies.security import (
    get_current_user
)


def require_role(*roles):

    def role_checker(
        current_user=Depends(
            get_current_user
        )
    ):

        if current_user["role"] not in roles:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        return current_user

    return role_checker