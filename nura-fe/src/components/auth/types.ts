export interface SignupFormData {
  fullName: string;
  email: string;
  phoneNumber: string;
  password: string;
  confirmPassword: string;
}
export type USER = Omit<SignupFormData, "confirmPassword" | "password"> & {
  isVerified: boolean;
};