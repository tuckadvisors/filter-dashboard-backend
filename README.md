# Filter Dashboard
 - Password: TuckSummer24
 - API currently running on: http://ec2-18-219-255-92.us-east-2.compute.amazonaws.com:8000/

## API Design
Mongo + Flask + Gunicorn
Running on a Ubuntu VM via an EC2 instance

## Selenium setup
 - Download a chrome driver from here: https://googlechromelabs.github.io/chrome-for-testing/
 - Make sure you see a "chromedriver" executable (.exe file) once you download and unzip the folder
   - This only matters for testing changes you develop locally, because once you deploy your code to the ec2 instance, you can use the chromedriver already installed there

## Environment Variables

// in progress

## Deployment

// in progress

Restarting the server
 - sudo systemctl daemon-reload
 - sudo systemctl restart flask_app

Network settings on MongoDB

# How to connect to the EC2 Instance
Open terminal and run `ssh -i ~/Downloads/filter-dashboard-backend-key.pem ubuntu@ec2-3-144-143-77.us-east-2.compute.amazonaws.com`