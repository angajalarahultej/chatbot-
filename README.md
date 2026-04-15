# Food Delivery Chatbot

A simple web-based chatbot for taking food delivery orders using Streamlit.

## Usage

First, install dependencies:

```bash
pip install -r requirements.txt
```

Then, run the app locally:

```bash
python -m streamlit run main.py --server.headless true
```

Open the provided URL in your browser to interact with the chatbot.

## Deployment

To deploy this app online so others can use it:

1. **Create a GitHub repository** and push your code:
   - Create a new repo on GitHub.
   - Add all files from this project.
   - Commit and push.

2. **Deploy to Streamlit Cloud** (free and easy):
   - Go to [share.streamlit.io](https://share.streamlit.io).
   - Connect your GitHub account.
   - Select your repo and branch.
   - Set the main file path to `main.py`.
   - In the secrets section, add your SMTP and Twilio credentials (see `.streamlit/secrets.toml` for format).
   - Click Deploy.

3. **Alternative: Deploy to Heroku**:
   - Create a `Procfile` with: `web: streamlit run main.py --server.port $PORT --server.headless true`
   - Set environment variables in Heroku dashboard.
   - Push to Heroku Git.

## Notification settings

You can configure notifications in two ways:

1. Directly in the app sidebar using the SMTP and Twilio fields.
2. Or by setting environment variables for SMTP and Twilio.

For Gmail, use these defaults in the sidebar:

- SMTP host: `smtp.gmail.com`
- SMTP port: `465`
- SMTP user: `rahultej2610@gmail.com`
- SMTP password: your Gmail app password
- Email from address: `rahultej2610@gmail.com`
- Recipient email: `rahultej.a@haystek.com`

Then enable "Send summary by email" and click "Save order and notify."

To send SMS notifications via Twilio, either fill the Twilio fields in the sidebar or set these environment variables:

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_NUMBER`

Enter the recipient email or phone number in the sidebar before pressing "Save order and notify." The app also stores each order in `orders.json`.

The email summary includes images for known items (e.g., biriyani, ice) to enhance the user experience.

## Requirements

- Python 3.x
- streamlit
- twilio (optional for SMS)