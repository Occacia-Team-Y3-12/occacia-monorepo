# Vendor Registration Form - Advanced Client-Side Validation

## Overview
This implementation provides a complete vendor registration form with advanced client-side validation, real-time error feedback, and TypeScript type safety. The form is built using React + Next.js App Router with Tailwind CSS styling.

## Features Implemented

### ✅ Core Validation Requirements
- **Required Field Validation**: All fields display inline errors when empty
- **Password Matching**: Confirms that password and confirm password fields match
- **Email Format Validation**: Uses regex to validate email format (account email and business email)
- **NIC Number Validation**: Validates Sri Lankan NIC format (9 digits + letter or 12 digits)
- **Conditional Organization Fields**:
  - If "Join Existing Organization" → organization code is required
  - If "Create New Organization" → all KYM business fields are required
- **Error Display**: Errors appear below each input field in red text
- **Submit Button Disabled State**: Button remains disabled until form is completely valid
- **Two-Step Form**: Separates account details from organization details

### ✅ UI/UX Enhancements
- **Dynamic Border Colors**: Input borders turn red when there are validation errors
- **Real-Time Validation**: Errors trigger as user types (onChange validation)
- **Tailwind Styling**: Uses existing project color scheme (`#1e88e5`, `#2c3e50`, etc.)
- **Step Navigation**: Back button allows navigation between form steps
- **Accessibility**: Proper form structure and semantic HTML

### ✅ Code Architecture
- **TypeScript Types** (`VendorFormData`): Strongly typed form state
- **Reusable Validation Logic**: Decoupled validation functions in `@/lib/validation.ts`
- **Clean State Management**: Single source of truth using React hooks
- **Proper Error State**: Partial type for errors keyed by field names

## File Structure

### 1. **Component File**
📁 `src/app/(auth)/vendor/register.page.tsx` (508 lines)

Key features:
- Two-step form with "Account" and "Organization" steps
- State management for form data, errors, and validity flags
- Real-time onChange validation
- useEffect hooks for dependency tracking

### 2. **Validation Library**
📁 `src/lib/validation.ts` (121 lines)

Exports:
- `VendorFormData` - TypeScript interface for form state
- `emailRegex` - Email format validation regex
- `nicRegex` - NIC format validation regex
- `validateVendorField()` - Per-field validation logic
- `isVendorAccountValid()` - Validates entire account step
- `isVendorFinalValid()` - Validates entire organization step

## Validation Rules

### Account Step (Page 1)

| Field | Validation |
|-------|-----------|
| Username | Required, non-empty |
| Full Name | Required, non-empty |
| Email | Required, must match email regex |
| Password | Required, non-empty |
| Confirm Password | Required, must match password |
| Address | Required, non-empty |
| NIC Number | Required, must match NIC regex (9+letter or 12 digits) |
| Gender | Required, one of: male/female/other |

### Organization Step (Page 2)

**If "Join Existing Organization":**
- Organization Code: Required, non-empty

**If "Create New Organization":**
- Business Name: Required, non-empty
- Business Reg Number: Required, non-empty
- Business Address: Required, non-empty
- Business Phone: Required, non-empty
- Business Email: Required, must match email regex

## How It Works

### 1. Form Initialization
```typescript
const [formData, setFormData] = useState<VendorFormData>({...})
const [errors, setErrors] = useState<Partial<Record<keyof VendorFormData, string>>>({})
const [isAccountValid, setIsAccountValid] = useState(false)
const [isFinalValid, setIsFinalValid] = useState(false)
```

### 2. On User Input
```typescript
const handleChange = (e) => {
  setFormData((prev) => {
    const updated = { ...prev, [name]: value } as VendorFormData
    validateField(name, value, updated) // validate immediately
    return updated
  })
}
```

### 3. Validity Tracking
```typescript
useEffect(() => {
  setIsAccountValid(isAccountStepValid(formData))
}, [formData.username, formData.fullName, ...])
```

### 4. Form Submission
- Prevents submission if form is invalid
- Triggers validation for all fields on submit attempt
- Displays errors for missing/invalid fields
- Only proceeds to next step or submits API call if valid

## Error Styling

Using Tailwind CSS with dynamic class binding:
```tsx
className={`border ${
  errors.email ? 'border-red-500' : 'border-[#d1dce5]'
}`}
```

Error messages:
```tsx
{errors.email && (
  <p className="text-red-600 text-sm mt-1">{errors.email}</p>
)}
```

## Backend Integration Ready

The validation logic is:
- ✅ Reusable in hooks or utility functions
- ✅ Exportable for backend validation mirrors
- ✅ Error messages consistent with backend requirements
- ✅ Ready for API integration with minimal changes

Example backend validation pattern:
```typescript
// Reuse same validateVendorField in API route
const errors = {}
Object.keys(formData).forEach(field => {
  const error = validateVendorField(field, formData[field], formData, orgChoice)
  if (error) errors[field] = error
})
```

## Testing the Form

### Test Scenarios

1. **Submit Empty Form**
   - All fields show red borders and error messages

2. **Enter Invalid Email**
   - Email error: "Invalid email format"

3. **Enter Mismatched Passwords**
   - Both password fields show error: "Passwords do not match"

4. **Enter Invalid NIC**
   - NIC error: "Invalid NIC number"

5. **Select "Join Organization" without code**
   - Organization code shows required error
   - Submit button disabled

6. **Select "Create Organization" without business details**
   - All business fields show required errors
   - Submit button disabled

7. **Fill all fields correctly**
   - All borders turn normal color
   - All error messages disappear
   - Submit buttons become enabled
   - Can navigate to next step

## Browser Support

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Mobile browsers (responsive)

## Performance

- Real-time validation without debouncing (field-level is fast)
- No external validation libraries (pure JavaScript)
- Efficient error state updates with partial record type
- Minimal re-renders using dependency arrays

## Future Enhancements

Potential add-ons for production:
1. Debounced validation for NIC/Email uniqueness checks
2. Server-side validation mirroring validation.ts logic
3. Progressive form saving to localStorage
4. Multi-language error messages
5. Async organization code lookup
6. Business registration number verification API

## Files Modified/Created

| File | Status | Change |
|------|--------|--------|
| `src/app/(auth)/vendor/register.page.tsx` | Modified | Complete rewrite with validation |
| `src/lib/validation.ts` | Created | Shared validation utilities |

## Importing the Validation Library

In other components:
```typescript
import {
  VendorFormData,
  validateVendorField,
  isVendorAccountValid,
  isVendorFinalValid,
  emailRegex,
  nicRegex
} from '@/lib/validation'
```

This is ready for use in customer registration, profile updates, or any other forms requiring validation logic.
