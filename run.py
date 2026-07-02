from backend.app import app


if __name__ == "__main__":
    print("Starting Laptop AI Recommender...")
    print("Open your browser and go to: http://localhost:8080")
    app.run(debug=True, port=8080, host="127.0.0.1")
