from backend import app

if __name__ == '__main__':
  print("songs application.")
  app.run(host="0.0.0.0", port=8080, debug=True, use_reloader=True)