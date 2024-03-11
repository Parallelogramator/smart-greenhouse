import requests, sqlite3, threading, time
import dash
from dash import dcc, html
import plotly.graph_objs as go
from dash.dependencies import Output, Input
from flask import Flask, request, render_template, make_response, redirect, url_for

app = Flask(__name__)
dash_app = dash.Dash(__name__, server=app, routes_pathname_prefix='/graf/')

dash_app.layout = html.Div(children=[
    dcc.Graph(id='live-update-graph'),
    dcc.Interval(
        id='interval-component',
        interval=1 * 1000,  # in milliseconds
        n_intervals=0
    ),
    dcc.Slider(
        min=0,
        max=50,
        marks={i: '{}'.format(i) for i in range(10, 50, 10)},
        value=20,
        id='my-slider'
    )
])


@dash_app.callback(Output('live-update-graph', 'figure'),
                   Input('my-slider', 'value'))
def update_graph_live(value):
    # функция для чтения данных из базы данных
    print(value)
    value = int(value)
    data = read_db()
    temperatures = [el[1] for el in data[-value:]]
    humidities = [el[2] for el in data[-value:]]
    humidities_earth = [el[3] for el in data[-value:]]
    times = [el[4] for el in data[-value:]]

    traces = list()
    traces.append(go.Scatter(
        x=times,
        y=temperatures,
        name='Temperature',
        mode='lines+markers'
    ))

    traces.append(go.Scatter(
        x=times,
        y=humidities,
        name='Humidity',
        mode='lines+markers'
    ))
    traces.append(go.Scatter(
        x=times,
        y=humidities_earth,
        name='Humidity earth',
        mode='lines+markers'
    ))

    return {
        'data': traces,
    }


def controll(temperature, humidity, humidity_earth):
    # Например, если температура выше 30 градусов, включаем реле1
    if humidity > average_humidity + dispersion_humidity:
        contr['ventilation'] = 1
    elif humidity < average_humidity - dispersion_humidity:
        contr['vibr_water'] = 1
        contr['ventilation'] = 0
    else:
        contr['ventilation'] = 0
        contr['vibr_water'] = 0
    if temperature < average_temperatures - dispersion_temperatures:
        contr['term'] = 1
    elif temperature == average_temperatures:
        contr['term'] = 0
    elif temperature > average_temperatures + dispersion_temperatures:
        contr['ventilation'] = 1

    if humidity_earth < average_humidity_earth - dispersion_humidity_earth:
        contr['water'] = 1
    else:
        contr['water'] = 0


def read_db():
    conn = sqlite3.connect('web.db')
    c = conn.cursor()
    c.execute('SELECT * FROM Grafics')
    fetch = c.fetchall()
    conn.close()
    return fetch


def update_db(key, temperature, humidity, humidity_earth):
    conn = sqlite3.connect('web.db')  # Данное соединение создаст файл web.db, если таковой не существует
    c = conn.cursor()

    # Вставляем данные в таблицу
    c.execute('''
        INSERT INTO Grafics (id, temperature, humidity, humidity_earth, time)
        VALUES (?, ?, ?, ?, ?)
    ''', (key, temperature, humidity, humidity_earth, time.ctime(time.time()).split()[3]))

    # Сохраняем изменения
    conn.commit()

    # Закрываем соединение с базой данных
    conn.close()


# Список устройств и их состояний (0 - выключено, 1 - включено)
contr = {'ventilation': 1,
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


@app.route('/graph')
def render_dash_app():
    return dash_app.index()


@app.route('/auth', methods=['POST'])
def auth():
    import re
    mac = request.json.get('mac')
    key = int(request.json.get('key'))

    if re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac.lower()) and key == 0:
        conn = sqlite3.connect('web.db')  # Данное соединение создаст файл web.db, если таковой не существует
        c = conn.cursor()
        c.execute("SELECT EXISTS(SELECT 1 FROM keys WHERE MAC=? LIMIT 1)", (mac,))

        if not (c.fetchone()[0]):
            # Вставляем данные в таблицу
            c.execute('INSERT INTO keys (MAC) VALUES (?)', (mac, ))
            conn.commit()

        # Сохраняем изменения

        c.execute('SELECT id FROM keys WHERE MAC = ?', (mac,))
        id_value = c.fetchone()

        # Закрываем соединение с базой данных
        conn.close()
        return str(id_value[0])
    return str('')


@app.route('/update', methods=['POST', 'GET'])
def update_values():
    new_temp = request.json.get('temperature')
    new_humidity = request.json.get('humidity')

    print(new_temp, new_humidity)
    return {'status': 'success'}, 200


@app.route('/send_new_values', methods=['POST'])
def send_new_values():
    global average_temperatures, average_humidity, average_humidity_earth, dispersion_humidity, dispersion_temperatures, dispersion_humidity_earth
    print(request.form)
    if request.form['avg_temperature']:
        average_temperatures = request.form['avg_temperature']
    if request.form['avg_humidity']:
        average_humidity = request.form['avg_humidity']
    if request.form['avg_humidity_earth']:
        average_humidity_earth = request.form['avg_humidity_earth']
    print(request)
    return redirect(url_for('index'))


@app.route('/updater', methods=['POST', 'GET'])
def update():
    html_content = render_template(
        'index.html',
        avg_temperature = average_temperatures,
        avg_humidity = average_humidity,
        avg_humidity_earth = average_humidity_earth,
    )
    response = make_response(html_content)

    return response


@app.route('/')
def index():
    html_content = render_template(
        'main.html'
    )
    response = make_response(html_content)
    return response


@app.route('/<int:pin>/<state>')
def control_pin(pin, state):
    if state == 'on':
        print(f'GPIO {pin} is turned ON')  # Simulate turning on the GPIO pin
    elif state == 'off':
        print(f'GPIO {pin} is turned OFF')  # Simulate turning off the GPIO pin
    else:
        return 'Invalid state', 400
    return index(), 200


# Маршрут для получения данных от NodeMCU
@app.route('/update_data', methods=['POST'])
def update_data():
    global contr
    data = request.get_json()

    print(data)
    for k in data.items():
        print(k)
    key = int(data['key'])
    temperature = float(data.get("temperature"))
    humidity = float(data.get("humidity"))

    humidity_earth = float(data.get("humidity_earth"))

    # Здесь вы можете добавить код для обработки данных и логики
    # на основе полученных значений температуры и влажности.
    controll(temperature, humidity, humidity_earth)
    update_db(key, temperature, humidity, humidity_earth)

    # эта хрень просто ответ. можно прочесть на ардуине
    return str(contr)


# а отсюда мы можем брать значения
@app.route('/get_data')
def get_data():
    # Получить последние данные из базы данных
    ser = read_db()[-1]
    update = {
        'temperature': ser[1],
        'humidity': ser[2],
        'humidity_earth': ser[3],
    }
    update = dict(list(update.items()) + list(contr.items()))
    return update


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
