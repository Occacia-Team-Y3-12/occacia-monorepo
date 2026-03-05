// reusable validation logic for forms

export type VendorFormData = {
  username: string;
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
  address: string;
  nicNumber: string;
  gender: string;
  organizationCode: string;
  businessName: string;
  businessRegNumber: string;
  businessAddress: string;
  businessPhone: string;
  businessEmail: string;
};

// basic regexes used across the app
export const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
export const nicRegex = /^(\d{9}[vVxX]|\d{12})$/;
export const fullNameRegex = /^[A-Za-z\s]+$/; // letters and spaces only
// strong password: 8+ characters, upper, lower, number, special
export const strongPasswordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{8,}$/;

// field-level validator returns error message or empty string
export function validateVendorField(
  name: keyof VendorFormData,
  value: string,
  data: VendorFormData,
  orgChoice: 'join' | 'create' | ''
): string {
  let error = '';
  switch (name) {
    case 'username':
      if (!value.trim()) error = 'Username is required';
      break;
    case 'fullName':
      if (!value.trim()) error = 'Full name is required';
      else if (!fullNameRegex.test(value))
        error = 'Full name can contain only letters';
      break;
    case 'email':
      if (!value.trim()) error = 'Email is required';
      else if (!emailRegex.test(value)) error = 'Invalid email format';
      break;
    case 'password':
      if (!value) error = 'Password is required';
      else if (!strongPasswordRegex.test(value))
        error =
          'Password must be at least 8 characters and include uppercase, lowercase, number, and special character';
      else if (data.confirmPassword && data.confirmPassword !== value)
        error = 'Passwords do not match';
      break;
    case 'confirmPassword':
      if (!value) error = 'Please confirm your password';
      else if (data.password && data.password !== value)
        error = 'Passwords do not match';
      break;
    case 'address':
      if (!value.trim()) error = 'Address is required';
      break;
    case 'nicNumber':
      if (!value.trim()) error = 'NIC number is required';
      else if (!nicRegex.test(value)) error = 'Invalid NIC number';
      break;
    case 'gender':
      if (!value) error = 'Gender is required';
      break;
    case 'organizationCode':
      if (orgChoice === 'join' && !value.trim())
        error = 'Organization code is required';
      break;
    case 'businessName':
      if (orgChoice === 'create' && !value.trim())
        error = 'Business name is required';
      break;
    case 'businessRegNumber':
      if (orgChoice === 'create' && !value.trim())
        error = 'Registration number is required';
      break;
    case 'businessAddress':
      if (orgChoice === 'create' && !value.trim())
        error = 'Business address is required';
      break;
    case 'businessPhone':
      if (orgChoice === 'create' && !value.trim())
        error = 'Business phone is required';
      break;
    case 'businessEmail':
      if (orgChoice === 'create') {
        if (!value.trim()) error = 'Business email is required';
        else if (!emailRegex.test(value)) error = 'Invalid email format';
      }
      break;
  }
  return error;
}

export function isVendorAccountValid(data: VendorFormData): boolean {
  return (
    data.username.trim() !== '' &&
    fullNameRegex.test(data.fullName) &&
    emailRegex.test(data.email) &&
    strongPasswordRegex.test(data.password) &&
    data.password === data.confirmPassword &&
    data.address.trim() !== '' &&
    nicRegex.test(data.nicNumber) &&
    data.gender !== ''
  );
}

export function isVendorFinalValid(
  data: VendorFormData,
  orgChoice: 'join' | 'create' | ''
): boolean {
  if (orgChoice === 'join') {
    return data.organizationCode.trim() !== '';
  }
  if (orgChoice === 'create') {
    return (
      data.businessName.trim() !== '' &&
      data.businessRegNumber.trim() !== '' &&
      data.businessAddress.trim() !== '' &&
      data.businessPhone.trim() !== '' &&
      emailRegex.test(data.businessEmail)
    );
  }
  return false;
}
