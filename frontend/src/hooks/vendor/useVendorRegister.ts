import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ROUTES } from '@/lib/routes';
import {
  VendorFormData,
  isVendorAccountValid,
  isVendorFinalValid,
  validateVendorField,
} from '@/lib/validation';
import { vendorAuthService } from '@/services/vendor/authService';

type VendorStep = 'account' | 'organization';
type OrgChoice = 'join' | 'create' | '';

const ACCOUNT_FIELDS: Array<keyof VendorFormData> = [
  'username',
  'fullName',
  'email',
  'password',
  'confirmPassword',
  'address',
  'nicNumber',
  'gender',
];

const CREATE_ORG_FIELDS: Array<keyof VendorFormData> = [
  'businessName',
  'businessRegNumber',
  'businessAddress',
  'businessPhone',
  'businessEmail',
];

export const useVendorRegister = () => {
  const router = useRouter();
  const [step, setStep] = useState<VendorStep>('account');
  const [orgChoice, setOrgChoice] = useState<OrgChoice>('');
  const [errors, setErrors] = useState<Partial<Record<keyof VendorFormData, string>>>({});
  const [isAccountValid, setIsAccountValid] = useState(false);
  const [isFinalValid, setIsFinalValid] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  const [formData, setFormData] = useState<VendorFormData>({
    username: '',
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    address: '',
    nicNumber: '',
    gender: '',
    organizationCode: '',
    businessName: '',
    businessRegNumber: '',
    businessAddress: '',
    businessPhone: '',
    businessEmail: '',
  });

  const validateField = (name: keyof VendorFormData, value: string, data: VendorFormData = formData) => {
    const error = validateVendorField(name, value, data, orgChoice);
    setErrors((prev) => ({ ...prev, [name]: error }));
    return error;
  };

  useEffect(() => {
    if (orgChoice === 'join') {
      validateField('organizationCode', formData.organizationCode);
    }

    if (orgChoice === 'create') {
      CREATE_ORG_FIELDS.forEach((field) => validateField(field, formData[field]));
    }
  }, [orgChoice]);

  useEffect(() => {
    setIsAccountValid(isVendorAccountValid(formData));
  }, [
    formData.username,
    formData.fullName,
    formData.email,
    formData.password,
    formData.confirmPassword,
    formData.address,
    formData.nicNumber,
    formData.gender,
  ]);

  useEffect(() => {
    setIsFinalValid(isVendorFinalValid(formData, orgChoice));
  }, [
    formData.organizationCode,
    formData.businessName,
    formData.businessRegNumber,
    formData.businessAddress,
    formData.businessPhone,
    formData.businessEmail,
    orgChoice,
  ]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => {
      const updated = { ...prev, [name]: value } as VendorFormData;
      validateField(name as keyof VendorFormData, value, updated);
      return updated;
    });
  };

  const handleAccountSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (isVendorAccountValid(formData)) {
      setStep('organization');
      return;
    }

    ACCOUNT_FIELDS.forEach((field) => validateField(field, formData[field]));
  };

  const handleFinalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError('');

    if (!isVendorFinalValid(formData, orgChoice)) {
      if (orgChoice === 'join') {
        validateField('organizationCode', formData.organizationCode);
      } else if (orgChoice === 'create') {
        CREATE_ORG_FIELDS.forEach((field) => validateField(field, formData[field]));
      }
      return;
    }

    setSubmitting(true);
    try {
      const result = await vendorAuthService.register({
        ...formData,
        organizationType: orgChoice as 'join' | 'create',
      });

      if (result.ok) {
        router.push(
          `${ROUTES.VENDOR.VERIFY_EMAIL}?email=${encodeURIComponent(formData.email)}`
        );
      } else {
        setSubmitError(result.message || result.data?.detail || 'Registration failed. Please try again.');
      }
    } catch {
      setSubmitError('Registration failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return {
    step,
    orgChoice,
    formData,
    errors,
    isAccountValid,
    isFinalValid,
    submitting,
    submitError,
    setStep,
    setOrgChoice,
    handleChange,
    handleAccountSubmit,
    handleFinalSubmit,
  };
};
