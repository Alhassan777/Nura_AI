import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  safetyNetworkApi,
  AddContactPayload,
  UpdateEmergencyContactPayload,
} from "../apis/safety-network";

// Get safety network
export const useSafetyNetwork = () => {
  return useQuery({
    queryKey: ["safety-network"],
    queryFn: safetyNetworkApi.getNetwork,
  });
};

// Get emergency contacts
export const useEmergencyContacts = () => {
  return useQuery({
    queryKey: ["emergency-contacts"],
    queryFn: safetyNetworkApi.getEmergencyContacts,
  });
};

// Add contact to safety network
export const useAddContact = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AddContactPayload) => safetyNetworkApi.addContact(data),
    onSuccess: () => {
      // Invalidate safety network queries
      queryClient.invalidateQueries({ queryKey: ["safety-network"] });
      queryClient.invalidateQueries({ queryKey: ["emergency-contacts"] });
    },
  });
};

// Remove contact from safety network
export const useRemoveContact = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (contactId: string) =>
      safetyNetworkApi.removeContact(contactId),
    onSuccess: () => {
      // Invalidate safety network queries
      queryClient.invalidateQueries({ queryKey: ["safety-network"] });
      queryClient.invalidateQueries({ queryKey: ["emergency-contacts"] });
    },
  });
};

// Update emergency contact status
export const useUpdateEmergencyContact = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      contactId,
      data,
    }: {
      contactId: string;
      data: UpdateEmergencyContactPayload;
    }) => safetyNetworkApi.updateEmergencyContact(contactId, data),
    onSuccess: () => {
      // Invalidate safety network queries
      queryClient.invalidateQueries({ queryKey: ["safety-network"] });
      queryClient.invalidateQueries({ queryKey: ["emergency-contacts"] });
    },
  });
};
