from flask import Flask, render_template, request, redirect, url_for, g, jsonify, make_response, session
from flask_caching import Cache
import sync_controller as db
import datetime as dt
import methods as m
import statistics
import functools
import requests
import logging
import json
import time
import math
import os

app = Flask(__name__)

app.config['CACHE_TYPE'] = 'FileSystemCache'  # Используем файловое кеширование
app.config['CACHE_DIR'] = 'cache/'  # Папка для хранения кеша
app.config['CACHE_DEFAULT_TIMEOUT'] = 18000  # Время жизни кеша в секундах

cache = Cache(app)

BOT_TOKEN = os.getenv('BOT_TOKEN') # Токен бота
PAYMENT_TOKEN = os.getenv('PAYMENT_TOKEN') # Токен оплаты основного бота
SECRET_KEY = os.getenv('SECRET_KEY')
app.config['SECRET_KEY'] = SECRET_KEY


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

def auth_required(view_func):
    @functools.wraps(view_func)
    def wrapped_view(*args, **kwargs):
        cookies = {
            'access_token': request.cookies.get('access_token'),
            'refresh_token': request.cookies.get('refresh_token')
        }

        # Проверка access_token
        if cookies['access_token']:
            checked_access, access_status = m.verify_token(cookies['access_token'], 'access')
            if checked_access:
                g.tg_id = checked_access.get('tg_id')
                return view_func(*args, **kwargs)

        
        if cookies['refresh_token']:
            checked_refresh, refresh_status = m.verify_token(cookies['refresh_token'], 'refresh')

            if checked_refresh:
                # Refresh токен валиден — обновляем токены
                g.tg_id = checked_refresh.get('tg_id')
                new_access_token, exp_at = m.create_token(g.tg_id, token_type='access')
                new_refresh_token, exp_rt = m.create_token(g.tg_id, token_type='refresh')
                response = view_func(*args, **kwargs)
                if isinstance(response, str):
                    response = make_response(response)
                response.set_cookie('access_token', new_access_token, httponly=True, secure=True, expires=exp_at)
                response.set_cookie('refresh_token', new_refresh_token, httponly=True, secure=True, expires=exp_rt)
                
                db.save_refresh_token(g.tg_id, new_refresh_token)
                return response

        # Если refresh_token отсутствует или невалиден — проверяем init_data
        return redirect(url_for('init_data'))

    return wrapped_view


@app.route("/")
def start():
    return 'Start Page'


@app.route("/form")
@auth_required
def form():
    tg_id = g.tg_id
    form_data = db.check_form(tg_id)
    
    if form_data:
        state = form_data.get("state")
        if state != "deleted":
            return redirect(url_for('profile'))
   
    return render_template('form.html', timestamp=int(time.time()))


@app.route('/save_form', methods=['POST'])
def save_form():
    # init_data = request.form.get("init")
    # data = request.form.get("data")
    # file = request.files['file']
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Ошибка получения данных!'}), 400
    
    init_data = data.get('init')
    
    # if not data and file:
    #     return jsonify({'success': False, 'message': 'Ошибка получения данных!'}), 400
    
    check_data = m.validate_init_data(init_data, BOT_TOKEN)
    check_status = check_data.get("status")
    
    if not check_status:
        return jsonify({'success': False, 'message': 'Проверка данных инициализации завершилась неудачей!'}), 400
    
    tg_id = check_data.get("id")
    username = check_data.get("username")
    
    user = db.check_user(tg_id)
    if not user:
        if not username:
            username = '-'
        db.add_new_user(tg_id, username)
    
    load_data = data.get('form')
    app.logger.info(f'Сохраняем анкету: telegram id - {tg_id}, username - {username}, анкета:')
    app.logger.info(load_data)
    
    # filename = None
    # folder_name = str(tg_id)
    # create_folder(folder_name)
    
    # if file.filename.lower().endswith('.png'):
    #     filename = 'photo1.png'
    # elif file.filename.lower().endswith('.jpg'):
    #     filename = 'photo1.jpg'
    # elif file.filename.lower().endswith('.jpeg'):
    #     filename = 'photo1.jpeg'
    
    # load_status = load_photo(folder_name, filename, file)
    
    # if not load_status:
    #     return jsonify({'success': False, 'message': 'В процессе загрузки изображения произошла ошибка!'})
    
    db.add_form(tg_id, load_data)
    return jsonify({'success': True, 'message': 'Анкета успешно сохранена!'})


@app.route('/delete_form')
@auth_required
def delete_form():
    tg_id = g.tg_id
    
    db.delete_match_status(tg_id)
    db.delete_form(tg_id)
    
    return jsonify({'success': True, 'message': 'Анкета успешно удалена!'})


@app.route('/init', methods=['GET', 'POST'])
def init_data():
    if request.method == 'POST':
        data = request.get_json()
        
        if not data:
            return render_template('error.html')
    
        init_data = data.get('init')
        check_data = m.validate_init_data(init_data, BOT_TOKEN)
        check_status = check_data.get("status")
        
        if not check_status:
            return redirect(url_for('error'))
        
        tg_id = check_data.get("id")
        username = check_data.get("username")
        user = db.check_user(tg_id)
        
        if not user:
            db.add_new_user(tg_id, username)
            
        access_token, exp_at = m.create_token(tg_id, token_type='access')
        refresh_token, exp_rt= m.create_token(tg_id, token_type='refresh')
        db.save_refresh_token(tg_id, refresh_token)
        
        response = redirect(url_for('profile'))
        response.set_cookie('access_token', access_token, httponly=True, secure=True, expires=exp_at)
        response.set_cookie('refresh_token', refresh_token, httponly=True, secure=True, expires=exp_rt)
        return response
    else:
        return render_template('init.html')


@app.route("/profile")
@auth_required
def profile():
    tg_id = g.tg_id
    form_data = db.check_form(tg_id)
    
    if not form_data:
        return render_template('profile.html', timestamp=int(time.time()))
    
    state = form_data.get('state')
    if state == "deleted":
        return render_template('profile.html', timestamp=int(time.time()))
    
    details = db.check_user_profile_details(tg_id)
    if not details:
        db.add_new_details(tg_id)
    
    # Словари для преобразования пола и пути к иконке
    sex_map = {"Мужской": "Мужчина", "Женский": "Женщина"}
    gender_map = {"Мужчина": "male.png", "Женщина": "female.png"}

    # Обработка пола
    gender = form_data.get('sex')
    sex = sex_map.get(gender)
    gender_path = gender_map.get(sex)
    form_data['sex'] = sex
    
    birth_dt = form_data.get('birth_dt')
    digit_age, your_age = m.get_age(birth_dt)
    location = form_data.get('location').split(' (')[0];
    form_data['location'] = location
    social_link, social_name = form_data.get('social').split(', ')
    social = {
        "link": social_link.lower() + ".svg", 
        "name": social_name.strip() 
    }
    
    sign = form_data.get('sign')
    sign_path = m.get_sign_path(sign)
    
    image_data = None
    # filename = form_data.get('photo_link')
    # if filename != 'Нет фото':
    #     url_photo = f"{WEBDAV_URL}/{tg_id}/{filename}"
    #     image_data = get_profile_image(tg_id, url_photo)
        
    return render_template('profile.html', timestamp=int(time.time()), form=form_data, gender_path=gender_path, sign_path=sign_path, age=your_age, social=social, image=image_data)


@app.route("/upload_photo", methods=["POST"])
@auth_required
def upload_photo():
    tg_id = g.tg_id
    file = request.files["file"]
    
    if m.upload_photo(file, "profile_photos", str(tg_id)):
        return jsonify({'success': True, 'message': 'Фото успешно загружено!'})
    else:
        return jsonify({'success': False, 'message': 'Ошибка при загрузке файла!'})


@app.route("/about_me")
@auth_required
def about_me():
    tg_id = g.tg_id
    form_data = db.check_form(tg_id)
    
    gives = form_data.get('gives').split(", ")
    my_appearance = form_data.get('my_appearance').split(", ")
    my_character = form_data.get('my_character').split(", ")
    
    gets = form_data.get('gets').split(", ")
    partner_appearance = form_data.get('partner_appearance').split(", ")
    partner_character = form_data.get('partner_character').split(", ")
    interests = form_data.get('interests').split(", ")
    
    headers = ['height', 'physique', 'hair_color', 'hair_type', 'eye_color', 'skin_color', 'face_type', 'tattoos']
    my_app_dict = None
    if len(my_appearance) == 8:
        my_app_dict = dict(zip(headers, my_appearance))
    part_app_dict = None
    if len(partner_appearance) == 8:
        part_app_dict = dict(zip(headers, partner_appearance))
        
    return render_template('about_me.html', form=form_data, gives=gives, my_appearance=my_app_dict, my_character=my_character, gets=gets, partner_appearance=part_app_dict, partner_character=partner_character, interests=interests)


@app.route("/tariffs")
@auth_required
def tariffs():
    return render_template('tariffs.html')


@app.route('/buy', methods=['POST'])
def buy():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'Ошибка получения данных!'}), 400
    
    init_data = data.get('init')
    
    check_data = m.validate_init_data(init_data, BOT_TOKEN)
    check_status = check_data.get("status")
    
    if not check_status:
        return jsonify({'success': False, 'message': 'Проверка данных завершилась неудачей!'}), 400
    
    tg_id = check_data.get("id")
    username = check_data.get("username")
    tariff_name = data.get('tariff')
    app.logger.info(f'Запрос /buy: {tg_id} - {username} - Тариф: {tariff_name}')
    
    if tariff_name == "ЗНАКОМСТВО":
        details = db.check_user_profile_details(tg_id)
        
        gift_status = details.get('gift')
        if gift_status == "received":
            return jsonify({'success': False, 'message': 'Вы уже получили этот тариф!'}), 200
        db.update_user_tariff(tg_id, 1)
        db.update_gift_status(tg_id)
        return jsonify({'success': False, 'message': 'Тариф успешно установлен!'}), 200
        
            
    price = data.get('price')
    payload = data.get('payload')
    promocode = data.get('promocode')
    
    discount = False
    referral = db.check_promocode(promocode)

    if referral:
        ref_tg_id = referral.get('tg_id')
        discount_percent = referral.get('discount_percent')
        if tg_id != ref_tg_id:
            discount = True
            payload = payload + "_" + promocode
            app.logger.info(f'{payload}')
    message = m.get_tariff_description(tariff_name)
    message_data = {
        'chat_id': tg_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    response = requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage', data=message_data)
    
    if discount:
        price = round(price - price * (discount_percent / 100))
        # db.add_new_promo_apply(tg_id, ref_tg_id)
        message = f'Промокод успешно применён! ✅\n\nВаша скидка по промокоду на покупку тарифа составляет — {discount_percent}%'
        message_discount = {
            'chat_id': tg_id,
            'text': message
        }
        response = requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage', data=message_discount)
    
    date_invoice = f'{dt.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}'
    
    invoice_data = {
        'chat_id': tg_id,
        'title': f'Покупка тарифа {tariff_name}',
        'description': f'Создано ------ {date_invoice} ------ Счёт на оплату сформирован. Оплата осуществляется через Telegram.',
        'payload': payload,
        'provider_token': PAYMENT_TOKEN,
        'currency': 'RUB',
        'prices': [{'label': 'Стоимость выбранного тарифа', 'amount': price * 100}],  # price в копейках
    }
    response = requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendInvoice', json=invoice_data)

    if response.status_code != 200:
        return jsonify({'success': False, 'message': response.text}), response.status_code
        
    return jsonify({'success': True , 'message': 'Сообщение успешно отправлено в бот'}), 200


@app.route("/change_form")
@auth_required
def change_form():
    return render_template('change_form.html')


@app.route("/match")
@auth_required
def match():
    tg_id = g.tg_id
    form_data = db.check_form(tg_id)
    if not form_data:
        return render_template('match.html', state="Для доступа к функции необходимо заполнить анкету")
    
    state = form_data.get('state')
    if state == 'active':
        matches = db.match_list(tg_id)
        
        for match in matches:
            partner_sign = match.get('partner_sign')
            partner_sign_path = m.get_match_sign_path(partner_sign)
            match['partner_sign_path'] = partner_sign_path
        
        return render_template('match.html', state="Здесь пока что пусто", matches=matches)
    elif state == 'hide':
        return render_template('match.html', state="Мэтчи не отображаются, ваша анкета скрыта")
    else:
        return render_template('match.html', state="Для доступа к функции необходимо заполнить анкету")    


@app.route("/match/<int:select_id>")
@auth_required
def show_match(select_id):
    tg_id = g.tg_id
    matches = db.match_list(tg_id)
    
    selected_match = next(filter(lambda match: match.get('tg_id') == select_id, matches), None)
    
    if not selected_match:
        return redirect(url_for('match'))
    
    match_status = db.check_match_status(tg_id, select_id)
    
    if not match_status or match_status not in ('просмотрено', 'ожидание ответа', 'мэтч', 'нет мэтча'):
        status = "просмотрено"
        db.update_match_status(tg_id, select_id, status)
        match_status = status
    selected_match['status'] = match_status
    
    partner_sign = selected_match.get('partner_sign')
    relation_type = selected_match.get('relation_type')
    result_compatibility = selected_match.get('result_compatibility')
    
    selected_match['partner_sign_path'] = m.get_match_sign_path(partner_sign)
    selected_match['partner_sign_description'] = m.get_sign_description(partner_sign)
    selected_match['relation_type_description'] = m.get_type_description(relation_type)
    selected_match['compatibility_description'] = m.get_compatibility_description(result_compatibility)
    
    partner_gives = selected_match.get('partner_gives').split(", ")
    partner_gets = selected_match.get('partner_gets').split(", ")
    partner_character = selected_match.get('partner_character').split(", ")

    headers = ['height', 'physique', 'hair_color', 'hair_type', 'eye_color', 'skin_color', 'face_type', 'tattoos']
    partner_appearance = selected_match.get('partner_appearance').split(", ")
    partner_app_dict = None
    if len(partner_appearance) == 8:
        partner_app_dict = dict(zip(headers, partner_appearance))
    
    partner_interests = selected_match.get('partner_interests').split(", ")
    
    return render_template('match_open.html', selected_match=selected_match, partner_gives=partner_gives, partner_gets=partner_gets, partner_character=partner_character, partner_appearance=partner_app_dict, partner_interests=partner_interests)


@app.route("/deny/<int:select_id>", methods=['POST'])
@auth_required
def deny_match(select_id):
    tg_id = g.tg_id
    
    user_details = db.check_user_profile_details(tg_id) 
    tariff_id = user_details.get('tariff_id')
    amount_matches = user_details.get('amount_matches')
    
    if amount_matches == 0 and tariff_id in (1, 2, 3):
        return jsonify({"status": False , "message": "На вашем балансе недостаточно мэтчей для проведения операции"})
        
    status = "нет мэтча"
    db.update_match_status(tg_id, select_id, status)
    db.update_match_status(select_id, tg_id, status)
    
    return jsonify({"status": True , "message": "Данный мэтч был успешно отклонён"})


@app.route("/agree/<int:select_id>", methods=['POST'])
@auth_required
def agree_match(select_id):
    tg_id = g.tg_id
    
    match_status = db.check_match_status(tg_id, select_id)
    partner_match_status = db.check_match_status(select_id, tg_id)
    
    user_details = db.check_user_profile_details(tg_id)
    partner_details = db.check_user_profile_details(select_id) 
    
    tariff_id = user_details.get('tariff_id')
    partner_tariff_id = partner_details.get('tariff_id')
    
    amount_matches = user_details.get('amount_matches')
    partner_amount_matches = partner_details.get('amount_matches')
    
    if amount_matches == 0 and tariff_id in (1, 2, 3, 6):
        return jsonify({"status": False , "message": "На вашем балансе недостаточно мэтчей для проведения операции"})
    
    
    if match_status in (None, 'просмотрено') and partner_match_status in (None, 'просмотрено'):
        # Устанавливаем статус "ожидание ответа" для текущего пользователя
        db.update_match_status(tg_id, select_id, "ожидание ответа")

        
        # Отправляем уведомление второму пользователю
        message = "Вам пришёл мэтч! ✨️\n\n"\
            "<i>Кто-то проявил к вам интерес и хочет познакомиться!</i>\n"
        
        message_data = {
            'chat_id': select_id,
            'text': message,
            'parse_mode': 'HTML',
            'reply_markup': json.dumps({
                "inline_keyboard": [[{
                    "text": "Посмотреть",
                    "web_app": {
                        "url": f'https://astro-love.online/match/{tg_id}'
                    }
                }]]
            })
        }
        requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage', data=message_data)
        
        return jsonify({"status": True , "message": "Ожидаем ответа от пользователя"})
    
    # Если второй пользователь уже ожидает нашего ответа
    elif partner_match_status == "ожидание ответа":
        # Устанавливаем мэтч для обоих пользователей
        if partner_amount_matches == 0 and partner_tariff_id in (1, 2, 3, 6):
            keyboard = {
                "inline_keyboard": [
                    [
                        {
                            "text": "Купить тариф",
                            "web_app": {
                                "url": f'https://astro-love.online/tariffs'
                            }
                        }
                    ]
                ]
            }
            
            message = "У вас взаимный мэтч!✨️\n\n<i>Пополните свой баланс!</i>"
            message_data = {
                'chat_id': select_id,
                'text': message,
                'parse_mode': 'HTML',
                'reply_markup': json.dumps(keyboard)
            }
            requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage', data=message_data)
            
            return jsonify({"status": False , "message": "На балансе предполагаемого партнёра недостаточно мэтчей для проведения операции"})
    
        if tariff_id in (1, 2, 3, 6):
            db.update_amount_matches(tg_id, 1)
        if partner_tariff_id in (1, 2, 3, 6):
            db.update_amount_matches(select_id, 1)
        
        db.update_match_status(tg_id, select_id, "мэтч")
        db.update_match_status(select_id, tg_id, "мэтч")
    
        # Отправляем уведомления обоим пользователям
        
        # Пары user_id и соответствующих профилей для кнопок
        users_id = {
            tg_id: select_id,
            select_id: tg_id
        }
        
        message_data = None
        success_message = None
        
        for user_id, profile_id in users_id.items():
            user = db.check_user(profile_id)
            username = user.get('username')
            
            if username != "-":
                # success_message = "У вас случился взаимный мэтч! 🎉\nТеперь вы можете общаться! "
                success_message = "У вас взаимный мэтч! 💖🎉\n\n"\
                    "<b>Теперь вы можете написать друг другу!</b>\n\n"\
                    "<i>Советы для начала беседы:</i>\n"\
                    "• Представьтесь и напишите о своих интересах\n"\
                    "• Спросите о хобби или увлечениях\n"\
                    "• Предложите тему для обсуждения\n\n"\
                    "<i>💌 Не стесняйтесь сделать первый шаг!</i>\n"\
                    "Желаем вам приятного общения! 💞"
                
                message_data = {
                    'chat_id': user_id,
                    'text': success_message,
                    'parse_mode': 'HTML',
                    'reply_markup': json.dumps({
                        "inline_keyboard": [[{
                            "text": "Написать сообщение",
                            "url": f'https://t.me/{username}'
                        }]]
                    })
                }
            else:
                form_data = db.check_form(profile_id)
                social = form_data.get('social')
                success_message = "У вас взаимный мэтч! 💖🎉\n\n"\
                    "<b>Теперь вы можете найти друг друга и начать общение!</b>\n\n"\
                    "<i>Советы для начала беседы:</i>\n"\
                    "• Представьтесь и напишите о своих интересах\n"\
                    "• Спросите о хобби или увлечениях\n"\
                    "• Предложите тему для обсуждения\n\n"\
                    "<i>💌 Не стесняйтесь сделать первый шаг!</i>\n"\
                    "Желаем вам приятного общения! 💞\n\n"\
                   f"<b>Чтобы найти человека, используйте указанную социальную сеть:</b>\n📲 <code>{social}</code>"
            
                message_data = {
                    'chat_id': user_id,
                    'text': success_message,
                    'parse_mode': 'HTML'
                }
            
            # message_data = {
            #     'chat_id': user_id,
            #     'text': success_message,
            #     'reply_markup': json.dumps({
            #         "inline_keyboard": [[{
            #             "text": "Открыть профиль",
            #             "url": f"tg://user?id={profile_id}"
            #         }]]
            #     })
            # }
            requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage', data=message_data)
        
        return jsonify({"status": True, "message": "Поздравляем! У вас произошел взаимный мэтч!"})
            
    # Если мэтч уже существует
    elif match_status == "мэтч" or partner_match_status == "мэтч":
        db.update_match_status(tg_id, select_id, "мэтч")
        db.update_match_status(select_id, tg_id, "мэтч")
        return jsonify({"status": "already_matched", "message": "Мэтч уже существует"})
    
    # Если текущий пользователь уже ожидает ответа
    elif match_status == "ожидание ответа":
        return jsonify({"status": False, "message": "Вы уже ожидаете ответа от этого пользователя"})
    
    return jsonify({"status": False , "message": "Произошла ошибка! Перезагрузите страницу и попробуйте снова"})


@app.route("/love")
@auth_required
def love():
    return render_template('love.html')    


@app.route("/calculate_love", methods=['POST'])
@auth_required
def calc_love():
    tg_id = g.tg_id
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'Ошибка получения данных!'}), 400
    
    user_details = db.check_user_profile_details(tg_id)
    tariff_id = user_details.get('tariff_id')
    amount_love = user_details.get('amount_love')

    if amount_love == 0 and tariff_id in (1, 2, 3, 6):
        return jsonify({"status": False , "message": "На вашем балансе недостаточно средств для проведения операции"})
    
    birth_date = data.get('birth_date')
    
    sign = m.get_zodiac_sign(birth_date)
    monad, chakras = m.calculate_chakras(birth_date)
    sign_influence = db.get_sign_point(sign)
    anahata_influence = db.get_anahata_influence(chakras['Анахата'])
    destiny_influence = db.get_destiny_influence(monad)
    how_much_love = sign_influence + anahata_influence + destiny_influence
    
    inn = chakras['Муладхара'] + chakras['Вишудха'] + chakras['Аджна']
    yann = chakras['Свадхистана'] + chakras['Анахата'] + chakras['Манипура']
    
    session['result'] = {
        'how_much_love': how_much_love,
        'inn': inn,
        'yann': yann,
        'chakras': chakras
    }
    
    if tariff_id in (1, 2, 3, 6):
        db.update_amount_love(tg_id, 1)

    return jsonify({"status": True , "message": "Успешно!"})
    

@app.route("/result_love")
@auth_required
def result_love():
    data = session.get('result', {})
    
    if not data:
        return render_template('love.html')
    
    how_much_love = data.get('how_much_love') 
    inn = data.get('inn')
    yann = data.get('yann')
    chakras = data.get('chakras')
    love_description = m.get_love_description(how_much_love)
    chakras_description = m.get_chakras_description(chakras)
    inn_description = m.get_inn_description(inn)
    yann_description = m.get_yann_description(yann)
    
    return render_template('result_love.html', how_much_love=how_much_love, inn=inn, yann=yann, chakras=chakras, love_description=love_description, inn_description=inn_description, chakras_description=chakras_description, yann_description=yann_description)


@app.route("/speed")
@auth_required
def speed():
    return render_template('speedometr.html')


@app.route("/calculate_speed", methods=['POST'])
@auth_required
def calc_speed():
    tg_id = g.tg_id
    
    user_details = db.check_user_profile_details(tg_id)
    tariff_id = user_details.get('tariff_id')
    amount_speed = user_details.get('amount_speed')
    
    if amount_speed == 0 and tariff_id in (1, 2, 3, 6):
        return jsonify({"status": False , "message": "На вашем балансе недостаточно средств для проведения операции"})
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Ошибка получения данных!'}), 400
    
    
    birth_date_one = data.get('birth_date_one')
    birth_date_two = data.get('birth_date_two')
    
    sign_one = m.get_zodiac_sign(birth_date_one)
    sign_two = m.get_zodiac_sign(birth_date_two)
    sign_compatibility, relation_type = db.get_sign_compatibility(sign_one, sign_two)
    
    sign_one_path = m.get_sign_path(sign_one)
    sign_two_path = m.get_sign_path(sign_two)
    
    element_one = m.get_sign_element(sign_one)
    element_two = m.get_sign_element(sign_two)
    elemental_index = db.get_elemental_index(element_one, element_two)
    
    active_one = m.get_sign_activity(sign_one)
    active_two = m.get_sign_activity(sign_two)
    
    monad_one, chakras_one = m.calculate_chakras(birth_date_one)
    monad_two, chakras_two = m.calculate_chakras(birth_date_two)
    
    love = (sign_compatibility - 30) * 1.2 * elemental_index * 0.6 + statistics.mean((chakras_one['Анахата'], chakras_two['Анахата'])) * 0.25 + statistics.mean((chakras_one['Свадхистана'], chakras_two['Свадхистана'])) * 0.1 + statistics.mean((chakras_one['Сахасрара'], chakras_two['Сахасрара'])) * 0.05
    conflict = (100 - sign_compatibility) * 0.4 * elemental_index + math.fabs(chakras_one['Муладхара'] - chakras_two['Муладхара']) * 0.05 + math.fabs(chakras_one['Манипура'] - chakras_two['Манипура']) * 0.1 + math.fabs(chakras_one['Аджна'] - chakras_two['Аджна']) * 0.05
    family = (sign_compatibility * 0.3 + elemental_index * 100 * 0.3) * 0.4 + statistics.mean((chakras_one['Анахата'], chakras_two['Анахата'], chakras_one['Вишудха'], chakras_two['Вишудха'])) * 0.15 + statistics.mean((chakras_one['Муладхара'], chakras_two['Муладхара'], chakras_one['Манипура'], chakras_two['Манипура'])) * 0.15
    children = elemental_index * (statistics.mean((chakras_one['Свадхистана'], chakras_two['Свадхистана'])) * 0.5 +  statistics.mean((chakras_one['Анахата'], chakras_two['Анахата'])) * 0.3 + statistics.mean((chakras_one['Аджна'], chakras_two['Аджна'])) * 0.2)
    sex = statistics.mean((chakras_one['Свадхистана'], chakras_two['Свадхистана'])) * 0.4 + statistics.mean((chakras_one['Муладхара'], chakras_two['Муладхара'])) * 0.3 + statistics.mean((chakras_one['Манипура'], chakras_two['Манипура'])) * 0.2 + elemental_index * 100 * 0.1
    total = ((love + conflict + family + children + sex) * sign_compatibility  / 100) * 0.455
    if conflict < 10:
        conflict = 10
        
    session['speedometr'] = {
        'sign_one': sign_one,
        'sign_two': sign_two,
        'active_one': active_one,
        'active_two': active_two,
        'element_one': element_one,
        'element_two': element_two,
        'sign_one_path': sign_one_path,
        'sign_two_path': sign_two_path,
        'relation_type': relation_type,
        'love': round(love),
        'conflict': round(conflict),
        'family': round(family),
        'children': round(children),
        'sex': round(sex),
        'total': round(total)
    }
    
    if tariff_id in (1, 2, 3, 6):
        db.update_amount_speed(tg_id, 1)

    return jsonify({"status": True , "message": "Успешно!"}) 


@app.route("/result_speed")
@auth_required
def result_speed():
    data = session.get('speedometr', {})
    
    if not data:
        return render_template('speed_test.html')
        
    sign_one_desc = m.get_full_sign_description(data['sign_one'])
    sign_two_desc = m.get_full_sign_description(data['sign_two'])
    active_one_desc = m.get_activity_description(data['active_one'])
    active_two_desc = m.get_activity_description(data['active_two'])
    element_one_desc = m.get_element_description(data['element_one'])
    element_two_desc = m.get_element_description(data['element_two'])
    type_desc = m.get_type_description(data['relation_type'])
    love_desc = m.get_loves_description(data['love'])
    conflict_desc = m.get_conflict_description(data['conflict'])
    family_desc = m.get_family_description(data['family'])
    children_desc = m.get_children_description(data['children'])
    sex_desc = m.get_sex_description(data['sex'])
    total_desc = m.get_total_description(data['total'])
    
    description = {
        'sign_one': sign_one_desc,
        'sign_two': sign_two_desc,
        'active_one' : active_one_desc,
        'active_two' : active_two_desc,
        'element_one' : element_one_desc,
        'element_two' : element_two_desc,
        'type': type_desc,
        'love': love_desc,
        'conflict': conflict_desc,
        'family': family_desc,
        'children': children_desc,
        'sex': sex_desc,
        'total': total_desc
    }
    
    return render_template('speed_test.html', data=data, description=description)


# @app.route("/test")
# @auth_required
# def test():
#     tg_id = g.tg_id
#     form_data = db.check_form(tg_id)

@app.route("/hide_form", methods=['POST'])
@auth_required
def hide_form():
    tg_id = g.tg_id
    db.update_form_status(tg_id, "hide")
    return jsonify({"status": True , "message": "Анкета успешно скрыта и не отображается в мэтчах"}) 


@app.route("/show_form", methods=['POST'])
@auth_required
def show_form():
    tg_id = g.tg_id
    db.update_form_status(tg_id, "active")
    return jsonify({"status": True , "message": "Анкета теперь снова отображается в мэтчах"}) 


@app.route("/my_tariff")
@auth_required
def my_tariff():
    tg_id = g.tg_id
    details = db.check_user_profile_details(tg_id)
    amount_matches = details.get('amount_matches')
    amount_love = details.get('amount_love')
    amount_speed = details.get('amount_speed')
    tariff_id = details.get('tariff_id')
    set_at = details.get('set_at').split(' ')[0]
    expires_at = details.get('expires_at').split(' ')[0]
    duration = None
    if set_at != "-" and expires_at != "-":
        duration = f'c {set_at} по {expires_at}'
        
    tariff = db.check_tariff(tariff_id)
    tariff_name = tariff.get('name')
    tariff_desc = m.get_tariff_description(tariff_name, "list")
    
    return render_template('my_tariff.html', tariff=tariff_name, amount_matches=amount_matches, amount_love=amount_love, amount_speed=amount_speed, duration=duration, tariff_desc=tariff_desc)


@app.route("/error")
def error():
    return render_template('error.html')
