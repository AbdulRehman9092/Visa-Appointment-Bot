# Visa-Appointment-Bot

This repository contains a Python script that automates the process of finding and booking visa appointments for Italy via `appointment.theitalyvisa.com`. The bot is built using `SeleniumBase` and is designed to handle the entire workflow, from logging in and solving captchas to selecting appointment slots and completing payment.

## How It Works

The script automates the following steps:
1.  **Navigation**: Opens the visa appointment portal and navigates to the "New Appointment" section.
2.  **Login & Captcha**: Handles the login process. It utilizes a separate, concurrent browser instance to solve image captchas by uploading a screenshot to an AI chat service (`easemate.ai`).
3.  **Email OTP Retrieval**: Connects to a specified Gmail account using IMAP to automatically fetch and use One-Time Passwords (OTPs) required for login and payment authorization.
4.  **Visa Selection**: Programmatically selects the visa location, category, type, and sub-type based on pre-configured values.
5.  **Slot Checking**: Continuously monitors the appointment calendar for available slots. If none are found, it gracefully restarts the process.
6.  **Slot Selection**: If slots are available, it executes custom JavaScript to find and select the latest possible date and time slot.
7.  **Applicant & Payment Forms**: Fills in applicant details, uploads required documents, and enters payment card information to finalize the booking.
8.  **Error Handling**: The bot is designed to be resilient. It detects and handles common web errors such as `403 Forbidden`, `502 Bad Gateway`, `Access Denied`, and network tunnel failures.

## Features

-   **End-to-End Automation**: Manages the complete appointment booking process without manual intervention.
-   **AI-Powered Captcha Solving**: Employs a multi-threaded approach to solve complex image captchas, preventing the main automation flow from being blocked.
-   **Automatic OTP Handling**: Fetches OTPs directly from an email inbox for seamless two-factor authentication.
-   **Advanced JavaScript Injection**: Uses tailored JavaScript snippets to interact with complex UI components like Kendo UI dropdowns and calendars, ensuring precise selections.
-   **Resilient Operation**: Includes robust error-checking and retry logic to handle common website and network issues gracefully.
-   **State-Aware Logic**: Tracks the current URL to understand the state of the application and calls the appropriate handler for each step of the workflow.

## Configuration

Before running the script, you must configure several hardcoded values directly within the `Visa appointment.py` file.

1.  **IMAP Credentials**: In the `imap()` function, replace the placeholder values for `USERNAME` and `PASSWORD`. For Gmail, you must use an **App Password**.
    ```python
    # In imap() function
    USERNAME = "your-email@gmail.com"
    PASSWORD = "your_gmail_app_password"
    ```
2.  **Login Credentials**:
    - In `handle_login_type()`, replace `'youremail'` with your login email.
    - In `handle_logincaptcha_type()`, replace `'yourPassword'` with your portal password.
    ```python
    # In handle_login_type()
    visible.value = 'your-email@gmail.com';

    # In handle_logincaptcha_type()
    visible.value = 'your_portal_password';
    ```
3.  **Visa Details**: In `handle_visa_type()`, modify the `pickList` array to match your desired appointment criteria.
    ```python
    # In handle_visa_type()
    var pickList = [
        ["Location",    "Lahore"],
        ["Category",    "Normal"],
        ["Visa Type",   "National Visa"],
        ["Visa Sub Type","Study"]
    ];
    ```
4.  **Applicant Data**: In `handle_datafill_type()`, update the file path for the photo upload and the travel dates.
    ```python
    # In handle_datafill_type()
    sb.send_keys("input#uploadfile-1", r"C:\path\to\your\pic.png")
    sb.type("input#TravelDate", "2025-09-15")
    sb.type("input#IntendedDateOfArrival", "2025-09-15")
    sb.type("input#IntendedDateOfDeparture", "2025-09-16")
    ```
5.  **Payment Information**: In `handle_merchant_type()`, replace the placeholder values for the credit/debit card details.
    ```python
    # In handle_merchant_type()
    sb.driver.switch_to.active_element.send_keys("your_card_number")
    # ...
    if (span.textContent.trim() === "August") { // Replace with expiry month
        span.click();
    }
    # ...
    if (span.textContent.trim() === "2030") { // Replace with expiry year
        span.click();
    }
    # ...
    cvvInput.value = "123"; // Replace with your CVV
    ```

## Prerequisites

-   Python 3.x
-   `seleniumbase` library

## Installation

1.  Clone the repository:
    ```sh
    git clone https://github.com/abdulrehman9092/visa-appointment-bot.git
    cd visa-appointment-bot
    ```

2.  Install the required Python package:
    ```sh
    pip install seleniumbase
    ```

## Usage

After configuring the script as described above, run it from your terminal:
```sh
python "Visa appointment.py"
```
The script will launch a browser window and begin the automated appointment booking process. It will print its progress and any detected errors to the console.
