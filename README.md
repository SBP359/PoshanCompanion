# Nutrient Intake Tracker

The Nutrient Intake Tracker is a Flask-based web application that allows users to track their daily nutrient intake and generate reports based on their data. The application provides features for uploading food data, calculating nutrient intake levels, and visualizing the data through graphs.

## Features

- **Upload Food Data**: Users can upload information about the food they consume, including the food name, calories, and nutrient values.

- **Nutrient Intake Calculation**: The application calculates the total nutrient intake for each user based on the uploaded food data.

- **Graph Generation**: The application generates line graphs and bar charts to visualize the nutrient intake data over time.

- **Report Generation**: Users can generate PDF reports summarizing their nutrient intake levels and graph visualizations.


## Usage

1. Access the application through a web browser at `http://localhost:5000`.

2. Upload food data using the provided form.

3. View the generated line graphs and bar charts to visualize nutrient intake over time.

4. Generate PDF reports summarizing nutrient intake levels and graph visualizations.

## Database Structure

The application uses an SQLite database to store user information. The `user_info` table has the following structure:

- `id`: Primary key for the user entry.
- `time_uploaded`: Timestamp of when the food data was uploaded.
- `food_name`: Name of the food item.
- `calories`: Calories in the food item.
- `nutrients`: JSON string containing nutrient values for the food item.

## Sample Data

To populate the database with sample data for testing, you can use the provided `generate_fake_data.py` script. This script creates a SQLite database file with fake data for the past 7 days.


