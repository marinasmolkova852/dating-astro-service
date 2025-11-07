const add_photo_btn = document.getElementById("addPhotoBtn");
const modal = document.getElementById("modal");
const choose_file_btn = document.getElementById("chooseFileBtn");
const file_input = document.getElementById("fileInput");
const hide_btn = document.getElementById("hide_form");
const show_btn = document.getElementById("show_form");


add_photo_btn.addEventListener("click", () => {
  modal.style.display = "flex";
});

choose_file_btn.addEventListener("click", () => {
  file_input.click();
});

file_input.addEventListener("change", () => {
  const file = file_input.files[0];
  if (file && file.size > 5 * 1024 * 1024) {
    alert("Файл слишком большой! Максимум 5 МБ.");
  } else if (file) {
    alert(`Загрузка фото в профиль скоро будет доступна!`);
    modal.style.display = "none";
  }
});

modal.addEventListener("click", (e) => {
  if (e.target === modal) {
    modal.style.display = "none";
  }
});


function hide_form(){
    let status = 'hide';
    
    fetch('/hide_form', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(status),
    })
    .then((response) => response.json())
    .then((data) => {
        if (data.status){
            alert(data.message);
            window.location.reload();
        } 
        else{
            alert(data.message);
        }
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

function show_form(){
    let status = 'active';
    
    fetch('/show_form', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(status),
    })
    .then((response) => response.json())
    .then((data) => {
        if (data.status){
            alert(data.message);
            window.location.reload();
            
        } 
        else{
            alert(data.message);
        }
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

if (hide_btn) hide_btn.addEventListener("click", hide_form);
if (show_btn) show_btn.addEventListener("click", show_form);