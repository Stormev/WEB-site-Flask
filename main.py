from flask import Flask, render_template, send_from_directory, request, redirect, flash
from data.db_session import create_session, global_init
from data.DBTables.user import User
from data.DBTables.tickets import Ticket
from data.DBTables.attractions import Attractions
from data.DBTables.data_loaded_images import DLI
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
import os
from flask_restful import abort


app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'cool_park5'
app.config['UPLOAD_FOLDER'] = 'data/loaded_images/'

# инициализация flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/login'

# Курс 1 детали (пополнение баланса)
cost_detail = 0.1


@login_manager.user_loader
def load_user(user_id):
    db_sess = create_session()
    return db_sess.get(User, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    return redirect('/login')


# Функция для поиск пользователя в БД
def find_user(user_id=None, user_login=None):
    result = None
    sess = create_session()

    if user_id:
        result = sess.get(User, user_id)
    elif user_login:
        result = sess.query(User).filter(User.login == user_login).first()

    if result:
        return result


# Главная страница (о сайте и парке)
@app.route('/')
def main_page():
    send_from_directory(os.path.join(app.root_path, 'templates'), 'main_page.html')
    return render_template('main_page.html',
                           file=list((map(lambda x: x.rstrip('\n'),
                                          open('README.txt', 'r', encoding='utf-8').readlines()[8:]))))


# Профиль
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_page():
    if request.method == 'POST' and request.form.get('out'):
        logout_user()
        return redirect('/')
    sess = create_session()
    tickets = sess.query(Ticket).filter(Ticket.owner_id == current_user.id).all()
    return render_template('profile.html', tickets=tickets, user_name=current_user.login, balance=current_user.balance)


# Генерирует билет
def create_ticket(attraction_id):
    sess = create_session()
    attraction = sess.query(Attractions).get(attraction_id)

# Снятие денег
    user = sess.query(User).filter(User.id == current_user.id).first()
    if user:
        # Нет денег
        if (user.balance - attraction.cost) < 0:
            return redirect('/replenish')
        # Успешно
        user.balance -= attraction.cost
    else:
        return redirect('/reg')
# Генератор
    if attraction and current_user:
        maybe_ticket = sess.query(Ticket).filter(
            Ticket.owner_id == current_user.id,
            Ticket.name == attraction.name).first()

        if not maybe_ticket:
            sess.add(Ticket(
                name=attraction.name,
                count=1,
                id_attraction=attraction_id,
                owner_id=current_user.id,
                cost=attraction.cost
            ))
        elif maybe_ticket:
            maybe_ticket.count = int(maybe_ticket.count) + 1
        sess.commit()


# Аттракционы и покупка билетов
@app.route('/attractions', methods=['GET', 'POST'])
def attractions_page():
    # [{'id': 1, 'name': 'Машинки', 'image':'ссылка на картинку', 'cost':50, 'description': 'гы'}]
    if request.method == 'POST' and request.form:
        attraction_id = request.form.to_dict().popitem()[0]
        return redirect(f'/pay/{attraction_id}')

    sess = create_session()
    data = sess.query(Attractions)
    return render_template('attractions.html', attractions_data=data)


# Авторизация
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST' and request.form:
        # Проверка подленности
        if not all([request.form.get('login'), request.form.get('password')]):
            return render_template('login.html', message='Заполните форму полностью!')

        # Проверка аккаунта
        acc = find_user(user_login=request.form.get('login'))

        if acc and acc.password == request.form.get('password'):
            login_user(acc)
        else:
            return render_template('login.html', message='Неверный логин или пароль')

        return redirect('/profile')

    # GET Запрос
    return render_template('login.html')


# Регистрация
@app.route('/reg', methods=['GET', 'POST'])
def reg_page():
    if request.method == 'POST' and request.form:

        sess = create_session()

        # Проверка подленности
        if find_user(user_login=request.form.get('login')):
            return render_template('registration.html', message='Такой логин уже существует!')
        if not all([request.form.get('login'), request.form.get('password'), request.form.get('age')]):
            return render_template('registration.html', message='Заполните форму регистрации полностью!')

        # Создание акаунта
        sess.add(User(
            login=request.form.get('login'),
            password=request.form.get('password'),
            age=request.form.get('age')
        ))
        sess.commit()

        login_user(find_user(user_login=request.form.get('login')))
        return app.redirect('/profile')

    # GET Запрос
    return render_template('registration.html')


# Применение RESTFul
def abort_if_id_notFound_Attraction(att_id):
    sess = create_session()
    result = sess.query(Attractions).get(att_id)
    if not result:
        abort(404, message=f"Аттракцион {att_id} не найден")


# Покупка билета, применение REST
@app.route('/pay/<int:att_id>', methods=['GET', 'POST'])
@login_required
def pay(att_id):
    abort_if_id_notFound_Attraction(att_id)

    sess = create_session()
    attraction = sess.query(Attractions).get(att_id)
    if request.method == 'POST':
        create_ticket(attraction.id)
        return redirect('/profile')

    return render_template('pay.html', balance=current_user.balance, cost=attraction.cost, choise=attraction.name)


def image_to_money(img):
    if os.path.isfile(f'data/loaded_images/{img.filename}'):
        return 'Такая картинка уже существует!'
    else:
        img.save(f'data/loaded_images/{img.filename}')
        path = f'data/loaded_images/{img.filename}'

        with open(path, 'rb') as file:
            details_ = str(file.read()).count('/')
            cost = round(details_ * cost_detail)

            sess = create_session()
            sess.add(DLI(
                name=img.filename,
                details=details_,
                image_path=path,
                owner_id=current_user.id
            ))

            user = sess.query(User).filter(User.id == current_user.id).first()
            user.balance += cost
            sess.commit()
            return f'Вы успешно загрузили картинку! Ваша прибыль: {cost}'


# Пополнение баланса
@app.route('/replenish', methods=['GET', 'POST'])
@login_required
def replenish():
    result_message = ''
    if request.method == 'POST':
        file = request.files['image']
        if file.filename:
            result = image_to_money(file)
            result_message = result
        else:
            result_message = 'Возникла ошибка, проверьте наличие файла!'
    return render_template('replenish.html', message=result_message, balance=current_user.balance)


# Иконка в браузере
@app.route('/favicon.ico')
def fav():
    return send_from_directory(os.path.join(app.root_path, 'static/images'), 'favicon.ico')


# Инициализация
if __name__ == '__main__':
    global_init('data/data_base.db')
    app.run(debug=True)