import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

// Mock API functions - these would be replaced with actual API calls
const schedulingApi = {
  getEvents: async () => {
    // Mock data
    return Array.from({ length: 8 }, (_, i) => ({
      id: `event-${i + 1}`,
      title: `Event ${i + 1}`,
      start_time: new Date(
        Date.now() +
          i * 24 * 60 * 60 * 1000 +
          Math.random() * 8 * 60 * 60 * 1000
      ).toISOString(),
      end_time: new Date(
        Date.now() +
          i * 24 * 60 * 60 * 1000 +
          Math.random() * 8 * 60 * 60 * 1000 +
          60 * 60 * 1000
      ).toISOString(),
      type: [
        "wellness_check",
        "therapy_session",
        "meditation",
        "exercise",
        "self_care",
      ][Math.floor(Math.random() * 5)],
      description: `Description for event ${i + 1}`,
      reminder_minutes: [15, 30, 60][Math.floor(Math.random() * 3)],
      status: ["scheduled", "completed", "cancelled"][
        Math.floor(Math.random() * 3)
      ],
      created_at: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString(),
    }));
  },

  createEvent: async (event: any) => {
    return {
      id: `event-${Date.now()}`,
      ...event,
      created_at: new Date().toISOString(),
      status: "scheduled",
    };
  },

  updateEvent: async (event: any) => {
    return event;
  },

  deleteEvent: async (eventId: string) => {
    return { success: true };
  },

  getEvent: async (eventId: string) => {
    return {
      id: eventId,
      title: `Event ${eventId}`,
      start_time: new Date().toISOString(),
      end_time: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
      type: "wellness_check",
      description: "Event description",
      reminder_minutes: 15,
      status: "scheduled",
      created_at: new Date().toISOString(),
    };
  },

  getAvailableSlots: async (date: string) => {
    return ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"];
  },
};

export const useSchedulingEvents = () => {
  return useQuery({
    queryKey: ["scheduling", "events"],
    queryFn: schedulingApi.getEvents,
  });
};

export const useCreateEvent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: schedulingApi.createEvent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduling", "events"] });
    },
  });
};

export const useUpdateEvent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: schedulingApi.updateEvent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduling", "events"] });
    },
  });
};

export const useDeleteEvent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: schedulingApi.deleteEvent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduling", "events"] });
    },
  });
};

export const useEvent = (eventId: string) => {
  return useQuery({
    queryKey: ["scheduling", "events", eventId],
    queryFn: () => schedulingApi.getEvent(eventId),
    enabled: !!eventId,
  });
};

export const useAvailableSlots = (date: string) => {
  return useQuery({
    queryKey: ["scheduling", "slots", date],
    queryFn: () => schedulingApi.getAvailableSlots(date),
    enabled: !!date,
  });
};
