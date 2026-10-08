import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config

db = SQLAlchemy()

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    db.init_app(app)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.devices import devices_bp
    from app.routes.sensors import sensors_bp
    from app.routes.lock import lock_bp
    from app.routes.automation import automation_bp
    from app.routes.alerts import alerts_bp
    from app.routes.logs import logs_bp
    from app.routes.users import users_bp
    from app.routes.settings import settings_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(devices_bp)
    app.register_blueprint(sensors_bp)
    app.register_blueprint(lock_bp)
    app.register_blueprint(automation_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Security HTTP headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self';"
        )
        return response

    # Error Handlers
    @app.errorhandler(403)
    def forbidden(e):
        from flask import request, jsonify, render_template
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Forbidden', 'message': 'Access Denied', 'code': 403}), 403
        return render_template('errors/403.html', message='You do not have permission to access this resource.'), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import request, jsonify, render_template
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not Found', 'message': 'Requested endpoint does not exist', 'code': 404}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        from flask import request, jsonify, render_template
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred', 'code': 500}), 500
        return render_template('errors/500.html'), 500

    return app
