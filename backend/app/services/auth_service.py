from app.schemas.auth import CustomerRegister, VendorRegister

class AuthService:
    def register(self, payload):
        if isinstance(payload, CustomerRegister):
            return self._register_customer(payload)
        if isinstance(payload, VendorRegister):
            return self._register_vendor(payload)
        raise ValueError("Unsupported payload type")

    def _register_customer(self, p: CustomerRegister):
        # common user create + customer row
        return {"message": "customer registered", "email": str(p.email)}

    def _register_vendor(self, p: VendorRegister):
        # common user create + vendor row (approval_status=PENDING)
        return {"message": "vendor registered", "email": str(p.email)}

auth_service = AuthService()