const count_btn = document.getElementById('count');
const bd_input_one = document.getElementById('birth_date_one');
const bd_input_two = document.getElementById('birth_date_two');


// function validateDateAdvanced(dateString) {
//     // Проверка формата
//     if (!/^\d{2}\.\d{2}\.\d{4}$/.test(dateString)) {
//         return false;
//     }
    
//     // Разделяем на части
//     const parts = dateString.split('.');
//     const day = parseInt(parts[0], 10);
//     const month = parseInt(parts[1], 10);
//     const year = parseInt(parts[2], 10);
    
//     // Проверяем диапазоны
//     if (year < 1899 || year > 2151) {
//         return false;
//     }
    
//     if (month < 1 || month > 12) {
//         return false;
//     }
    
//     // Проверяем дни в месяце
//     const daysInMonth = new Date(year, month, 0).getDate();
//     if (day < 1 || day > daysInMonth) {
//         return false;
//     }
    
//     return true;
// }

function send_birth_dates(){
    let birth_date_one = bd_input_one.value;
    let birth_date_two = bd_input_two.value;
    
    if (birth_date_one && birth_date_two){
        fetch('/calculate_speed', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({'birth_date_one': birth_date_one, 'birth_date_two': birth_date_two,}),
        })
        .then((response) => response.json())
        .then((data) => {
            if (data.status){
                document.querySelector(".arrow").classList.toggle("arrow-rotate"); 
                setTimeout(() => {
                    let path = "/result_speed";
                    window.location.href = path;
                }, 2500);
            } else {
                alert(data.message);
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    
    } else {
        alert("Заполните все поля!");
    }
}

count_btn.addEventListener("click", send_birth_dates);