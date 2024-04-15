import requests, re
import dash
from datetime import datetime, timedelta
import pandas as pd
from dash import dcc, html
import plotly.graph_objs as go
from dash.dependencies import Output, Input
from flask import Flask, request, render_template, make_response, redirect, url_for

from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Создание движка базы данных
engine = create_engine('sqlite:///web.db', echo=True)

# Создание сессии
Session = sessionmaker(bind=engine)
session = Session()

# Базовый класс моделей
Base = declarative_base()


# Определение моделей
class Grafics(Base):
    __tablename__ = 'Grafics'
    number = Column(Integer, primary_key=True)
    id = Column(Integer, ForeignKey('keys.id'))
    temperature = Column(Integer)
    humidity = Column(Integer)
    humidity_earth = Column(Integer)
    time = Column(DateTime, default=datetime.utcnow)

    keys = relationship('Keys')


class Keys(Base):
    __tablename__ = 'keys'
    id = Column(Integer, primary_key=True)
    MAC = Column(String(17), unique=True)
    permissions = relationship('Permissions', back_populates='keys')
    grafics = relationship('Grafics', back_populates='keys')


class Permissions(Base):
    __tablename__ = 'permissions'
    id = Column(Integer, ForeignKey('keys.id'), primary_key=True)
    on_TEMPERATURE = Column(Integer, default=0)
    on_HUMIDITY = Column(Integer, default=0)
    on_WATER_EARTH = Column(Integer, default=0)
    on_FOTORES = Column(Integer, default=0)
    on_WATERLEVEL = Column(Integer, default=0)
    on_VENTILATION = Column(Integer, default=0)
    on_WATER = Column(Integer, default=0)
    on_LIGHT = Column(Integer, default=0)
    on_TERM = Column(Integer, default=0)
    on_VIBR = Column(Integer, default=0)

    keys = relationship('Keys')


# Создание таблиц
Base.metadata.create_all(engine)


# Определяем функции для взаимодействия с базой данных
def read_db(id=None):
    if id is not None:
        return session.query(Grafics).filter(Grafics.id == id).all()
    else:
        return session.query(Grafics).all()


def read_id():
    return session.query(Keys.id).all()


def update_db(key, temperature, humidity, humidity_earth, light):
    new_record = Grafics(id=key, temperature=temperature, humidity=humidity, humidity_earth=humidity_earth,
                         time=datetime.now())
    session.add(new_record)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Ошибка при добавлении данных: {e}")


def controll(key, temperature, humidity, humidity_earth, light):
    # Например, если температура выше 30 градусов, включаем реле1
    if humidity and humidity > value_contr[key]['average_humidity'] + value_contr[key]['dispersion_humidity']:
        contr[key]['ventilation'] = 1
    elif humidity and humidity < value_contr[key]['average_humidity'] - value_contr[key]['dispersion_humidity']:
        contr[key]['vibr_water'] = 1
        contr[key]['ventilation'] = 0
    else:
        contr[key]['ventilation'] = 0
        contr[key]['vibr_water'] = 0
    if temperature and temperature < value_contr[key]['average_temperatures'] - value_contr[key][
        'dispersion_temperatures']:
        contr[key]['term'] = 1
    elif temperature and temperature == value_contr[key]['average_temperatures']:
        contr[key]['term'] = 0

    elif temperature and temperature > value_contr[key]['average_temperatures'] + value_contr[key][
        'dispersion_temperatures']:
        contr[key]['ventilation'] = 1
    if humidity_earth and humidity_earth < value_contr[key]['average_humidity_earth'] - value_contr[key][
        'dispersion_humidity_earth']:
        contr[key]['water'] = 1
    else:
        contr[key]['water'] = 0

    if light and (datetime.now().strftime('%H:%M:%S') > '19:00:00' or datetime.now().strftime('%H:%M:%S') < '07:00:00'):
        contr[key]['light'] = 1
    else:
        contr[key]['light'] = 0


def get_weather():
    response = requests.get(
        f"http://api.weatherapi.com/v1/forecast.json?&q=Moscow&days=1&aqi=yes&alerts=no&lang=ru&key=e6445624d3694167836183224242603")
    data = response.json()['forecast']['forecastday'][0]['hour'][int(datetime.now().strftime('%H'))]
    print(data)
    print(data['temp_c'])
    print(data['cloud'])
    print(data['chance_of_rain'])
    print(data['humidity'])
    print(data['wind_kph'])
    ''''ventilation': температура, ветер,
    'water': дождь, солнце,
    'term': солнце,
    'vibr_water': влажность, солнце
    '''


app = Flask(__name__)
dash_app = dash.Dash(__name__, server=app, routes_pathname_prefix='/graf/')


# Функция для преобразования данных из базы данных в Pandas DataFrame



# Переписываем функцию fetch_data_db для использования SQLAlchemy
def fetch_data_db(id_list, start, end, frequency):
    frames = []
    for _id in id_list:
        # Получаем данные с фильтрацией по id и временному диапазону
        data = session.query(Grafics).filter(
            Grafics.id == _id,
            Grafics.time.between(start, end)
        ).all()[:-1]
        print(data)

        # Преобразование списка результатов в DataFrame
        df = pd.DataFrame([{
            'id': d.id,
            'temperature': d.temperature,
            'humidity': d.humidity,
            'humidity_earth': d.humidity_earth,
            'time': d.time
        } for d in data])

        # Обработка DataFrame
        if not df.empty:
            df['time'] = pd.to_datetime(df['time'])
            df.set_index('time', inplace=True)
            df = df.resample(frequency).mean().reset_index()
            frames.append(df)

    return frames


# Переписываем функцию fetch_data_db0 для использования SQLAlchemy
def fetch_data_db0(start, end, frequency):
    # Получаем все данные за указанный временной период
    data = session.query(Grafics).filter(
        Grafics.time.between(start, end)
    ).all()[:-1]
    print(data)

    # Преобразование списка результатов в DataFrame
    df = pd.DataFrame([{
        'id': d.id,
        'temperature': d.temperature,
        'humidity': d.humidity,
        'humidity_earth': d.humidity_earth,
        'time': d.time
    } for d in data])

    # Обработка DataFrame
    if not df.empty:
        df['time'] = pd.to_datetime(df['time'])
        df.set_index('time', inplace=True)
        df = df.resample(frequency).mean().reset_index()

    return df


def convert_to_datetime(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')


base_layout = [{'label': 'Все', 'value': 0}]
# Добавление компонентов выбора временного диапазона и частоты
dash_app.layout = html.Div(children=[
    dcc.Graph(id='live-update-graph'),
    dcc.Interval(
        id='interval-component',
        interval=1 * 1000,  # in milliseconds
        n_intervals=0
    ),
    dcc.Dropdown(
        id='dropdown',
        options=base_layout + [{'label': i[0], 'value': i[0]} for i in read_id()],
        multi=True,
        value=0),
    dcc.DatePickerRange(
        id='date-picker-range',
        start_date=datetime.today() - timedelta(days=10),
        end_date=datetime.today(),
        display_format='YYYY-MM-DD'
    ),
    dcc.Dropdown(
        id='frequency-selector',
        options=[
            {'label': 'Каждый 10 минут', 'value': '10min'},
            {'label': 'Каждый 30 минут', 'value': '30min'},
            {'label': 'Каждый час', 'value': 'h'},
            {'label': 'Каждые 3 часа', 'value': '3h'},
            {'label': 'Каждые 6 часов', 'value': '6h'},
            {'label': 'Каждые 12 часов', 'value': '12h'},
            {'label': 'Ежедневно', 'value': 'D'},
            {'label': 'Еженедельно', 'value': '7D'},
            {'label': 'Ежемесячно', 'value': '30D'}
        ],
        value='30min',  # Стандартное значение - ежедневно
        clearable=False
    ),
])


# Обновляем callback
@dash_app.callback(
    Output('live-update-graph', 'figure'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('frequency-selector', 'value'),
     Input('dropdown', 'value')]
)
def update_graph_live(start_date, end_date, frequency, id_list):
    # Если никакие идентификаторы не выбраны, возвращаем пустой график
    print(id_list)

    print(type(id_list))
    if id_list == []:
        return {'data': []}
    print(id_list)
    traces = []

    # Преобразование выбора временного диапазона
    start = (start_date.split('T')[0] + ' 00:00:00')
    end = (end_date.split('T')[0] + ' 23:59:59')

    # Получение и агрегация данных

    if 0 == id_list or 0 in id_list:
        df = fetch_data_db0(start, end, frequency)
        print(df)
        traces = []
        traces.append(go.Scatter(
            x=df['time'],
            y=df['temperature'],
            mode='lines+markers',
            name=f'Temperature'
        ))
        traces.append(go.Scatter(
            x=df['time'],
            y=df['humidity'],
            mode='lines+markers',
            name=f'Humidity'
        ))
        traces.append(go.Scatter(
            x=df['time'],
            y=df['humidity_earth'],
            mode='lines+markers',
            name=f'Humidity Earth'
        ))

        return {'data': traces}
    # Создание трассировок данных для отображения в графике
    data_frames = fetch_data_db(id_list, start, end, frequency)
    print(data_frames)
    for df in data_frames:
        if not df.empty:
            # Предполагаем, что у вас есть столбцы 'temperature', 'humidity' и 'humidity_earth'
            traces.append(go.Scatter(
                x=df['time'],
                y=df['temperature'],
                mode='lines+markers',
                name=f'Temperature {df["id"][0]}'
            ))
            traces.append(go.Scatter(
                x=df['time'],
                y=df['humidity'],
                mode='lines+markers',
                name=f'Humidity {df["id"][0]}'
            ))
            traces.append(go.Scatter(
                x=df['time'],
                y=df['humidity_earth'],
                mode='lines+markers',
                name=f'Humidity Earth {df["id"][0]}'
            ))

    return {'data': traces}


values = dict()
users = {
    'Pumbiwe': '1234pw',
    'user': '12345'
}

authorized_users = {'127.0.0.1':'user'}

# Список устройств и их состояний (0 - выключено, 1 - включено)
contr = {0: {'ventilation': 1,
             'water': 1,
             'term': 1,
             'vibr_water': 1,
             'light': 0}}

value_contr = {}


@app.route('/graph')
def render_dash_app():
    if request.remote_addr not in authorized_users:
        return redirect('/login')

    return dash_app.index()


@app.route('/management', methods=['GET', 'POST'])
def management():
    if request.remote_addr not in authorized_users:
        return redirect('/login')
    if request.method == 'POST':
        selected = dict(request.form)['optradio']
        print(dict(request.form)['optradio'])

    return render_template("panel.html")


@app.route('/auth', methods=['POST'])
def auth():
    mac = request.json.get('mac')
    key = int(request.json.get('key'))

    if re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac.lower()) and key == 0:
        # Используем сессию для выполнения запросов через SQLAlchemy
        key_entry = session.query(Keys).filter_by(MAC=mac).first()
        print(key_entry)

        if not key_entry:
            # Создаем новый ключ
            key_entry = Keys(MAC=mac)
            session.add(key_entry)
            session.commit()
            print(key_entry)

            # Создаем разрешения
            permissions = Permissions(id=key_entry.id)
            session.add(permissions)
            session.commit()

        # Получаем разрешения
        permission_entry = session.query(Permissions).join(Keys).filter(Keys.MAC == mac).one()
        response = {
            'key': permission_entry.id,
            'on_TEMPERATURE': permission_entry.on_TEMPERATURE,
            'on_HUMIDITY': permission_entry.on_HUMIDITY,
            'on_WATER_EARTH': permission_entry.on_WATER_EARTH,
            'on_FOTORES': permission_entry.on_FOTORES,
            'on_WATERLEVEL': permission_entry.on_WATERLEVEL,
            'on_VENTILATION': permission_entry.on_VENTILATION,
            'on_WATER': permission_entry.on_WATER,
            'on_LIGHT': permission_entry.on_LIGHT,
            'on_TERM': permission_entry.on_TERM,
            'on_VIBR': permission_entry.on_VIBR
        }
        # Не забывайте закрывать сессию после использования
        session.close()

        contr[key_entry.id] = {'ventilation': 0,
                              'water': 0,
                              'term': 0,
                              'vibr_water': 0,
                              'light': 0}

        value_contr[key_entry.id] = {'average_temperatures': 20,
                                    'dispersion_temperatures': 5,
                                    'average_humidity_earth': 20,
                                    'dispersion_humidity_earth': 5,
                                    'average_humidity': 20,
                                    'dispersion_humidity': 5}
        return str(response)
    return str('')


@app.route('/login')
def login_user():
    r = request.args.get('r')
    print(r)
    if r:
        authorized_users[request.remote_addr] = r
    username = request.args.get('login')
    password = request.args.get('password')
    print(username, password)
    if username and password:
        if username in users:
            if users[username] == password:

                if authorized_users[request.remote_addr]:
                    r = authorized_users[request.remote_addr]
                    authorized_users[request.remote_addr] = username
                    return redirect(url_for(r))
                else:
                    return render_template("authorized.html")
        return render_template("wrong_password.html")
    return render_template("auth.html")


@app.route('/update', methods=['POST', 'GET'])
def update_values():
    if request.remote_addr not in authorized_users:
        return redirect('/login?r=update_values')

    new_temp = request.json.get('temperature')
    new_humidity = request.json.get('humidity')

    print(new_temp, new_humidity)
    return {'status': 'success'}, 200


@app.route('/send_new_values', methods=['POST'])
def send_new_values():
    if request.remote_addr not in authorized_users:
        return redirect('/login?r=send_new_values')

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


@app.route('/updater', methods=['GET', 'POST'])
def base_data():
    if request.remote_addr not in authorized_users:
        return redirect('/login?r=base_data')

    global average_humidity, average_temperatures
    #temperature, humidity, times = [el[1] for el in read_db()], [el[2] for el in read_db()], [el[4] for el in read_db()]

    if request.method == 'POST':
        if request.form['avg_temperature']:
            average_temperatures = int(request.form['avg_temperature'])
        if request.form['avg_humidity']:
            average_temperatures = int(request.form['avg_humidity'])

        print(request.form)
        return render_template("datachanger.html", data=[i[0] for i in read_id()], skr=value_contr[1], entry=0)

    return render_template("datachanger.html", data=[i[0] for i in read_id()], skr=value_contr[1], entry=0)


@app.route('/submit_data', methods=['POST'])
def submit():
    if request.remote_addr not in authorized_users:
        return redirect('/login?r=submit')

    values = {}
    print(request.form)
    for tup in dict(request.form).items():
        values[tup[0]] = tup[1]
    print(values)
    for i in value_contr[int(values['selectedNode'])]:
        if i in values:
            value_contr[int(values['selectedNode'])][i] = int(values[i])

    print(value_contr)

    return redirect('/updater')


@app.route('/')
def index():
    if request.remote_addr not in authorized_users:
        return redirect('/login?r=index')
    data = [i[0] for i in read_id()]
    html_content = render_template(
        'main.html', data=data
    )
    return  make_response(html_content)


@app.errorhandler(404)
def handle_bad_request(e):
    if request.remote_addr not in authorized_users:
        return redirect('/login')
    return render_template('404.html')


@app.route('/<int:pin>/<state>')
def control_pin(pin, state):
    if request.remote_addr not in authorized_users:
        return redirect('/login')

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
    if request.remote_addr not in authorized_users:
        return redirect('/login?r=update_data')

    global contr
    data = request.get_json()

    print(data)
    for k in data.items():
        print(k)
    key = int(data['key'])

    temperature = float(data.get("temperature"))
    if temperature == -50:
        temperature = None

    humidity = float(data.get("humidity"))
    if humidity == -50:
        humidity = None

    humidity_earth = float(data.get("humidity_earth"))
    if humidity_earth == -1:
        humidity_earth = None

    light = float(data.get("light"))
    if light == -1:
        light = None

    # Здесь вы можете добавить код для обработки данных и логики
    # на основе полученных значений температуры и влажности.
    controll(key, temperature, humidity, humidity_earth, light)
    update_db(key, temperature, humidity, humidity_earth, light)

    # эта хрень просто ответ. можно прочесть на ардуине
    return str(contr[key])


# а отсюда мы можем брать значения
@app.route('/get_data')
def get_data():
    id = request.args.get('id')  # Получаем id из параметров запроса
    print(id)
    if request.remote_addr not in authorized_users:
        return redirect('/login?r=index')

    # Получить последние данные из базы данных
    ser = read_db(id)
    print(ser)
    ser = ser[-2]

    update = {
        'temperature': ser.temperature,
        'humidity': ser.humidity,
        'humidity_earth': ser.humidity_earth
    }
    update = dict(list(update.items()) + list(contr[1].items()))
    print(update)
    return update


# а отсюда мы можем брать значения
@app.route('/example', methods=['POST'])
def example():
    print(1)
    data = request.get_json()
    print(2)
    print(data['selectedOption'])

    # Получить последние д

    update = dict(list(value_contr[int(data['selectedOption'])].items()))

    return update


if __name__ == '__main__':
    id = read_id()

    for i in id:
        contr[i[0]] = {'ventilation': 0,
                       'water': 0,
                       'term': 0,
                       'vibr_water': 0,
                       'light': 0}
        value_contr[i[0]] = {'average_temperatures': 20,
                             'dispersion_temperatures': 5,
                             'average_humidity_earth': 20,
                             'dispersion_humidity_earth': 5,
                             'average_humidity': 20,
                             'dispersion_humidity': 5}
    app.run(host='0.0.0.0', port=5000, debug=True)
