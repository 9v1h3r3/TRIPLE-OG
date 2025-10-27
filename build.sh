#!/bin/bash
echo "🔧 Starting build process on Render..."

# Install Chrome for Render
apt-get update
apt-get install -y wget curl unzip

# Install Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
apt-get update
apt-get install -y google-chrome-stable

# Check Chrome version
google-chrome --version

# Install ChromeDriver
CHROME_VERSION=$(google-chrome --version | awk '{print $3}')
CHROMEDRIVER_VERSION=$(echo $CHROME_VERSION | cut -d'.' -f1,2,3)
wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip"
unzip -q chromedriver-linux64.zip
mv chromedriver-linux64/chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver

# Check ChromeDriver
chromedriver --version

# Create necessary directories
mkdir -p data/logs
mkdir -p templates
mkdir -p static

# Create default messages file if not exists
if [ ! -f "data/messages.txt" ]; then
    echo "Hello from Render Bot!" > data/messages.txt
    echo "This is automated message" >> data/messages.txt
    echo "Deployed on Render cloud" >> data/messages.txt
fi

echo "✅ Build completed successfully!"
