#made by sbp
from flask import Flask, render_template, request, url_for, redirect, session
import os
from datetime import datetime
import sqlite3
from image_utils import recognize_food
import json
import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend before importing pyplot
import matplotlib.pyplot as plt
import numpy as np
import calendar
import io
from flask import send_file, render_template
from xhtml2pdf import pisa
from datetime import datetime, timedelta
from calendar import monthrange
import base64

app = Flask(__name__)
app.secret_key = "456123"


# Homepage now redirects to home
@app.route("/")
def homepage():
    return redirect(url_for('home'))


@app.route("/home")
def home():
    user_info = get_user_info_from_db()
    total_calories = sum(int(float(info[3])) for info in user_info)
    total_nutrients = {"Protein": 0, "Carbs": 0, "Fat": 0}
    total_micronutrients = {"Iron": 0, "Magnesium": 0, "Calcium": 0}
    for i in range(len(user_info)):
        info = list(user_info[i])
        nutrients = json.loads(info[4])  # Convert nutrients from JSON string to dictionary
        micronutrients = json.loads(info[5])  # Convert micronutrients from JSON string to dictionary
        # Format nutrient values to two decimal places
        nutrients = {k: round(v, 2) for k, v in nutrients.items()}
        micronutrients = {k: round(v, 2) for k, v in micronutrients.items()}
        info[4] = nutrients
        info[5] = micronutrients
        user_info[i] = tuple(info)
        for nutrient, value in nutrients.items():
            if nutrient in total_nutrients:
                total_nutrients[nutrient] += value
        for micronutrient, value in micronutrients.items():
            if micronutrient in total_micronutrients:
                total_micronutrients[micronutrient] += value
    # Format total nutrient values to two decimal places
    total_nutrients = {k: round(v, 2) for k, v in total_nutrients.items()}
    total_micronutrients = {k: round(v, 2) for k, v in total_micronutrients.items()}
    child = session.get("child", "Pregnant Women")
    calorie_intake_level = get_calorie_intake_level(total_calories, child)
    return render_template(
        "index.html",
        prediction=None,
        calories=[0],
        nutrients=[0],
        prediction_index=0,
        user_info=user_info,
        total_calories=total_calories,
        total_nutrients=total_nutrients,
        total_micronutrients=total_micronutrients,
        calorie_intake_level=calorie_intake_level,
        child=child,
    )


def get_user_info_from_db():
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT * FROM user_info WHERE DATE(time_uploaded) = ?", (today,))
    user_info = cursor.fetchall()
    conn.close()
    return user_info


def get_user_info_from_db_within_range(start_date, end_date):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM user_info WHERE time_uploaded BETWEEN ? AND ?",
        (
            start_date.strftime("%Y-%m-%d %H:%M:%S"),
            end_date.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    user_info = cursor.fetchall()
    conn.close()
    return user_info


@app.route("/predict", methods=["POST"])
def predict():
    if "file" in request.files:
        file = request.files["file"]
        servings = float(request.form["servings"])  # Get the number of servings
        if file.filename != "":
            if not os.path.exists("temp"):
                os.makedirs("temp")

            file_path = os.path.join("temp", file.filename)
            file.save(file_path)
            time_uploaded = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Adjusted to receive five return values
            (
                food_name,
                nutrients,
                calories,
                predicted_index,
                micronutrient_info,
            ) = recognize_food(file_path, servings)
            # Multiply calories and nutrients by the number of servings
            calories *= servings
            nutrients = {k: v * servings for k, v in nutrients.items()}
            conn = sqlite3.connect("user_data.db")
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_info (time_uploaded, food_name, calories, nutrients, micronutrients)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    time_uploaded,
                    food_name,
                    str(calories),
                    json.dumps(nutrients),
                    json.dumps(micronutrient_info),
                ),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("home"))  # Redirect to home after processing
        else:
            return redirect(url_for("home"))  # Redirect to home if filename is empty
    else:
        return redirect(url_for("home"))  # Redirect to home if no file in request


@app.route("/delete", methods=["POST"])
def delete():
    time_uploaded = request.form["time_uploaded"]
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM user_info
        WHERE time_uploaded = ?
    """,
        (time_uploaded,),
    )
    conn.commit()
    conn.close()
    return "OK"


@app.route("/update_child", methods=["POST"])
def update_child():
    child = request.form["child"]
    session["child"] = child  # Update child in session with the new value
    return redirect(url_for("home"))  # Redirect to home after updating child


def get_calorie_intake_level(total_calories, child="Pregnant Women"):
    if child == "child":
        if total_calories < 1000:
            return "Low"
        elif 1000 <= total_calories <= 1700:
            return "Medium"
        else:
            return "High"
    else:  # For Pregnant Women
        if total_calories < 1600:
            return "Low"
        elif 1600 <= total_calories <= 3000:
            return "Medium"
        else:
            return "High"


def create_and_save_graph(user_nutrients, average_nutrients, file_name):
    # Clear any existing plots
    plt.close('all')
    
    # Create new figure with white background
    plt.figure(figsize=(10, 5), facecolor='white')
    
    nutrients_names = list(user_nutrients.keys())
    user_values = list(user_nutrients.values())
    average_values = [average_nutrients[k] for k in nutrients_names]

    x = np.arange(len(nutrients_names))
    width = 0.35

    plt.bar(x - width/2, user_values, width, label='Your Intake', color='#1f77b4')
    plt.bar(x + width/2, average_values, width, label='Required Intake', color='#2ca02c')

    plt.ylabel('Amount (g)')
    plt.title('Daily Nutrient Intake Comparison')
    plt.xticks(x, nutrients_names)
    plt.legend()
    
    # Add grid for better readability
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Generate unique filename using timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_file_name = file_name.replace('.png', f'_{timestamp}.png')
    
    # Save with high quality
    plt.savefig(unique_file_name, dpi=300, bbox_inches='tight', transparent=False)
    plt.close()  # Close the figure to free memory
    
    return unique_file_name


# Daily Report
@app.route("/daily")
def daily_report():
    try:
        import glob
        import os
        
        user_info = get_user_info_from_db()
        total_calories = sum(int(float(info[3])) for info in user_info)
        total_nutrients = {"Protein": 0, "Carbs": 0, "Fat": 0}
        
        for info in user_info:
            nutrients = json.loads(info[4])
            for nutrient, value in nutrients.items():
                if nutrient in total_nutrients:
                    total_nutrients[nutrient] += float(value)

        child = session.get("child", "Pregnant Women")
        if child == "child":
            average_daily_requirements = {"Protein": 13, "Carbs": 150, "Fat": 40}
        else:
            average_daily_requirements = {"Protein": 50, "Carbs": 300, "Fat": 70}

        # Clean up old nutrient comparison graphs (keep last 5)
        graph_files = glob.glob("static/nutrient_intake_comparison_*.png")
        graph_files.sort(reverse=True)
        for old_file in graph_files[5:]:  # Keep only the 5 most recent files
            try:
                os.remove(old_file)
            except:
                pass

        # Generate new graph with unique name
        graph_file_path = create_and_save_graph(
            total_nutrients,
            average_daily_requirements,
            "static/nutrient_intake_comparison.png"
        )

        return render_template(
            "report_base.html",
            user_info=user_info,
            total_nutrients=total_nutrients,
            total_calories=total_calories,
            average_daily_requirements=average_daily_requirements,
            graph_file_path=graph_file_path,
            calorie_intake_level=get_calorie_intake_level(total_calories, child),
            datetime=datetime
        )

    except Exception as e:
        print("Error in daily_report:", str(e))
        return "An error occurred while generating the report", 500


# Weekly Report (Past 7 days)
@app.route("/weekly")
def weekly_report():
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        import io
        import base64
        
        # Initialize dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=6)
        days_in_range = (end_date - start_date).days + 1

        # Get user data
        user_info = get_user_info_from_db_within_range(start_date, end_date)

        # Initialize nutrient tracking
        nutrients = ["Protein", "Carbs", "Fat"]
        daily_nutrients = {nutrient: [0] * days_in_range for nutrient in nutrients}
        total_nutrients = {nutrient: 0 for nutrient in nutrients}

        # Process daily nutrients
        for info in user_info:
            nutrients_data = json.loads(info[4])
            date = datetime.strptime(info[1], "%Y-%m-%d %H:%M:%S")
            day_index = (date - start_date).days
            
            if 0 <= day_index < days_in_range:
                for nutrient, value in nutrients_data.items():
                    if nutrient in daily_nutrients:
                        value_float = float(value)
                        daily_nutrients[nutrient][day_index] += value_float
                        total_nutrients[nutrient] += value_float

        # Calculate averages
        avg_nutrients = {
            nutrient: round(total / days_in_range, 2)
            for nutrient, total in total_nutrients.items()
        }
        total_nutrients = {
            nutrient: round(total, 2)
            for nutrient, total in total_nutrients.items()
        }

        # Get requirements based on user type
        child = session.get("child", "Pregnant Women")
        daily_requirements = {
            "child": {"Protein": 13, "Carbs": 150, "Fat": 40},
            "Pregnant Women": {"Protein": 50, "Carbs": 300, "Fat": 70}
        }[child if child == "child" else "Pregnant Women"]

        # Create weekly graph with improved styling
        plt.close('all')  # Close all existing figures
        
        # Create figure with specified size and DPI
        fig = plt.figure(figsize=(10, 6), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#f8f9fa')
        
        # Set modern style elements
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_linewidth(0.5)
        ax.spines['bottom'].set_linewidth(0.5)
        
        # Setup graph parameters
        days = list(range(days_in_range))
        colors = {
            "Protein": "#1f77b4",  # Blue
            "Carbs": "#2ca02c",    # Green
            "Fat": "#ff7f0e"       # Orange
        }
        markers = {"Protein": "o", "Carbs": "s", "Fat": "^"}
        
        # Plot each nutrient line with requirement reference
        for nutrient, values in daily_nutrients.items():
            # Plot actual intake
            line = ax.plot(days, values, 
                         marker=markers[nutrient], 
                         label=f"{nutrient} Intake",
                         color=colors[nutrient],
                         linewidth=2,
                         markersize=6,
                         markerfacecolor='white',
                         markeredgewidth=2)
            
            # Plot requirement line
            ax.axhline(y=daily_requirements[nutrient],
                      color=colors[nutrient],
                      linestyle='--',
                      label=f"{nutrient} Required",
                      alpha=0.3,
                      linewidth=1)

        # Configure graph appearance
        ax.set_title("Weekly Nutrient Intake", fontsize=14, pad=20)
        ax.set_xlabel("Day", fontsize=12, labelpad=10)
        ax.set_ylabel("Amount (grams)", fontsize=12, labelpad=10)
        
        # Format x-axis with dates
        date_labels = [(start_date + timedelta(days=i)).strftime('%a\n%d/%m') for i in days]
        ax.set_xticks(days)
        ax.set_xticklabels(date_labels, fontsize=10, rotation=30, ha='right')
        
        # Customize grid
        ax.grid(True, linestyle=':', color='gray', alpha=0.2, which='both')
        ax.set_axisbelow(True)  # Put grid below plots
        
        # Customize legend
        ax.legend(bbox_to_anchor=(1.02, 1.0), 
                 loc='upper left',
                 fontsize=10,
                 frameon=True,
                 framealpha=0.8,
                 facecolor='white',
                 edgecolor='none')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save graph to bytes with high quality
        buffer = io.BytesIO()
        plt.savefig(buffer, 
                   format='png',
                   dpi=300,
                   bbox_inches='tight',
                   pad_inches=0.1,
                   facecolor='white',
                   edgecolor='none')
        plt.close('all')  # Close all figures to free memory
        
        # Convert to base64 string
        buffer.seek(0)
        graph_uri = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"

        # Calculate nutrient status
        nutrient_status = {}
        for nutrient, avg in avg_nutrients.items():
            req = daily_requirements[nutrient]
            if avg < 0.8 * req:
                nutrient_status[nutrient] = "Low"
            elif avg > 1.2 * req:
                nutrient_status[nutrient] = "High"
            else:
                nutrient_status[nutrient] = "Normal"

        return render_template(
            "weekmonthreport.html",
            graph_uri=graph_uri,
            total_nutrients=total_nutrients,
            avg_nutrients=avg_nutrients,
            nutrient_status=nutrient_status,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            report_type="Weekly",
            avg_daily_requirements=daily_requirements
        )

    except Exception as e:
        print("Error in weekly_report:", str(e))
        return "An error occurred while generating the report", 500


# Monthly Report (Past 30 days)
@app.route("/monthly")
def monthly_report():
    today = datetime.now()
    start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_date = today
    days_in_month = (end_date - start_date).days + 1

    user_info = get_user_info_from_db_within_range(start_date, end_date)
    daily_nutrients = {
        "Protein": [0] * days_in_month,
        "Carbs": [0] * days_in_month,
        "Fat": [0] * days_in_month,
    }

    for info in user_info:
        nutrients = json.loads(info[4])
        date = datetime.strptime(info[1], "%Y-%m-%d %H:%M:%S")
        day_index = date.day - 1
        for nutrient, value in nutrients.items():
            if nutrient in daily_nutrients:
                daily_nutrients[nutrient][day_index] += float(value)

    # Calculate averages
    avg_nutrients = {}
    for nutrient, values in daily_nutrients.items():
        avg_nutrients[nutrient] = sum(values) / days_in_month

    # Create monthly graph
    plt.figure(figsize=(15, 7))
    days = list(range(1, days_in_month + 1))
    colors = {"Protein": "blue", "Carbs": "orange", "Fat": "green"}
    
    for nutrient, values in daily_nutrients.items():
        plt.plot(days, values[:days_in_month], marker='o', label=nutrient, color=colors[nutrient])

    plt.title("Monthly Nutrient Intake", fontsize=16, pad=20)
    plt.xlabel("Day of Month", fontsize=14, labelpad=10)
    plt.ylabel("Amount (g)", fontsize=14, labelpad=10)
    plt.xticks(days[::2], fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(fontsize=12, bbox_to_anchor=(1.02, 1.0), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save graph
    graph_data = io.BytesIO()
    plt.savefig(graph_data, format='png', bbox_inches='tight')
    plt.close()
    graph_data.seek(0)
    graph_uri = f"data:image/png;base64,{base64.b64encode(graph_data.getvalue()).decode()}"

    total_nutrients = {nutrient: sum(values) for nutrient, values in daily_nutrients.items()}
    
    child = session.get("child", "Pregnant Women")
    if child == "child":
        daily_requirements = {"Protein": 13, "Carbs": 150, "Fat": 40}
    else:
        daily_requirements = {"Protein": 50, "Carbs": 300, "Fat": 70}

    nutrient_status = {}
    for nutrient, total in total_nutrients.items():
        daily_avg = total / days_in_month
        if daily_avg < 0.8 * daily_requirements[nutrient]:
            nutrient_status[nutrient] = "Low"
        elif daily_avg > 1.2 * daily_requirements[nutrient]:
            nutrient_status[nutrient] = "High"
        else:
            nutrient_status[nutrient] = "Normal"

    return render_template(
        "weekmonthreport.html",
        graph_uri=graph_uri,
        total_nutrients=total_nutrients,
        avg_nutrients=avg_nutrients,
        nutrient_status=nutrient_status,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        report_type="Monthly",
        avg_daily_requirements=daily_requirements
    )


# Micronutrient Report
@app.route("/micronutrients")
def micronutrient_report():
    try:
        # Initialize dates and basic setup
        today = datetime.now()
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = today
        days_in_month = (end_date - start_date).days + 1
        
        # Define nutrients and their properties
        nutrients_config = {
            "Iron": {
                "color": "red",
                "risks": ["Anemia", "Fatigue", "Reduced immune function"],
                "food_sources": ["Red meat", "Spinach", "Lentils", "Fortified cereals"],
                "high_risks": ["Iron overload", "Liver damage"],
                "unit": "mg"
            },
            "Magnesium": {
                "color": "green",
                "risks": ["Muscle cramps", "Fatigue", "Irregular heartbeat"],
                "food_sources": ["Nuts", "Seeds", "Whole grains", "Leafy greens"],
                "high_risks": ["Diarrhea", "Nausea", "Muscle weakness"],
                "unit": "mg"
            },
            "Calcium": {
                "color": "blue",
                "risks": ["Weak bones", "Muscle cramps", "Dental problems"],
                "food_sources": ["Dairy products", "Leafy greens", "Fish with bones"],
                "high_risks": ["Kidney stones", "Heart problems"],
                "unit": "mg"
            }
        }

        # Get requirements based on user type
        child = session.get("child", "Pregnant Women")
        requirements = {
            "child": {"Iron": 10, "Magnesium": 8, "Calcium": 800},
            "Pregnant Women": {"Iron": 30, "Magnesium": 19, "Calcium": 1000}
        }
        daily_requirements = requirements["child" if child == "child" else "Pregnant Women"]

        # Initialize tracking dictionaries
        daily_data = {}
        for nutrient in nutrients_config.keys():
            daily_data[nutrient] = {
                "daily_values": [0] * days_in_month,
                "total": 0,
                "average": 0,
                "status": "Normal",
                "requirement": daily_requirements[nutrient]
            }

        # Process user data
        user_info = get_user_info_from_db_within_range(start_date, end_date)
        for info in user_info:
            if info[5]:  # Check if micronutrients exist
                micronutrients = json.loads(info[5])
                date = datetime.strptime(info[1], "%Y-%m-%d %H:%M:%S")
                day_index = date.day - 1
                if 0 <= day_index < days_in_month:
                    for nutrient, value in micronutrients.items():
                        if nutrient in daily_data:
                            value_float = float(value)
                            daily_data[nutrient]["daily_values"][day_index] += value_float
                            daily_data[nutrient]["total"] += value_float

        # Calculate averages and status
        for nutrient, data in daily_data.items():
            data["average"] = round(data["total"] / days_in_month if days_in_month > 0 else 0, 2)
            if data["average"] < 0.8 * data["requirement"]:
                data["status"] = "Low"
            elif data["average"] > 1.2 * data["requirement"]:
                data["status"] = "High"

        # Create graph
        plt.clf()
        fig = plt.figure(figsize=(15, 7))
        days = list(range(1, days_in_month + 1))

        # Plot data
        for nutrient, data in daily_data.items():
            plt.plot(days, data["daily_values"][:days_in_month], marker='o',
                    label=f"{nutrient} Intake", color=nutrients_config[nutrient]["color"],
                    markersize=6, markerfacecolor='white', markeredgewidth=2)
            plt.axhline(y=data["requirement"], color=nutrients_config[nutrient]["color"],
                       linestyle='--', label=f"{nutrient} Requirement", alpha=0.3)

        # Configure graph appearance with larger text
        plt.title("Monthly Micronutrient Intake", fontsize=16, pad=20)
        plt.xlabel("Day of Month", fontsize=14, labelpad=10)
        plt.ylabel("Amount (mg)", fontsize=14, labelpad=10)
        plt.xticks(days[::2], fontsize=12)
        plt.yticks(fontsize=12)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # Save graph
        graph_data = io.BytesIO()
        plt.savefig(graph_data, format='png', dpi=300, bbox_inches='tight')
        plt.close('all')
        graph_data.seek(0)
        graph_uri = f"data:image/png;base64,{base64.b64encode(graph_data.getvalue()).decode('utf-8')}"

        # Prepare template data
        micronutrient_data = {}
        avg_nutrients = {}
        total_nutrients = {}
        nutrient_status = {}

        for nutrient, data in daily_data.items():
            # Update nutrient information
            micronutrient_data[nutrient] = {
                **nutrients_config[nutrient],
                "level": data["average"],
                "status": data["status"],
                "range": {
                    "min": round(data["requirement"] * 0.8, 2),
                    "max": round(data["requirement"] * 1.2, 2)
                }
            }
            
            # Update summary data
            avg_nutrients[nutrient] = data["average"]
            total_nutrients[nutrient] = data["total"]
            nutrient_status[nutrient] = data["status"]

        # Get deficient nutrients
        deficient_nutrients = [n for n, d in daily_data.items() if d["status"] == "Low"]

        # Render template
        return render_template(
            "micronutrient.html",
            micronutrient_data=micronutrient_data,
            graph_uri=graph_uri,
            total_nutrients=total_nutrients,
            avg_nutrients=avg_nutrients,
            nutrient_status=nutrient_status,
            deficient_nutrients=deficient_nutrients,
            report_type="Micronutrient",
            avg_daily_requirements=daily_requirements
        )

        # Create and setup graph
        plt.clf()
        fig = plt.figure(figsize=(15, 7))
        days = list(range(1, days_in_month + 1))
        colors = {"Iron": "red", "Magnesium": "green", "Calcium": "blue"}

        # Plot nutrient lines and requirements
        for nutrient, values in daily_nutrients.items():
            plt.plot(days, values[:days_in_month], marker='o', 
                    label=f"{nutrient} Intake", color=colors[nutrient])
            plt.axhline(y=daily_requirements[nutrient], color=colors[nutrient], 
                       linestyle='--', label=f"{nutrient} Requirement")

        # Configure graph appearance
        plt.title("Monthly Micronutrient Intake", fontsize=12, pad=15)
        plt.xlabel("Day of Month", fontsize=10)
        plt.ylabel("Amount (mg)", fontsize=10)
        plt.xticks(days[::2], fontsize=8)
        plt.yticks(fontsize=8)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # Save graph
        graph_data = io.BytesIO()
        plt.savefig(graph_data, format='png', dpi=300, bbox_inches='tight')
        plt.close('all')
        graph_data.seek(0)
        graph_uri = f"data:image/png;base64,{base64.b64encode(graph_data.getvalue()).decode('utf-8')}"

        # Define micronutrient metadata with dynamic data
        micronutrient_data = {
            "Iron": {
                "risks": ["Anemia", "Fatigue", "Reduced immune function"],
                "food_sources": ["Red meat", "Spinach", "Lentils", "Fortified cereals"],
                "high_risks": ["Iron overload", "Liver damage"],
                "unit": "mg",
                "level": avg_nutrients["Iron"],
                "status": nutrient_status["Iron"],
                "range": {
                    "min": round(daily_requirements["Iron"] * 0.8, 2),
                    "max": round(daily_requirements["Iron"] * 1.2, 2)
                }
            },
            "Magnesium": {
                "risks": ["Muscle cramps", "Fatigue", "Irregular heartbeat"],
                "food_sources": ["Nuts", "Seeds", "Whole grains", "Leafy greens"],
                "high_risks": ["Diarrhea", "Nausea", "Muscle weakness"],
                "unit": "mg",
                "level": avg_nutrients["Magnesium"],
                "status": nutrient_status["Magnesium"],
                "range": {
                    "min": round(daily_requirements["Magnesium"] * 0.8, 2),
                    "max": round(daily_requirements["Magnesium"] * 1.2, 2)
                }
            },
            "Calcium": {
                "risks": ["Weak bones", "Muscle cramps", "Dental problems"],
                "food_sources": ["Dairy products", "Leafy greens", "Fish with bones"],
                "high_risks": ["Kidney stones", "Heart problems"],
                "unit": "mg",
                "level": avg_nutrients["Calcium"],
                "status": nutrient_status["Calcium"],
                "range": {
                    "min": round(daily_requirements["Calcium"] * 0.8, 2),
                    "max": round(daily_requirements["Calcium"] * 1.2, 2)
                }
            }
        }

        deficient_nutrients = [n for n, s in nutrient_status.items() if s == "Low"]

        # Render template
        return render_template(
            "micronutrient.html",
            micronutrient_data=micronutrient_data,
            graph_uri=graph_uri,
            total_nutrients=total_nutrients,
            avg_nutrients=avg_nutrients,
            nutrient_status=nutrient_status,
            deficient_nutrients=deficient_nutrients,
            report_type="Micronutrient",
            avg_daily_requirements=daily_requirements
        )

        # Calculate averages
        avg_nutrients = {
            nutrient: round(total / days_in_month if days_in_month > 0 else 0, 2)
            for nutrient, total in total_nutrients.items()
        }

        # Get requirements based on user type
        child = session.get("child", "Pregnant Women")
        requirements = {
            "child": {"Iron": 10, "Magnesium": 8, "Calcium": 800},
            "Pregnant Women": {"Iron": 30, "Magnesium": 19, "Calcium": 1000}
        }
        daily_requirements = requirements["child" if child == "child" else "Pregnant Women"]

        # Create and setup graph
        plt.clf()
        fig = plt.figure(figsize=(15, 7))
        days = list(range(1, days_in_month + 1))
        colors = {"Iron": "red", "Magnesium": "green", "Calcium": "blue"}

        # Plot nutrient lines and requirements
        for nutrient, values in daily_nutrients.items():
            plt.plot(days, values[:days_in_month], marker='o', 
                    label=f"{nutrient} Intake", color=colors[nutrient])
            plt.axhline(y=daily_requirements[nutrient], color=colors[nutrient], 
                       linestyle='--', label=f"{nutrient} Requirement")

        # Configure graph appearance
        plt.title("Monthly Micronutrient Intake", fontsize=12, pad=15)
        plt.xlabel("Day of Month", fontsize=10)
        plt.ylabel("Amount (mg)", fontsize=10)
        plt.xticks(days[::2], fontsize=8)
        plt.yticks(fontsize=8)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # Save graph with high quality
        graph_data = io.BytesIO()
        plt.savefig(graph_data, format='png', dpi=300, bbox_inches='tight')
        plt.close('all')
        graph_data.seek(0)
        graph_uri = f"data:image/png;base64,{base64.b64encode(graph_data.getvalue()).decode('utf-8')}"

        # Calculate nutrient status
        nutrient_status = {}
        for nutrient, avg in avg_nutrients.items():
            req = daily_requirements[nutrient]
            if avg < 0.8 * req:
                nutrient_status[nutrient] = "Low"
            elif avg > 1.2 * req:
                nutrient_status[nutrient] = "High"
            else:
                nutrient_status[nutrient] = "Normal"

        # Define micronutrient metadata
        micronutrient_data = {
            "Iron": {
                "risks": ["Anemia", "Fatigue", "Reduced immune function"],
                "food_sources": ["Red meat", "Spinach", "Lentils", "Fortified cereals"],
                "high_risks": ["Iron overload", "Liver damage"],
                "unit": "mg"
            },
            "Magnesium": {
                "risks": ["Muscle cramps", "Fatigue", "Irregular heartbeat"],
                "food_sources": ["Nuts", "Seeds", "Whole grains", "Leafy greens"],
                "high_risks": ["Diarrhea", "Nausea", "Muscle weakness"],
                "unit": "mg"
            },
            "Calcium": {
                "risks": ["Weak bones", "Muscle cramps", "Dental problems"],
                "food_sources": ["Dairy products", "Leafy greens", "Fish with bones"],
                "high_risks": ["Kidney stones", "Heart problems"],
                "unit": "mg"
            }
        }

        # Add dynamic data to micronutrient information
        for nutrient, data in micronutrient_data.items():
            if nutrient in avg_nutrients and nutrient in nutrient_status and nutrient in daily_requirements:
                data.update({
                    "level": avg_nutrients[nutrient],
                    "status": nutrient_status[nutrient],
                    "range": {
                        "min": round(daily_requirements[nutrient] * 0.8, 2),
                        "max": round(daily_requirements[nutrient] * 1.2, 2)
                    }
                })

        # Get list of deficient nutrients
        deficient_nutrients = [n for n, s in nutrient_status.items() if s == "Low"]

        # Render template with all data
        return render_template(
            "micronutrient.html",
            micronutrient_data=micronutrient_data,
            graph_uri=graph_uri,
            total_nutrients=total_nutrients,
            avg_nutrients=avg_nutrients,
            nutrient_status=nutrient_status,
            deficient_nutrients=deficient_nutrients,
            report_type="Micronutrient",
            avg_daily_requirements=daily_requirements
        )

        # Get list of deficient nutrients
        deficient_nutrients = [n for n, s in nutrient_status.items() if s == "Low"]

        # Return template with all data
        return render_template(
            "micronutrient.html",
            micronutrient_data=micronutrient_data,
            graph_uri=graph_uri,
            total_nutrients=total_nutrients,
            avg_nutrients=avg_nutrients,
            nutrient_status=nutrient_status,
            deficient_nutrients=deficient_nutrients,
            report_type="Micronutrient",
            avg_daily_requirements=daily_requirements
        )

    except Exception as e:
        print("Error in micronutrient_report:", str(e))
        return "An error occurred while generating the report", 500


@app.route("/reports")
def reports():
    return render_template("reports.html")


# Download routes updated to match new template names
@app.route("/download_report")
def download_report():
    try:
        user_info = get_user_info_from_db()
        total_calories = sum(int(float(info[3])) for info in user_info)
        total_nutrients = {"Protein": 0, "Carbs": 0, "Fat": 0}
        
        for info in user_info:
            nutrients = json.loads(info[4])
            for nutrient, value in nutrients.items():
                if nutrient in total_nutrients:
                    total_nutrients[nutrient] += value

        child = session.get("child", "Pregnant Women")
        if child == "child":
            average_daily_requirements = {"Protein": 13, "Carbs": 150, "Fat": 40}
        else:
            average_daily_requirements = {"Protein": 50, "Carbs": 300, "Fat": 70}

        # Generate nutrients comparison graph
        graph_file_path = create_and_save_graph(
            total_nutrients,
            average_daily_requirements,
            "static/nutrient_intake_comparison.png"
        )

        report_html = render_template(
            "report_base.html",
            user_info=user_info,
            total_nutrients=total_nutrients,
            total_calories=total_calories,
            average_daily_requirements=average_daily_requirements,
            graph_file_path=graph_file_path,
            calorie_intake_level=get_calorie_intake_level(total_calories, child),
            datetime=datetime
        )

        # Convert HTML to PDF
        pdf_file_path = "static/daily_report.pdf"
        with open(pdf_file_path, "w+b") as pdf_file:
            pisa_status = pisa.CreatePDF(
                report_html,
                dest=pdf_file,
                encoding="UTF-8",
                link_callback=link_callback,
            )
        return send_file(pdf_file_path, as_attachment=True)

    except Exception as e:
        print("Error in download_report:", str(e))
        return "An error occurred while generating the report", 500


@app.route("/download_weekly_report")
def download_weekly_report():
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=6)
        user_info = get_user_info_from_db_within_range(start_date, end_date)

        daily_nutrients = {
            "Protein": [0] * 7,
            "Carbs": [0] * 7,
            "Fat": [0] * 7,
        }

        for info in user_info:
            nutrients = json.loads(info[4])
            date = datetime.strptime(info[1], "%Y-%m-%d %H:%M:%S")
            day_index = (date - start_date).days
            if 0 <= day_index < 7:
                for nutrient, value in nutrients.items():
                    if nutrient in daily_nutrients:
                        daily_nutrients[nutrient][day_index] += float(value)

        # Calculate averages
        avg_nutrients = {}
        for nutrient, values in daily_nutrients.items():
            avg_nutrients[nutrient] = sum(values) / 7

        # Create weekly graph
        plt.figure(figsize=(12, 6))
        days = list(range(7))
        colors = {"Protein": "blue", "Carbs": "orange", "Fat": "green"}
        
        for nutrient, values in daily_nutrients.items():
            plt.plot(days, values, marker='o', label=nutrient, color=colors[nutrient])

        plt.title("Weekly Nutrient Intake")
        plt.xlabel("Day")
        plt.ylabel("Amount (g)")
        plt.xticks(days, [(start_date + timedelta(days=i)).strftime('%a\n%d/%m') for i in days])
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # Save graph
        graph_data = io.BytesIO()
        plt.savefig(graph_data, format='png', bbox_inches='tight')
        plt.close()
        graph_data.seek(0)
        graph_uri = f"data:image/png;base64,{base64.b64encode(graph_data.getvalue()).decode()}"

        total_nutrients = {nutrient: sum(values) for nutrient, values in daily_nutrients.items()}
        child = session.get("child", "Pregnant Women")
        if child == "child":
            daily_requirements = {"Protein": 13, "Carbs": 150, "Fat": 40}
        else:
            daily_requirements = {"Protein": 50, "Carbs": 300, "Fat": 70}

        nutrient_status = {}
        for nutrient, total in total_nutrients.items():
            daily_avg = total / 7
            if daily_avg < 0.8 * daily_requirements[nutrient]:
                nutrient_status[nutrient] = "Low"
            elif daily_avg > 1.2 * daily_requirements[nutrient]:
                nutrient_status[nutrient] = "High"
            else:
                nutrient_status[nutrient] = "Normal"

        report_html = render_template(
            "weekmonthreport.html",
            graph_uri=graph_uri,
            total_nutrients=total_nutrients,
            avg_nutrients=avg_nutrients,
            nutrient_status=nutrient_status,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            report_type="Weekly",
            avg_daily_requirements=daily_requirements
        )

        # Convert HTML to PDF
        pdf_file_path = "static/weekly_report.pdf"
        with open(pdf_file_path, "w+b") as pdf_file:
            pisa_status = pisa.CreatePDF(
                report_html,
                dest=pdf_file,
                encoding="UTF-8",
                link_callback=link_callback,
            )
        return send_file(pdf_file_path, as_attachment=True)

    except Exception as e:
        print("Error in download_weekly_report:", str(e))
        return "An error occurred while generating the report", 500


@app.route("/download_monthly_report")
def download_monthly_report():
    try:
        today = datetime.now()
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = today

        user_info = get_user_info_from_db_within_range(start_date, end_date)
        daily_nutrients = {
            "Protein": [0] * 30,
            "Carbs": [0] * 30,
            "Fat": [0] * 30,
        }

        for info in user_info:
            nutrients = json.loads(info[4])
            date = datetime.strptime(info[1], "%Y-%m-%d %H:%M:%S")
            day_index = date.day - 1
            for nutrient, value in nutrients.items():
                if nutrient in daily_nutrients:
                    daily_nutrients[nutrient][day_index] += float(value)

        # Calculate averages
        avg_nutrients = {}
        for nutrient, values in daily_nutrients.items():
            avg_nutrients[nutrient] = sum(values) / 30

        # Create monthly graph
        plt.figure(figsize=(15, 7))
        days = list(range(1, 31))
        colors = {"Protein": "blue", "Carbs": "orange", "Fat": "green"}
        
        for nutrient, values in daily_nutrients.items():
            plt.plot(days, values[:30], marker='o', label=nutrient, color=colors[nutrient])

        plt.title("Monthly Nutrient Intake")
        plt.xlabel("Day of Month")
        plt.ylabel("Amount (g)")
        plt.xticks(days[::2])
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # Save graph
        graph_data = io.BytesIO()
        plt.savefig(graph_data, format='png', bbox_inches='tight')
        plt.close()
        graph_data.seek(0)
        graph_uri = f"data:image/png;base64,{base64.b64encode(graph_data.getvalue()).decode()}"

        total_nutrients = {nutrient: sum(values) for nutrient, values in daily_nutrients.items()}
        
        child = session.get("child", "Pregnant Women")
        if child == "child":
            daily_requirements = {"Protein": 13, "Carbs": 150, "Fat": 40}
        else:
            daily_requirements = {"Protein": 50, "Carbs": 300, "Fat": 70}

        nutrient_status = {}
        for nutrient, total in total_nutrients.items():
            daily_avg = total / 30
            if daily_avg < 0.8 * daily_requirements[nutrient]:
                nutrient_status[nutrient] = "Low"
            elif daily_avg > 1.2 * daily_requirements[nutrient]:
                nutrient_status[nutrient] = "High"
            else:
                nutrient_status[nutrient] = "Normal"

        report_html = render_template(
            "weekmonthreport.html",
            graph_uri=graph_uri,
            total_nutrients=total_nutrients,
            avg_nutrients=avg_nutrients,
            nutrient_status=nutrient_status,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            report_type="Monthly",
            avg_daily_requirements=daily_requirements
        )

        # Convert HTML to PDF
        pdf_file_path = "static/monthly_report.pdf"
        with open(pdf_file_path, "w+b") as pdf_file:
            pisa_status = pisa.CreatePDF(
                report_html,
                dest=pdf_file,
                encoding="UTF-8",
                link_callback=link_callback,
            )
        return send_file(pdf_file_path, as_attachment=True)

    except Exception as e:
        print("Error in download_monthly_report:", str(e))
        return "An error occurred while generating the report", 500


@app.route("/download_micronutrient_report")
def download_micronutrient_report():
    try:
        today = datetime.now()
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = today

        user_info = get_user_info_from_db_within_range(start_date, end_date)
        daily_nutrients = {
            "Iron": [0] * 30,
            "Magnesium": [0] * 30,
            "Calcium": [0] * 30
        }

        for info in user_info:
            if info[5]:  # Check if micronutrients exist
                micronutrients = json.loads(info[5])
                date = datetime.strptime(info[1], "%Y-%m-%d %H:%M:%S")
                day_index = date.day - 1
                for nutrient, value in micronutrients.items():
                    if nutrient in daily_nutrients:
                        daily_nutrients[nutrient][day_index] += float(value)

        # Create micronutrient graph
        plt.figure(figsize=(15, 7))
        days = list(range(1, 31))
        colors = {"Iron": "red", "Magnesium": "green", "Calcium": "blue"}
        
        child = session.get("child", "Pregnant Women")
        requirements = {
            "child": {"Iron": 10, "Magnesium": 8, "Calcium": 800},
            "Pregnant Women": {"Iron": 30, "Magnesium": 19, "Calcium": 1000}
        }
        daily_requirements = requirements["child" if child == "child" else "Pregnant Women"]

        for nutrient, values in daily_nutrients.items():
            plt.plot(days, values[:30], marker='o', label=f"{nutrient} Intake", color=colors[nutrient])
            plt.axhline(y=daily_requirements[nutrient], color=colors[nutrient], linestyle='--', 
                       label=f"{nutrient} Requirement")

        plt.title("Monthly Micronutrient Intake")
        plt.xlabel("Day of Month")
        plt.ylabel("Amount (mg)")
        plt.xticks(days[::2])
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # Save graph
        graph_data = io.BytesIO()
        plt.savefig(graph_data, format='png', bbox_inches='tight')
        plt.close()
        graph_data.seek(0)
        graph_uri = f"data:image/png;base64,{base64.b64encode(graph_data.getvalue()).decode()}"

        # Calculate status
        total_nutrients = {nutrient: sum(values) for nutrient, values in daily_nutrients.items()}
        nutrient_status = {}
        for nutrient, total in total_nutrients.items():
            daily_avg = total / 30
            if daily_avg < 0.8 * daily_requirements[nutrient]:
                nutrient_status[nutrient] = "Low"
            elif daily_avg > 1.2 * daily_requirements[nutrient]:
                nutrient_status[nutrient] = "High"
            else:
                nutrient_status[nutrient] = "Normal"

    except Exception as e:
        print("Error in micronutrient_report:", str(e))
        return "An error occurred while generating the report", 500


def link_callback(uri, rel):
    # Convert relative URI to absolute path
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        uri.replace("static/", "static/")
    )
    return path

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
