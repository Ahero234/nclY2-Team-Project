# CSC2033_Team04_23-24
CSC2033 Team Assignment - Health and Wellbeing Application

# 4Health

A web program called 4Health assists users in monitoring their daily health indicators, including steps, sleep duration, calories burnt, weight, and calorie consumption. Interactive graphs allow users to track their development over time by logging their entries.

## Features
- Relates to goal 4 (Good Health and Wellbeing) of the UN sustainable development goals.
- This project's aim is to provide important information about maintaining  good health, including tips on nutrition and exercises.
- Users will provide information about themselves like height and weight and also set fitness goals and track progress (steps taken, calories burned, etc.) over time.
- Users can access personalized meal plans like recipes based on dietary preferences and health goals.
- The web app will include a medications reminder to help users manage medication schedules.
- User authorization and authentication 
- User management admin panel
- Daily notes in the journal for health indicators
- Data visualization to monitor development 
- Bootstrap 5 responsive design

## Functionalities
- Can be accessed via a website (Built on Flask).
- Administrator can view and manage user accounts, along with adding new data such as recipes that can be accessed by all users, and responded to like a forum/blog system.
- Recipes stored in a MongoDB database.
- Users can search through the data to learn more about health benefits, exercise requirements, and meals consumed. 
- Website could potentially include a food log, with the option to upload photos of food (or packaging) which can be saved as a draft to process its nutritional information later.

## Running the Project

## Installation

1. Clone the repository:
   git clone https://github.com/yourusername/4Health.git

   cd 4Health

2. Create and activate a virtual environment:

```
python3 -m venv venv
source venv/bin/activate
```

3. Install the required dependencies:

```
pip install -r requirements.txt
```
4. Set up the database:

```
flask db upgrade
```
5. Run the application:

```
flask run
```
6. Open your web browser and go to http://127.0.0.1:5000

