import { axiosInstance } from "./index";

export interface Contact {
  id: string;
  contact_user_id?: string;
  relationship_type: string;
  is_emergency_contact: boolean;
  created_at: string;
  updated_at: string;
  full_name?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone_number?: string;
  priority_order: number;
  is_active: boolean;
}

export interface AddContactPayload {
  contact_id: string;
  relationship_type: string;
}

export interface UpdateEmergencyContactPayload {
  is_emergency_contact: boolean;
}

// Safety Network API functions
export const safetyNetworkApi = {
  // Get user's safety network
  getNetwork: () =>
    axiosInstance
      .get("/safety-network/contacts")
      .then((res) => res.data.contacts || []),

  // Add contact to safety network
  addContact: (data: AddContactPayload) =>
    axiosInstance
      .post("/safety-network/contacts", data)
      .then((res) => res.data),

  // Remove contact from safety network
  removeContact: (contactId: string) =>
    axiosInstance
      .delete(`/safety-network/contacts/${contactId}`)
      .then((res) => res.data),

  // Get emergency contacts
  getEmergencyContacts: () =>
    axiosInstance
      .get("/safety-network/contacts?emergency_only=true")
      .then((res) => res.data.contacts || []),

  // Update emergency contact status
  updateEmergencyContact: (
    contactId: string,
    data: UpdateEmergencyContactPayload
  ) =>
    axiosInstance
      .put(`/safety-network/contacts/${contactId}`, data)
      .then((res) => res.data),
};
