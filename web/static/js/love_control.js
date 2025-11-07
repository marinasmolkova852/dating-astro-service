const know_btn = document.getElementById('much');
const birth_date_input = document.getElementById('date');


function send_birth_date(){
    let birth_date = birth_date_input.value;
    
    if (birth_date){
        fetch('/calculate_love', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({'birth_date': birth_date}),
        })
        .then((response) => response.json())
        .then((data) => {
            if (data.status){
                document.querySelector(".heart-clip").checked = true;
                setTimeout(() => {
                    let path = "/result_love";
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
        alert("Заполните дату рождения!");
    }
}

know_btn.addEventListener("click", send_birth_date);