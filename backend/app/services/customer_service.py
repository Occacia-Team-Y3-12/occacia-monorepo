from sqlalchemy.orm import Session

from app.models import Customer


class CustomerService:
    def get_customer_by_email(self, db: Session, email: str) -> Customer | None:
        return db.query(Customer).filter(Customer.email == email).first()


customer_service = CustomerService()