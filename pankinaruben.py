import pandas as pd
import numpy as np
import streamlit as st
import datetime
from datetime import date
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

# Calcolo della data attuale e titolo
data = date.today().strftime("%d/%m/%Y")
st.header('Pankina ' + data)

shabbat = st.radio(
     'Is shabbat today?',
     ['No', 'Yes'])

# Totale mance
tip_amount = st.text_input("Total tips amount", 0.0)

waiters = st.slider('Number of waiters', value=1,
                    min_value=0, max_value=10, step=1)
barmen = st.slider('Number of barmen', value=1,
                   min_value=0, max_value=10, step=1)
ahmash = st.slider('Number of ahmash', value=0,
                   min_value=0, max_value=10, step=1)

if int(waiters) > 0:
    st.subheader('Hours per waiter')

waiter_hours = np.array([0.0 for x in range(int(waiters))])

for i in range(int(waiters)):
    start_hours_txt = "Start time waiter " + str(i + 1)
    start_time = st.time_input(start_hours_txt, datetime.time(10, 0))
    start = datetime.datetime.combine(datetime.date.today(), start_time)
    end_hours_txt = "End time waiter " + str(i + 1)
    end_time = st.time_input(end_hours_txt, datetime.time(17, 30))
    end = datetime.datetime.combine(datetime.date.today(), end_time)
    difference = end - start
    if difference.total_seconds() / 3600 < 0:
        waiter_hours[i] = 24 + difference.total_seconds() / 3600
    else:
        waiter_hours[i] = difference.total_seconds() / 3600

if int(barmen) > 0:
    st.subheader('Hours per barman')

barman_hours = np.array([0.0 for x in range(int(barmen))])

for i in range(int(barmen)):
    start_hours_txt = "Start time barman " + str(i + 1)
    start_time = st.time_input(start_hours_txt, datetime.time(12, 0))
    start = datetime.datetime.combine(datetime.date.today(), start_time)
    end_hours_txt = "End time barman " + str(i + 1)
    end_time = st.time_input(end_hours_txt, datetime.time(18, 0))
    end = datetime.datetime.combine(datetime.date.today(), end_time)
    difference = end - start
    if difference.total_seconds() / 3600 < 0:
        barman_hours[i] = 24 + difference.total_seconds() / 3600
    else:
        barman_hours[i] = difference.total_seconds() / 3600

if int(ahmash) > 0:
    st.subheader('Hours per ahmash')

ahmash_hours = np.array([0.0 for x in range(int(ahmash))])

for i in range(int(ahmash)):
    start_hours_txt = "Start time ahmash " + str(i + 1)
    start_time = st.time_input(start_hours_txt, datetime.time(12, 0))
    start = datetime.datetime.combine(datetime.date.today(), start_time)
    end_hours_txt = "End time ahmash " + str(i + 1)
    end_time = st.time_input(end_hours_txt, datetime.time(18, 0))
    end = datetime.datetime.combine(datetime.date.today(), end_time)
    difference = end - start
    if difference.total_seconds() / 3600 < 0:
        ahmash_hours[i] = 24 + difference.total_seconds() / 3600
    else:
        ahmash_hours[i] = difference.total_seconds() / 3600

if shabbat == 'No':
    # Le prime due ore sono 35 shekels ciascuna
    waiter_hours[0] -= 2
    total_tip = float(tip_amount) - 70
else:
    total_tip = float(tip_amount)

total_hours_waiters = np.sum(waiter_hours)
total_hours_barmen = np.sum(barman_hours)
total_hours_ahmashim = np.sum(ahmash_hours)

restaurant_entry = total_hours_waiters * 3
total_tip = float(total_tip) - restaurant_entry
tip_per_hour = total_tip / total_hours_waiters

# Calcolo differenziale per determinare se il tip per hour supera le 72 NIS
if tip_per_hour > 72:
    # Modifica il calcolo delle mance dei barman per far sì che ricevano l'equivalente di mezza ora dei camerieri
    barman_tip = min((total_tip / 2) / total_hours_barmen, total_tip)  # Assicura che il barman non guadagni più del totale delle mance
else:
    barman_tip = total_tip / total_hours_barmen

# Parametro Ahmash
ahmash_tip = total_tip / total_hours_ahmashim

results = {}

results['Shabbat'] = str(shabbat)
results['Total tips'] = str(tip_amount)
results['Tip per hour (waiter)'] = str("{:.1f}".format(tip_per_hour))

a = 0

for i, waiter in enumerate(waiter_hours):
    name = 'Waiter ' + str(i + 1)
    value = waiter * tip_per_hour
    results[name] = str("{:.1f}".format(value))
    a += value

for i, barman in enumerate(barman_hours):
    name = 'Barman ' + str(i + 1)
    value = barman * barman_tip
    results[name] = str("{:.1f}".format(value))
    a += value

for i, ahmash in enumerate(ahmash_hours):
    name = 'Ahmash ' + str(i + 1)
    value = ahmash * ahmash_tip
    results[name] = str("{:.1f}".format(value))
    a += value

results['Restaurant'] = str("{:.1f}".format(restaurant_entry))
a += restaurant_entry

st.subheader('Tips per worker')
df = pd.DataFrame.from_dict(results, orient='index')
df = df.rename({0: 'tips'}, axis='columns')
df.reset_index(inplace=True)
df = df.rename(columns={'index': 'worker'})
st.write(df)

smtp_server = "smtp.gmail.com"
port = 587  # Per starttls
sender_email = "pankinatip@gmail.com"
password = 'M1chelangel0'
recipients = ["pankinatlv@gmail.com"]
receiver_email = [elem.strip().split(',') for elem in recipients]

context = ssl.create_default_context()

msg = MIMEMultipart()
msg['Subject'] = 'Pankina ' + data
msg['From'] = sender_email

html = """\
<html>
  <head></head>
  <body>
    {0}
  </body>
</html>
""".format(df.to_html())

part1 = MIMEText(html, 'html')
msg.attach(part1)

if st.button('Send Email'):
    try:
        server = smtplib.SMTP(smtp_server, port)
        server.ehlo()  # Può essere omesso
        server.starttls(context=context)  # Protegge la connessione
        server.ehlo()  # Può essere omesso
        server.login(sender_email, password)
        server.sendmail(msg['From'], receiver_email, msg.as_string())
        st.success('Email sent successfully')
    except Exception as e:
        st.error('Check connection')
    finally:
        server.quit()
