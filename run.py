import os
from app import create_app, db

env = os.environ.get('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    print(f"Starting Smart Home Security System on http://127.0.0.1:{port} (Environment: {env})")
    app.run(host=host, port=port, debug=False, use_reloader=False)
