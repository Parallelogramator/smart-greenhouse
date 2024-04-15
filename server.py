import flask
from flask import Flask, request, jsonify, render_template
import requests, sqlite3, threading, time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
users = {
    'Pumbiwe': '1234pw'
}
authorized_users = dict()

def save_hist(x, y, name):
    plt.close()
    plt.plot(x, y)
    plt.savefig(name)


def controll(temperature, humidity, humidity_earth):
    # Например, если температура выше 30 градусов, включаем реле1
    if humidity > average_humidity + dispersion_humidity:
        control_dict['ventilation'] = 1
    elif humidity < average_humidity - dispersion_humidity:
        control_dict['vibr_water'] = 1
        control_dict['ventilation'] = 0
    else:
        control_dict['ventilation'] = 0
        control_dict['vibr_water'] = 0
    if temperature < average_temperatures - dispersion_temperatures:
        control_dict['term'] = 1
    elif temperature == average_temperatures:
        control_dict['term'] = 0
    elif temperature > average_temperatures + dispersion_temperatures:
        control_dict['ventilation'] = 1

    if humidity_earth < average_humidity_earth - dispersion_humidity_earth:
        control_dict['water'] = 1
    else:
        control_dict['water'] = 0



def read_db():
    conn = sqlite3.connect('web.db')
    c = conn.cursor()
    c.execute('SELECT * FROM Grafics')
    fetch = c.fetchall()
    conn.close()
    return fetch


def update_db(temperature, humidity, humidity_earth):
    conn = sqlite3.connect('web.db')  # Данное соединение создаст файл web.db, если таковой не существует
    c = conn.cursor()

    # Вставляем данные в таблицу
    c.execute('''
        INSERT INTO Grafics (temperature, humidity, humidity_earth, time)
        VALUES (?, ?, ?, ?)
    ''', (temperature, humidity, humidity_earth, time.ctime(time.time()).split()[3]))

    # Сохраняем изменения
    conn.commit()

    # Закрываем соединение с базой данных
    conn.close()

values = dict()
app = Flask(__name__)

# Список устройств и их состояний (0 - выключено, 1 - включено)
control_dict = {'ventilation': 1,
     'water': 0,
     'term': 1,
     'vibr_water': 1}

# вот эти значения нужно принять из веба, после можно сохранить в текстовый файл для защиты от перезапуска
average_temperatures = 20
dispersion_temperatures = 5

average_humidity_earth = 20
dispersion_humidity_earth = 5

average_humidity = 20
dispersion_humidity = 5

# IP-адрес и порт NodeMCU
node_mcu_ip = "192.168.0.15"  # Замените на IP-адрес вашего NodeMCU
node_mcu_port = 5000  # Замените на порт NodeMCU


# а это базовый вызов для сайта
@app.route('/', methods=['GET', 'POST'])
def base_data():
    global average_humidity, average_temperatures
    temperature, humidity, times = [el[0] for el in read_db()], [el[1] for el in read_db()], [el[3] for el in read_db()]

    plt.plot(times, temperature)

    # Сохранение графика в объект BytesIO
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Преобразование графика в формат данных, который можно использовать в HTML
    data = base64.b64encode(buf.read()).decode()
    buf.close()
    if request.method == 'POST':
        if request.form['avg_temperature']:
            average_temperatures = int(request.form['avg_temperature'])
        if request.form['avg_humidity']:
            average_temperatures = int(request.form['avg_humidity'])

        print(request.form)
        return render_template("datachanger.html", hist="hist.png", hist1="hist1.png", data=data)
    save_hist(times, temperature, 'hist.png')
    save_hist(times, humidity, 'hist1.png')


    return render_template("datachanger.html", hist="hist.png", hist1="hist1.png", data=data)


@app.route('/submit_data', methods=['POST'])
def submit():
    global values
    for tup in dict(request.form).items():
        values[tup[0]] = tup[1]
    print(values)
    return flask.redirect('/')


@app.route('/login')
def login_user():
    username = request.args.get('login')
    password = request.args.get('password')
    print(username, password)
    if username and password:
        if username in users:
            if users[username] == password:
                authorized_users[request.remote_addr] = username
                return render_template("authorized.html")
        return render_template("wrong_password.html")
    if request.remote_addr not in authorized_users:
        return render_template("auth.html")
    else:
        return render_template("authorized.html")


@app.route('/hist.png', methods=['GET', 'POST'])
def hist():
    with open('hist.png', 'rb') as file:
        return file.read()

@app.route('/hist1.png', methods=['GET', 'POST'])
def hist1():
    with open('hist1.png', 'rb') as file:
        return file.read()


# Маршрут для получения данных от NodeMCU
@app.route('/update_data', methods=['POST'])
def update_data():
    global control_dict
    data = request.get_json()

    print(data)
    for k in data.items():
        print(k)
    temperature = float(data.get("temperature"))
    humidity = float(data.get("humidity"))

    humidity_earth = float(data.get("humidity_earth"))

    # Здесь вы можете добавить код для обработки данных и логики
    # на основе полученных значений температуры и влажности.
    controll(temperature, humidity, humidity_earth)
    db_thread = threading.Thread(target=update_db, args=(temperature, humidity, humidity_earth))
    db_thread.start()

    # эта хрень просто ответ. можно прочесть на ардуине
    return str(control_dict)


# а отсюда мы можем брать значения
@app.route('/get_data', methods=['GET'])
def get_data():
    global control_dict
    # Возвращаем данные в формате JSON
    return control_dict


def get_weather():
    '''response = requests.get(
        f"http://api.openweathermap.org/geo/1.0/direct?q=Москва&limit={1}&appid=457c544c41ade9c83e72506da2b6a53e")
    print(response.json())
    lat = response.json()[0]['lat']
    lon = response.json()[0]['lon']
    response = requests.get(
        f"https://api.openweathermap.org/data/2.5/forecast/hourly?lat={lat}&lon={lon}&units=metric&lang=ru&cnt=2&&appid=457c544c41ade9c83e72506da2b6a53e")
    '''
    response = requests.get(
        f"http://api.weatherapi.com/v1/forecast.json?&q=Moscow&days=2&aqi=yes&alerts=no&key=e6445624d3694167836183224242603")
    data = response.json()
    print(data)


if __name__ == '__main__':
    get_weather()
    app.run(host='0.0.0.0', port=5000)
