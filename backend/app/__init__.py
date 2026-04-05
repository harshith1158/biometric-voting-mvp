def create_app():
	# Lazy import avoids package import side effects during startup.
	from app.main import create_app as _create_app
	return _create_app()
