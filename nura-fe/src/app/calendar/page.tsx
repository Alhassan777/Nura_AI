"use client";
import { useState, useMemo, useCallback } from "react";
import dayjs, { Dayjs } from "dayjs";
import { WEEKDAYS } from "@/constants/calendar";
import { CalendarHeader } from "@/components/calendar/CalendarHeader";
import { CalendarDay } from "@/components/calendar/CalendarDay";
import { Reflection } from "@/types/reflection";
import { useGetReflections } from "@/services/hooks/use-gamification";
import {
  useSchedulingEvents,
  useCreateEvent,
} from "@/services/hooks/use-scheduling";
import {
  Spin,
  Button,
  Modal,
  Form,
  Input,
  DatePicker,
  Select,
  Typography,
  Card,
  Space,
  Tag,
} from "antd";
import { useAuth } from "@/contexts/AuthContext";
import { User } from "@supabase/supabase-js";
import {
  Plus,
  Clock,
  Heart,
  Target,
  Users,
  Video,
  Calendar as CalendarIcon,
} from "lucide-react";

interface CalendarReflectionsMap {
  [key: string]: Reflection[];
}

interface ScheduleEvent {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  type:
    | "wellness_check"
    | "therapy_session"
    | "meditation"
    | "exercise"
    | "self_care"
    | "nura_session"
    | "safety_network_checkup";
  description?: string;
  status: "scheduled" | "completed" | "cancelled";
}

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

export default function CalendarPage() {
  const today = dayjs();
  const [viewMonth, setViewMonth] = useState(today.month());
  const [viewYear, setViewYear] = useState(today.year());
  const [showEventModal, setShowEventModal] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Dayjs | null>(null);
  const [showBookingModal, setShowBookingModal] = useState(false);
  const [bookingType, setBookingType] = useState<"nura" | "safety_network">(
    "nura"
  );

  const { user } = useAuth();
  const [form] = Form.useForm();
  const [bookingForm] = Form.useForm();

  // Main store for all reflections - an array of StoredReflection objects
  const { data: reflections, isLoading: isLoadingReflections } =
    useGetReflections();
  const { data: events, isLoading: isLoadingEvents } = useSchedulingEvents();
  const { mutate: createEvent, isPending: isCreatingEvent } = useCreateEvent();

  const calendarViewReflections = useMemo(() => {
    if (!reflections) return {};
    return reflections?.reduce((acc, reflection) => {
      const dateKey = dayjs(reflection.created_at).format("YYYY-MM-DD");
      acc[dateKey] = [...(acc[dateKey] || []), reflection];
      return acc;
    }, {} as CalendarReflectionsMap);
  }, [reflections]);

  const calendarMatrix = useMemo(() => {
    const firstDayOfMonth = dayjs()
      .year(viewYear)
      .month(viewMonth)
      .startOf("month");
    const lastDayOfMonth = dayjs()
      .year(viewYear)
      .month(viewMonth)
      .endOf("month");
    const firstDayOfWeek = firstDayOfMonth.day();
    const daysInMonth = lastDayOfMonth.date();
    const matrix: (Dayjs | null)[][] = [];
    let currentWeek: (Dayjs | null)[] = [];
    for (let i = 0; i < firstDayOfWeek; i++) currentWeek.push(null);
    for (let day = 1; day <= daysInMonth; day++) {
      currentWeek.push(dayjs().year(viewYear).month(viewMonth).date(day));
      if (currentWeek.length === 7) {
        matrix.push(currentWeek);
        currentWeek = [];
      }
    }
    while (currentWeek.length > 0 && currentWeek.length < 7)
      currentWeek.push(null);
    if (currentWeek.length > 0) matrix.push(currentWeek);
    return matrix;
  }, [viewMonth, viewYear, reflections]);

  const handlePrevMonth = useCallback(() => {
    if (viewMonth === 0) {
      setViewMonth(11);
      setViewYear(viewYear - 1);
    } else {
      setViewMonth(viewMonth - 1);
    }
  }, [viewMonth, viewYear]);

  const handleNextMonth = useCallback(() => {
    if (viewMonth === 11) {
      setViewMonth(0);
      setViewYear(viewYear + 1);
    } else {
      setViewMonth(viewMonth + 1);
    }
  }, [viewMonth, viewYear]);

  const handleToday = useCallback(() => {
    setViewMonth(today.month());
    setViewYear(today.year());
  }, [today]);

  const handleCreateEvent = (values: any) => {
    const eventData = {
      ...values,
      start_time:
        selectedDate?.format("YYYY-MM-DD") + "T" + values.start_time + ":00",
      end_time:
        selectedDate?.format("YYYY-MM-DD") + "T" + values.end_time + ":00",
    };
    createEvent(eventData);
    setShowEventModal(false);
    form.resetFields();
  };

  const handleBookAppointment = (values: any) => {
    const appointmentData = {
      title:
        bookingType === "nura"
          ? `Nura ${values.sessionType || "Wellness Session"}`
          : `Safety Network Checkup - ${values.contact}`,
      type: bookingType === "nura" ? "nura_session" : "safety_network_checkup",
      start_time: values.datetime.format("YYYY-MM-DD HH:mm:ss"),
      end_time: values.datetime
        .add(values.duration || 30, "minute")
        .format("YYYY-MM-DD HH:mm:ss"),
      description: values.notes || values.message || "",
      status: "scheduled",
    };

    createEvent(appointmentData);
    setShowBookingModal(false);
    bookingForm.resetFields();
  };

  const handleDateClick = (date: Dayjs) => {
    setSelectedDate(date);
    setShowEventModal(true);
  };

  const getEventTypeColor = (type: string) => {
    switch (type) {
      case "wellness_check":
        return "blue";
      case "therapy_session":
        return "purple";
      case "meditation":
        return "green";
      case "exercise":
        return "orange";
      case "self_care":
        return "pink";
      case "nura_session":
        return "purple";
      case "safety_network_checkup":
        return "blue";
      default:
        return "default";
    }
  };

  const getEventTypeIcon = (type: string) => {
    switch (type) {
      case "wellness_check":
        return <Heart className="h-3 w-3" />;
      case "therapy_session":
        return <Target className="h-3 w-3" />;
      case "meditation":
        return <Clock className="h-3 w-3" />;
      case "exercise":
        return <Target className="h-3 w-3" />;
      case "self_care":
        return <Heart className="h-3 w-3" />;
      case "nura_session":
        return <Heart className="h-3 w-3" />;
      case "safety_network_checkup":
        return <Users className="h-3 w-3" />;
      default:
        return <Clock className="h-3 w-3" />;
    }
  };

  // Group events by date
  const eventsByDate = useMemo(() => {
    if (!events) return {};
    return events.reduce((acc: any, event: any) => {
      const dateKey = dayjs(event.start_time).format("YYYY-MM-DD");
      acc[dateKey] = [...(acc[dateKey] || []), event];
      return acc;
    }, {});
  }, [events]);

  if (isLoadingReflections || isLoadingEvents) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <CalendarIcon className="h-8 w-8 text-indigo-600" />
          <Title level={2} className="!mb-0">
            Calendar & Scheduling
          </Title>
        </div>
        <Button
          type="primary"
          icon={<Plus className="h-4 w-4" />}
          onClick={() => setShowEventModal(true)}
        >
          Add Event
        </Button>
      </div>

      {/* Quick Booking Actions */}
      <Card>
        <div className="mb-4">
          <Title level={4} className="flex items-center gap-2 !mb-2">
            <CalendarIcon className="h-5 w-5" />
            Quick Appointment Booking
          </Title>
          <Text className="text-gray-600">
            Schedule wellness sessions with Nura or checkups with your safety
            network
          </Text>
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          {/* Book with Nura */}
          <div className="p-4 border rounded-lg hover:shadow-md transition-shadow border-purple-200 bg-purple-50">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-purple-100 rounded-full">
                <Heart className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <h3 className="font-medium text-purple-800">
                  Book Session with Nura
                </h3>
                <p className="text-sm text-purple-600">
                  Schedule a dedicated wellness session
                </p>
              </div>
            </div>
            <Button
              type="primary"
              className="w-full bg-purple-600 hover:bg-purple-700 border-purple-600"
              onClick={() => {
                setBookingType("nura");
                setShowBookingModal(true);
              }}
            >
              Schedule Nura Session
            </Button>
          </div>

          {/* Book with Safety Network */}
          <div className="p-4 border rounded-lg hover:shadow-md transition-shadow border-blue-200 bg-blue-50">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-blue-100 rounded-full">
                <Users className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <h3 className="font-medium text-blue-800">
                  Book Safety Network Checkup
                </h3>
                <p className="text-sm text-blue-600">
                  Schedule time with trusted contacts
                </p>
              </div>
            </div>
            <Button
              type="default"
              className="w-full border-blue-300 text-blue-700 hover:border-blue-400"
              onClick={() => {
                setBookingType("safety_network");
                setShowBookingModal(true);
              }}
            >
              Schedule Checkup
            </Button>
          </div>
        </div>
      </Card>

      {/* Calendar Component */}
      <Card>
        <div className="calendar">
          <CalendarHeader
            viewMonth={viewMonth}
            viewYear={viewYear}
            onPrevMonth={handlePrevMonth}
            onNextMonth={handleNextMonth}
            onToday={handleToday}
          />

          <div className="grid grid-cols-7 gap-1 mt-4">
            {WEEKDAYS.map((day) => (
              <div
                key={day}
                className="p-2 text-center text-xs font-medium text-gray-500 bg-gray-50"
              >
                {day}
              </div>
            ))}
          </div>

          <div className="grid grid-cols-7 gap-1">
            {calendarMatrix.flat().map((date, index) => {
              if (!date) {
                return <div key={index} className="min-h-32"></div>;
              }
              return (
                <CalendarDay
                  key={index}
                  date={date}
                  isCurrentMonth={date.month() === viewMonth}
                  reflections={
                    calendarViewReflections[date.format("YYYY-MM-DD")] || []
                  }
                  user={user as any}
                />
              );
            })}
          </div>
        </div>
      </Card>

      {/* Event Creation Modal */}
      <Modal
        title={`Add Event - ${selectedDate?.format("MMMM D, YYYY")}`}
        open={showEventModal}
        onCancel={() => {
          setShowEventModal(false);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateEvent}>
          <Form.Item
            name="title"
            label="Event Title"
            rules={[{ required: true, message: "Please enter event title" }]}
          >
            <Input placeholder="Enter event title" />
          </Form.Item>

          <div className="grid grid-cols-2 gap-4">
            <Form.Item
              name="type"
              label="Event Type"
              rules={[{ required: true, message: "Please select event type" }]}
            >
              <Select placeholder="Select event type">
                <Option value="wellness_check">Wellness Check</Option>
                <Option value="therapy_session">Therapy Session</Option>
                <Option value="meditation">Meditation</Option>
                <Option value="exercise">Exercise</Option>
                <Option value="self_care">Self Care</Option>
                <Option value="nura_session">Nura Session</Option>
                <Option value="safety_network_checkup">
                  Safety Network Checkup
                </Option>
              </Select>
            </Form.Item>

            <Form.Item name="description" label="Description">
              <Input placeholder="Optional description" />
            </Form.Item>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Form.Item
              name="start_time"
              label="Start Time"
              rules={[{ required: true, message: "Please select start time" }]}
            >
              <Select placeholder="Start time">
                {Array.from({ length: 24 }, (_, i) => (
                  <Option key={i} value={`${i.toString().padStart(2, "0")}:00`}>
                    {`${i.toString().padStart(2, "0")}:00`}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              name="end_time"
              label="End Time"
              rules={[{ required: true, message: "Please select end time" }]}
            >
              <Select placeholder="End time">
                {Array.from({ length: 24 }, (_, i) => (
                  <Option key={i} value={`${i.toString().padStart(2, "0")}:00`}>
                    {`${i.toString().padStart(2, "0")}:00`}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </div>

          <div className="flex justify-end gap-2">
            <Button onClick={() => setShowEventModal(false)}>Cancel</Button>
            <Button type="primary" htmlType="submit" loading={isCreatingEvent}>
              Create Event
            </Button>
          </div>
        </Form>
      </Modal>

      {/* Appointment Booking Modal */}
      <Modal
        title={
          <div className="flex items-center gap-2">
            {bookingType === "nura" ? (
              <Heart className="h-5 w-5 text-purple-600" />
            ) : (
              <Users className="h-5 w-5 text-blue-600" />
            )}
            <span>
              {bookingType === "nura"
                ? "Schedule Session with Nura"
                : "Schedule Safety Network Checkup"}
            </span>
          </div>
        }
        open={showBookingModal}
        onCancel={() => {
          setShowBookingModal(false);
          bookingForm.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={bookingForm}
          layout="vertical"
          onFinish={handleBookAppointment}
        >
          {bookingType === "nura" ? (
            <>
              <div className="bg-purple-50 p-4 rounded-lg mb-6">
                <h4 className="font-medium text-purple-800 mb-2">
                  Nura Wellness Session
                </h4>
                <p className="text-sm text-purple-700">
                  Schedule a dedicated one-on-one session with Nura for deeper
                  emotional support, goal setting, or working through specific
                  challenges.
                </p>
              </div>

              <Form.Item
                name="sessionType"
                label="Session Type"
                rules={[
                  { required: true, message: "Please select session type" },
                ]}
              >
                <Select placeholder="Choose session type">
                  <Option value="general">General Wellness Check</Option>
                  <Option value="crisis_followup">Crisis Follow-up</Option>
                  <Option value="goal_setting">Goal Setting & Planning</Option>
                  <Option value="therapy_support">Therapeutic Support</Option>
                  <Option value="mindfulness">Mindfulness & Meditation</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="datetime"
                label="Preferred Date & Time"
                rules={[
                  { required: true, message: "Please select date and time" },
                ]}
              >
                <DatePicker
                  showTime={{ format: "HH:mm" }}
                  format="YYYY-MM-DD HH:mm"
                  className="w-full"
                  placeholder="Select appointment time"
                  disabledDate={(current) =>
                    current && current < dayjs().startOf("day")
                  }
                />
              </Form.Item>

              <div className="grid grid-cols-2 gap-4">
                <Form.Item
                  name="sessionFormat"
                  label="Session Format"
                  rules={[{ required: true, message: "Please select format" }]}
                >
                  <Select placeholder="Choose format">
                    <Option value="voice">Voice Call</Option>
                    <Option value="text">Text Chat</Option>
                    <Option value="video">Video Call (if available)</Option>
                  </Select>
                </Form.Item>

                <Form.Item
                  name="duration"
                  label="Duration (minutes)"
                  rules={[
                    { required: true, message: "Please select duration" },
                  ]}
                >
                  <Select placeholder="Duration">
                    <Option value={15}>15 minutes</Option>
                    <Option value={30}>30 minutes</Option>
                    <Option value={45}>45 minutes</Option>
                    <Option value={60}>60 minutes</Option>
                  </Select>
                </Form.Item>
              </div>

              <Form.Item name="notes" label="Notes (Optional)">
                <TextArea
                  rows={3}
                  placeholder="Any specific topics you'd like to discuss or prepare for..."
                />
              </Form.Item>
            </>
          ) : (
            <>
              <div className="bg-blue-50 p-4 rounded-lg mb-6">
                <h4 className="font-medium text-blue-800 mb-2">
                  Safety Network Checkup
                </h4>
                <p className="text-sm text-blue-700">
                  Schedule a wellness check with someone from your safety
                  network. This can be a casual chat or a more structured
                  check-in.
                </p>
              </div>

              <Form.Item
                name="contact"
                label="Select Contact"
                rules={[{ required: true, message: "Please select a contact" }]}
              >
                <Select placeholder="Choose from your safety network">
                  <Option value="mom">Mom - Emergency Contact</Option>
                  <Option value="sarah">Sarah Johnson - Close Friend</Option>
                  <Option value="therapist">Dr. Mitchell - Therapist</Option>
                  <Option value="brother">Alex - Brother</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="checkupType"
                label="Checkup Type"
                rules={[
                  { required: true, message: "Please select checkup type" },
                ]}
              >
                <Select placeholder="Choose checkup type">
                  <Option value="casual">Casual Check-in</Option>
                  <Option value="structured">Structured Wellness Review</Option>
                  <Option value="crisis_support">Crisis Support Session</Option>
                  <Option value="family_meeting">Family Support Meeting</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="datetime"
                label="Preferred Date & Time"
                rules={[
                  { required: true, message: "Please select date and time" },
                ]}
              >
                <DatePicker
                  showTime={{ format: "HH:mm" }}
                  format="YYYY-MM-DD HH:mm"
                  className="w-full"
                  placeholder="When would you like to connect?"
                  disabledDate={(current) =>
                    current && current < dayjs().startOf("day")
                  }
                />
              </Form.Item>

              <div className="grid grid-cols-2 gap-4">
                <Form.Item
                  name="duration"
                  label="Duration (minutes)"
                  rules={[
                    { required: true, message: "Please select duration" },
                  ]}
                >
                  <Select placeholder="Duration">
                    <Option value={15}>15 minutes</Option>
                    <Option value={30}>30 minutes</Option>
                    <Option value={60}>1 hour</Option>
                    <Option value={120}>2 hours</Option>
                  </Select>
                </Form.Item>

                <Form.Item
                  name="communicationMethod"
                  label="Communication Method"
                  rules={[{ required: true, message: "Please select method" }]}
                >
                  <Select placeholder="How to connect">
                    <Option value="phone">Phone Call</Option>
                    <Option value="video">Video Call</Option>
                    <Option value="in_person">In Person</Option>
                    <Option value="text">Text Messages</Option>
                  </Select>
                </Form.Item>
              </div>

              <Form.Item name="message" label="Message to Contact">
                <TextArea
                  rows={3}
                  placeholder="Hi [Name], I'd like to schedule a wellness check-in with you. Would you be available..."
                />
              </Form.Item>
            </>
          )}

          <div className="flex justify-end gap-2 mt-6">
            <Button onClick={() => setShowBookingModal(false)}>Cancel</Button>
            <Button type="primary" htmlType="submit" loading={isCreatingEvent}>
              Book Appointment
            </Button>
          </div>
        </Form>
      </Modal>
    </div>
  );
}
