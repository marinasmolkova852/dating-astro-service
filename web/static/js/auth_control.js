const initData = window.Telegram.WebApp.initData; // Получаем данные из Telegram Web App

function send_user_data(){
    // const current_page = window.location.pathname;
    // const auth_url = current_page + '?auth=' + encodeURIComponent(initData);
    const str_init = String(initData);
    let data = {
        'init': str_init
    };
    // fetch(`/init?auth=${encodeURIComponent(initData)}`)

    fetch('/init', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then((response) => {
        if (response.redirected){
            window.location.href = response.url;
        }
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

if (initData) send_user_data();

