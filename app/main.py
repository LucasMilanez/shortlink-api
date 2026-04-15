from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import auth, crud, schemas
from app.database import Base, engine, get_db
from app.models import User


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="ShortLink API",
    description=(
        "URL shortener with click analytics. JWT-authenticated, "
        "per-user link ownership, and redirect tracking."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["Meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


# ---------- Auth ----------


@app.post(
    "/auth/register",
    response_model=schemas.UserOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Auth"],
)
def register(
    payload: schemas.UserCreate,
    db: Annotated[Session, Depends(get_db)],
):
    if crud.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    hashed = auth.hash_password(payload.password)
    return crud.create_user(db, email=payload.email, hashed_password=hashed)


@app.post("/auth/login", response_model=schemas.Token, tags=["Auth"])
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    user = crud.get_user_by_email(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = auth.create_access_token(sub=str(user.id))
    return schemas.Token(access_token=token)


# ---------- Links (authenticated) ----------


@app.post(
    "/links",
    response_model=schemas.LinkOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Links"],
)
def create_link(
    payload: schemas.LinkCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(auth.get_current_user)],
):
    return crud.create_link(
        db, target_url=str(payload.target_url), owner_id=current_user.id
    )


@app.get("/links", response_model=list[schemas.LinkOut], tags=["Links"])
def list_links(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(auth.get_current_user)],
):
    return crud.get_user_links(db, user_id=current_user.id)


@app.get(
    "/links/{link_id}/stats",
    response_model=schemas.LinkStats,
    tags=["Links"],
)
def link_stats(
    link_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(auth.get_current_user)],
):
    link = crud.get_link_by_id(db, link_id=link_id, user_id=current_user.id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    recent = [
        c.clicked_at
        for c in sorted(link.clicks, key=lambda x: x.clicked_at, reverse=True)[:20]
    ]
    return schemas.LinkStats(
        short_code=link.short_code,
        target_url=link.target_url,
        click_count=link.click_count,
        created_at=link.created_at,
        recent_clicks=recent,
    )


@app.delete(
    "/links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Links"],
)
def delete_link(
    link_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(auth.get_current_user)],
):
    link = crud.get_link_by_id(db, link_id=link_id, user_id=current_user.id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    crud.delete_link(db, link)


# ---------- Public redirect ----------


@app.get("/r/{short_code}", tags=["Redirect"])
def redirect(
    short_code: str,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    link = crud.get_link_by_code(db, code=short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    crud.register_click(
        db,
        link,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer"),
    )
    return RedirectResponse(url=link.target_url, status_code=307)
