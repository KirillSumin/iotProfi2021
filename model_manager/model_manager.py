import PySimpleGUI as sg
# import PySimpleGUIWeb as sg
import paho.mqtt.client as paho
import ssl
from sensor import BMP180

import RPi.GPIO as GPIO
import dht11 as dht11_sens

buzzer_state = "0"
ventilation_state = "0"
delay_pub = 2000

mcs_id = ""  # paste id
mcs_username = ""  # paste username
mcs_password = ""  # paste password
sert_dir = ""  # paste path to certificate
mcs_domain = ""  # paste domain

dht11_pin = 14
stby = 16
a_in1 = 20
a_in2 = 21
buzzer_pin = 23


def mqtt_init():
    mcs = paho.Client(client_id=mcs_id)
    mcs.username_pw_set(mcs_username, password=mcs_password)
    # mcs.on_log = on_log    #mqtt logs
    mcs.on_connect = on_connect
    mcs.tls_set(sert_dir, tls_version=ssl.PROTOCOL_TLSv1_2)
    mcs.tls_insecure_set(False)
    mcs.connect(mcs_domain, 8883, 60)
    mcs.loop_start()
    return mcs


def gpio_and_dht_init():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    dht11 = dht11_sens.DHT11(pin=dht11_pin)
    GPIO.setup(a_in1, GPIO.OUT, initial=0)
    GPIO.setup(a_in2, GPIO.OUT, initial=0)
    GPIO.setup(stby, GPIO.OUT, initial=0)
    GPIO.setup(buzzer_pin, GPIO.OUT, initial=0)
    return dht11


def on_message_ventilation(client, userdata, message):
    ventilation_state = str(message.payload.decode("utf-8"))
    if ventilation_state == "1":
        window['ventilation_state'].update("Включена")
        GPIO.output(stby, 1)
        GPIO.output(a_in1, 0)
        GPIO.output(a_in2, 1)
    elif ventilation_state == "0":
        window['ventilation_state'].update("Выключена")
        GPIO.output(stby, 0)
        GPIO.output(a_in1, 0)
        GPIO.output(a_in2, 0)


def on_message_buzzer(client, userdata, message):
    buzzer_state = str(message.payload.decode("utf-8"))
    if buzzer_state == "1":
        window['buzzer_state'].update("Включена")
        GPIO.output(buzzer_pin, GPIO.HIGH)
    elif buzzer_state == "0":
        window['buzzer_state'].update("Выключена")
        GPIO.output(buzzer_pin, GPIO.LOW)


# def on_log(client, userdata, level, buf):       #mqtt logs
#     print("log: ", buf)


def on_connect(client, userdata, flags, rc):
    client.message_callback_add("mcs/ventilation", on_message_ventilation)
    client.message_callback_add("mcs/buzzer", on_message_buzzer)


def window_init():
    sg.theme('Dark Blue 3')
    layout = [[sg.Text('DHT11, температура и влажность:'), ],
              [sg.Text(size=(5, 1), key='dht11_temp'), sg.Text('°C, '), sg.Text(size=(5, 1), key='dht11_hum'),
               sg.Text('%')],
              [sg.Text('BME180 температура, давление:'), ],
              [sg.Text(size=(5, 1), key='bme180_temp'), sg.Text('°C, '), sg.Text(size=(7, 1), key='bme180_pres'),
               sg.Text('гПа')],
              [sg.Text('Состояние вентиляции:'), sg.Text(size=(10, 1), key='ventilation_state')],
              [sg.Text('Состояние сирены:'), sg.Text(size=(10, 1), key='buzzer_state')],
              [sg.Button('Disconnect')]]
    return sg.Window('Мониторинг состояния', layout, font=("Helvetica", 20))


def bmp_read_and_init():
    try:
        bmp = BMP180(1, 0x77)
        cur_temp_bmp180 = bmp.temperature().C
        cur_pres_bmp180 = bmp.pressure().hPa
    except:
        cur_temp_bmp180 = "---"
        cur_pres_bmp180 = "---"
    return cur_temp_bmp180, cur_pres_bmp180


mcs = mqtt_init()

window = window_init()

try:
    dht11 = gpio_and_dht_init()
    event, values = window.read(1)
    window['buzzer_state'].update("---")
    window['ventilation_state'].update("---")
    while True:
        dht11_result = dht11.read()
        if dht11_result.is_valid():
            window['dht11_temp'].update(dht11_result.temperature)
            window['dht11_hum'].update(dht11_result.humidity)
            mcs.publish("mcs/temp1", dht11_result.temperature)
            # mcs.publish("mcs/hum", dht11_result.humidity)
        cur_temp_bmp180, cur_pres_bmp180 = bmp_read_and_init()
        window['bme180_temp'].update(cur_temp_bmp180)
        window['bme180_pres'].update(cur_pres_bmp180)
        mcs.publish("mcs/temp2", cur_temp_bmp180)
        # mcs.publish("mcs/pres", cur_pres_bmp180)
        event, values = window.read(delay_pub)
        if event == sg.WIN_CLOSED or event == 'Disconnect':
            mcs.disconnect()
            break
finally:
    GPIO.cleanup()
    print("Завершение программы, состояние пинов сброшено")
