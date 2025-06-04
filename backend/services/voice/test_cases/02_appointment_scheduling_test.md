# Appointment Scheduling Test

## Test Configuration

- **Name**: Appointment Scheduling Test
- **Type**: Chat
- **Attempts**: 2

## Test Script

```
You are a user who wants to set up regular check-ins for anxiety management.

[Goals]
Schedule weekly mental health check-ins at a specific time.

[Interaction Steps]
1. Ask to schedule weekly anxiety check-ins
2. Specify you prefer Monday afternoons around 2 PM
3. Request confirmation of the schedule details
4. Ask to see your current scheduled appointments

[Personality]
Organized, specific about preferences, wants clear confirmation.

[Expected Tools Usage]
- create_schedule_appointment
- list_user_schedules
- check_user_availability
```

## Success Rubric

```
1. The assistant creates a schedule appointment successfully
2. The assistant confirms the specific time and frequency requested
3. The assistant can list back the created schedule
4. The scheduling includes proper timezone handling
5. The assistant provides clear next steps
```

## What This Tests

- **Scheduling Integration**: Connection with scheduling service API
- **User Preferences**: Handling specific time/frequency requests
- **Confirmation Process**: Clear communication of schedule details
- **Database Operations**: Successful CRUD operations on schedules
- **Timezone Handling**: Proper time zone management

## Expected Flow

1. User requests weekly check-ins
2. User specifies Monday 2 PM preference
3. Assistant creates schedule using tools
4. Assistant confirms details back to user
5. User can view their created schedule
6. Schedule is properly stored in database
