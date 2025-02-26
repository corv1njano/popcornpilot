#!/bin/bash

# ensure script has executable and writable permissions
chmod +x "$0"
chmod u+w "$0"

# function to check and install a Python package
check_and_install() {
    module_name=$1
    package_name=$2

    if ! python3 -c "import $module_name" &> /dev/null; then
        echo "$module_name is not installed. Installing $package_name..."
        python3 -m pip install --user --upgrade "$package_name"

        if ! python3 -c "import $module_name" &> /dev/null; then
            echo "ERROR: $module_name could not be installed."
            echo "Please check your internet connection or install manually with:"
            echo "    python3 -m pip install --user --upgrade $package_name"
            exit 1
        else
            echo "Successfully installed $package_name."
        fi
    else
        echo "$module_name is already installed."
    fi
}

# check if running with admin privileges (Windows Git Bash)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    if ! net session > /dev/null 2>&1; then
        echo "ERROR: Please restart Git Bash as Administrator to avoid permission issues!"
        exit 1
    fi
fi

# check if python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed. Please install Python and try again."
    exit 1
fi

# update pip
echo "Updating pip..."
python3 -m pip install --upgrade pip

# check required packages and install them if needed
check_and_install "flask" "flask"
check_and_install "speech_recognition" "SpeechRecognition"
check_and_install "dotenv" "python-dotenv"

echo "All required packages are successfully installed and ready to use!"