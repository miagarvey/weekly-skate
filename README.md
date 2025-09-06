# Weekly Skate - Automated Goalie Payment System

Web application that automates weekly hockey signup management with intelligent SMS processing and automated payment distribution to goalies.

## Overview

Streamlines the process of organizing weekly hockey games by automatically tracking signups, notifying goalie managers when quotas are met, and processing payments through an SMS-based workflow.

## Key Features

### Intelligent SMS Processing
- **NLP Analysis**: Sophisticated natural language processing with confidence scoring
- **Context-Aware Responses**: Analyzes sentiment, urgency, and emotional indicators
- **Multi-Pattern Recognition**: Handles various confirmation styles and ambiguous messages
- **Automatic Venmo Username Extraction**: Smart parsing of payment information

### Automated Payment System
- **PayPal/Venmo Integration**: Seamless payment processing through MCP (Model Context Protocol)
- **Safety Guards**: Comprehensive protection against accidental payments during development
- **Real-time Transaction Tracking**: Complete audit trail of all payment activities
- **Flexible Payment Methods**: Support for multiple payment platforms

### Admin Dashboard
- **Real-time Monitoring**: Live signup tracking and quota management
- **Broadcast Messaging**: Bulk SMS notifications to participants
- **Payment Testing**: Safe testing environment for payment flows
- **Configuration Management**: Dynamic quota and contact management

## Architecture

### Backend Framework
- **Flask**: Lightweight, modular web framework
- **SQLite/PostgreSQL**: Flexible database support
- **Gunicorn**: Production WSGI server
- **Modular Design**: Clean separation of concerns

### External Integrations
- **Twilio**: SMS messaging and webhook processing
- **PayPal MCP**: Payment processing and order management
- **Model Context Protocol**: Advanced AI-powered integrations

### Advanced Features
- **Sophisticated NLP Engine**: Custom-built message analysis system
- **Confidence-Based Decision Making**: Intelligent response generation
- **Production Logging**: Comprehensive monitoring and debugging
- **Docker Support**: Containerized deployment ready

## Quick Start

### Prerequisites
```bash
Python 3.8+
pip install -r requirements.txt
```

### Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Configure your credentials (see Configuration section)
# Edit .env with your API keys and settings
```

### Database Initialization
```bash
python scripts/init_db.py
```

### Development Server
```bash
python app.py
```

### Production Deployment
```bash
gunicorn -c gunicorn.conf.py app:app
```

## Configuration

The application uses environment variables for secure configuration management:

### Required Settings
- `SECRET_KEY`: Flask session security
- `ADMIN_TOKEN`: Admin panel access
- `TWILIO_ACCOUNT_SID`: SMS service configuration
- `TWILIO_AUTH_TOKEN`: SMS authentication
- `TWILIO_FROM`: SMS sender number
- `PAYPAL_CLIENT_ID`: Payment processing
- `PAYPAL_CLIENT_SECRET`: Payment authentication

### Optional Settings
- `FLASK_ENV`: Environment mode (development/production)
- `DB_PATH`: Database file location
- `DEFAULT_QUOTA`: Default weekly signup limit
- `LOG_LEVEL`: Logging verbosity
- `SENTRY_DSN`: Error monitoring

## API Endpoints

### Public Endpoints
- `GET /` - Main signup interface
- `POST /signup` - Player registration
- `POST /sms-webhook` - Twilio message processing

### Admin Endpoints (Token Protected)
- `GET /admin` - Administrative dashboard
- `POST /admin/quota` - Quota management
- `POST /admin/broadcast/send` - Bulk messaging
- `POST /admin/pay-goalie` - Manual payment processing

### Payment Endpoints
- `GET /pay-goalie` - Payment interface
- `POST /create-goalie-order` - Order creation
- `GET /payment/success` - Payment confirmation
- `GET /payment/cancel` - Payment cancellation

## Testing

### Unit Tests
```bash
python -m pytest tests/
```

### Integration Testing
```bash
python test_mcp_venmo.py
```

### SMS Webhook Testing
```bash
# Use ngrok for local webhook testing
ngrok http 5000
```

**Note**: This application is designed for private use. The live deployment URL is not publicly accessible for security reasons. Demo credentials and sandbox environments are used for testing purposes.

