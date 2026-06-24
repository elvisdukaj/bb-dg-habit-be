
### Habit Tracker Backend Web Service Specification

#### Overview
This specification defines a backend web service for a habit tracker application. The service allows users to register and log in, and manage habits by creating, editing, and deleting them.

#### Core Features

##### 1. User Authentication
- Users can register with the service.
- Users can log in with their credentials.
- Authenticated users can access habit management endpoints.

##### 2. Habit Management
Each habit includes:
- `title`: string, required
- `frequency`: enum, required, one of:
  - `daily`
  - `weekly`

Authenticated users can:
- Create a habit
- Edit a habit
- Delete a habit
- List their habits
- View a single habit

---

### Functional Requirements

#### Authentication

##### Register User
- **Endpoint:** `POST /api/auth/register`
- **Description:** Create a new user account.
- **Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```
- **Validation Rules:**
  - Email must be valid and unique.
  - Password must meet minimum security requirements.
- **Response:**
  - `201 Created` on success
  - Returns user ID and success message

##### Login User
- **Endpoint:** `POST /api/auth/login`
- **Description:** Authenticate a user and return an access token.
- **Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```
- **Response:**
  - `200 OK` on success
  - Returns access token
  - `401 Unauthorized` for invalid credentials

#### Habit Endpoints

##### Create Habit
- **Endpoint:** `POST /api/habits`
- **Auth Required:** Yes
- **Request Body:**
```json
{
  "title": "Drink water",
  "frequency": "daily"
}
```
- **Validation Rules:**
  - `title` is required and must be a non-empty string.
  - `frequency` must be either `daily` or `weekly`.
- **Response:**
  - `201 Created`
  - Returns created habit object

##### List Habits
- **Endpoint:** `GET /api/habits`
- **Auth Required:** Yes
- **Response:**
  - `200 OK`
  - Returns array of habits for the authenticated user

##### Get Habit
- **Endpoint:** `GET /api/habits/:id`
- **Auth Required:** Yes
- **Response:**
  - `200 OK` with habit object
  - `404 Not Found` if habit does not exist or does not belong to user

##### Edit Habit
- **Endpoint:** `PUT /api/habits/:id`
- **Auth Required:** Yes
- **Request Body:**
```json
{
  "title": "Read 10 pages",
  "frequency": "weekly"
}
```
- **Validation Rules:**
  - Same as create habit
- **Response:**
  - `200 OK`
  - Returns updated habit object
  - `404 Not Found` if habit does not exist or does not belong to user

##### Delete Habit
- **Endpoint:** `DELETE /api/habits/:id`
- **Auth Required:** Yes
- **Response:**
  - `204 No Content`
  - `404 Not Found` if habit does not exist or does not belong to user

---

### Data Model

#### User
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "passwordHash": "hashed_password",
  "createdAt": "2026-06-24T00:00:00Z"
}
```

#### Habit
```json
{
  "id": "uuid",
  "userId": "uuid",
  "title": "Drink water",
  "frequency": "daily",
  "createdAt": "2026-06-24T00:00:00Z",
  "updatedAt": "2026-06-24T00:00:00Z"
}
```

---

### Non-Functional Requirements
- Passwords must be securely hashed.
- Endpoints must require authentication except registration and login.
- Users may only access their own habits.
- API must return JSON responses.
- Input validation errors should return `400 Bad Request`.
- Unauthorized requests should return `401 Unauthorized`.
- Forbidden or inaccessible resources should not leak other users' data.

### Suggested Future Extensions
- Mark habits as completed
- Track completion history
- Add monthly/custom frequencies
- Password reset and email verification
- Rate limiting for auth endpoints
