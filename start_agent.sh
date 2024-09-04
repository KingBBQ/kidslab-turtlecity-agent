#!/bin/bash

# Check if the Python script is already running
if pgrep -f "python3 main.py" > /dev/null
then
	echo "The script is already running."
	exit 1
fi

# Activate the virtual environment
source venv/bin/activate

# Run the Python script and redirect output to a log file
python3 main.py >> agent.log 2>&1 &

# Deactivate the virtual environment
deactivate