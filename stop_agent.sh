#!/bin/bash

# Function to check if a screen session exists
# Screen session name
session_name="TurtleCityAgent"

screen -X "$session_name" term

