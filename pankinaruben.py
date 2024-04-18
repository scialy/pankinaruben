from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
import streamlit as st
import smtplib, ssl
import pandas as pd
import numpy as np
import datetime

##################################### CONFIGURATION #####################################
MINIMUM_FOR_WAITER_BEFORE_GIVING_TO_BARMAN = 50
BARMAN_PERCENTAGE = 0.33
MAXIMUM_HOURS_FOR_ALL_BARMEN_TOGETHER = 15 # Hours
FIRST_TWO_HOURS_OF_FIRST_WAITER = 35 #Each hour
#####################################cinoli
# ####################################################

def setup_initial_form():
    st.header('Pankina ' + date.today().strftime("%d/%m/%Y"))
    shabbat = st.radio(
        'Is shabbat today?',
        ['No', 'Yes'])
    # Tips totali
    tip_amount = st.text_input("Total tips amount", 0.0)
    waiters = setup_form_for_worker("melzar")
    barmans = setup_form_for_worker("barmen")
    ahmash = setup_form_for_worker("ahmash", default_value=0)
    return shabbat, tip_amount, waiters, barmans, ahmash


def setup_worker_form(worker: str, number: int):
    if number > 0:
        st.subheader(f'Hours per {worker}')

    workers_arr = np.array([0.0 for x in range(number)])

    for i in range(number):
        start_hours_txt = f"Start time {worker} " + str(i + 1)
        start_time = st.time_input(start_hours_txt, datetime.time(10, 0))
        start = datetime.datetime.combine(datetime.date.today(), start_time)
        end_hours_txt = f"End time {worker} " + str(i + 1)
        end_time = st.time_input(end_hours_txt, datetime.time(17, 30))
        end = datetime.datetime.combine(datetime.date.today(), end_time)
        difference = end - start
        if difference.total_seconds() / 3600 < 0:
            st.write(24 + difference.total_seconds() / 3600)
            workers_arr[i] = 24 + difference.total_seconds() / 3600
        else:
            st.write(difference.total_seconds() / 3600)
            workers_arr[i] = difference.total_seconds() / 3600

    return workers_arr


def setup_form_for_worker(worker, default_value=1):
    number_selected = st.slider(f'Number of {worker}', value=default_value,
              min_value=0, max_value=10, step=1)
    return setup_worker_form(worker, number_selected)


def regular_pipeline(total_hours_melzarim, total_hours_barmanim, total_hours_ahmashim, total_tip):
    restaurant_fee = total_hours_melzarim * 3
    total_tip = float(total_tip) - restaurant_fee
    tip_per_hour = total_tip / total_hours_melzarim

    ahuz = 1
    if total_hours_barmanim > 0:
        # Percentuale barman
        if tip_per_hour >= 100:
            ahuz = 0.9
        elif tip_per_hour < 100 and tip_per_hour >= 60:
            ahuz = 0.93
        else:
            ahuz = 0.95

    barman_tip = (total_tip * (1 - ahuz)) / total_hours_barmanim

    parametro_ahmash = total_hours_ahmashim
    if tip_per_hour >= 100:
        parametro_ahmash = 6
    elif tip_per_hour < 100 and tip_per_hour >= 50:
        parametro_ahmash = 5

    ahmash_hours = 0
    if total_hours_ahmashim > 0:
        ahmash_hours = total_hours_ahmashim / parametro_ahmash


    melzar_tip = (total_tip * ahuz) / (total_hours_melzarim + ahmash_hours)
    ahmash_tip = melzar_tip / parametro_ahmash

    return melzar_tip, barman_tip, ahmash_tip, restaurant_fee


def new_pipeline(total_tip, restaurant_fee, total_hours_melzarim, total_hours_barmanim, total_hours_ahmashim, ahmash_tip):
    tip_to_distribute = total_tip - restaurant_fee - (ahmash_tip * total_hours_ahmashim)

    meltzarim = MINIMUM_FOR_WAITER_BEFORE_GIVING_TO_BARMAN * total_hours_melzarim

    if tip_to_distribute >= meltzarim:
        tip_to_distribute -= meltzarim
        barmanim = MINIMUM_FOR_WAITER_BEFORE_GIVING_TO_BARMAN * BARMAN_PERCENTAGE * min(total_hours_barmanim, MAXIMUM_HOURS_FOR_ALL_BARMEN_TOGETHER)
        if tip_to_distribute >= barmanim:
            tip_to_distribute -= barmanim
            melzar_bonus = tip_to_distribute / (total_hours_melzarim + (BARMAN_PERCENTAGE * min(total_hours_barmanim, MAXIMUM_HOURS_FOR_ALL_BARMEN_TOGETHER)))
            return MINIMUM_FOR_WAITER_BEFORE_GIVING_TO_BARMAN + melzar_bonus, barmanim + (melzar_bonus * BARMAN_PERCENTAGE * min(total_hours_barmanim, MAXIMUM_HOURS_FOR_ALL_BARMEN_TOGETHER))
        return MINIMUM_FOR_WAITER_BEFORE_GIVING_TO_BARMAN, tip_to_distribute
    return tip_to_distribute / total_hours_melzarim, 0


shabbat, tip_amount, melzarim, barmanim, ahmashim = setup_initial_form()
if shabbat == 'No':
    # First two hours are 35 shekels each
    melzarim[0] -= 2
    total_tip = float(tip_amount) - (2 * FIRST_TWO_HOURS_OF_FIRST_WAITER)
else:
    total_tip = float(tip_amount)


total_hours_melzarim = np.sum(melzarim)
total_hours_barmanim = np.sum(barmanim)
total_hours_ahmashim = np.sum(ahmashim)

_, _, ahmash_tip, restaurant_fee = regular_pipeline(total_hours_melzarim, total_hours_barmanim, total_hours_ahmashim, total_tip)

melzar_per_hour, barmanim_tip_for_all = new_pipeline(total_tip, restaurant_fee, total_hours_melzarim, total_hours_barmanim, total_hours_ahmashim, ahmash_tip)

results = {}

results['Shabbat'] = str(shabbat)
results['Total tips'] = str(tip_amount)
# results['Tip per hour'] = str("{:.1f}".format(tip_per_hour))
results['Tip per hour (melzar)'] = str("{:.1f}".format(melzar_per_hour))

a = 0

for i, melzar in enumerate(melzarim):
    name = 'Waiter ' + str(i + 1)
    if i == 0 and shabbat == 'No':
        value = (melzar_per_hour) * melzar + (2 * FIRST_TWO_HOURS_OF_FIRST_WAITER)
        results[name] = str("{:.1f}".format(value))
        a += value
    else:
        value = (melzar_per_hour) * melzar
        results[name] = str("{:.1f}".format(value))
        a += value


for i, barman in enumerate(barmanim):
    name = 'Barman ' + str(i + 1)
    value = barmanim_tip_for_all * (barman / total_hours_barmanim)
    results[name] = str("{:.1f}".format(value))
    a += value

for i, ahmash in enumerate(ahmashim):
    name = 'Ahmash ' + str(i + 1)
    value = ahmash_tip * ahmash
    results[name] = str("{:.1f}".format(value))
    a += value

results['Restaurant'] = str("{:.1f}".format(restaurant_fee))
a += restaurant_fee
results['Total'] = a
# st.write(a)

st.subheader('Tips per worker')
# st.write(tip_per_hour)
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

# Create a secure SSL context
context = ssl.create_default_context()

msg = MIMEMultipart()
msg['Subject'] = 'Pankina ' + date.today().strftime("%d/%m/%Y")
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
    # Try to log in to server and send email
    try:
        server = smtplib.SMTP(smtp_server, port)
        server.ehlo()  # Can be omitted
        server.starttls(context=context)  # Secure the connection
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(msg['From'], receiver_email, msg.as_string())
        st.success('Email sent successfully')
    except Exception as e:
        # Print any error messages to stdout
        st.error('Check connection')
    finally:
        server.quit()
