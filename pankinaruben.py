import pandas as pd
import numpy as np
import streamlit as st
import datetime
from datetime import date
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

# Calcolo data attuale e titolo
data = date.today().strftime("%d/%m/%Y")
st.header('Pankina ' + data)

shabbat = st.radio(
     'Is shabbat today?',
     ['No', 'Yes'])

# Tips totali
tip_amount = st.text_input("Total tips amount", 0.0)

waiters = st.slider('Number of melzarim', value=1,
                    min_value=0, max_value=10, step=1)
barmen = st.slider('Number of barmanim', value=1,
                   min_value=0, max_value=10, step=1)
ahmash = st.slider('Number of ahmash', value=0,
                   min_value=0, max_value=10, step=1)

if int(waiters) > 0:
    st.subheader('Hours per melzar')

melzarim = np.array([0.0 for x in range(int(waiters))])

for i in range(int(waiters)):
    start_hours_txt = "Start time melzar " + str(i + 1)
    start_time = st.time_input(start_hours_txt, datetime.time(10, 0))
    start = datetime.datetime.combine(datetime.date.today(), start_time)
    end_hours_txt = "End time melzar " + str(i + 1)
    end_time = st.time_input(end_hours_txt, datetime.time(17, 30))
    end = datetime.datetime.combine(datetime.date.today(), end_time)
    difference = end - start
    if difference.total_seconds() / 3600 < 0:
        st.write(24 + difference.total_seconds() / 3600)
        melzarim[i] = 24 + difference.total_seconds() / 3600
    else:
        st.write(difference.total_seconds() / 3600)
        melzarim[i] = difference.total_seconds() / 3600

if int(barmen) > 0:
    st.subheader('Hours per barman')

barmanim = np.array([0.0 for x in range(int(barmen))])

for i in range(int(barmen)):
    start_hours_txt = "Start time barman " + str(i + 1)
    start_time = st.time_input(start_hours_txt, datetime.time(12, 0))
    start = datetime.datetime.combine(datetime.date.today(), start_time)
    end_hours_txt = "End time barman " + str(i + 1)
    end_time = st.time_input(end_hours_txt, datetime.time(18, 0))
    end = datetime.datetime.combine(datetime.date.today(), end_time)
    difference = end - start
    if difference.total_seconds() / 3600 < 0:
        st.write(24 + difference.total_seconds() / 3600)
        barmanim[i] = 24 + difference.total_seconds() / 3600
    else:
        st.write(difference.total_seconds() / 3600)
        barmanim[i] = difference.total_seconds() / 3600

if int(ahmash) > 0:
    st.subheader('Hours per ahmash')

ahmashim = np.array([0.0 for x in range(int(ahmash))])

for i in range(int(ahmash)):
    start_hours_txt = "Start time ahmash " + str(i + 1)
    start_time = st.time_input(start_hours_txt, datetime.time(12, 0))
    start = datetime.datetime.combine(datetime.date.today(), start_time)
    end_hours_txt = "End time ahmash " + str(i + 1)
    end_time = st.time_input(end_hours_txt, datetime.time(18, 0))
    end = datetime.datetime.combine(datetime.date.today(), end_time)
    difference = end - start
    if difference.total_seconds() / 3600 < 0:
        st.write(24 + difference.total_seconds() / 3600)
        ahmashim[i] = 24 + difference.total_seconds() / 3600
    else:
        st.write(difference.total_seconds() / 3600)
        ahmashim[i] = difference.total_seconds() / 3600

if shabbat == 'No':
    # First two hours are 35 shekels each
    melzarim[0] -= 2
    total_tip = float(tip_amount) - 70
else:
    total_tip = float(tip_amount)

total_hours_melzarim = np.sum(melzarim)
total_hours_barmanim = np.sum(barmanim)
total_hours_ahmashim = np.sum(ahmashim)

restaurant_entry = total_hours_melzarim * 3
total_tip = float(total_tip) - restaurant_entry
tip_per_hour = total_tip / total_hours_melzarim

# Calcoliamo le mance per i barman
if total_hours_barmanim > 0:
    # Percentuale barman
    if tip_per_hour >= 100:
        ahuz = 0.9
    elif tip_per_hour < 100 and tip_per_hour >= 60:
        ahuz = 0.93
    else:
        ahuz = 0.95

    # Se il tip per hour supera i 72 NIS, i barman guadagnano l'equivalente di mezza ora dei camerieri
    if tip_per_hour > 72:
        barman_tip = min((total_tip / 2) / total_hours_barmanim, total_tip)  # Assicura che il barman non guadagni più del totale delle mance
    else:
        # Altrimenti, calcoliamo normalmente la mancia per i barman
        barman_tip = (total_tip * (1 - ahuz)) / total_hours_barmanim
else:
    barman_tip = 0

# Calcoliamo le mance totali per i camerieri
total_tip_camerieri = total_tip - (barman_tip * total_hours_barmanim)

# Parametro Ahmash
if tip_per_hour >= 100:
    parametro_ahmash = 6
elif tip_per_hour < 100 and tip_per_hour >= 50:
    parametro_ahmash = 5
else:
    parametro_ahmash = total_hours_ahmashim

melzar_tip = (total_tip_camerieri * ahuz) / (total_hours_melzarim + total_hours_ahmashim / parametro_ahmash)
ahmash_tip = melzar_tip / parametro_ahmash

results = {}

results['Shabbat'] = str(shabbat)
results['Total tips'] = str(tip_amount)
results['Tip per hour (melzar)'] = str("{:.1f}".format(melzar_tip))

a = 0

for i, melzar in enumerate(melzarim):
    name = 'Waiter ' + str(i + 1)
    if i == 0:
        if shabbat == 'No':
            value = (melzar_tip) * melzar + 70
            results[name] = str("{:.1f}".format(value))
            a += value
        else:
            value = (melzar_tip) * melzar
            results[name] = str("{:.1f}".format(value))
            a += value
    else:
        # Adjust tip calculation based on hourly rate
        if melzar_tip > 72:
            # Waiter making more than 72 per hour
            # Calculate the difference between the hourly rate and 72
            difference = melzar_tip - 72
            # Half of the difference is awarded to the bartender
            award_to_bartender = (difference / 2) * melzar
            # Deduct the awarded amount from the waiter's tip
            value = (melzar_tip - (difference / 2)) * melzar
            results[name] = str("{:.1f}".format(value))
            a += value
            # Award the calculated amount to the bartender
            barman_name = 'Bartender 1'  # Assuming there's only one bartender
            results[barman_name] = str("{:.1f}".format(award_to_bartender))
            a += award_to_bartender
        else:
            # Waiter making less than 72 per hour
            value = (melzar_tip) * melzar
            results[name] = str("{:.1f}".format(value))
            a += value

for i, barman in enumerate(barmanim):
    name = 'Barman ' + str(i + 1)
    value = barman_tip * barman
    results[name] = str("{:.1f}".format(value))
    a += value

for i, ahmash in enumerate(ahmashim):
    name = 'Ahmash ' + str(i + 1)
    value = ahmash_tip * ahmash
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
port = 587  # For starttls
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
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender_email, password)
        server.sendmail(msg['From'], receiver_email, msg.as_string())
        st.success('Email sent successfully')
    except Exception as e:
        st.error('Check connection')
    finally:
        server.quit()
