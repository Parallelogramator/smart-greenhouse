import requests, sqlite3, threading, time
import dash
from dash import dcc, html
import plotly.graph_objs as go
from dash.dependencies import Output, Input
from flask import Flask, request, render_template, make_response, redirect, url_for


s = ''
app = Flask(__name__)
dash_app = dash.Dash(__name__, server=app, routes_pathname_prefix='/graf/')

dash_app.layout = html.Div(children=[
    dcc.Graph(id='live-update-graph'),
    dcc.Interval(
        id='interval-component',
        interval=1*1000000,  # in milliseconds
        n_intervals=0
    )
])


# Обработчик обновления графика
@dash_app.callback(
    Output('live-update-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_graph_live(n):
    # Функция для чтения данных из базы данных
    data = read_db()
    strength = [el[1] for el in data[-20:]]
    length = [el[2] for el in data[-20:]]

    # Создание отдельных точек для графика
    traces = list()
    traces.append(go.Scatter(
        x=length,
        y=strength,
        name='Сила x Удлинение',
        mode='markers'
    ))

    # Подписи осей и убираем линии осей
    layout = go.Layout(
        title='Сила x Удлинение',
        xaxis=dict(title='Удлинение, мм', showline=False),
        yaxis=dict(title='Сила, Н', showline=False)
    )

    # Возвращаемый объект содержит traces и layout
    return {
        'data': traces,
        'layout': layout
    }

def read_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM Logs')
    fetch = c.fetchall()
    conn.close()
    return fetch


@app.route('/graph')
def render_dash_app():
    return dash_app.index()


@app.route('/update', methods=['POST', 'GET'])
def update_values():
    new_temp = request.json.get('temperature')
    new_humidity = request.json.get('humidity')

    print(new_temp, new_humidity)

    return {'status': 'success'}, 200


@app.route('/send_new_values', methods=['POST'])
def send_new_values():
    global average_temperatures, average_humidity, average_humidity_earth, dispersion_humidity, dispersion_temperatures, dispersion_humidity_earth
    if request.form['avg_temperature']:
        average_temperatures = request.form['avg_temperature']
    if request.form['avg_humidity']:
        average_humidity = request.form['avg_humidity']
    if request.form['avg_humidity_earth']:
        average_humidity_earth = request.form['avg_humidity_earth']
    print(request.form)
    return redirect(url_for('index'))


@app.route('/history', methods=['POST', 'GET'])
def update():
    data = read_db()

    html_content = render_template(
        'i.html',
        data=data
    )
    response = make_response(html_content)

    return response


@app.route('/update-description', methods=['POST'])
def update_description():
    # Получение описания от формы
    description = request.form.get('description')
    try:
        # Обновление записи в базе данных
        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute('UPDATE Logs SET description = ? WHERE number = ?', (description, number))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
    finally:
        conn.close()

    # Переадресация пользователя обратно к странице просмотра данных
    return redirect(url_for('update'))


@app.route('/')
def index():
    html_content = render_template(
        'main.html'
    )
    response = make_response(html_content)
    return response


@app.route('/input_diameter', methods=['GET'])
def input_diameter():
    html_content = render_template('diameter_input.html', length=20)
    response = make_response(html_content)
    return response


@app.route('/start1', methods=['POST'])
def start1():
    global s
    diameter = request.form['diameter']
    coefficient = request.form['coefficient']
    length = request.form['length']

    s = 1
    if s:
        return redirect(url_for('brea'))

    return redirect(url_for('start'))


@app.route('/start')
def start():
    data = read_db()
    print(data[-1])
    data = [data[-1]]
    html_content = render_template(
        'datachanger.html',
        data=data
    )
    response = make_response(html_content)
    return response

@app.route('/break')
def brea():
    global s
    return ''.join(s)


# Маршрут для получения данных от NodeMCU
@app.route('/update_data', methods=['POST'])
def update_data():
    pass


# а отсюда мы можем брать значения
@app.route('/get_data')
def get_data():
    # Получить последние данные из базы данных
    ser = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    update = {
        'number': ser[0],
        'strength': ser[1],
        'length': ser[2],
        'time': ser[3],
        'description': ser[4],
    }
    return update


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
