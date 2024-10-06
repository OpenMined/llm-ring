import os
from syftbox.lib import ClientConfig

# Welcome to main_1_day.py!
# This script is part of the Example Project and demonstrates how to create
# functionality that runs when the program first starts and then once a day after that.

# Step 1: Set up the basic configuration
# The app_name is derived from the folder name
app_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))

# Load the client configuration
client_config = ClientConfig.load(
    os.path.expanduser("~/.syftbox/client_config.json")
)

# Step 2: Define your daily task
# This is where you'll add the code that should run once a day
def daily_task():
    # TODO: Add your daily task code here
    # For example:
    # - Process data in the pipeline folders
    # - Generate daily reports
    # - Perform cleanup operations
    # - Send notifications or updates
    print("Performing daily task...")
    
    # Your code here...
    
    print("Daily task completed.")

# Step 3: Execute the daily task
# This ensures the task runs when the script is called
daily_task()

# Congratulations! You've set up a daily task in your SyftBox application.
# Remember:
# - This script is called by run.sh once a day (see section_3 in run.sh)
# - It also runs when the program first starts
# - You can add any Python code here that you want to execute on this schedule
# - Consider using the pipeline folders (input, running, done) in your daily tasks

# Next steps:
# 1. Implement your specific daily task in the daily_task() function
# 2. Test your implementation by running this script directly
# 3. Check the output in your SyftBox logs to ensure it's working as expected
# 4. Consider how this daily task interacts with other parts of your application
# 5. Proceed to requirements.txt to complete the tutorial

# Happy coding!