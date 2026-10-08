
const chat = document.getElementById("chat");
const form = document.getElementById("composer");
const input = document.getElementById("message");
const fileInput = document.getElementById("fileInput");
const imageInput = document.getElementById("imageInput");
const attachments = document.getElementById("attachments");
let uploadedImages = [];

function setPrompt(text){ input.value=text; input.focus(); resize(); }
function focusImage(){ setPrompt("crea una imagen de "); input.focus(); }

function newChat(){
  chat.innerHTML=`<div class="welcome"><div class="welcome-icon">✦</div><h1>¿En qué puedo ayudarte?</h1><p>Nuevo chat iniciado.</p></div>`;
  uploadedImages=[]; attachments.innerHTML="";
}

function toggleTheme(){ document.body.classList.toggle("dark"); }

function resize(){input.style.height="auto";input.style.height=Math.min(input.scrollHeight,160)+"px";}
input.addEventListener("input",resize);
input.addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();form.requestSubmit();}});

fileInput.addEventListener("change",()=>uploadFiles(fileInput.files,false));
imageInput.addEventListener("change",()=>uploadFiles(imageInput.files,true));

async function uploadFiles(files,isImage){
  for(const file of files){
    const fd=new FormData(); fd.append("file",file);
    const res=await fetch("/upload",{method:"POST",body:fd});
    const data=await res.json();
    if(res.ok){
      const chip=document.createElement("span"); chip.className="file-chip";
      chip.textContent=(isImage?"🖼️ ":"📄 ")+data.name;
      attachments.appendChild(chip);
      if(isImage) uploadedImages.push(data.local_name);
    }else alert(data.detail||"No se pudo subir el archivo.");
  }
  fileInput.value=""; imageInput.value="";
}

function addMessage(role,text,html=false){
  const row=document.createElement("div"); row.className=`msg ${role}`;
  row.innerHTML=`<div class="avatar">${role==="user"?"T":"✦"}</div><div class="bubble"></div>`;
  const b=row.querySelector(".bubble");
  if(html)b.innerHTML=text; else b.textContent=text;
  chat.appendChild(row); chat.scrollTop=chat.scrollHeight; return row;
}

function loading(){
  return addMessage("assistant",'<div class="loading"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>',true);
}

form.addEventListener("submit",async e=>{
  e.preventDefault();
  const text=input.value.trim();
  if(!text && !uploadedImages.length)return;
  if(text.toLowerCase().startsWith("crea una imagen")||text.toLowerCase().startsWith("genera una imagen")){
    await generateImage(text); return;
  }
  addMessage("user",text||"Analiza las imágenes adjuntas.");
  input.value=""; resize();
  const wait=loading();
  const fd=new FormData(); fd.append("message",text); fd.append("image_names",uploadedImages.join(","));
  try{
    const res=await fetch("/chat",{method:"POST",body:fd});
    const data=await res.json(); wait.remove();
    if(!res.ok) throw new Error(data.detail||"Error");
    addMessage("assistant",data.answer);
  }catch(err){wait.remove();addMessage("assistant","Error: "+err.message);}
  uploadedImages=[];
  attachments.innerHTML="";
});

async function generateImage(optionalPrompt){
  const prompt=(optionalPrompt||input.value).trim();
  if(!prompt){setPrompt("crea una imagen de ");return;}
  addMessage("user",prompt);
  input.value="";resize();
  const wait=loading();
  const fd=new FormData();fd.append("prompt",prompt);
  try{
    const res=await fetch("/generate-image",{method:"POST",body:fd});
    const data=await res.json();wait.remove();
    if(!res.ok)throw new Error(data.detail||"No se pudo generar la imagen.");
    addMessage("assistant",`<p>Imagen generada:</p><img src="${data.url}" alt="Imagen generada">`,true);
  }catch(err){wait.remove();addMessage("assistant","Error: "+err.message);}
}
