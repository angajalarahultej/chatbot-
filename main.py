import json
import os
import ssl
import datetime
import smtplib
from email.message import EmailMessage

import streamlit as st

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

DATA_FILE = "orders.json"

# Item images mapping (add more as needed)
ITEM_IMAGES = {
    "biriyani": "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop",
    "ice": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=300&fit=crop",
    "pizza": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&h=300&fit=crop",
    "burger": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=300&fit=crop",
    "pasta": "https://images.unsplash.com/photo-1621996346565-e3dbc353d2e5?w=400&h=300&fit=crop",
    "salad": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop",
    # Add more items and their image URLs here
}

st.title("Food Delivery Chatbot")

# Sidebar notifications
st.sidebar.header("Notification settings")
st.sidebar.write("Enter recipient details and send after completing the order.")
notify_email = st.sidebar.text_input("Recipient email", value="rahultej.a@haystek.com", key="notify_email")
notify_phone = st.sidebar.text_input("Recipient phone number", key="notify_phone")
send_email = st.sidebar.checkbox("Send summary by email", value=False, key="send_email")
send_sms = st.sidebar.checkbox("Send summary by SMS", value=False, key="send_sms")

st.sidebar.markdown("---")
st.sidebar.write("Email configuration (optional):")
smtp_host = st.sidebar.text_input("SMTP host", value="smtp.gmail.com", key="smtp_host")
smtp_port = st.sidebar.text_input("SMTP port", value="465", key="smtp_port")
smtp_user = st.sidebar.text_input("SMTP user", value="rahultej2610@gmail.com", key="smtp_user")
smtp_pass = st.sidebar.text_input("SMTP password", type="password", key="smtp_pass")
email_from = st.sidebar.text_input("Email from address", value="rahultej2610@gmail.com", key="email_from")

st.sidebar.markdown("---")
st.sidebar.write("Twilio configuration (optional):")
twilio_account_sid = st.sidebar.text_input("Twilio Account SID", key="twilio_account_sid")
twilio_auth_token = st.sidebar.text_input("Twilio Auth Token", type="password", key="twilio_auth_token")
twilio_from_number = st.sidebar.text_input("Twilio From Number", key="twilio_from_number")

st.sidebar.markdown("---")
st.sidebar.write("If these fields are left blank, the app will use environment variables or Streamlit secrets.")

st.sidebar.markdown("---")
st.sidebar.write("Note: Emails include images for items like biriyani, ice, pizza, etc.")

if not TWILIO_AVAILABLE:
    st.sidebar.warning("Twilio library not installed. SMS will only work after installing 'twilio'.")

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Welcome to Food Delivery Chatbot! What's your name?"})
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'name' not in st.session_state:
    st.session_state.name = ''
if 'address' not in st.session_state:
    st.session_state.address = ''
if 'order' not in st.session_state:
    st.session_state.order = []
if 'current_item' not in st.session_state:
    st.session_state.current_item = ''
if 'order_complete' not in st.session_state:
    st.session_state.order_complete = False
if 'notification_status' not in st.session_state:
    st.session_state.notification_status = ''

# Helpers

def load_orders():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_order(order):
    orders = load_orders()
    orders.append(order)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, indent=2, ensure_ascii=False)


def format_order_summary(order):
    lines = [f"<h2>Order from {order['name']}</h2>", f"<p>Address: {order['address']}</p>", "<h3>Items:</h3>"]
    for item in order['items']:
        item_name = item['name'].lower()
        image_url = ITEM_IMAGES.get(item_name, "")
        if image_url:
            lines.append(f"<p><strong>{item['quantity']} x {item['name']}</strong><br><img src='{image_url}' alt='{item['name']}' style='max-width:300px; height:auto;'></p>")
        else:
            lines.append(f"<p><strong>{item['quantity']} x {item['name']}</strong></p>")
    lines.append(f"<p>Placed at: {order['timestamp']}</p>")
    return "\n".join(lines)


def send_email_summary(to_email, summary, smtp_host, smtp_port, smtp_user, smtp_pass, email_from):
    smtp_host = smtp_host or os.getenv('SMTP_HOST') or st.secrets.get('smtp', {}).get('host')
    smtp_port = smtp_port or os.getenv('SMTP_PORT') or st.secrets.get('smtp', {}).get('port')
    smtp_user = smtp_user or os.getenv('SMTP_USER') or st.secrets.get('smtp', {}).get('user')
    smtp_pass = smtp_pass or os.getenv('SMTP_PASS') or st.secrets.get('smtp', {}).get('pass')
    email_from = email_from or os.getenv('EMAIL_FROM') or st.secrets.get('smtp', {}).get('from')
    if not all([smtp_host, smtp_port, smtp_user, smtp_pass, email_from]):
        return False, 'SMTP variables not fully configured. Please enter SMTP settings in the sidebar, set environment variables, or configure Streamlit secrets.'
    message = EmailMessage()
    message['Subject'] = 'Food Delivery Order Summary'
    message['From'] = email_from
    message['To'] = to_email
    message.set_content(summary, subtype='html')
    try:
        port = int(smtp_port)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, port, context=context) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(message)
        return True, 'Email sent successfully.'
    except Exception as exc:
        return False, f'Email error: {exc}'


def send_sms_summary(phone_number, summary, account_sid, auth_token, from_number):
    if not TWILIO_AVAILABLE:
        return False, 'Twilio not installed. Install the twilio package to send SMS.'
    account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID') or st.secrets.get('twilio', {}).get('account_sid')
    auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN') or st.secrets.get('twilio', {}).get('auth_token')
    from_number = from_number or os.getenv('TWILIO_FROM_NUMBER') or st.secrets.get('twilio', {}).get('from_number')
    if not all([account_sid, auth_token, from_number]):
        return False, 'Twilio variables not fully configured. Please enter Twilio settings in the sidebar, set environment variables, or configure Streamlit secrets.'
    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=summary,
            from_=from_number,
            to=phone_number
        )
        return True, f'SMS sent: {message.sid}'
    except Exception as exc:
        return False, f'SMS error: {exc}'

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# Chat input
if st.session_state.step != 3:
    if prompt := st.chat_input('Type your response here...'):
        st.session_state.messages.append({'role': 'user', 'content': prompt})

        if st.session_state.step == 0:
            st.session_state.name = prompt
            st.session_state.messages.append({'role': 'assistant', 'content': "What's your delivery address?"})
            st.session_state.step = 1
        elif st.session_state.step == 1:
            st.session_state.address = prompt
            st.session_state.messages.append({'role': 'assistant', 'content': "What would you like to order? (type 'done' to finish)"})
            st.session_state.step = 2
        elif st.session_state.step == 2:
            if prompt.lower() == 'done':
                content = f"Thank you {st.session_state.name}, your order will be delivered to {st.session_state.address}."
                if st.session_state.order:
                    content += '\nHere is your order summary:'
                    for item, qty in st.session_state.order:
                        content += f"\n{qty} x {item}"
                else:
                    content += '\nYou did not add any items.'
                st.session_state.messages.append({'role': 'assistant', 'content': content})
                st.session_state.step = 3
                st.session_state.order_complete = True
            else:
                st.session_state.current_item = prompt
                st.session_state.messages.append({'role': 'assistant', 'content': f"How many {prompt}?"})
                st.session_state.step = 4
        elif st.session_state.step == 4:
            qty = prompt
            st.session_state.order.append((st.session_state.current_item, qty))
            st.session_state.messages.append({'role': 'assistant', 'content': "What would you like to order? (type 'done' to finish)"})
            st.session_state.step = 2

        st.rerun()
else:
    st.success('Order complete. Use the sidebar to save and notify.')
    order_data = {
        'name': st.session_state.name,
        'address': st.session_state.address,
        'items': [{'name': item, 'quantity': qty} for item, qty in st.session_state.order],
        'timestamp': datetime.datetime.now().isoformat(),
        'email': notify_email,
        'phone': notify_phone
    }
    summary_text = format_order_summary(order_data)
    st.markdown('**Order summary ready to save and send.**')
    st.markdown(summary_text, unsafe_allow_html=True)  # Allow HTML for images

    if st.sidebar.button('Save order and notify'):
        save_order(order_data)
        notifications = []
        if send_email and notify_email:
            success, message = send_email_summary(
                notify_email,
                summary_text,
                smtp_host,
                smtp_port,
                smtp_user,
                smtp_pass,
                email_from,
            )
            notifications.append(message)
        if send_sms and notify_phone:
            success, message = send_sms_summary(
                notify_phone,
                summary_text,
                twilio_account_sid,
                twilio_auth_token,
                twilio_from_number,
            )
            notifications.append(message)
        if not notifications:
            notifications.append('Order saved locally. No notification selected.')
        st.session_state.notification_status = '\n'.join(notifications)
        st.success('Order saved. ' + st.session_state.notification_status)

if st.session_state.notification_status:
    st.info(st.session_state.notification_status)

if st.sidebar.button('Start new order'):
    for key in ['messages', 'step', 'name', 'address', 'order', 'current_item', 'order_complete', 'notification_status']:
        if key in st.session_state:
            del st.session_state[key]
