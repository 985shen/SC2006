import os
from app import create_app, db
from config import config

env = os.environ.get('FLASK_ENV', 'production') # "development" or "production"
app = create_app(config[env])

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    if app.config['DEBUG']:
        # Dev server: auto-reload + interactive debugger.
        app.run(host='127.0.0.1', port=5000, debug=True)
    else:
        # Waitress: production-grade WSGI server, much faster than the
        # Flask dev server — especially on Windows. Set FLASK_ENV=production
        # before launching to use this path.
        from waitress import serve
        print("Serving on http://127.0.0.1:5000 (waitress, 4 threads)")
        serve(app, host='127.0.0.1', port=5000, threads=4)