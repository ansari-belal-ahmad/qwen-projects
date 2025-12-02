# Remote Desk

A comprehensive Node.js application for remote desktop control with enhanced features.

## Features

- **Remote Desktop Control**: Control remote desktops with mouse, keyboard, and clipboard operations
- **Real-time Dashboard**: Monitor connected devices and active sessions
- **File Transfer**: Upload and download files between local and remote systems
- **Screen Resolution Management**: Adjust remote desktop screen resolution
- **Session Management**: Start, stop, and monitor remote sessions
- **Admin Panel**: Administrative controls and system monitoring
- **Authentication**: Secure access with token-based authentication
- **API Endpoints**: RESTful API for integration with other systems
- **System Monitoring**: Track server status, uptime, and connections
- **Security Features**: Rate limiting, authentication, and authorization

## API Endpoints

- `GET /` - Main control panel
- `GET /admin` - Administrative panel (requires authentication)
- `GET /api/status` - Get server status
- `GET /api/desktop/info` - Get desktop information (requires authentication)
- `POST /api/desktop/control` - Send control commands (requires authentication)
- `GET /api/sessions` - Get active sessions (requires authentication)

## Authentication

Most API endpoints require a valid authentication token. Use `Bearer demo-token` as the authorization header.

## Installation

1. Clone the repository
2. Install dependencies: `npm install`
3. Start the server: `npm start`

## Usage

1. Start the server: `npm start`
2. Open your browser to `http://localhost:3000`
3. For admin panel, visit `http://localhost:3000/admin` (use token: demo-token)

## Technologies Used

- Node.js
- Express.js
- HTML/CSS/JavaScript
- RESTful API
- WebSockets (planned for future enhancement)