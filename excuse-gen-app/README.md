# Excuse Email Draft Tool

A modern web application that generates professional excuse emails using Databricks Model Serving LLM. Built with FastAPI backend and React frontend, designed to work locally and deploy seamlessly to Databricks Apps.

## Features

- **Smart Email Generation**: AI-powered excuse email creation based on category, tone, and seriousness level
- **Modern UI**: Clean, responsive interface built with React and Tailwind CSS
- **Multiple Categories**: Running Late, Missed Meeting, Deadline, WFH/OOO, Social, Travel
- **Tone Options**: Sincere, Playful, Corporate
- **Seriousness Levels**: 1 (very silly) to 5 (serious) with visual indicators
- **Copy to Clipboard**: One-click copying of generated emails
- **Real-time Validation**: Form validation with helpful error messages
- **Loading States**: Visual feedback during API calls
- **Error Handling**: Comprehensive error handling with user-friendly messages

## Project Structure

```
excuse-gen-app/
├── app.yaml                 # Databricks Apps configuration
├── requirements.txt         # Python dependencies
├── src/
│   └── app.py              # FastAPI backend entry point
├── public/
│   └── index.html          # Single-page React + Tailwind CSS frontend
├── README.md               # This file
├── .gitignore              # Git ignore rules
└── .env.example            # Environment variables template
```

## Quick Start

### Local Development

1. **Clone and Setup**
   ```bash
   cd excuse-gen-app
   python3 -m pip install -r requirements.txt
   cp .env.example .env
   ```

2. **Configure Environment**
   Edit `.env` with your Databricks credentials:
   ```bash
   DATABRICKS_API_TOKEN=your_databricks_personal_access_token
   DATABRICKS_ENDPOINT_URL=https://e2-dogfood.staging.cloud.databricks.com/serving-endpoints/databricks-gpt-oss-120b/invocations
   ```

3. **Run the Application**
   ```bash
   cd excuse-gen-app
   python3 -m uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access the App**
   Open your browser to: http://localhost:8000

### Databricks Apps Deployment

1. **Prerequisites**
   - Databricks workspace with Apps enabled
   - Databricks Model Serving endpoint accessible
   - App secret configured with key `databricks_token`

2. **Deploy**
   ```bash
   databricks apps deploy excuse-gen-app --source-code-path /path/to/excuse-gen-app
   ```

3. **Configure App Secret**
   In your Databricks workspace, create an App secret:
   - Key: `databricks_token`
   - Value: Your Databricks personal access token

## API Endpoints

### Main Endpoint
- `POST /api/generate-excuse` - Generate excuse email

### Health & Monitoring
- `GET /health` - Health check with version info
- `GET /healthz` - Kubernetes-style health check
- `GET /ready` - Readiness check
- `GET /ping` - Simple ping endpoint
- `GET /metrics` - Prometheus-style metrics
- `GET /debug` - Environment debugging info

### Static Files
- `GET /` - Serves the React application

## Request/Response Format

### Generate Excuse Request
```json
{
  "category": "Running Late",
  "tone": "Playful",
  "seriousness": 3,
  "recipient_name": "Alex",
  "sender_name": "Mona",
  "eta_when": "15 minutes"
}
```

### Generate Excuse Response
```json
{
  "subject": "Running Late - ETA 15 minutes",
  "body": "Dear Alex,\n\nI wanted to let you know...\n\nBest regards,\nMona",
  "success": true,
  "error": null
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABRICKS_API_TOKEN` | Databricks personal access token | Required |
| `DATABRICKS_ENDPOINT_URL` | Model serving endpoint URL | Provided in app.yaml |
| `PORT` | Server port | 8000 |
| `HOST` | Server host | 0.0.0.0 |

### Categories
- Running Late
- Missed Meeting
- Deadline
- WFH/OOO
- Social
- Travel

### Tones
- Sincere
- Playful
- Corporate
- Assertive

### Seriousness Levels
- 1: Very Silly
- 2: Silly
- 3: Neutral
- 4: Serious
- 5: Very Serious

## Technical Details

### Backend (FastAPI)
- **Framework**: FastAPI with CORS middleware
- **LLM Integration**: httpx for async HTTP calls to Databricks Model Serving
- **Error Handling**: Comprehensive error handling with meaningful messages
- **Logging**: Request/response logging for debugging
- **Static Files**: Multiple path resolution for different environments

### Frontend (React)
- **Framework**: React 18 with hooks
- **Styling**: Tailwind CSS via CDN
- **State Management**: React hooks for form and UI state
- **API Integration**: Fetch API with proper error handling
- **Responsive Design**: Mobile-first design with grid layout
- **Accessibility**: Proper labels, keyboard navigation, focus indicators

### Databricks Apps Compatibility
- **Port**: 8000 (critical requirement)
- **Command Format**: Array style in app.yaml
- **Secrets**: Uses `valueFrom` for sensitive data
- **File Sizes**: All files under 10MB limit
- **Host Binding**: 0.0.0.0 for container environments
- **Health Checks**: Multiple endpoints for monitoring

## Development

### Local Testing
   ```bash
   # Install dependencies
   python3 -m pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your credentials

# Run with auto-reload
cd excuse-gen-app
python3 -m uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/debug
```

### Debugging
- Check `/debug` endpoint for environment information
- Review logs for request/response details
- Use browser developer tools for frontend debugging
- Test API endpoints directly with curl or Postman

## Troubleshooting

### Common Issues

1. **"DATABRICKS_API_TOKEN not configured"**
   - Ensure `.env` file exists and contains valid token
   - For Databricks Apps, verify App secret is configured

2. **"Could not find index.html"**
   - Check that `public/index.html` exists
   - Verify file permissions

3. **CORS errors**
   - Backend includes CORS middleware for all origins
   - Check browser console for specific error details

4. **LLM service errors**
   - Verify Databricks endpoint URL is correct
   - Check API token permissions
   - Review Databricks Model Serving endpoint status

### Logs
- Backend logs include request/response details
- Check Databricks Apps logs for deployment issues
- Use `/debug` endpoint to verify environment configuration

## Security

- API tokens are loaded from environment variables
- No hardcoded credentials in source code
- CORS configured for development (adjust for production)
- Input validation on all form fields
- Error messages don't expose sensitive information

## Performance

- Async HTTP calls for LLM requests
- Efficient React state management
- Minimal dependencies for fast startup
- Optimized for Databricks Apps container environment

## License

This project is provided as-is for educational and demonstration purposes.

## Support

For issues related to:
- **Databricks Apps**: Check Databricks documentation and support
- **Model Serving**: Verify endpoint configuration and permissions
- **Application**: Review logs and debug endpoint for troubleshooting

