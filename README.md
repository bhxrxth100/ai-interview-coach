# AI Interview Coach - Premium Web Application

A modern, professional AI-powered interview coaching platform that helps users prepare for job interviews with realistic practice sessions and personalized feedback.

## Features

### 🔐 Authentication System
- OTP-based email verification
- Secure password management with encryption
- Password recovery with OTP
- Session management

### 🎯 Interview System
- Multiple interview modes (Text-based)
- AI-powered question generation
- Real-time interview timer
- Comprehensive performance analytics

### 📊 Performance Analytics
- Overall score tracking
- Interview performance trends
- Question-wise performance analysis
- Personalized improvement recommendations

### 💼 User Dashboard
- Profile management
- Interview history
- Performance statistics
- AI-generated insights

## Tech Stack

### Frontend
- React.js
- Tailwind CSS
- React Router
- Axios

### Backend
- Node.js
- Express.js
- JWT Authentication
- Nodemailer (OTP)

### Database
- MongoDB
- Mongoose ODM

### AI Integration
- OpenAI API / Gemini API

## Project Structure

```
ai-interview-coach/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── utils/
│   │   └── App.js
│   ├── public/
│   └── package.json
├── backend/
│   ├── models/
│   ├── routes/
│   ├── controllers/
│   ├── middleware/
│   ├── utils/
│   ├── config/
│   └── server.js
├── database/
│   ├── schemas/
│   └── seeds/
└── .env.example
```

## Installation

### Prerequisites
- Node.js (v14+)
- MongoDB
- Gmail account for OTP

### Setup

1. **Clone Repository**
```bash
git clone https://github.com/bhxrxth100/ai-interview-coach.git
cd ai-interview-coach
```

2. **Frontend Setup**
```bash
cd frontend
npm install
npm start
```

3. **Backend Setup**
```bash
cd backend
npm install
cp .env.example .env
# Add your environment variables
npm start
```

## Environment Variables

Create a `.env` file in the backend directory:

```
MONGODB_URI=mongodb://localhost:27017/interview_coach
JWT_SECRET=your_jwt_secret_key
GMAIL_USER=your_email@gmail.com
GMAIL_PASSWORD=your_app_password
OPENAI_API_KEY=your_openai_api_key
PORT=5000
```

## API Documentation

### Authentication Routes
- `POST /api/auth/register` - Register with email
- `POST /api/auth/verify-otp` - Verify OTP
- `POST /api/auth/login` - Login
- `POST /api/auth/forgot-password` - Initiate password reset
- `POST /api/auth/reset-password` - Reset password
- `POST /api/auth/logout` - Logout

### Interview Routes
- `POST /api/interviews/start` - Start new interview
- `POST /api/interviews/submit-answer` - Submit answer
- `POST /api/interviews/complete` - Complete interview
- `GET /api/interviews/history` - Get interview history

### User Routes
- `GET /api/users/profile` - Get user profile
- `PUT /api/users/profile` - Update profile
- `GET /api/users/dashboard` - Get dashboard data

## Features Breakdown

### Part 1: Authentication
- ✅ Premium landing page
- ✅ OTP-based registration
- ✅ Secure login
- ✅ Password recovery
- ✅ User profile management
- ✅ Session management

### Part 2: Interview System
- ✅ Interview setup (company, role, description)
- ✅ Resume upload/paste
- ✅ AI question generation
- ✅ Real-time interview session
- ✅ Performance evaluation
- ✅ Comprehensive analytics
- ✅ AI recommendations

## Security Features

- Password encryption with bcryptjs
- JWT-based authentication
- OTP expiry (10 minutes)
- Protected routes with middleware
- Environment variable protection
- SQL/NoSQL injection prevention
- CORS configuration

## Database Schema

### Users Collection
- userId (ObjectId)
- fullName (String)
- email (String, unique)
- password (String, encrypted)
- profilePicture (String, URL)
- createdDate (Date)
- updatedDate (Date)

### Interviews Collection
- interviewId (ObjectId)
- userId (ObjectId, ref: User)
- companyName (String)
- jobRole (String)
- jobDescription (String)
- resume (String)
- interviewDate (Date)
- duration (Number)
- completed (Boolean)

### Results Collection
- resultId (ObjectId)
- interviewId (ObjectId, ref: Interview)
- technicalScore (Number)
- confidenceScore (Number)
- communicationScore (Number)
- overallScore (Number)
- feedback (String)
- strongestArea (String)
- weakestArea (String)
- recommendations (Array)

## Admin Features

- View all registered users
- View all interviews conducted
- Access performance reports
- User management (edit, delete, view)
- Analytics dashboard

## Design Guidelines

- **Color Scheme**: White background with professional blue/gray accents
- **Responsive**: Mobile-first design
- **Accessibility**: WCAG 2.1 compliant
- **Typography**: Clean, readable fonts
- **UI Components**: Consistent design system

## Future Enhancements

- Video interview mode
- Multiple language support
- Mobile app (React Native)
- Advanced analytics with ML
- Interview scheduling
- Mock interview marketplace
- Peer comparison analytics

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For support, email support@interviewcoach.com or open an issue on GitHub.

---

**Built with ❤️ by bhxrxth100**
