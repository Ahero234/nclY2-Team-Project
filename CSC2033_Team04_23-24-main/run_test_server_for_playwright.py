from app import create_app

app = create_app(testing=True)
app.run()