import { axiosInstance } from "./index";

export interface Contact {
  id: string;
  contact_id: string;
  relationship_type: string;
  is_emergency_contact: boolean;
  created_at: string;
  updated_at: string;
  user_profile?: {
    email: string;
    full_name?: string;
  };
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
    axiosInstance.get("/safety_network").then((res) => res.data),

  // Add contact to safety network
  addContact: (data: AddContactPayload) =>
    axiosInstance
      .post("/safety_network/contacts", data)
      .then((res) => res.data),

  // Remove contact from safety network
  removeContact: (contactId: string) =>
    axiosInstance
      .delete(`/safety_network/contacts/${contactId}`)
      .then((res) => res.data),

  // Get emergency contacts
  getEmergencyContacts: () =>
    axiosInstance
      .get("/safety_network/emergency-contacts")
      .then((res) => res.data),

  // Update emergency contact status
  updateEmergencyContact: (
    contactId: string,
    data: UpdateEmergencyContactPayload
  ) =>
    axiosInstance
      .put(`/safety_network/emergency-contacts/${contactId}`, data)
      .then((res) => res.data),
};
