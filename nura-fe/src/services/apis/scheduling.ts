import { axiosInstance } from "./index";

export interface ScheduleEvent {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  type: string;
  description?: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface CreateEventPayload {
  title: string;
  start_time: string;
  end_time: string;
  type: string;
  description?: string;
}

export interface UpdateEventPayload {
  title?: string;
  start_time?: string;
  end_time?: string;
  type?: string;
  description?: string;
}

// Scheduling API functions
export const schedulingApi = {
  // Get user schedule/events
  getEvents: () =>
    axiosInstance.get("/scheduling/events").then((res) => res.data),

  // Create new event
  createEvent: (data: CreateEventPayload) =>
    axiosInstance.post("/scheduling/events", data).then((res) => res.data),

  // Update existing event
  updateEvent: (eventId: string, data: UpdateEventPayload) =>
    axiosInstance
      .put(`/scheduling/events/${eventId}`, data)
      .then((res) => res.data),

  // Delete event
  deleteEvent: (eventId: string) =>
    axiosInstance
      .delete(`/scheduling/events/${eventId}`)
      .then((res) => res.data),

  // Get events for specific date range
  getEventsByDateRange: (startDate: string, endDate: string) =>
    axiosInstance
      .get(`/scheduling/events?start_date=${startDate}&end_date=${endDate}`)
      .then((res) => res.data),
};
