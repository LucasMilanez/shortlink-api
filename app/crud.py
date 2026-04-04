import secrets

from sqlalchemy.orm import Session

from app.models import Click, Link, User


def generate_short_code(length: int = 7) -> str:
    return secrets.token_urlsafe(length)[:length]


def create_user(db: Session, email: str, hashed_password: str) -> User:
    user = User(email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_link(db: Session, target_url: str, owner_id: int) -> Link:
    for _ in range(5):  # retry on collision (unlikely at 7 chars of token_urlsafe)
        code = generate_short_code()
        if not db.query(Link).filter(Link.short_code == code).first():
            link = Link(
                short_code=code, target_url=target_url, owner_id=owner_id
            )
            db.add(link)
            db.commit()
            db.refresh(link)
            return link
    raise RuntimeError("Failed to generate unique short code after 5 attempts")


def get_link_by_code(db: Session, code: str) -> Link | None:
    return db.query(Link).filter(Link.short_code == code).first()


def get_user_links(db: Session, user_id: int) -> list[Link]:
    return (
        db.query(Link)
        .filter(Link.owner_id == user_id)
        .order_by(Link.created_at.desc())
        .all()
    )


def get_link_by_id(db: Session, link_id: int, user_id: int) -> Link | None:
    return (
        db.query(Link)
        .filter(Link.id == link_id, Link.owner_id == user_id)
        .first()
    )


def register_click(
    db: Session, link: Link, user_agent: str | None, referrer: str | None
) -> None:
    link.click_count += 1
    click = Click(link_id=link.id, user_agent=user_agent, referrer=referrer)
    db.add(click)
    db.commit()


def delete_link(db: Session, link: Link) -> None:
    db.delete(link)
    db.commit()
