const initData = window.Telegram.WebApp.initData; // Получаем данные из Telegram Web App
let load = false;

const named = document.getElementById('name');
const sex = document.getElementById('sex');
const social_type = document.getElementById('social_type');
const social = document.getElementById('social');

const save_btn = document.getElementById('next1');
const profile_btn = document.getElementById('profile');
const tariffs_btn = document.getElementById('tariffs');

const day_of_birth = document.getElementById('day');
const month_of_birth = document.getElementById('month');
const year_of_birth = document.getElementById('year');
const time_of_birth = document.getElementById('birthtime');
const birth_city = document.getElementById('birthcity');
const birth_country = document.getElementById('birthcountry');
const sign = document.getElementById('sign');
const current_country = document.getElementById("current_country");
const current_city = document.getElementById("current_city");
const distance = document.getElementById("distance");
const orientation_field = document.getElementById("orientation");
const searching = document.getElementById("searching");
const status_field = document.getElementById("status");
const older_gap = document.getElementById("gapage");
const younger_gap = document.getElementById("agegap");

const gives = document.querySelector(".give");
const show_hide_appearance = document.querySelector(".your_look_important");

const my_appearance = document.querySelector(".my-appearance");
const height = document.querySelector(".height");
const physique = document.querySelector(".physique");
const hair_color = document.querySelector(".hair_color");
const hair_type = document.querySelector(".hair_type");
const eye_color = document.querySelector(".eye_color");
const skin_color = document.querySelector(".skin_color");
const face_type = document.querySelector(".face_type");
const tattoos = document.querySelector(".tattoos");

const show_hide_character = document.querySelector(".your_char_important");
const my_character = document.querySelector(".my-character");

const gets = document.querySelector(".get");

const show_hide_part_appearance = document.querySelector(".partner_looks_important");
const partner_appearance = document.querySelector(".partner-appearance");
const partner_height = document.querySelector(".partner_height");
const partner_physique = document.querySelector(".partner_physique");
const partner_hair_color = document.querySelector(".partner_hair_color");
const partner_hair_type = document.querySelector(".partner_hair_type");
const partner_eye_color = document.querySelector(".partner_eye_color");
const partner_skin_color = document.querySelector(".partner_skin_color");
const partner_face_type = document.querySelector(".partner_face_type");
const partner_tattoos = document.querySelector(".partner_tattoos");

const show_hide_part_character = document.querySelector(".partner_char_important");
const partner_character = document.querySelector(".partner-character");

const interests = document.querySelector(".evening");
const moral_values = document.querySelector(".moral");
const about_me = document.getElementById("myself");

function save_form(){
    // let photo = photo_input.files[0];
    // что я могу предложить другому человеку
    let give_checkbox = gives.querySelectorAll('input[type=checkbox]:checked');
    
    let show_hide_appearance_radio = show_hide_appearance.querySelector('input[type=radio]:checked');
    // моя внешность
    let height_radio = height.querySelector('input[type=radio]:checked');
    let physique_radio = physique.querySelector('input[type=radio]:checked');
    let hair_color_radio = hair_color.querySelector('input[type=radio]:checked');
    let hair_type_radio = hair_type.querySelector('input[type=radio]:checked');
    let eye_color_radio = eye_color.querySelector('input[type=radio]:checked');
    let skin_color_radio = skin_color.querySelector('input[type=radio]:checked');
    let face_type_radio = face_type.querySelector('input[type=radio]:checked');
    let tattoos_radio = tattoos.querySelector('input[type=radio]:checked');
    
    let show_hide_character_radio = show_hide_character.querySelector('input[type=radio]:checked');
    // мой характер
    let my_character_checkbox = my_character.querySelectorAll('input[type=checkbox]:checked');


    // что я хочу получить от другого человека
    let get_checkbox = gets.querySelectorAll('input[type=checkbox]:checked');
    
    let show_hide_part_appearance_radio = show_hide_part_appearance.querySelector('input[type=radio]:checked');
    // внешность другого человека
    let partner_height_radio = partner_height.querySelector('input[type=radio]:checked');
    let partner_physique_radio = partner_physique.querySelector('input[type=radio]:checked');
    let partner_hair_color_radio = partner_hair_color.querySelector('input[type=radio]:checked');
    let partner_hair_type_radio = partner_hair_type.querySelector('input[type=radio]:checked');
    let partner_eye_color_radio = partner_eye_color.querySelector('input[type=radio]:checked');
    let partner_skin_color_radio = partner_skin_color.querySelector('input[type=radio]:checked');
    let partner_face_type_radio = partner_face_type.querySelector('input[type=radio]:checked');
    let partner_tattoos_radio = partner_tattoos.querySelector('input[type=radio]:checked');

    let show_hide_part_character_radio = show_hide_part_character.querySelector('input[type=radio]:checked');
    // характер другого человека
    let partner_character_checkbox = partner_character.querySelectorAll('input[type=checkbox]:checked');
    
    // мои интересы
    let interests_checkbox = interests.querySelectorAll('input[type=checkbox]:checked');
    
    let moral_values_radio = moral_values.querySelector('input[type=radio]:checked');
    let info_about_me = about_me.value;
    
    if (!info_about_me) {
        info_about_me = (sex.value == "Женский") ? "ASTRO LOVE знает обо мне больше, чем я сама 😉" : "ASTRO LOVE знает обо мне больше, чем я сам 😉";
    }

    let error = false;
    let error_list = [];
    
    if (!initData) {
        error = true;
        alert("Ошибка идентификации! Зайдите в приложение через Telegram!");
        return;
    }
    
    if (!named.value || !sex.value || !social.value || !social_type.value){
        error = true;
        error_list.push("Личная информация");
    }
    
    // if (!photo){
    //     error = true;
    //     error_list.push("Загрузка фото");
    // }
    
    if (!day_of_birth.value || !month_of_birth.value || !year_of_birth.value || !time_of_birth.value){
        error = true;
        error_list.push("Дата рождения");
    }
    
    if (!birth_city.value || !birth_country.value){
        error = true;
        error_list.push("Место рождения");
    }
    
    if (!sign.value){
        error = true;
        error_list.push("Знак зодиака");
    }
    
    if (!current_country.value || !current_city.value){
        error = true;
        error_list.push("Текущее местоположение");
    }
    
    if (!distance.value){
        error = true;
        error_list.push("Отношения на расстоянии");
    }
    if (!orientation_field.value){
        error = true;
        error_list.push("Ориентация");
    }
    if (!status_field.value){
        error = true;
        error_list.push("Ваш статус");
    }
    
    if (!searching.value){
        error = true;
        error_list.push("Цель поиска");
    }
    
    if (!older_gap.value || !younger_gap.value){
        error = true;
        error_list.push("Допустимая разница в возрасте");
    }
    
    let give_str = "";
    if (give_checkbox.length){
        const give_list = Array.from(give_checkbox).map(gt => gt.value);
        give_str = give_list.join(", ");
    }
    else{
        error = true;
        error_list.push("Что я могу предложить человеку");
    }
    
    let my_appearance_str = "";
    if (show_hide_appearance_radio !== null) {
        const selected_value = show_hide_appearance_radio.value;
        if (selected_value == "Указать") {
            const appearanceRadios = [
                height_radio,
                physique_radio, 
                hair_color_radio,
                hair_type_radio,
                eye_color_radio,
                skin_color_radio,
                face_type_radio,
                tattoos_radio
            ];
            const allRadiosSelected = appearanceRadios.every(radio => radio !== null);
            
            if (allRadiosSelected) {
                my_appearance_str = appearanceRadios.map(radio => radio.value).join(", ");
            } else {
                error = true;
                error_list.push("Описание своей внешности");
            }
        } else if (selected_value == "Пропустить"){
            const app_radios = my_appearance.querySelectorAll('input[type=radio]');
            app_radios.forEach(radio => radio.checked = false);
            my_appearance_str = "";
        }
    }

    let my_character_str = "";
    if (show_hide_character_radio !== null) {
        const selected_value = show_hide_character_radio.value;
        if (selected_value == "Указать") {
            if (my_character_checkbox.length > 0) {
                const my_character_list = Array.from(my_character_checkbox).map(mc => mc.value);
                my_character_str = my_character_list.join(", ");
            } else {
                error = true;
                error_list.push("Описание своего характера");
            }
        }else if (selected_value == "Пропустить"){
            my_character_str = "";
        }
    }
    
    let get_str = "";
    if (get_checkbox.length){
        const get_list = Array.from(get_checkbox).map(gt => gt.value);
        get_str = get_list.join(", ");

    } else{
        error = true;
        error_list.push("Что я хочу получить от человека");
    }

    let partner_appearance_str = "";
    if (show_hide_part_character_radio !== null) {
        const selected_value = show_hide_part_appearance_radio.value;
        if (selected_value == "Указать") {
            // Создаем массив всех radio-переменных
            const app_part_values = [
                partner_height_radio,
                partner_physique_radio,
                partner_hair_color_radio,
                partner_hair_type_radio,
                partner_eye_color_radio,
                partner_skin_color_radio,
                partner_face_type_radio,
                partner_tattoos_radio
            ];
            
            // Проверяем, что все не null
            const all_selected = app_part_values.every(radio => radio !== null);
            
            if (all_selected) {
                // Извлекаем значения из выбранных radio-кнопок
                partner_appearance_str = app_part_values.map(radio => radio.value).join(", ");
            } else {
                error = true;
                error_list.push("Описание внешности партнёра");
            }
        }else if (selected_value == "Пропустить"){
            partner_appearance_str = "";
        }
    }
    
    let partner_character_str = "";
    if (show_hide_part_character_radio !== null) {
        const selected_value = show_hide_part_character_radio.value;
        if (selected_value == "Указать") {
            if (partner_character_checkbox.length > 0) {
                const partner_character_list = Array.from(partner_character_checkbox).map(pc => pc.value);
                partner_character_str = partner_character_list.join(", ");
            } else {
                error = true;
                error_list.push("Описание характера партнёра");
            }        
        }else if (selected_value == "Пропустить"){
            partner_character_str = "";
        }
    }
    
    let interests_str = "";
    if (interests_checkbox.length){
        let interests_list = [];
        
        interests_checkbox.forEach((is) => {
            interests_list.push(is.value);
        });

        interests_str = interests_list.join(", ");
    }
    
    
    if (!error) {
        save_btn.disabled = true;
        save_btn.innerText = 'Подождите, сохраняем анкету ...';
        
        let social_info = social_type.value + ", " + social.value;
        let birth_dt = day_of_birth.value + "." + month_of_birth.value + "." + year_of_birth.value + " " + time_of_birth.value;
        let birth_place = birth_country.value + ", " + birth_city.value;
        let current_place = current_country.value + ", " + current_city.value;
        
        let min_older, max_older, min_younger, max_younger;
        
        
        if (older_gap.value == 'Категорическое нет'){
            min_older = 0;
            max_older = 0;
        } else if (older_gap.value == 'до 5 лет'){
            min_older = 0;
            max_older = 5;
        } else if (older_gap.value == '5-10 лет'){
            min_older = 5;
            max_older = 10;
        } else if (older_gap.value == 'до 10 лет'){
            min_older = 0;
            max_older = 10;
        } else if (older_gap.value == 'Не имеет значения'){
            min_older = 0;
            max_older = 50;
        }
        if (younger_gap.value == 'Категорическое нет'){
            min_younger = 0;
            max_younger = 0;
        } else if (younger_gap.value == 'до 5 лет'){
            min_younger = 0;
            max_younger = 5;
        } else if (younger_gap.value == '5-10 лет'){
            min_younger = 5;
            max_younger = 10;
        } else if (younger_gap.value == 'до 10 лет'){
            min_younger = 0;
            max_younger = 10;
        } else if (younger_gap.value == 'Не имеет значения'){
            min_younger = 0;
            max_younger = 50;
        }
        
        let data = {
            'init': String(initData),
            'form': { 
                'name': named.value,
                'sex': sex.value,
                'social': social_info,
                'birth_dt': birth_dt,
                'birth_place': birth_place,
                'sign': sign.value,
                'location': current_place, 
                'distance': distance.value,
                'orientation': orientation_field.value,
                'searching': searching.value,
                'status': status_field.value,
                'older_gap': older_gap.value,
                'younger_gap': younger_gap.value,
                'min_older': min_older,
                'max_older': max_older,
                'min_younger': min_younger,
                'max_younger': max_younger,
                'gives': give_str,
                'my_appearance': my_appearance_str ? my_appearance_str : 'Нет описания',
                'my_character': my_character_str ? my_character_str : 'Нет описания',
                'gets': get_str,
                'partner_appearance': partner_appearance_str ? partner_appearance_str : 'Не имеет значения',
                'partner_character': partner_character_str ? partner_character_str : 'Не имеет значения',
                'interests': interests_str ? interests_str : 'Не указано',
                'moral_values': moral_values_radio ? moral_values_radio.value : 'Не указано',
                'about_me': info_about_me
            }
        };
        
        // let form_data = new FormData();
        
        // form_data.append('init', String(initData));
        // form_data.append('data', JSON.stringify(data));
        // form_data.append('file', photo);
        
        fetch('/save_form', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
        .then((response) => response.json())
        .then((data) => {
            if (data.success){
                alert(data.message);
                document.getElementById("regist2").style.display = "none";
                document.getElementById("regist3").style.display = "block";
                document.getElementById("rectangle3").style.display = "block";
                document.getElementById("return").style.display = "none";
                document.getElementById("next1").style.display = "none";
            } else {
                alert(data.message);
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });
        
    } else {
        error_str = error_list.join("\n");
        error_msg = `Перед сохранением анкеты заполните указанные поля:\n${error_str}`;
        alert(error_msg);
    } 
}


function select_profile() {
    let path = '/profile';
    window.location.href = path;
}

function select_tariffs() {
    let path = '/tariffs';
    window.location.href = path;
}


save_btn.addEventListener('click', save_form);
profile_btn.addEventListener('click', select_profile);
tariffs_btn.addEventListener('click', select_tariffs);

