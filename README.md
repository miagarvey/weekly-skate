# Weekly Skate - Automated Goalie Payment System

A sophisticated Flask web application that automates weekly hockey signup management with intelligent SMS processing and automated payment distribution to goalies.

## Overview

Weekly Skate streamlines the process of organizing weekly hockey games by automatically tracking signups, notifying goalies when quotas are met, and processing payments through an intelligent SMS-based workflow.

## Key Features

### Intelligent SMS Processing
- **Advanced NLP Analysis**: Sophisticated natural language processing with confidence scoring
- **Context-Aware Responses**: Analyzes sentiment, urgency, and emotional indicators
- **Multi-Pattern Recognition**: Handles various confirmation styles and ambiguous messages
- **Automatic Venmo Username Extraction**: Smart parsing of payment information

### Automated Payment System
- **PayPal/Venmo Integration**: Seamless payment processing through MCP (Model Context Protocol)
- **Safety Guards**: Comprehensive protection against accidental payments during development
- **Real-time Transaction Tracking**: Complete audit trail of all payment activities
- **Flexible Payment Methods**: Support for multiple payment platforms

### Enterprise-Grade Security
- **Twilio Webhook Verification**: Cryptographic signature validation
- **Rate Limiting**: Protection against abuse and spam
- **Input Sanitization**: Comprehensive data validation and cleaning
- **CSRF Protection**: Cross-site request forgery prevention
- **Environment-Based Configuration**: Secure credential management

### Admin Dashboard
- **Real-time Monitoring**: Live signup tracking and quota management
- **Broadcast Messaging**: Bulk SMS notifications to participants
- **Payment Testing**: Safe testing environment for payment flows
- **Configuration Management**: Dynamic quota and contact management

## Technical Architecture

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

## NLP Engine Details

### Confidence Scoring System
- **Explicit Confirmations** (1.0): Clear "yes", "confirmed", "secured"
- **Strong Indicators** (0.9): "got it", "will do", "on it"
- **Moderate Signals** (0.7): "should be good", "think so"
- **Weak Patterns** (0.5): Contextual hints and implications

### Context Analysis
- **Temporal Awareness**: Time-sensitive response handling
- **Urgency Detection**: Priority-based message processing
- **Sentiment Analysis**: Emotional context understanding
- **Pattern Learning**: Adaptive response improvement

## Security Features

### Production Security
- **Webhook Signature Verification**: Cryptographic request validation
- **Rate Limiting**: Per-endpoint request throttling
- **Input Sanitization**: XSS and injection prevention
- **CSRF Protection**: Form submission security
- **Environment Isolation**: Development/production separation

### Payment Security
- **Sandbox Testing**: Safe payment environment
- **Transaction Logging**: Complete audit trails
- **Error Handling**: Graceful failure management
- **Rollback Capabilities**: Transaction reversal support

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

## Monitoring & Logging

### Application Logging
- **Structured Logging**: JSON-formatted log entries
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Request Tracking**: Complete request/response logging
- **Performance Metrics**: Response time monitoring

### Error Monitoring
- **Sentry Integration**: Real-time error tracking
- **Exception Handling**: Graceful error recovery
- **Alert System**: Critical issue notifications

## Deployment

### Production Checklist
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL certificates installed
- [ ] Monitoring systems active
- [ ] Backup procedures tested

### Scaling Considerations
- **Horizontal Scaling**: Multi-instance deployment
- **Database Optimization**: Query performance tuning
- **Caching Strategy**: Redis integration ready
- **Load Balancing**: Nginx configuration included

## Contributing

This project demonstrates enterprise-level software development practices including:
- Clean architecture and modular design
- Comprehensive testing strategies
- Security-first development approach
- Production-ready deployment configuration
- Advanced AI/ML integration patterns

## License

This project is private and proprietary. All rights reserved.

---

**Note**: This application is designed for private use. The live deployment URL is not publicly accessible for security reasons. Demo credentials and sandbox environments are used for testing purposes.

## Architecture Highlights

### Design Patterns
- **Service Layer Pattern**: Clean business logic separation
- **Repository Pattern**: Data access abstraction
- **Factory Pattern**: Service instantiation
- **Observer Pattern**: Event-driven SMS processing

### Code Quality
- **Type Hints**: Full Python type annotation
- **Docstrings**: Comprehensive code documentation
- **Error Handling**: Robust exception management
- **Code Organization**: Logical module structure

This project showcases advanced full-stack development skills, AI integration, payment processing, and production-ready software engineering practices.
