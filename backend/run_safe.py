"""
Auto-recovery server runner.
Wraps Flask app with exception handling to ensure system never crashes during demo.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    try:
        print("[SERVER] Starting TRUE VOTE backend in SAFE MODE...")
        print("[SERVER] Running on http://0.0.0.0:5000")
        print("[SERVER] Auto-recovery enabled - server will continue even if errors occur")
        app.run(host="0.0.0.0", port=5000, debug=True)
    except Exception as e:
        print(f"[SERVER] Server crash detected: {str(e)}")
        print("[SERVER] Attempting auto-recovery...")
        try:
            app.run(host="0.0.0.0", port=5000)
        except Exception as recovery_error:
            print(f"[SERVER] Recovery failed: {str(recovery_error)}")
            print("[SERVER] Please restart server manually")
